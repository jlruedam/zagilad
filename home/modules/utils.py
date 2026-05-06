# Python
import pandas as pd
# Zagilad
from home.modules.tipo_usuario import source_sql
from datetime import datetime, date

# Mantenido para compatibilidad con consumidores externos (ej: diag command).
_BATCH_SIZE_TIPO_USUARIO = source_sql._BATCH_SIZE


def obtener_tipo_usuario(documento):
    """
    Wrapper legacy: consulta SQL únicamente y devuelve un DataFrame
    con una sola columna (código SIESA) o vacío si no se encontró.

    Para fallback SQL→API usar `home.modules.tipo_usuario.obtener_tipo_usuario`.
    """
    siesa = source_sql.obtener(documento)
    if siesa:
        return pd.DataFrame([[siesa]])
    return pd.DataFrame()


def obtener_tipo_usuario_batch(documentos: list) -> dict:
    """
    Wrapper legacy: consulta SQL en batch. Devuelve `{str(doc): siesa}`.
    Para fallback SQL→API usar `home.modules.tipo_usuario.obtener_tipo_usuario_batch`.
    """
    return source_sql.obtener_batch(documentos)


def validar_fecha(fecha_str):
    formatos_validos = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]
    for formato in formatos_validos:
        try:
            return datetime.strptime(fecha_str, formato).date()
        except ValueError:
            continue
    raise ValueError("Formato de fecha inválido")
