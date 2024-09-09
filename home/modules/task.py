from __future__ import absolute_import
# PYTHON
import ast,time

# CELERY
from celery import shared_task
# from celery.decorators import task
from celery.utils.log import get_task_logger

# ZAGILAD
from home.models import TipoActividad, Actividad, ParametrosAreaPrograma
from home.models import Regional, Admision, AreaPrograma, Colaborador, Carga
from home.modules import peticiones_http
from home.modules import validador_actividades
from home.modules import notificaciones_email


logger = get_task_logger(__name__)


@shared_task
def procesar_cargue_actividades(id_carga):
    inicio = time.time()
    cantidad_inconsistencias = 0
    carga = Carga.objects.get(id= id_carga)
    print(carga)
    dict_data = ast.literal_eval(carga.data)
    # resultados_cargue = []
    print("CARGA PROCESAR",carga.id)
    
    for valores in dict_data['datos']:
        error = 0
        print("*"*100)
        print(valores)
        try:
            actividad = Actividad()
            actividad.carga = carga
            actividad.tipo_fuente = "EXCEL"
            actividad.tipo_documento = valores[0]
            actividad.documento_paciente = valores[1]
            actividad.nombre_paciente = f'{valores[4]} {valores[5]} {valores[2]} {valores[3]}' 
            actividad.regional = valores[6]
            actividad.fecha_servicio = str(valores[7])
            actividad.nombre_actividad = (valores[8]).strip()
            actividad.diagnostico_p = valores[9]

            # Consultador datos del afiliado
            ruta = f"/api/SisDeta/GetDatosBasicosPaciente?NumeroIdentificacion={actividad.documento_paciente}&TipoIdentificacion={actividad.tipo_documento}"
            datos_afiliado = peticiones_http.consultar_data(ruta)

            if len(datos_afiliado['Datos']):
                # Atributos inferidos
                regional = Regional.objects.get(regional = actividad.regional)
                actividad.tipo_actividad = TipoActividad.objects.get(nombre = actividad.nombre_actividad)
                actividad.parametros_programa = ParametrosAreaPrograma.objects.get(area_programa = actividad.tipo_actividad.area, regional = regional.id)
                
                # Validar si la actividad está repetida
                if validador_actividades.valida_actividad_repectiva_paciente(actividad):
                    print("ACTIVIDAD YA SE ENCUENTRA CARGADA PARA ESTE PACIENTE")
                    actividad.inconsistencias= "⚠️ Actividad repetida"
                    cantidad_inconsistencias +=1
            else:
                actividad.inconsistencias = "⚠️" + "Paciente no está registrado en Zeus"
                cantidad_inconsistencias +=1
                print("Paciente no está registrado en Zeus")
            
        except Exception as e:
            error = e
            actividad.inconsistencias = "⚠️" + str(error)
            cantidad_inconsistencias +=1
            print(e)
    
        actividad.save()

    final = time.time()
    carga.estado = "procesada"
    carga.tiempo_procesamiento = (final - inicio)/60
    carga.cantidad_actividades_inconsistencias = cantidad_inconsistencias
    carga.cantidad_actividades_ok = carga.cantidad_actividades - carga.cantidad_actividades_inconsistencias
    carga.save()
    
    # Enviar un correo de notificación cuando termine el Cargue
    
    colaborador = Colaborador.objects.filter(usuario = carga.usuario)
    if colaborador:
        if len(colaborador[0].email):
            notificaciones_email.notificar_carga_procesada(carga, [colaborador[0].email])

    # resultados_cargue.append(valores)
    return "CARGUE PROCESADO"
