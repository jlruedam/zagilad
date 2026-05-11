from datetime import datetime


def validar_fecha(fecha_str):
    formatos_validos = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]
    for formato in formatos_validos:
        try:
            return datetime.strptime(fecha_str, formato).date()
        except ValueError:
            continue
    raise ValueError("Formato de fecha inválido")
