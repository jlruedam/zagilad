# DJANGO
from django.shortcuts import render, redirect 
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

# ZAGILAD
from .modules import peticiones_http
from .modules import admision
from .modules import parametros_generales
from .modules import task
from  home.models import TipoActividad, Actividad
from  home.models import Admision, AreaPrograma, Colaborador, Carga


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
    
    actividades = Actividad.objects.filter(admision = None, inconsistencias = None)
    
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

@login_required(login_url="/login/")
def vista_actividades_inconsistencias(request):
    
    listado_actividades = Actividad.objects.exclude(inconsistencias = None)

    ctx = {
        "listado_actividades":listado_actividades
    }

    return render(request,"home/actividadesInconsistencias.html",ctx)

@login_required(login_url="/login/")
def informe_cargas(request):
    cargas = Carga.objects.all()

    for carga in cargas:
        carga.actualizar_info_actividades()

    ctx = {"cargas":cargas}
    return render(request,"home/informeCargas.html",ctx)

@login_required(login_url="/login/")
def ver_carga(request, id_carga):
    print(id_carga)
    carga = Carga.objects.get(id= id_carga)
    actividades_carga = Actividad.objects.filter(carga = carga)
    ctx = {
        "carga":carga,
        "actividades_carga":actividades_carga
    }
    return render(request,"home/verCarga.html",ctx)

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
    cant_act = len(dict_data['datos'])
    usuario_actual = User.objects.get(username=request.user.username)
    
    # Crear carga:
    carga_actividades = Carga(
        usuario = usuario_actual,
        data = json.dumps(dict_data), #Quitar esto y enviar a archivo json en el servidor
    )
    carga_actividades.save()

    
    # Aquí se debe crear la tarea programa.
    task.procesar_cargue_actividades.delay(carga_actividades.id)
    print("Carga en proceso...")

    resultados_cargue = {
        "num_carga":carga_actividades.id,
        "estado":carga_actividades.estado,
        "mensaje": "Carga en proceso"
    }

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
    
    task.tarea_grabar_admisiones.delay(token)
    
    respuesta = {
        "inconsistencias":"0"
    }
    return JsonResponse(respuesta)

@login_required(login_url="/login/")
def admisionar_actividades_carga(request, id_carga):
    token = peticiones_http.obtener_token()
    carga = Carga.objects.get(id = int(id_carga))
    carga.estado = "admisionando"
    carga.save()
    task.tarea_admisionar_actividades_carga.delay(token, id_carga)
    
    return redirect(f'/informeCargas/')

@login_required(login_url="/login/")
def admisionar_actividad_individual(request, id_actividad):
    token = peticiones_http.obtener_token()
    actividad = Actividad.objects.get(id = id_actividad)
    task.tarea_admisionar_actividad_individual.delay(token, id_actividad)

    return redirect(f'/verCarga/{actividad.carga.id}')

@login_required(login_url="/login/")
def eliminar_actividades_inconsistencia_carga(request, id_carga):
    carga = Carga.objects.get(id = int(id_carga))
    
    # Buscar las actividades sin admisión relacionadas a la carga
    actividades_carga_inconsistencia = Actividad.objects.filter(carga=carga).exclude(inconsistencias = None).delete()
    carga.actualizar_info_actividades()
    carga.save()
    return redirect(f'/verCarga/{id_carga}')

@login_required(login_url="/login/")
def eliminar_actividad_individual(request, id_actividad):
    actividad = Actividad.objects.get(id = int(id_actividad))
    carga = actividad.carga
    actividad.delete()

    carga.actualizar_info_actividades()
    carga.save()
    return redirect(f'/verCarga/{carga.id}')
# ADMISTRACIÓN 
@login_required(login_url="/login/")
def vista_administrador(request):
    ctx = {}
    return render(request,"home/administrador.html",ctx)

@login_required(login_url="/login/")
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