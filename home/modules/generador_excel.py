import pandas as pd
from pandas import ExcelWriter
import datetime

#-------------------------------------------------------
def genera_excel_carga(actividades_carga):
    dict_carga = {
        'id':[],
        'tipo_fuente':[],
        'admision':[],
        'identificador':[],
        'regional':[],
        'fecha_servicio':[],
        'nombre_actividad':[],
        # 'tipo_actividad':[],
        'diagnostico_p':[],
        'diagnostico_1':[],
        'diagnostico_2':[],
        'diagnostico_3':[],
        'tipo_documento':[],
        'documento_paciente':[],
        'nombre_paciente':[],
        'parametros_programa':[],
        'carga':[],
        'inconsistencias':[],
        'created_at':[],
        'updated_at':[],
    }

    print(dict_carga.keys())

    
    for carga in actividades_carga:
        
        dict_carga["id"].append(carga.id)
        dict_carga["tipo_fuente"].append(str(carga.tipo_fuente))
        dict_carga["admision"].append(carga.admision.numero_estudio if carga.admision else "")
        dict_carga["identificador"].append(carga.identificador)
        dict_carga["regional"].append(carga.regional)
        dict_carga["fecha_servicio"].append(str(carga.fecha_servicio))
        dict_carga["nombre_actividad"].append(carga.nombre_actividad)
        # dict_carga["tipo_actividad"].append(carga.tipo_actividad)
        dict_carga["diagnostico_p"].append(carga.diagnostico_p)
        dict_carga["diagnostico_1"].append(carga.diagnostico_1)
        dict_carga["diagnostico_2"].append(carga.diagnostico_2)
        dict_carga["diagnostico_3"].append(carga.diagnostico_3)
        dict_carga["tipo_documento"].append(carga.tipo_documento)
        dict_carga["documento_paciente"].append(carga.documento_paciente)
        dict_carga["nombre_paciente"].append(carga.nombre_paciente)
        dict_carga["parametros_programa"].append(carga.parametros_programa)
        dict_carga["carga"].append(carga.carga)
        dict_carga["inconsistencias"].append(carga.inconsistencias)
        dict_carga["created_at"].append(str(carga.created_at))
        dict_carga["updated_at"].append(str(carga.updated_at))

    print(dict_carga)

    df = pd.DataFrame(dict_carga)
    # df = df[[
    #     "id","fecha_solicitud","solicitud_asociada","estado","colaborador",
    #     "tipo_operacion","observaciones", "valor", "created_at", "updated_at"
    # ]]
    df = df[dict_carga.keys()]


    writer = ExcelWriter('media//listado_actividades_carga.xlsx')
    df.to_excel(writer, 'Hoja de datos', index = False)
    writer.close()