from __future__ import absolute_import
# PYTHON
import ast,time
import json
import os

# CELERY
from celery import shared_task
# from celery.decorators import task
from celery.utils.log import get_task_logger
from django_q.models import Task
from django_q.models import OrmQ
from django.db.models.functions import Replace
from django.db.models import Value

# ZAGILAD
from home.models import TipoActividad, Actividad, ParametrosAreaPrograma 
from home.models import Regional, Admision, AreaPrograma, Carga
from zeus_mirror.models import Medico, Finalidad
from home.modules import peticiones_http
from home.modules import validador_actividades
from home.modules import notificaciones_email
from home.modules import parametros_generales
from home.modules import admision
from home.modules import utils

logger = get_task_logger(__name__)

def procesar_actividad(carga, valores):
    try:
        actividad = Actividad()
        actividad.datos_json = valores
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
        actividad.documento_medico = (valores[10]).strip()
        actividad.medico = Medico.objects.get(documento = (valores[10]).strip()) 

        # Validar finalidad
        numero_finalidad =  (valores[11]).strip()
        actividad.finalidad = Finalidad.objects.get(valor = numero_finalidad)

        # Atributos inferidos
        regional = Regional.objects.get(regional = actividad.regional)
       
        tipo = validador_actividades.validar_tipo_actividad(actividad)
        if not tipo:
            raise Exception("Tipo de actividad no encontrado")
        
        actividad.tipo_actividad = tipo
        actividad.parametros_programa = ParametrosAreaPrograma.objects.get(area_programa = actividad.tipo_actividad.area, regional = regional.id)
        
        # Validar si la actividad está repetida
        if validador_actividades.valida_actividad_repetida_paciente(actividad):
            actividad.admisionada_otra_carga = True
            raise Exception("Actividad ya fue admisionada")
        
        # Validar si la actividad ya se encuentra en la carga actual.
        if validador_actividades.valida_actividad_repetida_paciente(actividad, carga):
            raise Exception("Actividad repetida en la misma carga, validar.")
        
        # Obtener tipo de Usuario
        
        try:
            tipo_usuario = utils.obtener_tipo_usuario(actividad.documento_paciente)            
            actividad.tipo_usuario = tipo_usuario.loc[0][0]
        except Exception as e:
            error = e
            actividad.inconsistencias = ("⚠️Error el consultar el Tipo de Usuario:" + str(error))[:500]

            
    except Exception as e:
        error = e
        actividad.inconsistencias = ("⚠️Error al procesar la actividad" + str(error))[:500]
        # print(e)

    actividad.save()
    
    return True
    
def procesar_lote_actividades(id_carga, bloque):

    carga = Carga.objects.get(id= id_carga)
    for valores in bloque["lote"]:
        # print("*"*100)
        # print(valores)
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
            # print(e)

        # Validar si la actividad ya se encuentra en la carga actual.
        if not validador_actividades.valida_actividad_repetida_paciente(actividad, carga):
            # print("✅Actividad se guarda correctamente")
            actividad.save()

        # actividad.save()

    carga.actualizar_info_actividades()
    carga.save()
    
    return True

# Tareas a procesar
def procesar_cargue_actividades(id_carga, datos, num_lote, cantidad_actividades, tiempo_inicial):
    estado = "procesando"
    carga = Carga.objects.get(id= id_carga)
    try:
        # Procesar actividades individualmente
        for valores in datos:
            if not Actividad.objects.filter(carga = carga).filter(datos_json = valores).count():
                procesar_actividad(carga, valores)
                
        # Validar si se completa la carga
        numero_actividades_carga = Actividad.objects.filter(carga = id_carga).count() 
        if numero_actividades_carga == cantidad_actividades:
            estado = "procesada"
            final = time.time()
            carga.tiempo_procesamiento = (final - tiempo_inicial)/60
            
            if len(carga.usuario.email):
                notificaciones_email.notificar_carga_procesada(carga, [carga.usuario.email])

        carga.estado = estado
        carga.actualizar_info_actividades()
        carga.save()
              
    except Exception as e:
        print("Error al procesar la carga", e)
        estado = "cancelada"
    finally:
        print(f"Lote: {num_lote}- num_actividades_tarea: {len(datos)} - Total Actividades Carga: {cantidad_actividades} - Estado: {estado}")
            
    return True

def tarea_admisionar_actividades_carga(token, id_carga, id_actividad = 0):
    respuesta = []
    carga = Carga.objects.get(id = int(id_carga))

    # Buscar las actividades sin admisión relacionadas a la carga
    actividades_carga = Actividad.objects.filter(carga = carga).filter(admision = None)
    
    if id_actividad:
        actividades_carga = Actividad.objects.filter(carga = carga, id=id_actividad , admisionada_otra_carga = False).filter(admision = None)
    
    for actividad in actividades_carga:
        print("TOKEN A USAR:", token)
        try:
            # Consultador datos del afiliado
            ruta = f"/api/SisDeta/GetDatosBasicosPaciente?NumeroIdentificacion={actividad.documento_paciente}&TipoIdentificacion={actividad.tipo_documento}"
            datos_afiliado = peticiones_http.consultar_data(ruta)

            print(datos_afiliado['Datos'])

            actividad.id_usuario = '1'
            actividad.nombre_usuario = 'admin'
            actividad.cedula_usuario = '123'
            actividad.nombre_persona_usuario = 'admin'

            # Validar Si el afiliado existe
            if not len(datos_afiliado['Datos']):
                raise Exception("No se obtuvieron datos del paciente")

            # Validar si la actividad ya fue admisionada
            if validador_actividades.valida_actividad_repetida_paciente(actividad):
                raise Exception("Esta actividad ya fue admisionada")
            
            if not actividad.tipo_actividad:
                actividad.tipo_actividad = TipoActividad.objects.get(nombre = actividad.nombre_actividad)
                
            try:
                if actividad.parametros_programa == None:
                    # Atributos inferidos
                    regional = Regional.objects.get(regional = actividad.regional)
                    actividad.tipo_actividad = TipoActividad.objects.get(nombre = actividad.nombre_actividad)
                    actividad.parametros_programa = ParametrosAreaPrograma.objects.get(area_programa = actividad.tipo_actividad.area, regional = regional.id)
        

                # Validación documento médico:
                if actividad.medico == None:
                    print(actividad.medico)
                    medico = Medico.objects.get(documento = actividad.documento_medico)
                    actividad.medico = medico

                # AutoID y nombre del regimen del afiliado
                auto_id = datos_afiliado['Datos'][0]['autoid']
                regimen = datos_afiliado['Datos'][0]['NombreRegimen']
                # tipo_usuario = datos_afiliado['Datos'][0]['tipo_usuario'] 

                tipo_usuario = actividad.tipo_usuario
                if not tipo_usuario:
                    try:
                        tipo_usuario = utils.obtener_tipo_usuario(actividad.documento_paciente)
                        print(tipo_usuario)            
                        actividad.tipo_usuario = tipo_usuario.loc[0][0]
                    except Exception as e:
                        error = e
                        actividad.inconsistencias = ("⚠️Error el consultar el Tipo de Usuario:" + str(error))[:500]

                if not datos_afiliado['Datos'][0]['NombreRegimen']:
                    raise Exception("No tiene regimen relacionado")

                
                # Inicializo la admisión con los parametros generales y la información de la actividad
                admision_actividad = admision.crear_admision(
                    autoid = auto_id,
                    regimen = regimen,
                    tipo_usuario = tipo_usuario,
                    codigo_entidad = parametros_generales.CODIGO_ENTIDAD[regimen],
                    tipo_diag = parametros_generales.TIPO_DIAGNOSTICO,
                    actividad = actividad
                )
                print(admision_actividad)

                try:
                    # Enviar Admisión a Zeus
                    
                    respuesta = peticiones_http.crear_admision(admision_actividad,token)
                    print(respuesta)
                   
                    if not respuesta:
                        raise Exception("Error en la petición a Zeus")
                    
                    print(respuesta['Datos'])
                    print(respuesta['Errores'])
                    
                    if(respuesta['Errores']):
                        raise Exception(respuesta['Errores'])

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

def tarea_grabar_admisiones_prueba(inicio, fin):
    print("INICIA TAREA DE ADMISIONES DE PRUEBA")
    tiempo_inicio = time.time()
    respuestas = []
    resultados = []
    admision_enviar = admision.admision_prueba

    for i in range(inicio,fin):
        try:
            # Se obtiene el token de Zeus
            token = peticiones_http.obtener_token()

            # Se genera un nuevo objeto de admisión para cada iteración
            respuesta = peticiones_http.crear_admision_prueba(admision_enviar,token)
            respuestas.append(respuesta)
            print(f"ADMISIÓN-{i+1}", respuesta)

            if respuesta:
                respuesta_admision =  ast.literal_eval(respuesta['Datos'][0]['infoTrasaction'])

                # Se verifica si la respuesta contiene datos de error o guardados
                datos_error = respuesta_admision[0]['DatosEnError']
        
                # Se verifica si la respuesta contiene datos guardados
                datos_guardados = respuesta_admision[0]['DatosGuardados']
                
                if datos_error:
                    print("Datos en error:", datos_error)

                # Se guarda la admisión si no hay errores
                if datos_guardados:
                    
                    admision_prueba = Admision(
                        documento_paciente = datos_guardados[0]['NumDoc'],
                        numero_estudio = datos_guardados[0]['Estudio'],
                        observacion = "Admisión de prueba",
                        json = admision_enviar
                    )
                    admision_prueba.save()
            else:
                print(respuesta)
        
        except Exception as e:
            print("Error al crear admisión:", e)
            resultados.append("Error al crear admisión")

           
    tiempo_final= time.time()

    print("Tiempo de creación admisiones:", tiempo_final - tiempo_inicio)
    return True