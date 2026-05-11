"""
Paquete `tipo_usuario` — orquesta la obtención del código SIESA de afiliados
de MUTUAL SER con dos fuentes, en este orden de prioridad:

1. **SQL MUTUAL_VIEW** (`DL_MS_AFILIADO_VIEW_CLEAN`) — fuente primaria, rápida y
   con datos depurados, accedida directamente sin OPENQUERY.
2. **API MUTUAL `validateRights`** — fallback autoritativo, más lento y por
   afiliado.

La fuente histórica OPR_SALUD fue archivada — ver
`docs/legacy/opr_salud_tipo_usuario.md` para detalles y cómo reactivarla.

API pública:
    obtener_tipo_usuario(documento, tipo_documento="CC") -> str
    obtener_tipo_usuario_batch(docs_tipos) -> dict

`docs_tipos` es una lista de tuplas (documento, tipo_documento) y la respuesta
es `{(str(doc), tipo_doc): codigo_siesa}`. Documentos no resueltos por
ninguna fuente NO aparecen en el dict.
"""

import logging

from home.modules.tipo_usuario import source_api, source_mutualser

logger = logging.getLogger(__name__)


def obtener_tipo_usuario(documento, tipo_documento: str = "CC") -> str:
    """
    Devuelve el código SIESA para un documento. Cascada MUTUAL_VIEW → API.
    Devuelve `''` si ninguna fuente lo resuelve.
    """
    documento_str = str(documento)
    tipo_doc_str = (tipo_documento or "CC").strip().upper() or "CC"

    # 1. MUTUAL_VIEW (primaria)
    mutualser_failed = False
    try:
        siesa = source_mutualser.obtener(documento_str)
        if siesa:
            return siesa
    except Exception as e:
        mutualser_failed = True
        logger.warning(
            "MUTUAL_VIEW falló para %s, intentando API MUTUAL: %s: %s",
            documento_str, type(e).__name__, e,
        )

    # 2. API MUTUAL (fallback)
    try:
        siesa = source_api.obtener(documento_str, tipo_doc_str)
        if siesa:
            if mutualser_failed:
                logger.info("API MUTUAL resolvió %s tras fallar MUTUAL_VIEW", documento_str)
            else:
                logger.info("API MUTUAL resolvió %s (no estaba en MUTUAL_VIEW)", documento_str)
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
      1. MUTUAL_VIEW con todos los docs (SQL directo, batch único).
      2. Los docs no resueltos por MUTUAL_VIEW → API MUTUAL (uno por uno).
      3. Si ambas fallan con excepción y nada se resolvió → re-lanza la
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
    docs_unicos = list({doc for doc, _ in pares})

    # ─── 1. MUTUAL_VIEW (primaria) ────────────────────────────────────────────
    mutualser_result: dict = {}
    try:
        mutualser_result = source_mutualser.obtener_batch(docs_unicos)
    except Exception as e:
        primera_excepcion = e
        logger.warning(
            "MUTUAL_VIEW batch falló (%s), usando API MUTUAL para todos: %s",
            type(e).__name__, e,
        )

    pendientes: list = []
    for doc, tipo_doc in pares:
        if doc in mutualser_result:
            resultado[(doc, tipo_doc)] = mutualser_result[doc]
        else:
            pendientes.append((doc, tipo_doc))

    # ─── 2. API MUTUAL (fallback) ───────────────────────────────────────────
    if pendientes:
        if primera_excepcion is not None:
            logger.warning(
                "Fallback API MUTUAL: MUTUAL_VIEW caído, consultando %s docs",
                len(pendientes),
            )
        else:
            logger.info(
                "Fallback API MUTUAL: %s docs no resueltos por MUTUAL_VIEW",
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
