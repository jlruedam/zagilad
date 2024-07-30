from django.shortcuts import render 
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect, JsonResponse, FileResponse
from .modules import peticiones_http
from .modules import admision
import ast


# Create your views here.

def index(request):

    ctx = {}
    return render(request,"home/index.html",ctx)

def grabar_admision(request):
    ctx = {}
    return render(request,"home/index.html",ctx)

def grabar_admision_prueba(request):

    token = peticiones_http.obtener_token()
    admision_enviar = admision.admision_prueba

    print(str(token), admision_enviar)

    respuesta = peticiones_http.crear_admision(admision_enviar,token)
    print(respuesta)


    ctx = {
        "respuesta_admision":respuesta
    }
    return JsonResponse(respuesta)

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



