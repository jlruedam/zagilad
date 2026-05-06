"""
Source SQL: consulta tipo de usuario en OPR_SALUD vía OPENQUERY.

Trae los valores crudos (regimen + tipo_afiliado) y delega la homologación
a `homologacion.py` para mantener una única tabla de reglas SIESA.
"""

from home.modules import conexionBD
from home.modules.tipo_usuario.homologacion import homologar_siesa, normalizar_tipo_afiliado

# Tamaño máximo de chunk para OPENQUERY (límite ~8000 bytes de SQL interno).
_BATCH_SIZE = 200


def obtener(documento) -> str:
    """
    Consulta un solo documento. Devuelve el código SIESA o `''` si no se
    encontró en OPR_SALUD o si el régimen/tipo no homologa.
    """
    query = f"""
        SELECT * FROM OPENQUERY(OPR_SALUD, '
        SELECT NRO_TIPO_IDENTIFICACION, AFIC_REGIMEN, TIPO_AFILIADO, CODIGO_BDUA
        FROM OASIS.T_AFILIADO_MUTUALSER_EP
        WHERE NRO_TIPO_IDENTIFICACION = ''{documento}''
        ')
        """
    rows = conexionBD.conexionBD(query) or []
    if not rows:
        return ""
    _doc, regimen, tipo_afiliado, *_ = list(rows[0]) + [None] * 4
    return homologar_siesa(regimen, normalizar_tipo_afiliado(tipo_afiliado))


def obtener_batch(documentos: list) -> dict:
    """
    Consulta múltiples documentos en lotes. Devuelve `{str(documento): codigo_siesa}`.
    Documentos no encontrados o sin homologación válida no aparecen en el dict.
    """
    if not documentos:
        return {}

    resultado: dict = {}

    for i in range(0, len(documentos), _BATCH_SIZE):
        chunk = documentos[i: i + _BATCH_SIZE]
        docs_in = ", ".join(f"''{str(doc)}''" for doc in chunk)

        query = f"""
            SELECT * FROM OPENQUERY(OPR_SALUD, '
            SELECT NRO_TIPO_IDENTIFICACION, AFIC_REGIMEN, TIPO_AFILIADO
            FROM OASIS.T_AFILIADO_MUTUALSER_EP
            WHERE NRO_TIPO_IDENTIFICACION IN ({docs_in})
            ')
            """

        rows = conexionBD.conexionBD(query) or []
        for row in rows:
            doc, regimen, tipo_afiliado, *_ = list(row) + [None] * 3
            siesa = homologar_siesa(regimen, normalizar_tipo_afiliado(tipo_afiliado))
            if siesa:
                resultado[str(doc)] = siesa

    return resultado
