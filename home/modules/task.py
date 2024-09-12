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
from home.models import Regional, Admision, AreaPrograma, Colaborador, Carga
from home.modules import peticiones_http
from home.modules import validador_actividades
from home.modules import notificaciones_email
from home.modules import parametros_generales
from home.modules import admision


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
    carga.actualizar_info_actividades()
    carga.save()
    
    # Enviar un correo de notificación cuando termine el Cargue
    
    colaborador = Colaborador.objects.filter(usuario = carga.usuario)
    if colaborador:
        if len(colaborador[0].email):
            notificaciones_email.notificar_carga_procesada(carga, [colaborador[0].email])

    # resultados_cargue.append(valores)
    return "CARGUE PROCESADO"

@shared_task
def tarea_admisionar_actividades_carga(token, id_carga):
    
    carga = Carga.objects.get(id = int(id_carga))
    
    # Buscar las actividades sin admisión relacionadas a la carga
    actividades_carga = Actividad.objects.filter(carga = carga).filter(admision = None)

    for actividad in actividades_carga:

        # Consultador datos del afiliado
        ruta = f"/api/SisDeta/GetDatosBasicosPaciente?NumeroIdentificacion={actividad.documento_paciente}&TipoIdentificacion={actividad.tipo_documento}"
        datos_afiliado = peticiones_http.consultar_data(ruta)

        try:
            # Si el afiliado existe
            if len(datos_afiliado['Datos']):

                # Validar si la actividad está repetida
                if validador_actividades.valida_actividad_repectiva_paciente(actividad, carga):
                    print("ACTIVIDAD YA SE ENCUENTRA CARGADA PARA ESTE PACIENTE")
                    actividad.inconsistencias= "⚠️ Actividad repetida"
                else:
                    # AutoID y nombre del regimen del afiliado
                    auto_id = datos_afiliado['Datos'][0]['autoid']
                    regimen = datos_afiliado['Datos'][0]['NombreRegimen']

                    # Inicializo la admisión con los parametros generales y la información de la actividad
                    admision_actividad = admision.crear_admision(
                        autoid = auto_id,
                        regimen = regimen,
                        codigo_entidad = parametros_generales.CODIGO_ENTIDAD[regimen],
                        medico = parametros_generales.CODIGO_MEDICO,
                        num_usuario =parametros_generales.NUMERO_USUARIO,
                        usuario_id = parametros_generales.IDENTIFICACION_USUARIO,
                        usuario_nombre = parametros_generales.NOMBRE_USUARIO,
                        tipo_diag = parametros_generales.TIPO_DIAGNOSTICO,
                        actividad = actividad
                    )

                    # Enviar Admisión a Zeus
                    respuesta = peticiones_http.crear_admision(admision_actividad,token)
                    print("CARGUE DE ADMISIÓN: ",respuesta['Datos'][0]['infoTrasaction'], type(respuesta['Datos'][0]['infoTrasaction']))

                    respuesta_admision = ast.literal_eval(respuesta['Datos'][0]['infoTrasaction'])
                    print("RESPUESTA ADMISIÓN:",respuesta_admision[0], type(respuesta_admision[0]))

                    # Encapsular respuesta
                    datos_error = respuesta_admision[0]['DatosEnError']
                    datos_guardados = respuesta_admision[0]['DatosGuardados']
                    print(datos_error, datos_guardados)

                    if datos_error:
                        actividad.inconsistencias += datos_error[0]
                        
                    
                    if datos_guardados:
                        numero_estudio = datos_guardados[0]['Estudio']
                        print("NÚMERO DE ESTUDIO:", numero_estudio)

                        nueva_admision = Admision()
                        nueva_admision.documento_paciente = actividad.documento_paciente
                        nueva_admision.numero_estudio = numero_estudio
                        nueva_admision.json = json.dumps(admision_actividad)
                        nueva_admision.save()

                        actividad.admision = nueva_admision
            else:
                actividad.inconsistencias = "⚠️" + "Paciente no está registrado en Zeus"
                print("Paciente no está registrado en Zeus")

        except Exception as e:
            print(e)
            actividad.inconsistencias = str(e)

        actividad.save()  
    carga.estado = "procesada"
    carga.actualizar_info_actividades()
    carga.save()


    # Enviar un correo de notificación cuando termine el Cargue
    
    colaborador = Colaborador.objects.filter(usuario = carga.usuario)
    if colaborador:
        if len(colaborador[0].email):
            notificaciones_email.notificar_carga_admisionada(carga, [colaborador[0].email])


    return f"CARGA PROCESADA"


@shared_task
def tarea_admisionar_actividad_individual(token, id_actividad):
    

    actividad = Actividad.objects.get(id = id_actividad)

    # Consultador datos del afiliado
    ruta = f"/api/SisDeta/GetDatosBasicosPaciente?NumeroIdentificacion={actividad.documento_paciente}&TipoIdentificacion={actividad.tipo_documento}"
    datos_afiliado = peticiones_http.consultar_data(ruta)

    try:
        # Si el afiliado existe
        if len(datos_afiliado['Datos']):

            # Validar si la actividad está repetida
            if validador_actividades.valida_actividad_repectiva_paciente(actividad, actividad.carga):
                print("ACTIVIDAD YA SE ENCUENTRA CARGADA PARA ESTE PACIENTE")
                actividad.inconsistencias= "⚠️ Actividad repetida"
            else:
                # AutoID y nombre del regimen del afiliado
                auto_id = datos_afiliado['Datos'][0]['autoid']
                regimen = datos_afiliado['Datos'][0]['NombreRegimen']

                # Inicializo la admisión con los parametros generales y la información de la actividad
                admision_actividad = admision.crear_admision(
                    autoid = auto_id,
                    regimen = regimen,
                    codigo_entidad = parametros_generales.CODIGO_ENTIDAD[regimen],
                    medico = parametros_generales.CODIGO_MEDICO,
                    num_usuario =parametros_generales.NUMERO_USUARIO,
                    usuario_id = parametros_generales.IDENTIFICACION_USUARIO,
                    usuario_nombre = parametros_generales.NOMBRE_USUARIO,
                    tipo_diag = parametros_generales.TIPO_DIAGNOSTICO,
                    actividad = actividad
                )

                # Enviar Admisión a Zeus
                respuesta = peticiones_http.crear_admision(admision_actividad,token)
                print("CARGUE DE ADMISIÓN: ",respuesta['Datos'][0]['infoTrasaction'], type(respuesta['Datos'][0]['infoTrasaction']))

                respuesta_admision = ast.literal_eval(respuesta['Datos'][0]['infoTrasaction'])
                print("RESPUESTA ADMISIÓN:",respuesta_admision[0], type(respuesta_admision[0]))

                # Encapsular respuesta
                datos_error = respuesta_admision[0]['DatosEnError']
                datos_guardados = respuesta_admision[0]['DatosGuardados']
                print(datos_error, datos_guardados)

                if datos_error:
                    actividad.inconsistencias += datos_error[0]
                    
                
                if datos_guardados:
                    numero_estudio = datos_guardados[0]['Estudio']
                    print("NÚMERO DE ESTUDIO:", numero_estudio)

                    nueva_admision = Admision()
                    nueva_admision.documento_paciente = actividad.documento_paciente
                    nueva_admision.numero_estudio = numero_estudio
                    nueva_admision.json = json.dumps(admision_actividad)
                    nueva_admision.save()

                    actividad.admision = nueva_admision
        else:
            actividad.inconsistencias = "⚠️" + "Paciente no está registrado en Zeus"
            print("Paciente no está registrado en Zeus")

    except Exception as e:
        print(e)
        actividad.inconsistencias = str(e)

    actividad.save()  
    actividad.carga.actualizar_info_actividades()
    actividad.carga.save()

    return f"CARGA PROCESADA"

@shared_task
def tarea_grabar_admisiones(token):
    
    cargas = Carga.objects.filter(estado = "procesada")
    for carga in cargas: 
        # Buscar las actividades sin inconsistencia al ser procesadas
        actividades_carga = Actividad.objects.filter(carga = carga).filter(inconsistencias = None).filter(admision = None)

        for actividad in actividades_carga:

            # Consultador datos del afiliado
            ruta = f"/api/SisDeta/GetDatosBasicosPaciente?NumeroIdentificacion={actividad.documento_paciente}&TipoIdentificacion={actividad.tipo_documento}"
            datos_afiliado = peticiones_http.consultar_data(ruta)

            try:
                # AutoID y nombre del regimen del afiliado
                auto_id = datos_afiliado['Datos'][0]['autoid']
                regimen = datos_afiliado['Datos'][0]['NombreRegimen']

                # Inicializo la admisión con los parametros generales y la informaciónde la actividad
                admision_actividad = admision.crear_admision(
                    autoid = auto_id,
                    regimen = regimen,
                    codigo_entidad = parametros_generales.CODIGO_ENTIDAD[regimen],
                    medico = parametros_generales.CODIGO_MEDICO,
                    num_usuario =parametros_generales.NUMERO_USUARIO,
                    usuario_id = parametros_generales.IDENTIFICACION_USUARIO,
                    usuario_nombre = parametros_generales.NOMBRE_USUARIO,
                    tipo_diag = parametros_generales.TIPO_DIAGNOSTICO,
                    actividad = actividad
                )

                # Enviar Admisión a Zeus
                respuesta = peticiones_http.crear_admision(admision_actividad,token)
                print("CARGUE DE ADMISIÓN: ",respuesta['Datos'][0]['infoTrasaction'], type(respuesta['Datos'][0]['infoTrasaction']))

                respuesta_admision = ast.literal_eval(respuesta['Datos'][0]['infoTrasaction'])
                print("RESPUESTA ADMISIÓN:",respuesta_admision[0], type(respuesta_admision[0]))

                # Encapsular respuesta
                datos_error = respuesta_admision[0]['DatosEnError']
                datos_guardados = respuesta_admision[0]['DatosGuardados']
                print(datos_error, datos_guardados)

                if datos_error:
                    if actividad.inconsistencias:
                        actividad.inconsistencias += "/" + datos_error[0]
                    else: 
                        actividad.inconsistencias += datos_error[0]
                
                if datos_guardados:

                    numero_estudio = datos_guardados[0]['Estudio']
                    print("NÚMERO DE ESTUDIO:", numero_estudio)

                    nueva_admision = Admision()
                    nueva_admision.documento_paciente = actividad.documento_paciente
                    nueva_admision.numero_estudio = numero_estudio
                    nueva_admision.json = json.dumps(admision_actividad)
                    nueva_admision.save()

                    actividad.admision = nueva_admision
                    actividad.save()

            except Exception as e:
                print(e)
                if actividad.inconsistencias:
                    actividad.inconsistencias += "/" + str(e)
                else: 
                    actividad.inconsistencias += str(e)
           
    
    return "ACTIVIDADES ADMISIONADAS"