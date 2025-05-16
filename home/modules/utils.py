# Python
import pandas as pd
# Zagilad
from home.modules import conexionBD
from datetime import datetime, date


def obtener_tipo_usuario(documento):
    
    query = f'''
        SELECT [ID_TIPO_AFILIADO]
            ,[TIPO_AFILIADO_HOMOLOGACION]
        FROM [DLSersocial].[dbo].[T_AFILIADO_MUTUALSER_EP]
        WHERE NRO_TIPO_IDENTIFICACION = '{documento}'
        '''
    resultado = conexionBD.conexionBD(query)
    df = pd.DataFrame(resultado)

    return df

def validar_fecha(fecha_str):
    formatos_validos = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]
    for formato in formatos_validos:
        try:
            return datetime.strptime(fecha_str, formato).date()
        except ValueError:
            continue
    raise ValueError("Formato de fecha inválido")