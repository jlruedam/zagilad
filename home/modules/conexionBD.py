import pyodbc
import threading
from decouple import config


_thread_local = threading.local()


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
    except pyodbc.Error:
        # Conexión caída — cerrar, limpiar y reconectar una vez
        try:
            _thread_local.conn.close()
        except Exception:
            pass
        _thread_local.conn = None
        conn = _get_conn()
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        return [list(row) for row in rows]
