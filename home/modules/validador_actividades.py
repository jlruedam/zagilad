from home.models import Actividad, TipoActividad


def valida_actividad_repetida_paciente(actividad, carga_actual=None):
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
    else:
        repetida = actividades_repetidas.filter(admision__isnull=False).exists()
    return repetida
    

def validar_tipo_actividad(actividad, tipos_actividad=None):
    """
    Busca el TipoActividad que coincide con el nombre de la actividad.
    Si se pasa `tipos_actividad` (lista pre-cargada), la usa en lugar de
    consultar la BD — evita una query por cada llamada en procesamiento masivo.
    """
    if tipos_actividad is None:
        tipos_actividad = TipoActividad.objects.all()

    nombre_actividad = actividad.nombre_actividad.replace(" ", "")
    for tipo in tipos_actividad:
        if tipo.nombre.replace(" ", "") in nombre_actividad:
            return tipo
    return False
