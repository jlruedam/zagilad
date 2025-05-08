# Python
import pandas as pd
# Zagilad
from home.modules import conexionBD


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
