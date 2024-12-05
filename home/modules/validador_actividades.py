from home.models import Actividad

def valida_actividad_repetida_paciente(actividad, carga_actual = []):
    actividades_repetidas = Actividad.objects.filter(
        regional = actividad.regional,
        fecha_servicio = actividad.fecha_servicio,
        nombre_actividad = actividad.nombre_actividad,
        tipo_actividad = actividad.tipo_actividad,
        diagnostico_p = actividad.diagnostico_p,
        diagnostico_1 = actividad.diagnostico_1,
        diagnostico_2 = actividad.diagnostico_2,
        diagnostico_3 = actividad.diagnostico_3,
        tipo_documento = actividad.tipo_documento,
        documento_paciente = actividad.documento_paciente,
        nombre_paciente = actividad.nombre_paciente,
        medico = actividad.medico,
    )
    if carga_actual:
       repetida = actividades_repetidas.filter(carga = carga_actual).exists()
    #    print(actividades_repetidas.filter(carga = carga_actual))
    else:
        repetida = actividades_repetidas.exclude(admision = None).exists()
    return repetida
    

        
        