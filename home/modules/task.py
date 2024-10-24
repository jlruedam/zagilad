from __future__ import absolute_import
# PYTHON
import ast,time
import json

# CELERY
from celery import shared_task
# from celery.decorators import task
from celery.utils.log import get_task_logger

# ZAGILAD
from home.models import TipoActividad, Actividad, ParametrosAreaPrograma 
from home.models import Regional, Admision, AreaPrograma, Carga
from zeus_mirror.models import Medico
from home.modules import peticiones_http
from home.modules import validador_actividades
from home.modules import notificaciones_email
from home.modules import parametros_generales
from home.modules import admision

logger = get_task_logger(__name__)

@shared_task
def procesar_cargue_actividades(id_carga, dict_data):
    inicio = time.time()
    carga = Carga.objects.get(id= id_carga)
    try:
        for valores in dict_data['datos']:
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

                # Consultar médico
                actividad.medico = Medico.objects.get(documento = (valores[10]).strip())

                # Consultador datos del afiliado
                ruta = f"/api/SisDeta/GetDatosBasicosPaciente?NumeroIdentificacion={actividad.documento_paciente}&TipoIdentificacion={actividad.tipo_documento}"
                datos_afiliado = peticiones_http.consultar_data(ruta)

                # Validar afiliado en Zeus
                if not len(datos_afiliado['Datos']):
                    raise Exception("Paciente no está registrado en Zeus")

                # Atributos inferidos
                regional = Regional.objects.get(regional = actividad.regional)
                actividad.tipo_actividad = TipoActividad.objects.get(nombre = actividad.nombre_actividad)
                actividad.parametros_programa = ParametrosAreaPrograma.objects.get(area_programa = actividad.tipo_actividad.area, regional = regional.id)
                
                # Validar si la actividad está repetida
                if validador_actividades.valida_actividad_repetida_paciente(actividad):
                    raise Exception("Actividad ya fue admisionada")
    
            except Exception as e:
                error = e
                actividad.inconsistencias = "⚠️" + str(error)
                print(e)

            # Validar si la actividad ya se encuentra en la carga actual.
            if not validador_actividades.valida_actividad_repetida_paciente(actividad, carga):
                print("✅Actividad se guarda correctamente")
                actividad.save()

        final = time.time()
        carga.estado = "procesada"
        carga.tiempo_procesamiento = (final - inicio)/60
        carga.actualizar_info_actividades()
        carga.save()
        
        
    except Exception as e:
        print("Error al procesar la carga")
        carga.estado = "cancelada"
        carga.save()
        return "Error al procesar la carga"   
    
    if len(carga.usuario.email):
        notificaciones_email.notificar_carga_procesada(carga, [carga.usuario.email])

    # resultados_cargue.append(valores)
    return "CARGUE PROCESADO"

@shared_task
def tarea_admisionar_actividades_carga(token, id_carga, id_actividad = 0):
    respuesta = []
    carga = Carga.objects.get(id = int(id_carga))

    # Buscar las actividades sin admisión relacionadas a la carga
    actividades_carga = Actividad.objects.filter(carga = carga).filter(admision = None)
    
    if id_actividad:
        actividades_carga = Actividad.objects.filter(carga = carga, id=id_actividad).filter(admision = None)
    
    for actividad in actividades_carga:
 
        try:
            # Consultador datos del afiliado
            ruta = f"/api/SisDeta/GetDatosBasicosPaciente?NumeroIdentificacion={actividad.documento_paciente}&TipoIdentificacion={actividad.tipo_documento}"
            datos_afiliado = peticiones_http.consultar_data(ruta)

            print(datos_afiliado['Datos'])

            # Validar Si el afiliado existe
            if not len(datos_afiliado['Datos']):
                raise Exception("Paciente no está registrado en Zeus")

            # Validar si la actividad ya fue admisionada
            if validador_actividades.valida_actividad_repetida_paciente(actividad):
                raise Exception("Esta actividad ya fue admisionada")
            
            if not actividad.tipo_actividad:
                actividad.tipo_actividad = TipoActividad.objects.get(nombre = actividad.nombre_actividad)

            try:
                # AutoID y nombre del regimen del afiliado
                auto_id = datos_afiliado['Datos'][0]['autoid']
                regimen = datos_afiliado['Datos'][0]['NombreRegimen']

                # Inicializo la admisión con los parametros generales y la información de la actividad
                admision_actividad = admision.crear_admision(
                    autoid = auto_id,
                    regimen = regimen,
                    codigo_entidad = parametros_generales.CODIGO_ENTIDAD[regimen],
                    # num_usuario =parametros_generales.NUMERO_USUARIO,
                    # usuario_id = parametros_generales.IDENTIFICACION_USUARIO,
                    # usuario_nombre = parametros_generales.NOMBRE_USUARIO,
                    tipo_diag = parametros_generales.TIPO_DIAGNOSTICO,
                    actividad = actividad
                )

                try:
                    # Enviar Admisión a Zeus
                    respuesta = peticiones_http.crear_admision(admision_actividad,token)
                    print(respuesta)
                   
                    if not respuesta:
                        raise Exception("Error en la petición a Zeus")
                    
                    print(respuesta['Datos'])
                    print(respuesta['Errores'])

                    respuesta_admision = ast.literal_eval(respuesta['Datos'][0]['infoTrasaction'])
                    print("RESPUESTA ADMISIÓN:",respuesta_admision[0], type(respuesta_admision[0]))

                    # Encapsular respuesta
                    datos_error = respuesta_admision[0]['DatosEnError']
                    datos_guardados = respuesta_admision[0]['DatosGuardados']
                    print(datos_error, datos_guardados)

                    if datos_error:
                        raise Exception(datos_error[0])
                        
                    if datos_guardados:
                        numero_estudio = datos_guardados[0]['Estudio']
                        print("NÚMERO DE ESTUDIO:", numero_estudio)

                        nueva_admision = Admision()
                        nueva_admision.documento_paciente = actividad.documento_paciente
                        nueva_admision.numero_estudio = numero_estudio
                        nueva_admision.json = json.dumps(admision_actividad)
                        nueva_admision.save()

                        actividad.admision = nueva_admision
                        actividad.inconsistencias = None
                except Exception as e:
                    print("Error al enviar admisión: ", e)
                    actividad.inconsistencias = "⚠️Error al enviar admisión: "+ str(e)
            
            except Exception as e:
                print("Error al crear la admisión: ", e)
                actividad.inconsistencias = "⚠️Error al crear la admisión: "+ str(e)
                    
        except Exception as e:
            print(e)
            actividad.inconsistencias ="⚠️" + str(e)

        actividad.save()  

    carga.estado = "procesada"
    carga.actualizar_info_actividades()
    carga.save()

    # Enviar un correo de notificación cuando termine el Cargue
    if len(carga.usuario.email) and len(actividades_carga) > 1:
        print("Enviar notificiación a:", carga.usuario.email)
        notificaciones_email.notificar_carga_admisionada(carga, [carga.usuario.email])

    return f"CARGA PROCESADA"

