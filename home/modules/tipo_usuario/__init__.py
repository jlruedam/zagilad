"""
Paquete `tipo_usuario` — orquesta la obtención del código SIESA de afiliados
con cascada de fuentes:

1. **Fuentes SQL configurables** (`source_dinamica`) — itera todas las filas
   activas de `FuenteTipoUsuario` en orden de prioridad. La fuente histórica
   MUTUAL_VIEW vive ahora como una fila más en esa tabla (seed en migración
   `0050_seed_fuente_mutualser`).
2. **API MUTUAL `validateRights`** (`source_api`) — fallback autoritativo,
   más lento y por afiliado. Sigue hardcoded como último recurso porque es
   un canal HTTP, no SQL.

La fuente histórica OPR_SALUD fue archivada — ver
`docs/legacy/opr_salud_tipo_usuario.md`. El path que iba directo a
`MUTUALSER.dbo.DL_MS_AFILIADO_VIEW_CLEAN` (`source_mutualser.py`) fue
reemplazado por `source_dinamica.py` en Fase 2 — la configuración vive en DB.

API pública (no cambió):
    obtener_tipo_usuario(documento, tipo_documento="CC") -> str
    obtener_tipo_usuario_batch(docs_tipos) -> dict

`docs_tipos` es una lista de tuplas (documento, tipo_documento) y la respuesta
es `{(str(doc), tipo_doc): codigo_siesa}`. Documentos no resueltos por
ninguna fuente NO aparecen en el dict.
"""

import logging

from home.modules.tipo_usuario import source_api, source_dinamica

logger = logging.getLogger(__name__)


def obtener_tipo_usuario(documento, tipo_documento: str = "CC") -> str:
    """
    Devuelve el código SIESA para un documento. Cascada SQL configurable → API.
    Devuelve `''` si ninguna fuente lo resuelve.
    """
    documento_str = str(documento)
    tipo_doc_str = (tipo_documento or "CC").strip().upper() or "CC"

    # 1. Fuentes SQL configurables en cascada (primarias)
    sql_failed = False
    try:
        siesa = source_dinamica.obtener(documento_str, tipo_doc_str)
        if siesa:
            return siesa
    except Exception as e:
        sql_failed = True
        logger.warning(
            "Fuentes SQL fallaron para %s, intentando API MUTUAL: %s: %s",
            documento_str, type(e).__name__, e,
        )

    # 2. API MUTUAL (fallback)
    try:
        siesa = source_api.obtener(documento_str, tipo_doc_str)
        if siesa:
            if sql_failed:
                logger.info(
                    "API MUTUAL resolvió %s tras fallar las fuentes SQL",
                    documento_str,
                )
            else:
                logger.info(
                    "API MUTUAL resolvió %s (no estaba en ninguna fuente SQL)",
                    documento_str,
                )
            return siesa
    except Exception as e:
        logger.warning(
            "API MUTUAL falló para %s: %s: %s",
            documento_str, type(e).__name__, e,
        )

    return ""


def obtener_tipo_usuario_batch(docs_tipos) -> dict:
    """
    Resuelve un lote. Acepta:
      - lista de tuplas: [(doc, tipo_doc), ...]
      - lista de docs (str/int): se asume tipo_doc="CC" para todos

    Devuelve `{(str(doc), tipo_doc_upper): codigo_siesa}`. Solo entradas
    resueltas. Documentos no resueltos no aparecen.

    Estrategia:
      1. Fuentes SQL configurables (cascada de `FuenteTipoUsuario` activas
         por prioridad) con todos los docs únicos en un solo batch por
         fuente.
      2. Los docs no resueltos por ninguna fuente SQL → API MUTUAL (uno por
         uno).
      3. Si todas fallan con excepción y nada se resolvió → re-lanza la
         primera excepción (task.py la convierte en mensaje de inconsistencia).
    """
    if not docs_tipos:
        return {}

    # Normalizar entrada
    pares: list = []
    for item in docs_tipos:
        if isinstance(item, (tuple, list)):
            doc, tipo_doc = item[0], item[1] if len(item) > 1 else "CC"
        else:
            doc, tipo_doc = item, "CC"
        doc_str = str(doc)
        tipo_doc_str = (str(tipo_doc) if tipo_doc else "CC").strip().upper() or "CC"
        pares.append((doc_str, tipo_doc_str))

    resultado: dict = {}
    primera_excepcion: Exception | None = None
    pares_unicos = list({(doc, tipo_doc) for doc, tipo_doc in pares})

    # ─── 1. Fuentes SQL configurables (primarias) ──────────────────────────
    # Pasamos los pares (doc, tipo_doc) — source_dinamica usará tipo_doc como
    # filtro adicional solo en las fuentes que tengan `campo_tipo_documento`
    # configurado. La salida queda keyed por (doc, tipo_doc).
    sql_result: dict = {}
    try:
        sql_result = source_dinamica.obtener_batch(pares_unicos)
    except Exception as e:
        primera_excepcion = e
        logger.warning(
            "Fuentes SQL batch fallaron (%s), usando API MUTUAL para todos: %s",
            type(e).__name__, e,
        )

    pendientes: list = []
    for doc, tipo_doc in pares:
        clave = (doc, tipo_doc)
        if clave in sql_result:
            resultado[clave] = sql_result[clave]
        else:
            pendientes.append((doc, tipo_doc))

    # ─── 2. API MUTUAL (fallback) ──────────────────────────────────────────
    if pendientes:
        if primera_excepcion is not None:
            logger.warning(
                "Fallback API MUTUAL: fuentes SQL caídas, consultando %s docs",
                len(pendientes),
            )
        else:
            logger.info(
                "Fallback API MUTUAL: %s docs no resueltos por las fuentes SQL",
                len(pendientes),
            )
        try:
            api_result = source_api.obtener_batch(pendientes)
            resultado.update(api_result)
        except Exception as e:
            if primera_excepcion is None:
                primera_excepcion = e
            logger.exception("API MUTUAL también falló: %s", e)

    # Si ambas fallaron y no resolvimos nada → propagar la primera excepción.
    if primera_excepcion is not None and not resultado:
        raise primera_excepcion

    return resultado
