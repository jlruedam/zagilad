"""
Paquete `tipo_usuario` — orquesta la obtención del código SIESA de afiliados
de MUTUAL SER con dos fuentes:

1. **SQL (OPR_SALUD)** — rápido, batch, fuente primaria.
2. **API (MUTUAL validateRights)** — fallback cuando SQL falla o no encuentra
   un documento.

API pública:
    obtener_tipo_usuario(documento, tipo_documento="CC") -> str
    obtener_tipo_usuario_batch(docs_tipos) -> dict

`docs_tipos` es una lista de tuplas (documento, tipo_documento) y la respuesta
es `{(str(doc), tipo_doc): codigo_siesa}`. Documentos no resueltos por
ninguna fuente NO aparecen en el dict.
"""

import logging

from home.modules.tipo_usuario import source_api, source_sql

logger = logging.getLogger(__name__)


def obtener_tipo_usuario(documento, tipo_documento: str = "CC") -> str:
    """
    Devuelve el código SIESA para un documento. Intenta SQL → API.
    Devuelve `''` si ninguna fuente lo resuelve.
    """
    documento_str = str(documento)
    tipo_doc_str = (tipo_documento or "CC").strip().upper() or "CC"

    sql_failed = False
    try:
        siesa = source_sql.obtener(documento_str)
        if siesa:
            return siesa
    except Exception as e:
        sql_failed = True
        logger.warning(
            "SQL OPR_SALUD falló para %s, intentando API MUTUAL: %s: %s",
            documento_str, type(e).__name__, e,
        )

    try:
        siesa = source_api.obtener(documento_str, tipo_doc_str)
        if siesa:
            if sql_failed:
                logger.info("API MUTUAL resolvió %s tras fallar SQL", documento_str)
            else:
                logger.info("API MUTUAL resolvió %s (no estaba en OPR_SALUD)", documento_str)
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
      1. Llama SQL con todos los docs (batch único, ~instantáneo).
      2. Los docs no resueltos por SQL → consulta API uno por uno.
      3. Si SQL falla con excepción → todos los docs van a API.
      4. Si ambas fallan → re-lanza la excepción del path API
         (task.py lo convierte en mensaje de inconsistencia).
    """
    if not docs_tipos:
        return {}

    # Normalizar entrada: aceptar lista de docs sueltos o lista de tuplas
    pares: list = []
    for item in docs_tipos:
        if isinstance(item, (tuple, list)):
            doc, tipo_doc = item[0], item[1] if len(item) > 1 else "CC"
        else:
            doc, tipo_doc = item, "CC"
        doc_str = str(doc)
        tipo_doc_str = (str(tipo_doc) if tipo_doc else "CC").strip().upper() or "CC"
        pares.append((doc_str, tipo_doc_str))

    # 1. SQL primero (batch). Match solo por documento.
    sql_result: dict = {}
    sql_failed = False
    sql_error: Exception | None = None
    docs_unicos = list({doc for doc, _ in pares})
    try:
        sql_result = source_sql.obtener_batch(docs_unicos)
    except Exception as e:
        sql_failed = True
        sql_error = e
        logger.warning(
            "SQL OPR_SALUD batch falló (%s), usando API MUTUAL para todos: %s",
            type(e).__name__, e,
        )

    # 2. Construir resultado con lo que SQL sí resolvió.
    resultado: dict = {}
    pendientes: list = []
    for doc, tipo_doc in pares:
        if doc in sql_result:
            resultado[(doc, tipo_doc)] = sql_result[doc]
        else:
            pendientes.append((doc, tipo_doc))

    # 3. Pendientes → API.
    if pendientes:
        if sql_failed:
            logger.warning(
                "Fallback API MUTUAL: SQL caído, consultando %s docs", len(pendientes),
            )
        else:
            logger.info(
                "Fallback API MUTUAL: %s docs no resueltos por OPR_SALUD",
                len(pendientes),
            )
        try:
            api_result = source_api.obtener_batch(pendientes)
            resultado.update(api_result)
        except Exception as e:
            logger.exception("API MUTUAL también falló: %s", e)
            # Si SQL ya había caído y API tampoco resolvió → propagar para
            # que task.py muestre el error original al usuario.
            if sql_failed and sql_error is not None and not resultado:
                raise sql_error from e

    return resultado
