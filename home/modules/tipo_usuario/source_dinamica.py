"""
Source dinámico: itera todas las fuentes activas (`FuenteTipoUsuario`) en
orden de `prioridad` y resuelve el código SIESA usando la tabla + columnas
configuradas en cada una.

Reemplaza a `source_mutualser.py` — la fuente MUTUAL_VIEW ahora vive como
fila en `home_fuentetipousuario` (seed en migración `0050`).

Seguridad:
  - El password se mantiene cifrado en DB y se descifra solo en runtime para
    armar el connection string. Nunca se loguea.
  - Los identificadores SQL (`tabla`, `campo_documento`, `campo_regimen`,
    `campo_tipo_afiliado`, y `campo_tipo_documento` si está configurado) se
    validan contra una whitelist regex antes de armar la query. Sin esta
    validación el módulo sería una puerta a SQL injection — el conector
    pyodbc no parametriza con `?` en los nombres de objeto, así que la única
    defensa es la sanitización previa.
  - El documento de paciente y el tipo de documento también se sanitizan
    (solo alfanumérico).

Filtro opcional por tipo de documento:
  - Si la fuente tiene `campo_tipo_documento` configurado y el caller pasa
    `tipo_documento`, la consulta agrega `AND campo_tipo_documento = '...'`.
  - Si la fuente no tiene el campo configurado → comportamiento legacy
    (filtra solo por documento).

Pool de conexiones:
  - Thread-local indexed por `fuente_id`. Una conexión por (hilo × fuente).
  - Versionado por `fuente.updated_at`: si la fuente se editó (ej. cambio
    de password) la conexión cacheada se descarta y se reabre en la próxima
    consulta.
  - Reconnect-on-error con un reintento, igual al patrón de `conexionBD.py`.
"""

import logging
import re
import threading
from collections import defaultdict

import pyodbc

from home.modules.crypto import decrypt
from home.modules.tipo_usuario.homologacion import (
    homologar_siesa,
    normalizar_tipo_afiliado,
)


logger = logging.getLogger(__name__)


# Documentos y tipos de documento: siempre alfanuméricos.
_RX_DOC = re.compile(r"[^A-Za-z0-9]")

# Identificadores SQL permitidos: letra/_ inicial, alfanumérico/_ después,
# hasta 2 puntos de separación (DB.schema.tabla). Sin corchetes, comillas,
# punto y coma o espacios — estrictamente impide inyección por el lado del
# nombre de objeto.
_RX_SQL_IDENT = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*){0,2}$"
)

# Tamaño máximo del IN (...) por chunk para no generar planes gigantes.
_BATCH_SIZE = 500


# ─── Pool de conexiones ──────────────────────────────────────────────────────

_thread_local = threading.local()


def _sanitize_doc(documento) -> str:
    return _RX_DOC.sub("", str(documento or ""))


def _sanitize_tipo_doc(tipo_documento) -> str:
    """Tipo de documento: alfanumérico, normalizado a mayúsculas."""
    if not tipo_documento:
        return ""
    return _RX_DOC.sub("", str(tipo_documento)).upper()


def _validar_identificadores(fuente) -> None:
    """Lanza ValueError si algún identificador no pasa la whitelist."""
    requeridos = ("tabla", "campo_documento", "campo_regimen", "campo_tipo_afiliado")
    for campo in requeridos:
        valor = getattr(fuente, campo, "") or ""
        if not _RX_SQL_IDENT.match(valor):
            raise ValueError(
                f"Fuente '{fuente.nombre}': identificador SQL inválido en "
                f"{campo}={valor!r}. Sólo letras, dígitos, guion bajo y hasta "
                "dos puntos de separación."
            )
    # Campo opcional — solo validar si la fuente lo configuró.
    campo_tipo_doc = (getattr(fuente, "campo_tipo_documento", "") or "").strip()
    if campo_tipo_doc and not _RX_SQL_IDENT.match(campo_tipo_doc):
        raise ValueError(
            f"Fuente '{fuente.nombre}': identificador SQL inválido en "
            f"campo_tipo_documento={campo_tipo_doc!r}. Sólo letras, dígitos, "
            "guion bajo y hasta dos puntos de separación."
        )


def _build_conn_string(fuente, password: str) -> str:
    driver = (fuente.driver or "SQL Server").strip()
    return (
        f"DRIVER={{{driver}}};"
        f"SERVER={fuente.servidor};"
        f"UID={fuente.usuario};"
        f"PWD={password}"
    )


def _get_pool() -> dict:
    pool = getattr(_thread_local, "conns", None)
    if pool is None:
        pool = {}
        _thread_local.conns = pool
    return pool


def _close_pool_entry(fuente_id: int) -> None:
    pool = _get_pool()
    entry = pool.pop(fuente_id, None)
    if entry is None:
        return
    _, conn = entry
    try:
        conn.close()
    except Exception:
        pass


def _get_conn(fuente) -> "pyodbc.Connection":
    """Conexión por (hilo × fuente). Versionada por `fuente.updated_at`."""
    pool = _get_pool()
    version_actual = fuente.updated_at

    entry = pool.get(fuente.id)
    if entry is not None:
        version_cacheada, conn = entry
        if version_cacheada == version_actual:
            return conn
        # Fuente editada — descartar conexión vieja.
        _close_pool_entry(fuente.id)

    password = decrypt(fuente.password_encrypted)
    conn = pyodbc.connect(_build_conn_string(fuente, password), autocommit=True)
    pool[fuente.id] = (version_actual, conn)
    return conn


def _ejecutar(fuente, query: str) -> list:
    """Ejecuta una query con reintento de reconexión si la conexión cayó."""
    try:
        conn = _get_conn(fuente)
        cursor = conn.cursor()
        cursor.execute(query)
        return [list(row) for row in cursor.fetchall()]
    except pyodbc.Error as primer_error:
        logger.warning(
            "pyodbc.Error en fuente '%s', reconectando: %s",
            fuente.nombre, primer_error,
        )
        _close_pool_entry(fuente.id)
        conn = _get_conn(fuente)
        cursor = conn.cursor()
        cursor.execute(query)
        return [list(row) for row in cursor.fetchall()]


# ─── Lectura de fuentes activas ──────────────────────────────────────────────

def _fuentes_activas() -> list:
    """Lista ordenada por prioridad (menor primero). Lectura diferida."""
    from home.models import FuenteTipoUsuario
    return list(
        FuenteTipoUsuario.objects
        .filter(activa=True)
        .order_by("prioridad", "id")
    )


def _campo_tipo_doc(fuente) -> str:
    """Devuelve `campo_tipo_documento` saneado de la fuente, o '' si no aplica."""
    return (getattr(fuente, "campo_tipo_documento", "") or "").strip()


# ─── API pública ─────────────────────────────────────────────────────────────

def obtener(documento, tipo_documento: str | None = None) -> str:
    """
    Consulta un documento contra cada fuente activa en cascada.

    Si la fuente tiene `campo_tipo_documento` configurado y el caller pasa
    `tipo_documento`, la consulta agrega `AND campo_tipo_documento = '...'`.

    Devuelve el primer código SIESA que se logre resolver, o `''` si ninguna
    fuente lo tiene. Errores por fuente individual se loguean y no detienen
    la cascada — si TODAS fallan con excepción y ninguna resolvió, se
    propaga la primera excepción.
    """
    doc = _sanitize_doc(documento)
    if not doc:
        return ""

    tipo_doc = _sanitize_tipo_doc(tipo_documento)
    primera_excepcion: Exception | None = None

    for fuente in _fuentes_activas():
        try:
            _validar_identificadores(fuente)
            where_extra = ""
            campo_tipo_doc = _campo_tipo_doc(fuente)
            if campo_tipo_doc and tipo_doc:
                where_extra = f" AND {campo_tipo_doc} = '{tipo_doc}'"
            query = (
                f"SELECT TOP 1 {fuente.campo_regimen}, {fuente.campo_tipo_afiliado} "
                f"FROM {fuente.tabla} "
                f"WHERE {fuente.campo_documento} = '{doc}'{where_extra}"
            )
            rows = _ejecutar(fuente, query) or []
            if not rows:
                continue
            regimen, tipo_raw, *_ = list(rows[0]) + [None] * 2
            tipo = normalizar_tipo_afiliado(tipo_raw, fuente_id=fuente.id)
            siesa = homologar_siesa(regimen, tipo, fuente_id=fuente.id)
            if siesa:
                return siesa
        except Exception as e:
            if primera_excepcion is None:
                primera_excepcion = e
            logger.warning(
                "Fuente '%s' falló consultando %s: %s: %s",
                fuente.nombre, doc, type(e).__name__, e,
            )
            continue

    if primera_excepcion is not None:
        raise primera_excepcion
    return ""


def _normalizar_entrada_batch(entradas):
    """
    Acepta `list[str]` o `list[tuple[str, str|None]]`. Devuelve:
      - `pares_saneados`: lista deduplicada de `(doc_saneado, tipo_doc_upper)`.
      - `original_por_saneado`: dict `(doc_saneado, tipo_doc_upper) → key_original`
        donde `key_original` es la forma con la que el caller debe recibir el
        resultado: el doc string crudo si la entrada era `list[str]`, o la
        tupla `(doc_crudo, tipo_doc_crudo)` si la entrada era `list[tuple]`.

    Si dos entradas crudas distintas sanean al mismo par, gana la primera
    (semántica equivalente a `setdefault`).
    """
    pares: list[tuple[str, str]] = []
    original_por_saneado: dict = {}
    for item in entradas:
        if isinstance(item, (tuple, list)):
            doc_raw = item[0] if item else None
            tipo_raw = item[1] if len(item) > 1 else None
            key_original = (str(doc_raw) if doc_raw is not None else "",
                            (str(tipo_raw).strip().upper() if tipo_raw else ""))
        else:
            doc_raw, tipo_raw = item, None
            key_original = str(doc_raw) if doc_raw is not None else ""
        doc = _sanitize_doc(doc_raw)
        if not doc:
            continue
        tipo_doc = _sanitize_tipo_doc(tipo_raw)
        saneado = (doc, tipo_doc)
        if saneado in original_por_saneado:
            continue
        original_por_saneado[saneado] = key_original
        pares.append(saneado)
    return pares, original_por_saneado


def obtener_batch(entradas) -> dict:
    """
    Consulta múltiples documentos contra fuentes activas en cascada.

    Acepta:
      - `list[str]` (legacy): solo documentos, sin tipo. Resultado keyed por
        `str(documento)`.
      - `list[tuple[doc, tipo_doc]]`: pares documento + tipo. Resultado keyed
        por la tupla `(doc_str, tipo_doc_upper)`. `tipo_doc` puede venir como
        `None`/`""` y se trata como sin filtro.

    Si la fuente tiene `campo_tipo_documento` configurado y el par viene con
    tipo_doc no vacío, la consulta filtra por `documento IN (...) AND
    tipo_documento = '...'` (un query por valor distinto de tipo_doc dentro
    del lote pendiente para esa fuente).

    Devuelve solo entradas resueltas. La cascada va resolviendo pares: la
    primera fuente intenta resolver todos, las siguientes solo los que
    quedaron pendientes.

    Si TODAS las fuentes fallan con excepción y nada se resolvió, propaga la
    primera excepción.
    """
    if not entradas:
        return {}

    pares, original_por_saneado = _normalizar_entrada_batch(entradas)
    if not pares:
        return {}

    resultado: dict = {}
    pendientes: set[tuple[str, str]] = set(pares)
    primera_excepcion: Exception | None = None

    for fuente in _fuentes_activas():
        if not pendientes:
            break
        try:
            _validar_identificadores(fuente)
            campo_tipo_doc = _campo_tipo_doc(fuente)

            # Agrupar pendientes por tipo_doc solo si la fuente lo usa.
            # Si no, todo va en un único grupo (tipo_doc ignorado).
            grupos: dict[str, list[tuple[str, str]]] = defaultdict(list)
            if campo_tipo_doc:
                for par in pendientes:
                    grupos[par[1]].append(par)
            else:
                grupos[""] = list(pendientes)

            for tipo_doc_grupo, pares_grupo in grupos.items():
                docs_grupo = [doc for doc, _ in pares_grupo]
                where_extra = ""
                if campo_tipo_doc and tipo_doc_grupo:
                    where_extra = f" AND {campo_tipo_doc} = '{tipo_doc_grupo}'"

                for i in range(0, len(docs_grupo), _BATCH_SIZE):
                    chunk = docs_grupo[i: i + _BATCH_SIZE]
                    docs_in = ", ".join(f"'{d}'" for d in chunk)
                    query = (
                        f"SELECT {fuente.campo_documento}, {fuente.campo_regimen}, "
                        f"{fuente.campo_tipo_afiliado} "
                        f"FROM {fuente.tabla} "
                        f"WHERE {fuente.campo_documento} IN ({docs_in}){where_extra}"
                    )
                    rows = _ejecutar(fuente, query) or []
                    for row in rows:
                        doc_saneado, regimen, tipo_raw, *_ = list(row) + [None] * 3
                        doc_str = _sanitize_doc(doc_saneado)
                        tipo = normalizar_tipo_afiliado(tipo_raw, fuente_id=fuente.id)
                        siesa = homologar_siesa(regimen, tipo, fuente_id=fuente.id)
                        if not siesa:
                            continue
                        # Bajo este grupo, todos los pares pendientes con
                        # este doc comparten tipo_doc_grupo.
                        par_resuelto = (doc_str, tipo_doc_grupo)
                        if par_resuelto in pendientes:
                            clave = original_por_saneado.get(par_resuelto, par_resuelto)
                            resultado[clave] = siesa
                            pendientes.discard(par_resuelto)
        except Exception as e:
            if primera_excepcion is None:
                primera_excepcion = e
            logger.warning(
                "Fuente '%s' batch falló: %s: %s",
                fuente.nombre, type(e).__name__, e,
            )
            continue

    if primera_excepcion is not None and not resultado:
        raise primera_excepcion

    return resultado


def invalidar_conexion(fuente_id: int) -> None:
    """Cierra la conexión cacheada para una fuente (llamado por signal al editar)."""
    _close_pool_entry(fuente_id)
