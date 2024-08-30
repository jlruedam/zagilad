# DJANGO
from django.shortcuts import render 
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect, JsonResponse, FileResponse
from django.core.serializers import json
from django.core import serializers
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
# PYTHON
import ast, time
import pandas as pd
import numpy as np
import json
import datetime
import math

# ZAGILAD
from .modules import peticiones_http
from .modules import admision
from .modules import parametros_generales
from .modules import validador_actividades
from  home.models import TipoActividad, Actividad, ParametrosAreaPrograma
from  home.models import Regional, Admision, AreaPrograma, Colaborador


# Create your views here.

# VISTAS PRINCIPALES
@login_required(login_url="/login/")
def index(request):
    print("INDEX")

    listado_tipo_actividad = TipoActividad.objects.all()
    listado_actividades = Actividad.objects.all()

    ctx = {
        "listado_tipo_actividad":listado_tipo_actividad,
        "listado_actividades":listado_actividades
    }


    return render(request,"home/index.html",ctx)

@login_required(login_url="/login/")
def vista_carga_actividades(request):

    usuario_actual = User.objects.get(username=request.user.username)

    print(usuario_actual)
    colaborador_actual = Colaborador.objects.filter(usuario = usuario_actual)
    if not colaborador_actual:
        colaborador_actual = [""]

    print("CARGA ACTIVIDADES")
    listado_tipo_actividad = TipoActividad.objects.all()
    listado_actividades = Actividad.objects.all()
    areas_programas = AreaPrograma.objects.all()

    ctx = {
        "listado_tipo_actividad":listado_tipo_actividad,
        "listado_actividades":listado_actividades,
        "areas_programas":areas_programas,
        "colaborador_actual":colaborador_actual[0]
    }
    return render(request,"home/cargaActividades.html",ctx)

@login_required(login_url="/login/")
def vista_grabar_admisiones(request):
    
    actividades = Actividad.objects.filter(admision = None)
    
    print("ACTIVIDADES A ADMISIONAR: ", actividades)

    ctx = {"actividadesAdmisionar": actividades}
    return render(request,"home/grabarAdmisiones.html",ctx)

@login_required(login_url="/login/")
def cargar_tipos_actividad(request):
    
    ctx = {}
    return render(request,"home/cargarTiposActividad.html",ctx)

@login_required(login_url="/login/")
def vista_actividades_admisionadas(request):
    
    listado_actividades = Actividad.objects.all().exclude(admision = None)

    ctx = {
        "listado_actividades":listado_actividades
    }

    return render(request,"home/actividadesAdmisionadas.html",ctx)


# PROCESAMIENTO DE ACTIVIDADES
@login_required(login_url="/login/")
def cargar_actividades(request):
    
    archivo_masivo = pd.read_excel(request.FILES["adjunto"])
    archivo_masivo = archivo_masivo.fillna("")
    archivo_dict = archivo_masivo.to_dict()
    respuesta = []
       
    num_registros = []
    for columna in archivo_dict.values():
        num_registros.append(len(columna))

    if len(np.unique(num_registros)) == 1:
        print("Cantidad de registros OK")
        registros = {}
        for i in range((np.unique(num_registros))[0]):
            registros[i] = []
            for campo in archivo_dict.values():
                registros[i].append(campo[i])

        for registro, valores in registros.items():

            print(registro, valores)
            valores[1] = (str(valores[1])).strip()
            valores[7] = (str(valores[7]).split(" "))[0]
            valores[9] = (str(valores[9])).strip()
            valores.append("A procesar")
            respuesta.append(valores)
            
    
    # https://dev.to/chryzcode/django-json-response-safe-false-4f9i
    return JsonResponse(respuesta, safe = False)

@login_required(login_url="/login/")
def procesarCargue(request):
    datos = request.POST
    dict_data = ast.literal_eval(datos["data"])
    area_programa = int(dict_data['areaPrograma']) # Se debe tomar del formulario
    resultados_cargue = []

    for valores in dict_data['datos']:
        error = 0
        print("*"*100)
        print(valores)
        try:
            actividad = Actividad()
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
                actividad.parametros_programa = ParametrosAreaPrograma.objects.get(area_programa = area_programa, regional = regional.id)
                actividad.tipo_actividad = TipoActividad.objects.get(nombre = actividad.nombre_actividad)

                # Validar si la actividad está repetida
                if validador_actividades.valida_actividad_repectiva_paciente(actividad):
                    print("ACTIVIDAD YA SE ENCUENTRA CARGADA PARA ESTE PACIENTE")
                    valores[-1]="⚠️ Actividad repetida"
                else:
                    valores[-1]="✅"
                    actividad.save()
            else:
                valores[-1]="⚠️" + "Paciente no está registrado en Zeus"
            
        except Exception as e:
            error = e
            valores[-1]="⚠️" + str(error)
            print(e)
        
        resultados_cargue.append(valores)

    print("RESULTADOS DEL CARGUE",resultados_cargue)
       

    return JsonResponse(resultados_cargue, safe = False)

# GRABAR ADMISIONES
@login_required(login_url="/login/")
def grabar_admision(request):
    ctx = {}
    return render(request,"home/index.html",ctx)

@login_required(login_url="/login/")
def grabar_admision_prueba(request):
    inicio = time.time()
    cantidad = int(request.GET['cantidad'])
    token = peticiones_http.obtener_token()
    admision_enviar = admision.admision_prueba
    respuestas = []
    resultados = []
    for i in range(0,cantidad):
        respuesta = peticiones_http.crear_admision(admision_enviar,token)
        respuestas.append(respuesta)
        print(i, respuesta)

    for r in respuestas:
        resultados.append(r['Datos'][0])

    ctx = {
        "resultados":resultados, 
    }
    final= time.time()

    print("Tiempo de creación admisiones:", final - inicio)
    return JsonResponse(ctx)

@login_required(login_url="/login/")
def grabar_admisiones(request):
    token = peticiones_http.obtener_token()
    
    inconsistencias_actividades = []

    # Actividades a procesar como admisión
    actividades = Actividad.objects.filter(admision = None)
    for actividad in actividades:

        # Consultador datos del afiliado
        ruta = f"/api/SisDeta/GetDatosBasicosPaciente?NumeroIdentificacion={actividad.documento_paciente}&TipoIdentificacion={actividad.tipo_documento}"
        datos_afiliado = peticiones_http.consultar_data(ruta)
        # print(datos_afiliado)
        try:
          
            auto_id = datos_afiliado['Datos'][0]['autoid']
            regimen = datos_afiliado['Datos'][0]['NombreRegimen']

            # print(auto_id, regimen)
            
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

            print("ADMISION:",admision_actividad)

            # BLOQUE DE ENVÍO DE LA ADMISIÓN A ZEUS
            respuesta = peticiones_http.crear_admision(admision_actividad,token)
            print("CARGUE DE ADMISIÓN: ",respuesta['Datos'][0]['infoTrasaction'], type(respuesta['Datos'][0]['infoTrasaction']))

            respuesta_admision = ast.literal_eval(respuesta['Datos'][0]['infoTrasaction'])

            print("RESPUESTA ADMISIÓN:",respuesta_admision[0], type(respuesta_admision[0]))
            
            datos_error = respuesta_admision[0]['DatosEnError']
            datos_guardados = respuesta_admision[0]['DatosGuardados']
            print(datos_error, datos_guardados)

            if datos_error:
                print("INCONSISTENCIA")
                inconsistencias_actividades.append({
                "actividad":actividad.id,
                "identificador":actividad.identificador,
                "id_paciente":actividad.documento_paciente,
                "nombre_paciente":actividad.nombre_paciente,
                "descripcion": datos_error[0]
                })
            
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
            print(e, "Error al cargar la admisión")
            inconsistencias_actividades.append({
                "actividad":actividad.id,
                "identificador":actividad.identificador,
                "id_paciente":actividad.documento_paciente,
                "nombre_paciente":actividad.nombre_paciente,
                "descripcion": str(e)
            })
        print("----------------------------------------------------------------------------------------------------------------")

    print(inconsistencias_actividades)
    respuesta = {
        "inconsistencias":inconsistencias_actividades
    }
    return JsonResponse(respuesta)

# ADMISTRACIÓN 
@login_required(login_url="/login/")
def vista_administrador(request):
    ctx = {}
    return render(request,"home/administrador.html",ctx)

def cargar_configuracion_arranque(request):
    try:
        parametros_default = parametros_generales.cargar_configuracion_default()
        parametros_areas = parametros_generales.parametros_area_default()
        
        if parametros_default and parametros_areas:
            mensaje = "Proceso realizado"
        else:
            mensaje = "Ya existen datos"
    except Exception as e:
        mensaje = e
        
    ctx = {
        "mensaje_configuracion_arranque":mensaje
    }   
    
    return render(request,"home/administrador.html",ctx)