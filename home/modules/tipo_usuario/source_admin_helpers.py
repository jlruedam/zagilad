"""
Helpers de inspección de SQL Server para la UI admin de `FuenteTipoUsuario`.

Se usan ANTES de guardar la fuente — el wizard de creación necesita validar
credenciales, listar bases de datos, listar tablas y listar columnas sin que
la fuente exista todavía en la DB local.

Trabajan con parámetros sueltos (servidor / usuario / password / driver) en
vez de con un objeto `FuenteTipoUsuario` para permitir esto. Para fuentes ya
guardadas, el caller puede descifrar el password con `home.modules.crypto`.

Seguridad:
  - El password viaja en el body del request HTTP (POST). El servidor debe
    estar detrás de HTTPS en producción.
  - Cada conexión es one-shot: se abre, se ejecuta una sola query, se cierra.
    No se pooléa para evitar dejar credenciales arbitrarias en memoria.
  - Todas las queries son fijas y parametrizadas en cuanto a valores; los
    identificadores (cuando los hay) se validan contra una whitelist regex
    antes de armar SQL.
"""

import logging
import re

import pyodbc


logger = logging.getLogger(__name__)


# Identificadores SQL: igual al regex de source_dinamica para consistencia.
_RX_SQL_IDENT = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*){0,2}$"
)
_RX_SQL_IDENT_SIMPLE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

# Timeout corto: si el servidor no responde rápido, es un error de config.
_LOGIN_TIMEOUT_SEC = 8
_QUERY_TIMEOUT_SEC = 15


def _build_conn_string(servidor: str, usuario: str, password: str,
                       driver: str = "SQL Server", base_datos: str = "") -> str:
    parts = [
        f"DRIVER={{{(driver or 'SQL Server').strip()}}}",
        f"SERVER={servidor}",
        f"UID={usuario}",
        f"PWD={password}",
    ]
    if base_datos:
        parts.append(f"DATABASE={base_datos}")
    return ";".join(parts)


def _connect(servidor: str, usuario: str, password: str,
             driver: str = "SQL Server", base_datos: str = ""):
    if not (servidor and usuario and password):
        raise ValueError("Faltan credenciales (servidor, usuario y/o contraseña)")
    conn = pyodbc.connect(
        _build_conn_string(servidor, usuario, password, driver, base_datos),
        timeout=_LOGIN_TIMEOUT_SEC,
        autocommit=True,
    )
    conn.timeout = _QUERY_TIMEOUT_SEC
    return conn


def test_conexion(servidor: str, usuario: str, password: str,
                  driver: str = "SQL Server", base_datos: str = "") -> tuple[bool, str]:
    """
    Prueba la conexión y devuelve `(ok, mensaje)`. No expone credenciales en
    el mensaje. Ejecuta `SELECT 1` para confirmar que la sesión responde.
    """
    try:
        conn = _connect(servidor, usuario, password, driver, base_datos)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
        finally:
            conn.close()
        return True, "Conexión OK"
    except pyodbc.InterfaceError as e:
        return False, f"Driver/host no disponible: {e}"
    except pyodbc.OperationalError as e:
        return False, f"Error operacional: {e}"
    except pyodbc.ProgrammingError as e:
        return False, f"Credenciales rechazadas o error del servidor: {e}"
    except Exception as e:
        logger.exception("test_conexion error inesperado")
        return False, f"{type(e).__name__}: {e}"


def listar_bases_datos(servidor: str, usuario: str, password: str,
                       driver: str = "SQL Server") -> list[str]:
    """
    Devuelve las bases de datos visibles para el usuario, excluyendo las
    de sistema (`master`, `tempdb`, `model`, `msdb`).
    """
    conn = _connect(servidor, usuario, password, driver)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM master.sys.databases "
            "WHERE database_id > 4 "  # excluye master/tempdb/model/msdb
            "ORDER BY name"
        )
        return [row[0] for row in cursor.fetchall()]
    finally:
        conn.close()


def listar_tablas(servidor: str, usuario: str, password: str,
                  base_datos: str, driver: str = "SQL Server",
                  incluir_vistas: bool = True) -> list[str]:
    """
    Lista tablas y vistas en `base_datos` como `schema.nombre`. Requiere
    `base_datos` para acotar el scope (no se listan tablas cross-DB).
    """
    if not base_datos:
        raise ValueError("base_datos es requerida para listar tablas")
    if not _RX_SQL_IDENT_SIMPLE.match(base_datos):
        raise ValueError(
            f"base_datos inválida: {base_datos!r}. Sólo letras, dígitos y guion bajo."
        )

    conn = _connect(servidor, usuario, password, driver, base_datos)
    try:
        tipos = "('BASE TABLE', 'VIEW')" if incluir_vistas else "('BASE TABLE')"
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT TABLE_SCHEMA, TABLE_NAME "
            f"FROM [{base_datos}].INFORMATION_SCHEMA.TABLES "
            f"WHERE TABLE_TYPE IN {tipos} "
            f"ORDER BY TABLE_SCHEMA, TABLE_NAME"
        )
        return [f"{schema}.{nombre}" for schema, nombre in cursor.fetchall()]
    finally:
        conn.close()


def listar_columnas(servidor: str, usuario: str, password: str,
                    base_datos: str, tabla: str,
                    driver: str = "SQL Server") -> list[dict]:
    """
    Lista columnas de `tabla` (formato `schema.nombre` o sólo `nombre`).
    Devuelve `[{nombre, tipo, nullable}]`.
    """
    if not (base_datos and tabla):
        raise ValueError("base_datos y tabla son requeridos")
    if not _RX_SQL_IDENT_SIMPLE.match(base_datos):
        raise ValueError(f"base_datos inválida: {base_datos!r}")

    # `tabla` permite "schema.tabla" o "tabla".
    partes = tabla.split(".")
    if len(partes) == 2:
        schema, nombre_tabla = partes
    elif len(partes) == 1:
        schema, nombre_tabla = "dbo", partes[0]
    else:
        raise ValueError(f"Formato de tabla inválido: {tabla!r}")

    for ident in (schema, nombre_tabla):
        if not _RX_SQL_IDENT_SIMPLE.match(ident):
            raise ValueError(f"Identificador inválido en tabla: {ident!r}")

    conn = _connect(servidor, usuario, password, driver, base_datos)
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE "
            f"FROM [{base_datos}].INFORMATION_SCHEMA.COLUMNS "
            f"WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ? "
            f"ORDER BY ORDINAL_POSITION",
            schema, nombre_tabla,
        )
        return [
            {"nombre": nombre, "tipo": tipo, "nullable": (nullable == "YES")}
            for nombre, tipo, nullable in cursor.fetchall()
        ]
    finally:
        conn.close()
