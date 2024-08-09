# DJANGO
from django.shortcuts import render 
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect, JsonResponse, FileResponse

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
from  home.models import TipoActividad, Actividad


# Create your views here.

# VISTAS PRINCIPALES

def index(request):

    listado_tipo_actividad = TipoActividad.objects.all()
    listado_actividades = Actividad.objects.all()

    ctx = {
        "listado_tipo_actividad":listado_tipo_actividad,
        "listado_actividades":listado_actividades
    }
    return render(request,"home/index.html",ctx)

def consultas_zeus(request):
    print("CONSULTAS ZEUS")
    ctx = {}
    return render(request,"home/consultasZeus.html",ctx)

def vista_carga_actividades(request):
    print("CARGA ACTIVIDADES")
    listado_tipo_actividad = TipoActividad.objects.all()
    listado_actividades = Actividad.objects.all()

    ctx = {
        "listado_tipo_actividad":listado_tipo_actividad,
        "listado_actividades":listado_actividades
    }
    return render(request,"home/cargaActividades.html",ctx)

def vista_grabar_admisiones(request):
    
    ctx = {}
    return render(request,"home/grabarAdmisiones.html",ctx)

def cargar_tipos_actividad(request):
    
    ctx = {}
    return render(request,"home/cargarTiposActividad.html",ctx)

# GRABAR ADMISIONES

def grabar_admision(request):
    ctx = {}
    return render(request,"home/index.html",ctx)

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

def grabar_admisiones(request):
    token = peticiones_http.obtener_token()
    
    inconsistencias_actividades = []

    # Actividades a procesar como admisión
    actividades = Actividad.objects.all()
    for actividad in actividades:

        # Consultador datos del afiliado
        ruta = f"/api/SisDeta/GetDatosBasicosPaciente?NumeroIdentificacion={actividad.documento_paciente}&TipoIdentificacion={actividad.tipo_documento}"
        datos_afiliado = peticiones_http.consultar_data(ruta)
        # print(datos_afiliado)
        try:
            # Datos consultados del afiliado o paciente
            if len(datos_afiliado['Datos']):
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
                print("CARGUE DE ADMISIÓN: ",respuesta)

            else:
                print("INCONSISTENCIA")
                inconsistencias_actividades.append({
                    "actividad":actividad.id,
                    "identificador":actividad.identificador,
                    "id_paciente":actividad.documento_paciente,
                    "nombre_paciente":actividad.nombre_paciente,
                    "descripcion": "Datos del paciente No encontrados"
                })

        
            
        except Exception as e:
            print(e, "Datos del paciente No encontrados")
        print("----------------------------------------------------------------------------------------------------------------")

    print(inconsistencias_actividades)
    respuesta = {
        "inconsistencias":inconsistencias_actividades
    }
    return JsonResponse(respuesta)

# CONSULTAS ENDPOINT API ZEUS

def consultar_codigos_empresas(request):
    
    print(request.GET)
    respuesta = peticiones_http.consultar_data("/api/SisEmpre")
    print(respuesta, type(respuesta))

    # https://dev.to/chryzcode/django-json-response-safe-false-4f9i
    return JsonResponse(respuesta, safe = False)

def consultar_datos_paciente(request):
    print(request.GET)
    id = request.GET['id']
    tipo = request.GET['tipo']
    print(id, tipo)

    ruta = f"/api/SisDeta/GetDatosBasicosPaciente?NumeroIdentificacion={id}&TipoIdentificacion={tipo}"

    respuesta = peticiones_http.consultar_data(ruta)
    print(respuesta, type(respuesta))

    # https://dev.to/chryzcode/django-json-response-safe-false-4f9i
    return JsonResponse(respuesta, safe = False)

def consultar_medicos(request):
    
    print(request.GET)
    respuesta = peticiones_http.consultar_data("/api/SisMedi")
    print(respuesta, type(respuesta))

    # https://dev.to/chryzcode/django-json-response-safe-false-4f9i
    return JsonResponse(respuesta, safe = False)

def listar_tipos_servicios(request):
    print(request.GET)
    respuesta = peticiones_http.consultar_data("/api/SisTipo")
    print(respuesta, type(respuesta))

    # https://dev.to/chryzcode/django-json-response-safe-false-4f9i
    return JsonResponse(respuesta, safe = False)

def listar_vias_ingreso(request):
    print(request.GET)
    respuesta = peticiones_http.consultar_data("/api/Sismaelm/ObtenerViaIngreso")
    print(respuesta, type(respuesta))

    # https://dev.to/chryzcode/django-json-response-safe-false-4f9i
    return JsonResponse(respuesta, safe = False)

def listar_causas_externas(request):
    print(request.GET)
    respuesta = peticiones_http.consultar_data("/api/Sismaelm/GetCausaExterna")
    print(respuesta, type(respuesta))

    # https://dev.to/chryzcode/django-json-response-safe-false-4f9i
    return JsonResponse(respuesta, safe = False)

def listar_unidades_funcionales(request):
    print(request.GET)
    respuesta = peticiones_http.consultar_data("/api/Ufuncionales")
    print(respuesta, type(respuesta))

    # https://dev.to/chryzcode/django-json-response-safe-false-4f9i
    return JsonResponse(respuesta, safe = False)

def listar_seriales_sedes(request):
    print(request.GET)
    respuesta = peticiones_http.consultar_data("/api/Seriales")
    print(respuesta, type(respuesta))

    # https://dev.to/chryzcode/django-json-response-safe-false-4f9i
    return JsonResponse(respuesta, safe = False)

def listar_puntos_atencion(request):
    print(request.GET)
    respuesta = peticiones_http.consultar_data("/api/Puntoatencion")
    print(respuesta, type(respuesta))

    # https://dev.to/chryzcode/django-json-response-safe-false-4f9i
    return JsonResponse(respuesta, safe = False)

def listar_tipos_diagnosticos(request):
    print(request.GET)
    respuesta = peticiones_http.consultar_data("/api/Sismaelm/GetTipoDiagnosticos")
    print(respuesta, type(respuesta))

    # https://dev.to/chryzcode/django-json-response-safe-false-4f9i
    return JsonResponse(respuesta, safe = False)

def listar_finalidades(request):
    print(request.GET)
    respuesta = peticiones_http.consultar_data("/api/Sismaelm/GetFinalidades")
    print(respuesta, type(respuesta))

    # https://dev.to/chryzcode/django-json-response-safe-false-4f9i
    return JsonResponse(respuesta, safe = False)

def listar_centros_costos(request):
    print(request.GET)
    respuesta = peticiones_http.consultar_data("/api/CentroCostos")
    print(respuesta, type(respuesta))

    # https://dev.to/chryzcode/django-json-response-safe-false-4f9i
    return JsonResponse(respuesta, safe = False)

def listar_estratos(request):
    token = peticiones_http.obtener_token()
    print(token)
    respuesta = peticiones_http.consultar_data("/api/Estrato",token = token)
    print(respuesta)
    
    # https://dev.to/chryzcode/django-json-response-safe-false-4f9i
    return JsonResponse(respuesta, safe = False)

def listar_contratos(request):
    token = peticiones_http.obtener_token()
    print(token)
    respuesta = peticiones_http.consultar_data("/api/Contratos",token = token)
    print(respuesta)
    
    # https://dev.to/chryzcode/django-json-response-safe-false-4f9i
    return JsonResponse(respuesta, safe = False)


# PROCESAMIENTO DE ACTIVIDADES

def cargar_actividades(request):
    datos = request.POST
    format_string = "%Y-%m-%d %H:%M:%S"
    archivo_masivo = pd.read_excel(request.FILES["adjunto"])
    archivo_dict = archivo_masivo.to_dict()
    respuesta = {}
    dict_actividades = {}
    dict_data = ast.literal_eval(datos["data"])
    
    tipo_actividad = int(dict_data['tipoActividad'])
    print("TIPO ACTIVIDAD: ",tipo_actividad)

    # for campo, valores in archivo_dict.items():
    #     print(campo,valores)
    #     for num, valor in valores.items():
    #         print(num, valor)
       
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
            print((str(valores[3]).split(" "))[0])
            actividad = Actividad()
            actividad.identificador = valores[0]
            actividad.tipo_fuente = valores[1]
            actividad.tipo_actividad =  TipoActividad.objects.get(id = tipo_actividad)
            actividad.fecha_servicio = (str(valores[3]).split(" "))[0]
            actividad.diagnostico_p = valores[5] 
            actividad.diagnostico_1 = valores[6] 
            actividad.diagnostico_2 = valores[7] 
            actividad.diagnostico_3 = valores[8] 
            actividad.tipo_documento = valores[9]
            actividad.documento_paciente = valores[10]
            actividad.nombre_paciente = valores[11]
            actividad.embarazo = valores[12]
            actividad.sede = valores[13]
            actividad.punto_atencion = valores[14]

            actividad.save()

            # respuesta[registro] = valores
    
    # print(respuesta)
    
    data_json = json.dumps(respuesta)

    # https://dev.to/chryzcode/django-json-response-safe-false-4f9i
    return JsonResponse(data_json, safe = False)




