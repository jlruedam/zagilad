"""
Source MUTUALSER: consulta tipo de usuario en `MUTUALSER.dbo.DL_MS_AFILIADO_VIEW_CLEAN`.

A diferencia de OPR_SALUD, esta vista vive en el mismo SQL Server del data lake,
así que no requiere OPENQUERY — se accede directamente por 3-part name.

Trae los valores crudos (AFIC_REGIMEN + AFIC_TIPO) y delega la homologación a
`homologacion.py` — los valores de AFIC_TIPO coinciden uno a uno con los que ya
están mapeados para OPR_SALUD (incluido el typo histórico "CABEZA DE FAMLIA"),
así que la tabla de reglas SIESA se reutiliza sin cambios.
"""

import re

from home.modules import conexionBD
from home.modules.tipo_usuario.homologacion import homologar_siesa, normalizar_tipo_afiliado

# Documentos siempre alfanuméricos (CC, TI, RC, pasaportes). Cualquier carácter
# fuera de [A-Za-z0-9] se elimina antes de armar el SQL — el conector
# `conexionBD` no soporta parámetros bindeados, así que la única defensa
# contra inyección es la sanitización previa.
_RX_DOC = re.compile(r"[^A-Za-z0-9]")

# Tamaño máximo de chunk para el IN (...). No tenemos límite de OPENQUERY aquí,
# pero mantenemos un valor conservador para evitar planes de ejecución gigantes.
_BATCH_SIZE = 500


def _sanitize(documento) -> str:
    return _RX_DOC.sub("", str(documento or ""))


def obtener(documento) -> str:
    """
    Consulta un solo documento. Devuelve el código SIESA o `''` si no se
    encontró en MUTUALSER o si el régimen/tipo no homologa.
    """
    doc = _sanitize(documento)
    if not doc:
        return ""

    query = f"""
        SELECT TOP 1 AFIC_REGIMEN, AFIC_TIPO
        FROM MUTUALSER.dbo.DL_MS_AFILIADO_VIEW_CLEAN
        WHERE AFIC_DOCUMENTO = '{doc}'
    """
    rows = conexionBD.conexionBD(query) or []
    if not rows:
        return ""
    regimen, tipo_afiliado, *_ = list(rows[0]) + [None] * 2
    return homologar_siesa(regimen, normalizar_tipo_afiliado(tipo_afiliado))


def obtener_batch(documentos: list) -> dict:
    """
    Consulta múltiples documentos en lotes. Devuelve `{str(documento): codigo_siesa}`.
    Documentos no encontrados o sin homologación válida no aparecen en el dict.
    """
    if not documentos:
        return {}

    # Sanitizar y deduplicar manteniendo el mapeo a la forma original (la clave
    # del resultado se reporta con el documento tal cual lo pidió el caller).
    docs_originales_por_saneado: dict[str, str] = {}
    for doc in documentos:
        saneado = _sanitize(doc)
        if saneado:
            docs_originales_por_saneado.setdefault(saneado, str(doc))

    if not docs_originales_por_saneado:
        return {}

    resultado: dict = {}
    saneados = list(docs_originales_por_saneado.keys())

    for i in range(0, len(saneados), _BATCH_SIZE):
        chunk = saneados[i: i + _BATCH_SIZE]
        docs_in = ", ".join(f"'{d}'" for d in chunk)

        query = f"""
            SELECT AFIC_DOCUMENTO, AFIC_REGIMEN, AFIC_TIPO
            FROM MUTUALSER.dbo.DL_MS_AFILIADO_VIEW_CLEAN
            WHERE AFIC_DOCUMENTO IN ({docs_in})
        """
        rows = conexionBD.conexionBD(query) or []
        for row in rows:
            doc_saneado, regimen, tipo_afiliado, *_ = list(row) + [None] * 3
            siesa = homologar_siesa(regimen, normalizar_tipo_afiliado(tipo_afiliado))
            if siesa:
                clave = docs_originales_por_saneado.get(str(doc_saneado), str(doc_saneado))
                resultado[clave] = siesa

    return resultado
