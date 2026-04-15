# Python
import pandas as pd
# Zagilad
from home.modules import conexionBD
from datetime import datetime, date

# Tamaño máximo de chunk para OPENQUERY (límite ~8000 bytes de SQL interno)
_BATCH_SIZE_TIPO_USUARIO = 200


def obtener_tipo_usuario(documento):

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


def obtener_tipo_usuario_batch(documentos: list) -> dict:
    """
    Consulta el tipo de usuario para múltiples documentos en lotes,
    usando una sola query IN por lote en lugar de una query por documento.

    Returns:
        dict {str(documento): id_tipo_afiliado}
        Los documentos no encontrados no aparecen en el dict.
    """
    if not documentos:
        return {}

    resultado = {}

    for i in range(0, len(documentos), _BATCH_SIZE_TIPO_USUARIO):
        chunk = documentos[i: i + _BATCH_SIZE_TIPO_USUARIO]
        # Cada valor necesita comillas dobles dentro del string de OPENQUERY: ''valor''
        docs_in = ", ".join(f"''{str(doc)}''" for doc in chunk)

        query = f"""
            SELECT * FROM OPENQUERY(OPR_SALUD, '
            SELECT
                NRO_TIPO_IDENTIFICACION,
                CASE
                    WHEN AFIC_REGIMEN = ''S'' AND TIPO_AFILIADO IN (''BENEFICIARIO'', ''ND'', ''SEGUNDO COTIZANTE'', ''CABEZA DE FAMLIA'', ''COTIZANTE'', ''f'', ''O'') THEN ''04''
                    WHEN AFIC_REGIMEN = ''C'' AND TIPO_AFILIADO = ''CABEZA DE FAMLIA'' THEN ''02''
                    WHEN AFIC_REGIMEN = ''C'' AND TIPO_AFILIADO IN (''ND'', ''f'', ''COTIZANTE'', ''SEGUNDO COTIZANTE'') THEN ''01''
                    WHEN AFIC_REGIMEN = ''C'' AND TIPO_AFILIADO = ''BENEFICIARIO'' THEN ''02''
                    WHEN AFIC_REGIMEN = ''C'' AND TIPO_AFILIADO = ''ADICIONAL'' THEN ''03''
                    ELSE AFIC_REGIMEN
                END AS ID_TIPO_AFILIADO
            FROM OASIS.T_AFILIADO_MUTUALSER_EP
            WHERE NRO_TIPO_IDENTIFICACION IN ({docs_in})
            ')
            """

        rows = conexionBD.conexionBD(query)
        # rows: [[NRO_TIPO_IDENTIFICACION, ID_TIPO_AFILIADO], ...]
        for row in rows:
            resultado[str(row[0])] = row[1]

    return resultado


def validar_fecha(fecha_str):
    formatos_validos = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"]
    for formato in formatos_validos:
        try:
            return datetime.strptime(fecha_str, formato).date()
        except ValueError:
            continue
    raise ValueError("Formato de fecha inválido")
