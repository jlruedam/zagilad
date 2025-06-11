# Python
import pandas as pd
# Zagilad
from home.modules import conexionBD
from datetime import datetime, date


def obtener_tipo_usuario(documento):
    
    # query = f'''
    #     SELECT [ID_TIPO_AFILIADO]
    #         ,[TIPO_AFILIADO_HOMOLOGACION]
    #     FROM [DLSersocial].[dbo].[T_AFILIADO_MUTUALSER_EP]
    #     WHERE NRO_TIPO_IDENTIFICACION = '{documento}'
    #     '''

    query = f"""
        SELECT * FROM OPENQUERY(OPR_SALUD, '
        SELECT 
            CASE 
                WHEN AFIC_REGIMEN = ''S'' AND TIPO_AFILIADO IN (''BENEFICIARIO'', ''ND'', ''SEGUNDO COTIZANTE'', ''CABEZA DE FAMLIA'', ''COTIZANTE'', ''f'', ''O'') THEN ''04''
                WHEN AFIC_REGIMEN = ''C'' AND TIPO_AFILIADO = ''CABEZA DE FAMLIA'' THEN ''02''
                WHEN AFIC_REGIMEN = ''C'' AND TIPO_AFILIADO IN (''ND'', ''f'', ''COTIZANTE'', ''SEGUNDO COTIZANTE'') THEN ''01''
                WHEN AFIC_REGIMEN = ''C'' AND TIPO_AFILIADO = ''BENEFICIARIO'' THEN ''02''
                WHEN AFIC_REGIMEN = ''C'' AND TIPO_AFILIADO = ''ADICIONAL'' THEN ''03''
                ELSE AFIC_REGIMEN
            END AS ID_TIPO_AFILIADO,
            CASE 
                WHEN AFIC_REGIMEN = ''S'' AND TIPO_AFILIADO IN (''BENEFICIARIO'', ''ND'', ''SEGUNDO COTIZANTE'', ''CABEZA DE FAMLIA'', ''COTIZANTE'', ''f'', ''O'') THEN ''SUBSIDIADO''
                WHEN AFIC_REGIMEN = ''C'' AND TIPO_AFILIADO = ''CABEZA DE FAMLIA'' THEN ''CONTRIBUTIVO BENEFICIARIO''
                WHEN AFIC_REGIMEN = ''C'' AND TIPO_AFILIADO IN (''ND'', ''f'', ''COTIZANTE'', ''SEGUNDO COTIZANTE'') THEN ''CONTRIBUTIVO COTIZANTE''
                WHEN AFIC_REGIMEN = ''C'' AND TIPO_AFILIADO = ''BENEFICIARIO'' THEN ''CONTRIBUTIVO BENEFICIARIO''
                WHEN AFIC_REGIMEN = ''C'' AND TIPO_AFILIADO = ''ADICIONAL'' THEN ''CONTRIBUTIVO ADICIONAL''
                ELSE AFIC_REGIMEN
            END AS TIPO_AFILIADO_HOMOLOGACION,
            CODIGO_BDUA
        FROM OASIS.T_AFILIADO_MUTUALSER_EP
        WHERE NRO_TIPO_IDENTIFICACION = ''{documento}''
        ')
        """
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