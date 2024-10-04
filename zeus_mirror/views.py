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

# ZAGILAD - Home modules
from home.modules import peticiones_http

# MODELS zeus mirror
from zeus_mirror.models import Contrato, UnidadFuncional, PuntoAtencion 
from zeus_mirror.models import CentroCosto, Sede, TipoServicio, Medico

# Create your views here.

def consultas_zeus(request):
    print("CONSULTAS ZEUS DESDE EL MIRROR")
    ctx = {}
    return render(request,"zeus_mirror/consultasZeus.html",ctx)

# CONSULTAS ENDPOINT API ZEUS

def consultar_codigos_empresas(request):
    
    respuesta = peticiones_http.consultar_data("/api/SisEmpre")
    print(len(respuesta))
    # for empresa in respuesta:
    #     print("-"*100)
    #     print(empresa, type(empresa))
    #     print("-"*100)

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

def listar_estratos(request):
    token = peticiones_http.obtener_token()
    print(token)
    respuesta = peticiones_http.consultar_data("/api/Estrato",token = token)
    print(respuesta)
    
    # https://dev.to/chryzcode/django-json-response-safe-false-4f9i
    return JsonResponse(respuesta, safe = False)

# EN BD

def listar_unidades_funcionales(request):
    
    respuesta = peticiones_http.consultar_data("/api/Ufuncionales")
    cantidad_bd_unidades = UnidadFuncional.objects.count()
    cantidad_respuesta = len(respuesta)

    if cantidad_bd_unidades <= 0:

        for uf in respuesta:
            print("-"*100)
            print(uf)
            print("-"*100)
            u_funcional = UnidadFuncional()
            u_funcional.id_zeus = uf['Id']
            u_funcional.codigo = uf['Codigo']
            u_funcional.descripcion = uf['Descripcion']
            u_funcional.id_sede = uf['IdSede']
            u_funcional.save()

    # https://dev.to/chryzcode/django-json-response-safe-false-4f9i
    return JsonResponse(respuesta, safe = False)

def listar_centros_costos(request):
    respuesta = peticiones_http.consultar_data("/api/CentroCostos")
    cantidad_bd_centros = CentroCosto.objects.count()
    cantidad_respuesta = len(respuesta)

    if cantidad_bd_centros <= 0:

        for centro in respuesta:
            print("-"*100)
            print(centro)
            print("-"*100)
            centro_costo = CentroCosto()
            centro_costo.codigo = centro['Codigo']
            centro_costo.nombre = centro['Nombre']
            centro_costo.tipo = centro['Tipo']
            centro_costo.stock = centro['Stock']
            centro_costo.activo_zeus = centro['Activo']
            centro_costo.save()
    

    # https://dev.to/chryzcode/django-json-response-safe-false-4f9i
    return JsonResponse(respuesta, safe = False)

def listar_puntos_atencion(request):
    respuesta = peticiones_http.consultar_data("/api/Puntoatencion")
    cantidad_bd_puntos = PuntoAtencion.objects.count()
    cantidad_respuesta = len(respuesta)

    if cantidad_bd_puntos <= 0:

        for punto in respuesta:
            print("-"*100)
            print(punto)
            print("-"*100)
            punto_atencion = PuntoAtencion()
            punto_atencion.id_zeus = punto['Id']
            punto_atencion.codigo = punto['Codigo']
            punto_atencion.nombre = punto['Nombre']
            punto_atencion.nit = punto['Nit']
            punto_atencion.direccion = punto['Direccion']
            punto_atencion.departamento = punto['Departamento']
            punto_atencion.municipio = punto['Municipio']
            punto_atencion.save()
    

    # https://dev.to/chryzcode/django-json-response-safe-false-4f9i
    return JsonResponse(respuesta, safe = False)

def listar_contratos(request):
    token = peticiones_http.obtener_token()
    respuesta = peticiones_http.consultar_data("/api/Contratos",token = token)
    cantidad_bd_contratos = Contrato.objects.count()
    cantidad_respuesta = len(respuesta)

    if cantidad_bd_contratos <= 0:

        for contrato in respuesta:
            print("-"*100)

            # Consultar si el contrato existe sin cambios
            contrato_existente_sin_cambios = Contrato.objects.filter(
                codigo = contrato["Codigo"],
                nombre = contrato["Nombre"],
                empresa = contrato["Empresa"],
                fecha_inicial = contrato["Fechai"],
                fecha_final = contrato["Fechaf"],
                observacion = contrato["Obs"],
                numero = contrato["Numero"],
                id_sede = contrato["IdSede"],
                regimen = contrato["Regimen"],
                activo = contrato["Activo"],
            )

            # Si no existe contratos existente sin cambios
            if not contrato_existente_sin_cambios:
                
                # Consultar si ya existe por el código.
                contrato_existente = Contrato.objects.filter(
                    codigo = contrato["Codigo"],
                )

                print("CONTRATO EXISTENTE:", contrato_existente)

                if contrato_existente:
                    print("Actualizar Contrato")
                    # Entonces uno de sus campos cambió y se debe actualizar.
                    contrato_existente[0].nombre = contrato["Nombre"]
                    contrato_existente[0].empresa = contrato["Empresa"]
                    contrato_existente[0].fecha_inicial = contrato["Fechai"]
                    contrato_existente[0].fecha_final = contrato["Fechaf"]
                    contrato_existente[0].observacion = contrato["Obs"]
                    contrato_existente[0].numero = contrato["Numero"]
                    contrato_existente[0].id_sede = contrato["IdSede"]
                    contrato_existente[0].regimen = contrato["Regimen"]
                    contrato_existente[0].activo = contrato["Activo"]
                    contrato_existente[0].save()

                else:
                    print("Crear Contrato")
                    nuevo_contrato = Contrato(
                        codigo = contrato["Codigo"],
                        nombre = contrato["Nombre"],
                        empresa = contrato["Empresa"],
                        fecha_inicial = contrato["Fechai"],
                        fecha_final = contrato["Fechaf"],
                        observacion = contrato["Obs"],
                        numero = contrato["Numero"],
                        id_sede = contrato["IdSede"],
                        regimen = contrato["Regimen"],
                        activo = contrato["Activo"],
                    )
                    nuevo_contrato.save()

            print(contrato)
        
    # https://dev.to/chryzcode/django-json-response-safe-false-4f9i
    return JsonResponse(respuesta, safe = False)

def listar_seriales_sedes(request):
    respuesta = peticiones_http.consultar_data("/api/Seriales")
    cantidad_bd_sedes = Sede.objects.count()
    cantidad_respuesta = len(respuesta)

    if cantidad_bd_sedes <= 0:

        for sede in respuesta:
            print("-"*100)
            print(sede)
            print("-"*100)
            sede_atencion = Sede()
            sede_atencion.id_zeus = sede['Id']
            sede_atencion.nit = sede['Nit']
            sede_atencion.razon_social = sede['RSocial']
            sede_atencion.codigo_eps = sede['CodigoEps']
            sede_atencion.direccion = sede['Direccion']
            sede_atencion.ciudad = sede['Ciudad']
            sede_atencion.departamento = sede['Depto']
            sede_atencion.save()
    
    # https://dev.to/chryzcode/django-json-response-safe-false-4f9i
    return JsonResponse(respuesta, safe = False)

def listar_tipos_servicios(request):
    
    respuesta = peticiones_http.consultar_data("/api/SisTipo")
    cantidad_bd_servicios = TipoServicio.objects.count()
    cantidad_respuesta = len(respuesta)

    if cantidad_bd_servicios <= 0:

        for servicio in respuesta:
            print("-"*100)
            print(servicio)
            print("-"*100)
            tipo_servicio = TipoServicio()
            tipo_servicio.id_zeus = servicio['Id']
            tipo_servicio.fuente = servicio['Fuente']
            tipo_servicio.nombre = servicio['Nombre']
            tipo_servicio.tipo = servicio['Tipo']
            tipo_servicio.tipo_servicio = servicio['Tiposervicio']
            tipo_servicio.save()

    # https://dev.to/chryzcode/django-json-response-safe-false-4f9i
    return JsonResponse(respuesta, safe = False)

def consultar_medicos(request):
    
    respuesta = peticiones_http.consultar_data("/api/SisMedi")
    cantidad_bd_medicos = Medico.objects.count()

    if cantidad_bd_medicos <= 0:

        for medico in respuesta:
            # print("-"*100)
            # print(medico)
            # print("-"*100)
            medico_bd = Medico()
            medico_bd.codigo = medico['Codigo']
            medico_bd.documento = medico['Cedula']
            medico_bd.nombre = medico['Nombre']
            medico_bd.save()

    # https://dev.to/chryzcode/django-json-response-safe-false-4f9i
    return JsonResponse(respuesta, safe = False)