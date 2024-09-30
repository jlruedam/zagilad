import pandas as pd
from pandas import ExcelWriter
import datetime

#-------------------------------------------------------
def genera_excel_carga(actividades_carga):

    dict_carga = {
        'id':list(actividades_carga.values_list('id', flat=True)),
        'admision':list(actividades_carga.values_list('admision__numero_estudio', flat=True)),
        'identificador':list(actividades_carga.values_list('identificador', flat=True)),
        'regional':list(actividades_carga.values_list('regional', flat=True)),
        'fecha_servicio':list(actividades_carga.values_list('fecha_servicio', flat=True)),
        'nombre_actividad':list(actividades_carga.values_list('nombre_actividad', flat=True)),
        'diagnostico_p':list(actividades_carga.values_list('diagnostico_p', flat=True)),
        'diagnostico_1':list(actividades_carga.values_list('diagnostico_1', flat=True)),
        'diagnostico_2':list(actividades_carga.values_list('diagnostico_2', flat=True)),
        'diagnostico_3':list(actividades_carga.values_list('diagnostico_3', flat=True)),
        'tipo_documento':list(actividades_carga.values_list('tipo_documento', flat=True)),
        'documento_paciente':list(actividades_carga.values_list('documento_paciente', flat=True)),
        'nombre_paciente':list(actividades_carga.values_list('nombre_paciente', flat=True)),
        'carga':list(actividades_carga.values_list('carga', flat=True)),
        'inconsistencias':list(actividades_carga.values_list('inconsistencias', flat=True)),
    }

    df = pd.DataFrame(dict_carga)
    df = df[dict_carga.keys()]

    writer = ExcelWriter('media//listado_actividades_carga.xlsx')
    df.to_excel(writer, 'Hoja de datos', index = False)
    writer.close()