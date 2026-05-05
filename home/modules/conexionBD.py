import logging
import os
import threading

import pyodbc
from decouple import config


_thread_local = threading.local()


def _get_logger():
    """Logger dedicado a archivo plano (no depende de Django logging).
    Necesario porque los workers de Django Q se tragan logs del logger root."""
    logger = logging.getLogger("conexion_lake")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    log_dir = os.path.join(base_dir, "logs")
    os.makedirs(log_dir, exist_ok=True)
    handler = logging.FileHandler(os.path.join(log_dir, "conexion_lake.log"), encoding="utf-8")
    handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] [pid=%(process)d] %(message)s")
    )
    logger.addHandler(handler)
    return logger


_logger = _get_logger()


def _get_conn():
    """Retorna una conexión reutilizable por hilo (thread-local pooling)."""
    conn = getattr(_thread_local, 'conn', None)
    if conn is None:
        server = config('SERVER_LAKE')
        username = config('USERNAME_SERVER_LAKE')
        password = config('PASSWORD_SERVER_LAKE')
        _thread_local.conn = pyodbc.connect(
            f"DRIVER={{SQL Server}};SERVER={server};UID={username};PWD={password}",
            autocommit=True,
        )
        conn = _thread_local.conn
    return conn


def conexionBD(query):
    try:
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        return [list(row) for row in rows]
    except pyodbc.Error as primer_error:
        _logger.warning("pyodbc.Error en primer intento, reconectando: %s", primer_error)
        # Conexión caída — cerrar, limpiar y reconectar una vez
        try:
            _thread_local.conn.close()
        except Exception:
            pass
        _thread_local.conn = None
        try:
            conn = _get_conn()
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            return [list(row) for row in rows]
        except Exception as segundo_error:
            _logger.exception(
                "Reintento falló. Query (primeros 500 chars): %s", query[:500]
            )
            raise
    except Exception:
        _logger.exception("Error inesperado en conexionBD. Query (primeros 500 chars): %s", query[:500])
        raise
