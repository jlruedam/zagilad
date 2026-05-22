# DJANGO
from django.shortcuts import render, redirect 
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect, JsonResponse, FileResponse, HttpResponseServerError
from django.core.serializers import json
from django.core import serializers
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q, Count
from django.db import transaction
from django.http import FileResponse, Http404
from django.conf import settings

# PYTHON
from datetime import datetime, date
import ast, time
import pandas as pd
import numpy as np
import json
import logging
import os

# ZAGILAD
from home.models import TipoActividad, Actividad, ParametrosAreaPrograma
from home.models import Admision, AreaPrograma, Carga, ContratoMarco, Regional
from zeus_mirror.models import TipoServicio, UnidadFuncional, PuntoAtencion, CentroCosto, Sede, Contrato, Medico
from home.modules import peticiones_http, parametros_generales
from home.modules import generador_excel, utils
from home.modules import paginacion_actividades
from home.modules import revalidador
from home.modules.tipo_usuario.homologacion import SIESA_LABELS


# DJANGO Q
from django_q.tasks import async_task





# Configurar el logger
logger = logging.getLogger(__name__)

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

    listado_tipo_actividad = TipoActividad.objects.all()
    listado_actividades = Actividad.objects.all()
    areas_programas = AreaPrograma.objects.all()

    ctx = {
        "listado_tipo_actividad":listado_tipo_actividad,
        "listado_actividades":listado_actividades,
        "areas_programas":areas_programas,
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
    ctx = {}
    return render(request,"home/actividadesInconsistencias.html",ctx)

@login_required(login_url="/login/")
def listar_actividades_inconsistencias(request):
    dt = request.POST
    actividades = Actividad.objects.exclude(inconsistencias = None).order_by("id")
    context = paginacion_actividades.actividades_paginadas(dt,actividades)
    return JsonResponse(context, safe = False)

@login_required(login_url="/login/")
def stats_actividades_inconsistencias(request):
    base_qs = Actividad.objects.exclude(inconsistencias=None)
    por_tipo = list(
        base_qs.values("inconsistencias")
        .annotate(cantidad=Count("id"))
        .order_by("-cantidad")
    )
    por_actividad = list(
        base_qs.values("nombre_actividad")
        .annotate(cantidad=Count("id"))
        .order_by("-cantidad")[:20]
    )
    return JsonResponse({"por_tipo": por_tipo, "por_actividad": por_actividad})

@login_required(login_url="/login/")
def listar_actividades_admisionadas(request):
    dt = request.POST
    actividades = Actividad.objects.exclude(admision = None).order_by("id")
    context = paginacion_actividades.actividades_paginadas(dt,actividades)
    return JsonResponse(context, safe = False)
    
@login_required(login_url="/login/")
def listar_actividades_carga(request, num_carga):
    dt = request.POST
    actividades = Actividad.objects.filter(carga = num_carga).order_by("id")
    context = paginacion_actividades.actividades_paginadas(dt,actividades)
    return JsonResponse(context, safe = False)

@login_required(login_url="/login/")
def tipos_actividad(request):
    tipos_actividad = TipoActividad.objects.select_related("contrato", "tipo_servicio", "area").all()
    contratos = ContratoMarco.objects.order_by("numero")
    tipos_servicio = TipoServicio.objects.order_by("nombre")
    areas = AreaPrograma.objects.order_by("nombre")
    ctx = {
        "tipos_actividad": tipos_actividad,
        "contratos": contratos,
        "tipos_servicio": tipos_servicio,
        "areas": areas,
    }
    return render(request, "home/tiposActividad.html", ctx)


@login_required(login_url="/login/")
def crear_tipo_actividad(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método no permitido"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"ok": False, "error": "JSON inválido"}, status=400)

    requeridos = {
        "nombre": "Nombre",
        "cups": "CUPS",
        "contrato_id": "Contrato",
        "tipo_servicio_id": "Tipo de servicio",
        "area_id": "Área",
    }
    faltantes = [etiqueta for campo, etiqueta in requeridos.items() if not data.get(campo)]
    if faltantes:
        return JsonResponse(
            {"ok": False, "error": f"Campos requeridos: {', '.join(faltantes)}"},
            status=400,
        )

    try:
        contrato = ContratoMarco.objects.get(id=data["contrato_id"])
        tipo_servicio = TipoServicio.objects.get(id=data["tipo_servicio_id"])
        area = AreaPrograma.objects.get(id=data["area_id"])
    except (ContratoMarco.DoesNotExist, TipoServicio.DoesNotExist, AreaPrograma.DoesNotExist):
        return JsonResponse({"ok": False, "error": "Contrato, tipo de servicio o área no válidos"}, status=400)

    tipo = TipoActividad.objects.create(
        nombre=data["nombre"].strip(),
        cups=data["cups"].strip(),
        grupo=(data.get("grupo") or "").strip() or None,
        responsable=(data.get("responsable") or "").strip() or None,
        diagnostico=(data.get("diagnostico") or "").strip() or None,
        finalidad=(data.get("finalidad") or "").strip() or None,
        fuente=(data.get("fuente") or "").strip() or None,
        observacion=(data.get("observacion") or "").strip() or None,
        entrega=(data.get("entrega") or "").strip() or None,
        contrato=contrato,
        tipo_servicio=tipo_servicio,
        area=area,
    )

    return JsonResponse({
        "ok": True,
        "tipo": {
            "id": tipo.id,
            "nombre": tipo.nombre,
            "cups": tipo.cups,
        },
    })


@login_required(login_url="/login/")
def editar_tipo_actividad(request, id_tipo):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método no permitido"}, status=405)

    try:
        tipo = TipoActividad.objects.get(id=id_tipo)
    except TipoActividad.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Tipo de actividad no encontrado"}, status=404)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"ok": False, "error": "JSON inválido"}, status=400)

    requeridos = {
        "nombre": "Nombre",
        "cups": "CUPS",
        "contrato_id": "Contrato",
        "tipo_servicio_id": "Tipo de servicio",
        "area_id": "Área",
    }
    faltantes = [etiqueta for campo, etiqueta in requeridos.items() if not data.get(campo)]
    if faltantes:
        return JsonResponse(
            {"ok": False, "error": f"Campos requeridos: {', '.join(faltantes)}"},
            status=400,
        )

    try:
        contrato = ContratoMarco.objects.get(id=data["contrato_id"])
        tipo_servicio = TipoServicio.objects.get(id=data["tipo_servicio_id"])
        area = AreaPrograma.objects.get(id=data["area_id"])
    except (ContratoMarco.DoesNotExist, TipoServicio.DoesNotExist, AreaPrograma.DoesNotExist):
        return JsonResponse({"ok": False, "error": "Contrato, tipo de servicio o área no válidos"}, status=400)

    tipo.nombre = data["nombre"].strip()
    tipo.cups = data["cups"].strip()
    tipo.grupo = (data.get("grupo") or "").strip() or None
    tipo.responsable = (data.get("responsable") or "").strip() or None
    tipo.diagnostico = (data.get("diagnostico") or "").strip() or None
    tipo.finalidad = (data.get("finalidad") or "").strip() or None
    tipo.fuente = (data.get("fuente") or "").strip() or None
    tipo.observacion = (data.get("observacion") or "").strip() or None
    tipo.entrega = (data.get("entrega") or "").strip() or None
    tipo.contrato = contrato
    tipo.tipo_servicio = tipo_servicio
    tipo.area = area
    tipo.save()

    return JsonResponse({
        "ok": True,
        "tipo": {
            "id": tipo.id,
            "nombre": tipo.nombre,
            "cups": tipo.cups,
        },
    })


@login_required(login_url="/login/")
def vista_areas_programa(request):
    areas = AreaPrograma.objects.order_by("identificador")
    ctx = {"areas_programa": areas}
    return render(request, "home/areasPrograma.html", ctx)


@login_required(login_url="/login/")
def crear_area_programa(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método no permitido"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"ok": False, "error": "JSON inválido"}, status=400)

    identificador = (data.get("identificador") or "").strip()
    nombre = (data.get("nombre") or "").strip()

    if not identificador or not nombre:
        faltantes = []
        if not identificador: faltantes.append("Identificador")
        if not nombre: faltantes.append("Nombre")
        return JsonResponse(
            {"ok": False, "error": f"Campos requeridos: {', '.join(faltantes)}"},
            status=400,
        )

    if AreaPrograma.objects.filter(identificador=identificador).exists():
        return JsonResponse(
            {"ok": False, "error": f"Ya existe un área con el identificador '{identificador}'"},
            status=400,
        )

    area = AreaPrograma.objects.create(identificador=identificador, nombre=nombre)
    return JsonResponse({
        "ok": True,
        "area": {"id": area.id, "identificador": area.identificador, "nombre": area.nombre},
    })


@login_required(login_url="/login/")
def editar_area_programa(request, id_area):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método no permitido"}, status=405)

    try:
        area = AreaPrograma.objects.get(id=id_area)
    except AreaPrograma.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Área no encontrada"}, status=404)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"ok": False, "error": "JSON inválido"}, status=400)

    identificador = (data.get("identificador") or "").strip()
    nombre = (data.get("nombre") or "").strip()

    if not identificador or not nombre:
        faltantes = []
        if not identificador: faltantes.append("Identificador")
        if not nombre: faltantes.append("Nombre")
        return JsonResponse(
            {"ok": False, "error": f"Campos requeridos: {', '.join(faltantes)}"},
            status=400,
        )

    if identificador != area.identificador and \
       AreaPrograma.objects.filter(identificador=identificador).exclude(id=area.id).exists():
        return JsonResponse(
            {"ok": False, "error": f"Ya existe otra área con el identificador '{identificador}'"},
            status=400,
        )

    area.identificador = identificador
    area.nombre = nombre
    area.save()

    return JsonResponse({
        "ok": True,
        "area": {"id": area.id, "identificador": area.identificador, "nombre": area.nombre},
    })


@login_required(login_url="/login/")
def parametros_area_programa(request):
    areas = ParametrosAreaPrograma.objects.select_related(
        "area_programa", "regional", "unidad_funcional",
        "punto_atencion", "centro_costo", "sede",
    ).all()
    ctx = {
        "areas": areas,
        "areas_programa": AreaPrograma.objects.order_by("identificador"),
        "regionales": Regional.objects.order_by("regional"),
        "unidades_funcionales": UnidadFuncional.objects.order_by("codigo"),
        "puntos_atencion": PuntoAtencion.objects.order_by("nombre"),
        "centros_costo": CentroCosto.objects.order_by("codigo"),
        "sedes": Sede.objects.order_by("razon_social"),
    }
    return render(request, "home/parametrosPrograma.html", ctx)


@login_required(login_url="/login/")
def crear_parametros_area_programa(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método no permitido"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"ok": False, "error": "JSON inválido"}, status=400)

    requeridos = {
        "area_programa_id": ("Área de programa", AreaPrograma),
        "regional_id": ("Regional", Regional),
        "unidad_funcional_id": ("Unidad funcional", UnidadFuncional),
        "punto_atencion_id": ("Punto de atención", PuntoAtencion),
        "centro_costo_id": ("Centro de costo", CentroCosto),
        "sede_id": ("Sede", Sede),
    }

    faltantes = [label for campo, (label, _) in requeridos.items() if not data.get(campo)]
    if faltantes:
        return JsonResponse(
            {"ok": False, "error": f"Campos requeridos: {', '.join(faltantes)}"},
            status=400,
        )

    resueltos = {}
    for campo, (label, Modelo) in requeridos.items():
        try:
            resueltos[campo.replace("_id", "")] = Modelo.objects.get(id=data[campo])
        except Modelo.DoesNotExist:
            return JsonResponse(
                {"ok": False, "error": f"{label} no válido (id {data[campo]})"},
                status=400,
            )

    parametros = ParametrosAreaPrograma.objects.create(
        area_programa=resueltos["area_programa"],
        regional=resueltos["regional"],
        unidad_funcional=resueltos["unidad_funcional"],
        punto_atencion=resueltos["punto_atencion"],
        centro_costo=resueltos["centro_costo"],
        sede=resueltos["sede"],
    )

    return JsonResponse({
        "ok": True,
        "parametros": {
            "id": parametros.id,
            "area": str(parametros.area_programa),
            "regional": str(parametros.regional),
        },
    })


@login_required(login_url="/login/")
def editar_parametros_area_programa(request, id_parametros):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método no permitido"}, status=405)

    try:
        parametros = ParametrosAreaPrograma.objects.get(id=id_parametros)
    except ParametrosAreaPrograma.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Parámetro no encontrado"}, status=404)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"ok": False, "error": "JSON inválido"}, status=400)

    requeridos = {
        "area_programa_id": ("Área de programa", AreaPrograma),
        "regional_id": ("Regional", Regional),
        "unidad_funcional_id": ("Unidad funcional", UnidadFuncional),
        "punto_atencion_id": ("Punto de atención", PuntoAtencion),
        "centro_costo_id": ("Centro de costo", CentroCosto),
        "sede_id": ("Sede", Sede),
    }

    faltantes = [label for campo, (label, _) in requeridos.items() if not data.get(campo)]
    if faltantes:
        return JsonResponse(
            {"ok": False, "error": f"Campos requeridos: {', '.join(faltantes)}"},
            status=400,
        )

    resueltos = {}
    for campo, (label, Modelo) in requeridos.items():
        try:
            resueltos[campo.replace("_id", "")] = Modelo.objects.get(id=data[campo])
        except Modelo.DoesNotExist:
            return JsonResponse(
                {"ok": False, "error": f"{label} no válido (id {data[campo]})"},
                status=400,
            )

    parametros.area_programa = resueltos["area_programa"]
    parametros.regional = resueltos["regional"]
    parametros.unidad_funcional = resueltos["unidad_funcional"]
    parametros.punto_atencion = resueltos["punto_atencion"]
    parametros.centro_costo = resueltos["centro_costo"]
    parametros.sede = resueltos["sede"]
    parametros.save()

    return JsonResponse({
        "ok": True,
        "parametros": {
            "id": parametros.id,
            "area": str(parametros.area_programa),
            "regional": str(parametros.regional),
        },
    })


@login_required(login_url="/login/")
def vista_contratos_marco(request):
    contratos_marco = ContratoMarco.objects.select_related(
        "contrato_subsidiado", "contrato_contributivo"
    ).order_by("numero")
    ctx = {
        "contratos_marco": contratos_marco,
        "contratos": Contrato.objects.filter(activo=1).order_by("codigo"),
    }
    return render(request, "home/contratosMarco.html", ctx)


@login_required(login_url="/login/")
def crear_contrato_marco(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método no permitido"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"ok": False, "error": "JSON inválido"}, status=400)

    numero = (data.get("numero") or "").strip()
    if not numero:
        return JsonResponse({"ok": False, "error": "Campo requerido: Número"}, status=400)

    if ContratoMarco.objects.filter(numero=numero).exists():
        return JsonResponse(
            {"ok": False, "error": f"Ya existe un contrato marco con el número '{numero}'"},
            status=400,
        )

    subsidiado = None
    contributivo = None
    if data.get("contrato_subsidiado_id"):
        try:
            subsidiado = Contrato.objects.get(id=data["contrato_subsidiado_id"])
        except Contrato.DoesNotExist:
            return JsonResponse(
                {"ok": False, "error": f"Contrato subsidiado no válido (id {data['contrato_subsidiado_id']})"},
                status=400,
            )
    if data.get("contrato_contributivo_id"):
        try:
            contributivo = Contrato.objects.get(id=data["contrato_contributivo_id"])
        except Contrato.DoesNotExist:
            return JsonResponse(
                {"ok": False, "error": f"Contrato contributivo no válido (id {data['contrato_contributivo_id']})"},
                status=400,
            )

    cm = ContratoMarco.objects.create(
        numero=numero,
        contrato_subsidiado=subsidiado,
        contrato_contributivo=contributivo,
        observacion=(data.get("observacion") or "").strip() or None,
    )

    return JsonResponse({
        "ok": True,
        "contrato_marco": {"id": cm.id, "numero": cm.numero},
    })


@login_required(login_url="/login/")
def editar_contrato_marco(request, id_contrato_marco):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método no permitido"}, status=405)

    try:
        cm = ContratoMarco.objects.get(id=id_contrato_marco)
    except ContratoMarco.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Contrato marco no encontrado"}, status=404)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"ok": False, "error": "JSON inválido"}, status=400)

    numero = (data.get("numero") or "").strip()
    if not numero:
        return JsonResponse({"ok": False, "error": "Campo requerido: Número"}, status=400)

    if numero != cm.numero and ContratoMarco.objects.filter(numero=numero).exclude(id=cm.id).exists():
        return JsonResponse(
            {"ok": False, "error": f"Ya existe otro contrato marco con el número '{numero}'"},
            status=400,
        )

    subsidiado = None
    contributivo = None
    if data.get("contrato_subsidiado_id"):
        try:
            subsidiado = Contrato.objects.get(id=data["contrato_subsidiado_id"])
        except Contrato.DoesNotExist:
            return JsonResponse(
                {"ok": False, "error": f"Contrato subsidiado no válido (id {data['contrato_subsidiado_id']})"},
                status=400,
            )
    if data.get("contrato_contributivo_id"):
        try:
            contributivo = Contrato.objects.get(id=data["contrato_contributivo_id"])
        except Contrato.DoesNotExist:
            return JsonResponse(
                {"ok": False, "error": f"Contrato contributivo no válido (id {data['contrato_contributivo_id']})"},
                status=400,
            )

    cm.numero = numero
    cm.contrato_subsidiado = subsidiado
    cm.contrato_contributivo = contributivo
    cm.observacion = (data.get("observacion") or "").strip() or None
    cm.save()

    return JsonResponse({
        "ok": True,
        "contrato_marco": {"id": cm.id, "numero": cm.numero},
    })


@login_required(login_url="/login/")
def vista_medicos(request):
    medicos = Medico.objects.order_by("nombre")
    ctx = {"medicos": medicos}
    return render(request, "home/medicos.html", ctx)


@login_required(login_url="/login/")
def informe_cargas(request):
    cargas_qs = (
        Carga.objects
        .select_related("usuario")
        .order_by("-id")
    )

    paginator = Paginator(cargas_qs, 25)
    numero_pagina = request.GET.get("page")
    try:
        pagina = paginator.page(numero_pagina)
    except PageNotAnInteger:
        pagina = paginator.page(1)
    except EmptyPage:
        pagina = paginator.page(paginator.num_pages)

    ctx = {
        "cargas": pagina.object_list,
        "pagina": pagina,
        "paginator": paginator,
    }
    return render(request, "home/informeCargas.html", ctx)


@login_required(login_url="/login/")
def listar_resumen_cargas(request):
    qs = Carga.objects.select_related("usuario").order_by("id")

    # Si el front envía ?ids=1,2,3 solo se refrescan esas filas — evita escanear
    # toda la tabla en cada poll cuando la página está paginada.
    ids_param = request.GET.get("ids", "")
    if ids_param:
        ids = [int(x) for x in ids_param.split(",") if x.isdigit()]
        if ids:
            qs = qs.filter(id__in=ids)
        else:
            return JsonResponse({"cargas": []}, safe=False)

    resumen = []
    for carga in qs:
        porcentaje_procesamiento = 0
        porcentaje_admisionado = 0

        if carga.estado == "procesando" and carga.cantidad_actividades > 0:
            procesadas = carga.cantidad_actividades_ok + carga.cantidad_actividades_inconsistencias
            porcentaje_procesamiento = min(int(procesadas / carga.cantidad_actividades * 100), 99)

        if carga.estado == "admisionando" and carga.cantidad_actividades > 0:
            # Las inconsistencias ya están "resueltas" (no se admisionarán),
            # por eso se suman al numerador junto con las admisionadas.
            resueltas = carga.cantidad_actividades_admisionadas + carga.cantidad_actividades_inconsistencias
            porcentaje_admisionado = min(int(resueltas / carga.cantidad_actividades * 100), 99)

        resumen.append({
            "id": carga.id,
            "usuario": str(carga.usuario) if carga.usuario else "",
            "estado": carga.estado,
            "cantidad_actividades": carga.cantidad_actividades,
            "cantidad_actividades_inconsistencias": carga.cantidad_actividades_inconsistencias,
            "cantidad_actividades_ok": carga.cantidad_actividades_ok,
            "cantidad_actividades_admisionadas": carga.cantidad_actividades_admisionadas,
            "tiempo_procesamiento": f"{carga.tiempo_procesamiento:.2f}",
            "observacion": carga.observacion or "",
            "created_at": carga.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": carga.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
            "ver_url": f"/verCarga/{carga.id}/1",
            "porcentaje_procesamiento": porcentaje_procesamiento,
            "porcentaje_admisionado": porcentaje_admisionado,
        })

    return JsonResponse({"cargas": resumen}, safe=False)

@login_required(login_url="/login/")
def ver_carga(request, id_carga, pagina):

    carga = Carga.objects.get(id= id_carga)

    resumen_inconsistencias = (
    Actividad.objects.values("inconsistencias")
    .filter(carga=carga, inconsistencias__isnull=False)
    .annotate(cantidad=Count("id"))
    .order_by("-cantidad")
    )
   
    print(resumen_inconsistencias)
    
    # actividades_carga = Actividad.objects.filter(carga = carga)

    # paginador = Paginator(actividades_carga, 10)
    # pagina_previa = int(pagina)-1
    # pagina_siguiente = int(pagina)+1
    
    ctx = {
        "carga":carga,
        "resumen_inconsistencias":resumen_inconsistencias,
        # "pagina":paginador.page(pagina),
        # "pagina_previa":pagina_previa,
        # "pagina_siguiente":pagina_siguiente,
        # "total_paginas":paginador.num_pages
    }
    return render(request,"home/verCarga.html",ctx)


@login_required(login_url="/login/")
def ver_actividad(request, id_actividad):
    relaciones = [
        "tipo_actividad",
        "tipo_actividad__contrato",
        "tipo_actividad__area",
        "tipo_actividad__tipo_servicio",
        "contrato",
        "contrato__contrato_subsidiado",
        "contrato__contrato_contributivo",
        "parametros_programa",
        "parametros_programa__area_programa",
        "parametros_programa__regional",
        "parametros_programa__unidad_funcional",
        "parametros_programa__punto_atencion",
        "parametros_programa__centro_costo",
        "parametros_programa__sede",
        "medico",
        "finalidad",
        "admision",
        "carga",
        "carga__usuario",
    ]
    actividad = (
        Actividad.objects
        .select_related(*relaciones)
        .get(id=int(id_actividad))
    )

    contrato_marco = actividad.contrato if actividad.contrato_id else (
        actividad.tipo_actividad.contrato if actividad.tipo_actividad else None
    )
    contrato_es_snapshot = bool(actividad.contrato_id)

    ctx = {
        "actividad": actividad,
        "contrato_marco": contrato_marco,
        "contrato_es_snapshot": contrato_es_snapshot,
        "datos_json_pretty": json.dumps(actividad.datos_json, indent=2, ensure_ascii=False) if actividad.datos_json else "",
        "admision_json_pretty": json.dumps(actividad.admision.json, indent=2, ensure_ascii=False) if actividad.admision and actividad.admision.json else "",
        "puede_editar": not actividad.admision_id and not actividad.admisionada_otra_carga,
    }
    return render(request, "home/verActividad.html", ctx)


@login_required(login_url="/login/")
def editar_actividad(request, id_actividad):
    """
    Edita campos clave de una actividad NO admisionada. Tras guardar,
    re-corre las validaciones de cargue para reflejar el estado real
    (OK ↔ con inconsistencia) y actualiza los contadores de la carga.

    Solo se editan los campos que suelen causar inconsistencias:
      tipo_documento, documento_paciente, documento_medico,
      tipo_actividad, tipo_usuario, diagnostico_p, fecha_servicio.

    Bloquea con 403 si la actividad ya está admisionada (tiene
    numero_estudio) o quedó marcada como admisionada en otra carga.
    """
    try:
        actividad = (
            Actividad.objects
            .select_related("tipo_actividad", "medico", "carga", "admision")
            .get(id=id_actividad)
        )
    except Actividad.DoesNotExist:
        return HttpResponse("Actividad no encontrada", status=404)

    if actividad.admision_id or actividad.admisionada_otra_carga:
        return HttpResponse(
            "No se puede editar: la actividad ya está admisionada o tiene número de estudio asociado.",
            status=403,
        )

    if request.method == "GET":
        tipos = TipoActividad.objects.order_by("nombre").only("id", "nombre", "cups")
        medicos = (
            Medico.objects
            .only("documento", "nombre", "codigo")
            .order_by("nombre")
        )
        ctx = {
            "actividad": actividad,
            "tipos_actividad": tipos,
            "medicos": medicos,
            "tipos_usuario": list(SIESA_LABELS.items()),
        }
        return render(request, "home/editarActividad.html", ctx)

    # POST — aplicar cambios y re-validar
    tipo_documento = (request.POST.get("tipo_documento") or "").strip().upper()
    documento_paciente = (request.POST.get("documento_paciente") or "").strip()
    documento_medico = (request.POST.get("documento_medico") or "").strip()
    tipo_actividad_id = (request.POST.get("tipo_actividad_id") or "").strip()
    tipo_usuario = (request.POST.get("tipo_usuario") or "").strip().upper()
    diagnostico_p = (request.POST.get("diagnostico_p") or "").strip()
    fecha_servicio_str = (request.POST.get("fecha_servicio") or "").strip()

    if not tipo_documento:
        return HttpResponseBadRequest("Tipo de documento es requerido")
    if not documento_paciente:
        return HttpResponseBadRequest("Documento del paciente es requerido")
    if not documento_medico:
        return HttpResponseBadRequest("Documento del médico es requerido")
    if not tipo_actividad_id:
        return HttpResponseBadRequest("Tipo de actividad es requerido")
    if not fecha_servicio_str:
        return HttpResponseBadRequest("Fecha de servicio es requerida")
    if tipo_usuario and tipo_usuario not in SIESA_LABELS:
        return HttpResponseBadRequest(
            f"Tipo de usuario inválido: {tipo_usuario!r}. "
            f"Valores válidos: {', '.join(SIESA_LABELS)} o vacío para auto-consulta."
        )

    try:
        fecha_servicio = datetime.strptime(fecha_servicio_str, "%Y-%m-%d").date()
    except ValueError:
        return HttpResponseBadRequest("Fecha de servicio inválida (formato YYYY-MM-DD)")

    try:
        tipo_actividad = TipoActividad.objects.get(id=int(tipo_actividad_id))
    except (ValueError, TipoActividad.DoesNotExist):
        return HttpResponseBadRequest("Tipo de actividad inválido")

    actividad.tipo_documento = tipo_documento
    actividad.documento_paciente = documento_paciente
    actividad.documento_medico = documento_medico
    actividad.tipo_actividad = tipo_actividad
    actividad.tipo_usuario = tipo_usuario or None
    actividad.diagnostico_p = diagnostico_p
    actividad.fecha_servicio = fecha_servicio

    revalidador.revalidar_actividad(actividad)

    if actividad.carga_id:
        carga = actividad.carga
        carga.actualizar_info_actividades()
        carga.save(update_fields=[
            "cantidad_actividades",
            "cantidad_actividades_ok",
            "cantidad_actividades_admisionadas",
            "cantidad_actividades_inconsistencias",
            "updated_at",
        ])

    return redirect("ver_actividad", id_actividad=actividad.id)


# PROCESAMIENTO DE ACTIVIDADES
@login_required(login_url="/login/")
def cargar_actividades(request):
    """
    Carga actividades desde un archivo Excel y las procesa.
    Valida el formato del archivo y retorna los datos como JSON.
    """
    try:
        # Validar que se haya subido un archivo
        if 'adjunto' not in request.FILES:
            return JsonResponse({'error': 'No se ha proporcionado ningún archivo'}, status=400)
            
        archivo_masivo = pd.read_excel(request.FILES["adjunto"])
        archivo_masivo = archivo_masivo.fillna("")
        
        # Definir encabezados esperados
        encabezados_esperados = [
            "tipo_identificacion", "numero_identificacion", "primer_apellido",
            "segundo_apellido", "primer_nombre", "segundo_nombre",
            "regional", "fecha_gestion", "nombre", "ciex", "medico_id", "finalidad"
        ]
        
        # Verificar columnas
        columnas_archivo = list(archivo_masivo.columns)
        if set(columnas_archivo) != set(encabezados_esperados):
            columnas_faltantes = set(encabezados_esperados) - set(columnas_archivo)
            columnas_adicionales = set(columnas_archivo) - set(encabezados_esperados)
            mensaje_error = "Error en el formato del archivo. "
            if columnas_faltantes:
                mensaje_error += f"Columnas faltantes: {', '.join(columnas_faltantes)}. "
            if columnas_adicionales:
                mensaje_error += f"Columnas adicionales: {', '.join(columnas_adicionales)}."
            return JsonResponse({'error': mensaje_error}, status=400)
        archivo_masivo = archivo_masivo[encabezados_esperados]
        
        # Procesar registros
        respuesta = []
        registros_vistos = set()  # Para controlar registros duplicados
        
        for fila in archivo_masivo.itertuples(index=False, name=None):
            # Crear una lista con los valores de la fila
            valores = list(fila)
            
            # Limpiar y formatear datos
            valores[1] = str(valores[1]).strip()  # numero_identificacion
            
            # Validar fechas - fecha_gestion, solo la fecha sin hora
            valores[7] = utils.validar_fecha(str(valores[7]).split(" ")[0])
            valores[9] = str(valores[9]).strip()  # ciex
            valores[10] = str(valores[10]).strip()  # medico_id
            valores[11] = str(valores[11]).strip()  # medico_id

            # Agregar estado
            valores.append("A procesar")
            
            # Convertir a tupla para poder usar como clave en el conjunto
            registro_tupla = tuple(valores)
            
            # Evitar duplicados
            if registro_tupla not in registros_vistos:
                registros_vistos.add(registro_tupla)
                respuesta.append(valores)
        
        return JsonResponse(respuesta, safe=False, status=200)
    
    except pd.errors.EmptyDataError:
        return JsonResponse({'error': 'El archivo está vacío'}, status=400)
    except pd.errors.ParserError:
        return JsonResponse({'error': 'No se pudo analizar el archivo. Verifique que sea un archivo Excel válido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Error al procesar el archivo: {str(e)}'}, status=500)

@login_required(login_url="/login/")
def procesarCargue(request):
    
    # Medir tiempo inicial
    tiempo_inicial = time.time()
    size_task = 2000
    
    try:
        # Obtener datos como JSON directamente (evitamos ast.literal_eval)
        datos = json.loads(request.POST["data"])
        
        # Datos y parámetros
        usuario_actual = request.user  # No necesitamos una consulta adicional
        actividades = datos.get('datos', [])
        cant_act = len(actividades)
        
        logger.info(f"Iniciando procesamiento de carga con {cant_act} actividades")
        
        # Crear carga (utilizamos transacción para asegurar integridad)
        with transaction.atomic():
            carga_actividades = Carga(
                usuario=usuario_actual,
                estado="procesando",
                cantidad_actividades=cant_act,
                observacion=datos.get("observacion", "")
            )
            carga_actividades.save()
            logger.debug(f"Carga ID {carga_actividades.id} creada correctamente")
        
        # Calcular número de bloques y crear tareas
        if cant_act > 0:
            # División en lotes más eficiente
            num_bloques = (cant_act + size_task - 1) // size_task  # Redondeo hacia arriba
            logger.info(f"Dividiendo {cant_act} actividades en {num_bloques} bloques")
            
            # Crear tareas asíncronas
            for i in range(num_bloques):
                inicio = i * size_task
                fin = min((i + 1) * size_task, cant_act)  # Evitar índices fuera de rango
                lote_actividades = actividades[inicio:fin]
                
                logger.debug(f"Creando tarea para lote {i}: {len(lote_actividades)} actividades")
                
                # Crear tarea asíncrona con batch_size optimizado
                async_task(
                    'home.modules.task.procesar_cargue_actividades', 
                    carga_actividades.id, 
                    lote_actividades, 
                    i, 
                    cant_act, 
                    tiempo_inicial,
                    task_name=f'carga_{carga_actividades.id}_lote_{i}',
                    group='cargue',  # Agrupar tareas para mejor gestión
                )
        
        # Preparar respuesta
        resultados_cargue = {
            "num_carga": carga_actividades.id,
            "estado": carga_actividades.estado,
            "mensaje": "Carga en proceso",
            "total_actividades": cant_act,
            "lotes": num_bloques if cant_act > 0 else 0
        }
        
        logger.info(f"Carga ID {carga_actividades.id} iniciada exitosamente con {num_bloques} lotes")
        return JsonResponse(resultados_cargue, safe=False)
    
    except Exception as e:
        # Manejo de errores para evitar fallos silenciosos
        logger.error(f"Error en procesarCargue: {str(e)}", exc_info=True)
        return JsonResponse({
            "estado": "error",
            "mensaje": f"Error al procesar la carga: {str(e)}"
        }, status=500)

@login_required(login_url="/login/")
def grabar_admision_prueba(request):
    cantidad = int(request.GET['cantidad'])
    print("CANTIDAD A ADMISIONAR: ", cantidad)
    num_lotes = cantidad // 2000 + (1 if cantidad % 2000 > 0 else 0)
    for i in range(num_lotes):
        inicio = i * 2000
        fin = min((i + 1) * 2000, cantidad)
        print(f"Creando tarea para lote {i}: {fin - inicio} actividades")
        
        # Crear tarea asíncrona con batch_size optimizado
        async_task(
            'home.modules.task.tarea_grabar_admisiones_prueba', 
            inicio, 
            fin, 
            task_name=f'lote_{i}',
            group='admision_prueba',  # Agrupar tareas para mejor gestión
        )
    
    return JsonResponse({"estado":"Admisiones de prueba en proceso"}, safe=False)

@login_required(login_url="/login/")
def consultar_admisiones_prueba(request):
    fecha_str = request.GET.get('fechaInicial')
    print(fecha_str)

    try:
        # Convierte string a objeto datetime (ajusta formato según cómo llegue)
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
    except (ValueError, TypeError):
        return JsonResponse({"error": "Fecha inválida"}, status=400)

    cantidad = Admision.objects.filter(
        created_at__gte=fecha,
        observacion="Admisión de prueba"   
    ).only("id").count()

    print(cantidad)
    return JsonResponse({"cantidad": cantidad}, safe=False)

@login_required(login_url="/login/")
def admisionar_actividades_carga(request, id_carga):
    carga = Carga.objects.get(id=int(id_carga))

    ids_pendientes = list(
        Actividad.objects
        .filter(carga=carga, admision__isnull=True, admisionada_otra_carga=False)
        .order_by("id")
        .values_list("id", flat=True)
    )
    total = len(ids_pendientes)

    if total == 0:
        logger.info("Carga %s no tiene actividades pendientes de admisionar", carga.id)
        return redirect('/informeCargas/')

    lote_size = max(
        settings.ADMISIONADO_LOTE_MIN,
        min(
            settings.ADMISIONADO_LOTE_MAX,
            -(-total // settings.ADMISIONADO_TARGET_TASKS),
        ),
    )
    num_lotes = -(-total // lote_size)

    carga.estado = "admisionando"
    carga.save(update_fields=["estado", "updated_at"])

    logger.info(
        "Admisionando carga %s: %s actividades, %s lotes de hasta %s",
        carga.id, total, num_lotes, lote_size,
    )

    for i in range(num_lotes):
        ids_lote = ids_pendientes[i * lote_size:(i + 1) * lote_size]
        async_task(
            'home.modules.task.tarea_admisionar_actividades_carga',
            carga.id,
            ids_lote,
            i,
            task_name=f'admision_carga_{carga.id}_lote_{i}',
            group=f'admision_carga_{carga.id}',
        )

    return redirect('/informeCargas/')

@login_required(login_url="/login/")
def admisionar_actividad_individual(request, id_actividad, pagina):
    actividad = Actividad.objects.get(id=id_actividad)
    async_task(
        'home.modules.task.tarea_admisionar_actividades_carga',
        actividad.carga.id,
        [id_actividad],
        0,
        task_name=f'admision_actividad_{id_actividad}',
    )
    return redirect(f'/verCarga/{actividad.carga.id}/{pagina}')

@login_required(login_url="/login/")
def eliminar_actividades_inconsistencia_carga(request, id_carga):
    tipo_inconsistencia = request.POST.get('tipo_inconsistencia', 'all')
    carga = Carga.objects.get(id = int(id_carga))
    actividades_carga_inconsistencia = Actividad.objects.filter(carga=carga).exclude(inconsistencias=None)
    if tipo_inconsistencia != 'all':
        actividades_carga_inconsistencia = actividades_carga_inconsistencia.filter(inconsistencias=tipo_inconsistencia)
    
    actividades_carga_inconsistencia.delete()
    carga.actualizar_info_actividades()
    carga.save()

    cantidad_actividaes_carga = Actividad.objects.filter(carga = carga).count()
    if cantidad_actividaes_carga == 0:
        carga.delete()
        return redirect(f'/informeCargas/')    
    return redirect(f'/verCarga/{id_carga}/1')

@login_required(login_url="/login/")
def eliminar_actividad_individual(request, id_actividad, pagina):
    actividad = Actividad.objects.get(id = int(id_actividad))
    carga = actividad.carga
    actividad.delete()

    carga.actualizar_info_actividades()
    carga.save()
    return redirect(f'/verCarga/{carga.id}/{pagina}')

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

# @login_required(login_url="/login/")    
# def descargar_archivo(request, nombre_archivo):
#     print("Archivo a descargar:",nombre_archivo)
#     FOLDER_MEDIA = 'media/'    
#     return FileResponse(open(FOLDER_MEDIA+nombre_archivo, 'rb'), as_attachment=True, filename = nombre_archivo)

# @login_required(login_url="/login/")
# def descargar_archivo(request, nombre_archivo):
#     print("Archivo a descargar:", nombre_archivo)
    
#     # Ruta segura usando MEDIA_ROOT
#     ruta_archivo = os.path.join(settings.MEDIA_ROOT, nombre_archivo)

#     # Verificación de existencia del archivo
#     if not os.path.exists(ruta_archivo):
#         raise Http404("El archivo no existe.")

#     # Retornar el archivo como descarga
#     return FileResponse(open(ruta_archivo, 'rb'), as_attachment=True, filename=nombre_archivo)

def descargar_archivo(request, nombre_archivo):
    # Ruta absoluta al directorio "Formatos" (mismo nivel que media/)
    carpeta_formatos = os.path.join(settings.BASE_DIR, 'formatos')
    
    # Construir ruta completa al archivo
    ruta_archivo = os.path.join(carpeta_formatos, nombre_archivo)

    logger.info(f"Descarga solicitada: {ruta_archivo}")

    # Verifica si el archivo existe
    if not os.path.isfile(ruta_archivo):
        logger.warning(f"Archivo no encontrado: {ruta_archivo}")
        raise Http404("El archivo no existe.")

    try:
        return FileResponse(open(ruta_archivo, 'rb'), as_attachment=True, filename=nombre_archivo)
    except PermissionError as e:
        logger.error(f"Permiso denegado: {ruta_archivo} - {e}")
        return HttpResponseServerError("Error de permisos al acceder al archivo.")
    except Exception as e:
        logger.error(f"Error inesperado: {ruta_archivo} - {e}")
        return HttpResponseServerError("Error inesperado al descargar el archivo.")


@login_required(login_url="/login/")    
def exportar_carga_excel(request, id_carga,tipo):
    FOLDER_MEDIA = 'home\exports/'
    nombre_archivo = 'listado_actividades_carga.xlsx'
    print(id_carga)
    if tipo == "all":
        print(tipo)
        actividades_carga = Actividad.objects.filter(carga = id_carga)
    if tipo == 'inconsistencias':  
        print(tipo)
        actividades_carga = Actividad.objects.filter(carga = id_carga).exclude(inconsistencias = None)
        print(actividades_carga)
    if tipo == 'admisionadas':
        print(tipo)
        actividades_carga = Actividad.objects.filter(carga = id_carga).exclude(admision = None)
    if tipo == 'admisionar':
        print(tipo)
        actividades_carga = Actividad.objects.filter(carga = id_carga).filter(admision = None, inconsistencias = None)

    generador_excel.genera_excel_carga(actividades_carga)
    return FileResponse(open(FOLDER_MEDIA+nombre_archivo, 'rb'), as_attachment=True, filename = nombre_archivo)


# ═══════════════════════════════════════════════════════════════════════════
#  FUENTES DE TIPO DE USUARIO — admin del módulo configurable (Fase 3)
# ═══════════════════════════════════════════════════════════════════════════

import re

from django.utils import timezone

from home.models import (
    FuenteTipoUsuario,
    ReglaHomologacionSIESA,
    NormalizacionTipoAfiliado,
)
from home.modules.crypto import decrypt as _decrypt_password
from home.modules.crypto import encrypt as _encrypt_password
from home.modules.tipo_usuario import source_admin_helpers as _sah


# ─── helpers ───────────────────────────────────────────────────────────────

def _json_post(request):
    """Devuelve dict del body JSON o lanza JsonResponse 400."""
    try:
        return json.loads(request.body.decode("utf-8") or "{}")
    except (ValueError, UnicodeDecodeError):
        return None


def _resolver_creds(data, requerir_password: bool = True):
    """
    Devuelve dict con (servidor, usuario, password, driver, base_datos) o None
    si falta algo crítico. Si `id_fuente` está set y `password` viene vacío,
    descifra la del registro existente. Útil para AJAX de probar conexión
    sobre una fuente ya guardada sin pedir re-tipear el password.
    """
    id_fuente = data.get("id_fuente")
    servidor = (data.get("servidor") or "").strip()
    usuario = (data.get("usuario") or "").strip()
    password = data.get("password") or ""
    driver = (data.get("driver") or "").strip() or "SQL Server"
    base_datos = (data.get("base_datos") or "").strip()

    if id_fuente:
        try:
            fuente = FuenteTipoUsuario.objects.get(id=id_fuente)
        except FuenteTipoUsuario.DoesNotExist:
            return None
        if not password:
            try:
                password = _decrypt_password(fuente.password_encrypted)
            except Exception:
                # Si falla el descifrado, dejamos que el caller lo detecte
                password = ""
        servidor = servidor or fuente.servidor
        usuario = usuario or fuente.usuario
        driver = driver if data.get("driver") else (fuente.driver or driver)
        base_datos = base_datos if data.get("base_datos") is not None else (fuente.base_datos or "")

    if not (servidor and usuario):
        return None
    if requerir_password and not password:
        return None

    return {
        "servidor": servidor,
        "usuario": usuario,
        "password": password,
        "driver": driver,
        "base_datos": base_datos,
    }


def _serialize_fuente(fuente: FuenteTipoUsuario) -> dict:
    return {
        "id": fuente.id,
        "nombre": fuente.nombre,
        "descripcion": fuente.descripcion,
        "activa": fuente.activa,
        "prioridad": fuente.prioridad,
        "servidor": fuente.servidor,
        "base_datos": fuente.base_datos,
        "usuario": fuente.usuario,
        "driver": fuente.driver,
        "tabla": fuente.tabla,
        "campo_documento": fuente.campo_documento,
        "campo_tipo_documento": fuente.campo_tipo_documento,
        "campo_regimen": fuente.campo_regimen,
        "campo_tipo_afiliado": fuente.campo_tipo_afiliado,
        "estado_validacion": fuente.estado_validacion,
        "mensaje_validacion": fuente.mensaje_validacion,
        "ultima_validacion_at": (
            fuente.ultima_validacion_at.isoformat() if fuente.ultima_validacion_at else None
        ),
    }


_RX_SQL_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*){0,2}$")


def _validar_mapeo(tabla, campo_documento, campo_regimen, campo_tipo_afiliado,
                   campo_tipo_documento=""):
    """Valida identificadores SQL. Devuelve mensaje de error o None.

    `campo_tipo_documento` es opcional — se valida solo si viene con valor.
    """
    items = [
        ("Tabla", tabla),
        ("Campo documento", campo_documento),
        ("Campo régimen", campo_regimen),
        ("Campo tipo afiliado", campo_tipo_afiliado),
    ]
    for label, valor in items:
        if not valor:
            return f"{label} es requerido"
        if not _RX_SQL_IDENT.match(valor):
            return (
                f"{label} inválido: '{valor}'. Sólo letras, dígitos, "
                "guion bajo y hasta dos puntos de separación."
            )
    if campo_tipo_documento and not _RX_SQL_IDENT.match(campo_tipo_documento):
        return (
            f"Campo tipo documento inválido: '{campo_tipo_documento}'. "
            "Sólo letras, dígitos, guion bajo y hasta dos puntos de separación."
        )
    return None


# ─── listado y CRUD de fuentes ─────────────────────────────────────────────

@login_required(login_url="/login/")
def vista_fuentes_tipo_usuario(request):
    fuentes = FuenteTipoUsuario.objects.all().order_by("prioridad", "nombre")
    ctx = {"fuentes": fuentes}
    return render(request, "home/fuentesTipoUsuario.html", ctx)


@login_required(login_url="/login/")
def crear_fuente_tipo_usuario(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método no permitido"}, status=405)
    data = _json_post(request)
    if data is None:
        return JsonResponse({"ok": False, "error": "JSON inválido"}, status=400)

    nombre = (data.get("nombre") or "").strip()
    if not nombre:
        return JsonResponse({"ok": False, "error": "Nombre requerido"}, status=400)
    if FuenteTipoUsuario.objects.filter(nombre=nombre).exists():
        return JsonResponse(
            {"ok": False, "error": f"Ya existe una fuente con nombre '{nombre}'"},
            status=400,
        )

    error_mapeo = _validar_mapeo(
        (data.get("tabla") or "").strip(),
        (data.get("campo_documento") or "").strip(),
        (data.get("campo_regimen") or "").strip(),
        (data.get("campo_tipo_afiliado") or "").strip(),
        (data.get("campo_tipo_documento") or "").strip(),
    )
    if error_mapeo:
        return JsonResponse({"ok": False, "error": error_mapeo}, status=400)

    servidor = (data.get("servidor") or "").strip()
    usuario = (data.get("usuario") or "").strip()
    password = data.get("password") or ""
    if not (servidor and usuario and password):
        return JsonResponse(
            {"ok": False, "error": "Servidor, usuario y contraseña son requeridos"},
            status=400,
        )

    try:
        password_encrypted = _encrypt_password(password)
    except Exception as e:
        return JsonResponse(
            {"ok": False, "error": f"No se pudo cifrar la contraseña: {e}"},
            status=500,
        )

    try:
        prioridad = int(data.get("prioridad") or 100)
    except (TypeError, ValueError):
        prioridad = 100

    fuente = FuenteTipoUsuario.objects.create(
        nombre=nombre,
        descripcion=(data.get("descripcion") or "").strip(),
        activa=bool(data.get("activa", True)),
        prioridad=prioridad,
        servidor=servidor,
        base_datos=(data.get("base_datos") or "").strip(),
        usuario=usuario,
        password_encrypted=password_encrypted,
        driver=(data.get("driver") or "SQL Server").strip(),
        tabla=(data.get("tabla") or "").strip(),
        campo_documento=(data.get("campo_documento") or "").strip(),
        campo_tipo_documento=(data.get("campo_tipo_documento") or "").strip(),
        campo_regimen=(data.get("campo_regimen") or "").strip(),
        campo_tipo_afiliado=(data.get("campo_tipo_afiliado") or "").strip(),
    )
    return JsonResponse({"ok": True, "fuente": _serialize_fuente(fuente)})


@login_required(login_url="/login/")
def editar_fuente_tipo_usuario(request, id_fuente):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método no permitido"}, status=405)
    try:
        fuente = FuenteTipoUsuario.objects.get(id=id_fuente)
    except FuenteTipoUsuario.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Fuente no encontrada"}, status=404)

    data = _json_post(request)
    if data is None:
        return JsonResponse({"ok": False, "error": "JSON inválido"}, status=400)

    nombre = (data.get("nombre") or "").strip()
    if not nombre:
        return JsonResponse({"ok": False, "error": "Nombre requerido"}, status=400)
    if FuenteTipoUsuario.objects.filter(nombre=nombre).exclude(id=fuente.id).exists():
        return JsonResponse(
            {"ok": False, "error": f"Ya existe otra fuente con nombre '{nombre}'"},
            status=400,
        )

    error_mapeo = _validar_mapeo(
        (data.get("tabla") or "").strip(),
        (data.get("campo_documento") or "").strip(),
        (data.get("campo_regimen") or "").strip(),
        (data.get("campo_tipo_afiliado") or "").strip(),
        (data.get("campo_tipo_documento") or "").strip(),
    )
    if error_mapeo:
        return JsonResponse({"ok": False, "error": error_mapeo}, status=400)

    fuente.nombre = nombre
    fuente.descripcion = (data.get("descripcion") or "").strip()
    fuente.activa = bool(data.get("activa", fuente.activa))
    try:
        fuente.prioridad = int(data.get("prioridad") or fuente.prioridad)
    except (TypeError, ValueError):
        pass
    fuente.servidor = (data.get("servidor") or "").strip() or fuente.servidor
    fuente.base_datos = (data.get("base_datos") or "").strip()
    fuente.usuario = (data.get("usuario") or "").strip() or fuente.usuario
    fuente.driver = (data.get("driver") or "").strip() or fuente.driver
    fuente.tabla = (data.get("tabla") or "").strip()
    fuente.campo_documento = (data.get("campo_documento") or "").strip()
    fuente.campo_tipo_documento = (data.get("campo_tipo_documento") or "").strip()
    fuente.campo_regimen = (data.get("campo_regimen") or "").strip()
    fuente.campo_tipo_afiliado = (data.get("campo_tipo_afiliado") or "").strip()

    password = data.get("password") or ""
    if password:
        try:
            fuente.password_encrypted = _encrypt_password(password)
        except Exception as e:
            return JsonResponse(
                {"ok": False, "error": f"No se pudo cifrar la contraseña: {e}"},
                status=500,
            )

    fuente.save()
    return JsonResponse({"ok": True, "fuente": _serialize_fuente(fuente)})


@login_required(login_url="/login/")
def toggle_activa_fuente(request, id_fuente):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método no permitido"}, status=405)
    try:
        fuente = FuenteTipoUsuario.objects.get(id=id_fuente)
    except FuenteTipoUsuario.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Fuente no encontrada"}, status=404)
    fuente.activa = not fuente.activa
    fuente.save(update_fields=["activa", "updated_at"])
    return JsonResponse({"ok": True, "activa": fuente.activa})


@login_required(login_url="/login/")
def eliminar_fuente_tipo_usuario(request, id_fuente):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método no permitido"}, status=405)
    try:
        fuente = FuenteTipoUsuario.objects.get(id=id_fuente)
    except FuenteTipoUsuario.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Fuente no encontrada"}, status=404)
    fuente.delete()
    return JsonResponse({"ok": True})


# ─── AJAX: inspección SQL desde el wizard ──────────────────────────────────

@login_required(login_url="/login/")
def probar_conexion_fuente(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método no permitido"}, status=405)
    data = _json_post(request)
    if data is None:
        return JsonResponse({"ok": False, "error": "JSON inválido"}, status=400)

    creds = _resolver_creds(data)
    if creds is None:
        return JsonResponse(
            {"ok": False, "error": "Servidor, usuario y contraseña son requeridos"},
            status=400,
        )

    ok, mensaje = _sah.test_conexion(**creds)

    # Si la fuente existe, persistir el resultado
    id_fuente = data.get("id_fuente")
    if id_fuente:
        try:
            fuente = FuenteTipoUsuario.objects.get(id=id_fuente)
            fuente.estado_validacion = (
                FuenteTipoUsuario.ESTADO_OK if ok else FuenteTipoUsuario.ESTADO_ERROR
            )
            fuente.mensaje_validacion = mensaje
            fuente.ultima_validacion_at = timezone.now()
            fuente.save(update_fields=[
                "estado_validacion", "mensaje_validacion",
                "ultima_validacion_at", "updated_at",
            ])
        except FuenteTipoUsuario.DoesNotExist:
            pass

    return JsonResponse({"ok": ok, "mensaje": mensaje})


@login_required(login_url="/login/")
def listar_bases_datos_fuente(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método no permitido"}, status=405)
    data = _json_post(request)
    if data is None:
        return JsonResponse({"ok": False, "error": "JSON inválido"}, status=400)

    creds = _resolver_creds(data)
    if creds is None:
        return JsonResponse(
            {"ok": False, "error": "Servidor, usuario y contraseña son requeridos"},
            status=400,
        )

    try:
        bases = _sah.listar_bases_datos(
            servidor=creds["servidor"], usuario=creds["usuario"],
            password=creds["password"], driver=creds["driver"],
        )
        return JsonResponse({"ok": True, "bases_datos": bases})
    except Exception as e:
        logger.exception("listar_bases_datos_fuente fallo")
        return JsonResponse({"ok": False, "error": f"{type(e).__name__}: {e}"}, status=400)


@login_required(login_url="/login/")
def listar_tablas_fuente(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método no permitido"}, status=405)
    data = _json_post(request)
    if data is None:
        return JsonResponse({"ok": False, "error": "JSON inválido"}, status=400)

    creds = _resolver_creds(data)
    if creds is None:
        return JsonResponse(
            {"ok": False, "error": "Servidor, usuario y contraseña son requeridos"},
            status=400,
        )
    base_datos = (data.get("base_datos") or creds["base_datos"] or "").strip()
    if not base_datos:
        return JsonResponse(
            {"ok": False, "error": "Base de datos requerida para listar tablas"},
            status=400,
        )

    try:
        tablas = _sah.listar_tablas(
            servidor=creds["servidor"], usuario=creds["usuario"],
            password=creds["password"], driver=creds["driver"],
            base_datos=base_datos,
        )
        # Devolver con prefijo de DB para que el campo `tabla` quede completo.
        tablas_full = [f"{base_datos}.{t}" for t in tablas]
        return JsonResponse({"ok": True, "tablas": tablas_full})
    except Exception as e:
        logger.exception("listar_tablas_fuente fallo")
        return JsonResponse({"ok": False, "error": f"{type(e).__name__}: {e}"}, status=400)


@login_required(login_url="/login/")
def listar_columnas_fuente(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método no permitido"}, status=405)
    data = _json_post(request)
    if data is None:
        return JsonResponse({"ok": False, "error": "JSON inválido"}, status=400)

    creds = _resolver_creds(data)
    if creds is None:
        return JsonResponse(
            {"ok": False, "error": "Servidor, usuario y contraseña son requeridos"},
            status=400,
        )
    tabla = (data.get("tabla") or "").strip()
    if not tabla:
        return JsonResponse({"ok": False, "error": "Tabla requerida"}, status=400)

    # `tabla` puede venir como "DB.schema.nombre" o "schema.nombre" o "nombre".
    partes = tabla.split(".")
    if len(partes) == 3:
        base_datos = partes[0]
        tabla_sin_db = ".".join(partes[1:])
    elif len(partes) in (1, 2):
        base_datos = (data.get("base_datos") or creds["base_datos"] or "").strip()
        tabla_sin_db = tabla
    else:
        return JsonResponse({"ok": False, "error": f"Formato de tabla inválido: {tabla}"}, status=400)

    if not base_datos:
        return JsonResponse(
            {"ok": False, "error": "Base de datos requerida (en `base_datos` o como prefijo de tabla)"},
            status=400,
        )

    try:
        columnas = _sah.listar_columnas(
            servidor=creds["servidor"], usuario=creds["usuario"],
            password=creds["password"], driver=creds["driver"],
            base_datos=base_datos, tabla=tabla_sin_db,
        )
        return JsonResponse({"ok": True, "columnas": columnas})
    except Exception as e:
        logger.exception("listar_columnas_fuente fallo")
        return JsonResponse({"ok": False, "error": f"{type(e).__name__}: {e}"}, status=400)


# ─── reglas SIESA y normalizaciones ────────────────────────────────────────

def _serialize_regla(r: ReglaHomologacionSIESA) -> dict:
    return {
        "id": r.id,
        "fuente_id": r.fuente_id,
        "fuente_nombre": r.fuente.nombre if r.fuente_id else None,
        "regimen": r.regimen,
        "tipo_afiliado_codigo": r.tipo_afiliado_codigo,
        "codigo_siesa": r.codigo_siesa,
        "descripcion": r.descripcion,
    }


def _serialize_normalizacion(n: NormalizacionTipoAfiliado) -> dict:
    return {
        "id": n.id,
        "fuente_id": n.fuente_id,
        "fuente_nombre": n.fuente.nombre if n.fuente_id else None,
        "valor_crudo": n.valor_crudo,
        "codigo_normalizado": n.codigo_normalizado,
    }


def _resolver_fuente_id(data):
    """Devuelve (fuente_id_or_None, error_msg_or_None)."""
    fuente_id = data.get("fuente_id")
    if fuente_id in ("", None, 0, "0"):
        return None, None
    try:
        fuente_id = int(fuente_id)
    except (TypeError, ValueError):
        return None, "fuente_id inválido"
    if not FuenteTipoUsuario.objects.filter(id=fuente_id).exists():
        return None, f"Fuente {fuente_id} no encontrada"
    return fuente_id, None


@login_required(login_url="/login/")
def vista_reglas_homologacion(request):
    reglas = (
        ReglaHomologacionSIESA.objects
        .select_related("fuente")
        .order_by("fuente_id", "regimen", "tipo_afiliado_codigo")
    )
    normalizaciones = (
        NormalizacionTipoAfiliado.objects
        .select_related("fuente")
        .order_by("fuente_id", "valor_crudo")
    )
    fuentes = FuenteTipoUsuario.objects.all().order_by("prioridad", "nombre")
    ctx = {
        "reglas": reglas,
        "normalizaciones": normalizaciones,
        "fuentes": fuentes,
    }
    return render(request, "home/reglasHomologacion.html", ctx)


@login_required(login_url="/login/")
def crear_regla_siesa(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método no permitido"}, status=405)
    data = _json_post(request)
    if data is None:
        return JsonResponse({"ok": False, "error": "JSON inválido"}, status=400)

    regimen = (data.get("regimen") or "").strip().upper()
    tipo = (data.get("tipo_afiliado_codigo") or "").strip().upper()
    siesa = (data.get("codigo_siesa") or "").strip()
    descripcion = (data.get("descripcion") or "").strip()
    if not (regimen and tipo and siesa):
        return JsonResponse(
            {"ok": False, "error": "Régimen, tipo afiliado y código SIESA son requeridos"},
            status=400,
        )

    fuente_id, err = _resolver_fuente_id(data)
    if err:
        return JsonResponse({"ok": False, "error": err}, status=400)

    # Chequeo de duplicado (replica la UNIQUE parcial para devolver mensaje claro)
    dup_qs = ReglaHomologacionSIESA.objects.filter(
        fuente_id=fuente_id, regimen=regimen, tipo_afiliado_codigo=tipo,
    )
    if dup_qs.exists():
        scope = f"fuente {fuente_id}" if fuente_id else "global"
        return JsonResponse(
            {"ok": False, "error": f"Ya existe una regla {scope} para {regimen}+{tipo}"},
            status=400,
        )

    regla = ReglaHomologacionSIESA.objects.create(
        fuente_id=fuente_id,
        regimen=regimen,
        tipo_afiliado_codigo=tipo,
        codigo_siesa=siesa,
        descripcion=descripcion,
    )
    return JsonResponse({"ok": True, "regla": _serialize_regla(regla)})


@login_required(login_url="/login/")
def editar_regla_siesa(request, id_regla):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método no permitido"}, status=405)
    try:
        regla = ReglaHomologacionSIESA.objects.get(id=id_regla)
    except ReglaHomologacionSIESA.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Regla no encontrada"}, status=404)

    data = _json_post(request)
    if data is None:
        return JsonResponse({"ok": False, "error": "JSON inválido"}, status=400)

    regimen = (data.get("regimen") or "").strip().upper()
    tipo = (data.get("tipo_afiliado_codigo") or "").strip().upper()
    siesa = (data.get("codigo_siesa") or "").strip()
    descripcion = (data.get("descripcion") or "").strip()
    if not (regimen and tipo and siesa):
        return JsonResponse(
            {"ok": False, "error": "Régimen, tipo afiliado y código SIESA son requeridos"},
            status=400,
        )

    fuente_id, err = _resolver_fuente_id(data)
    if err:
        return JsonResponse({"ok": False, "error": err}, status=400)

    # Chequeo de duplicado excluyendo a sí misma
    dup_qs = (
        ReglaHomologacionSIESA.objects
        .filter(fuente_id=fuente_id, regimen=regimen, tipo_afiliado_codigo=tipo)
        .exclude(id=regla.id)
    )
    if dup_qs.exists():
        scope = f"fuente {fuente_id}" if fuente_id else "global"
        return JsonResponse(
            {"ok": False, "error": f"Ya existe otra regla {scope} para {regimen}+{tipo}"},
            status=400,
        )

    regla.fuente_id = fuente_id
    regla.regimen = regimen
    regla.tipo_afiliado_codigo = tipo
    regla.codigo_siesa = siesa
    regla.descripcion = descripcion
    regla.save()
    return JsonResponse({"ok": True, "regla": _serialize_regla(regla)})


@login_required(login_url="/login/")
def eliminar_regla_siesa(request, id_regla):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método no permitido"}, status=405)
    try:
        regla = ReglaHomologacionSIESA.objects.get(id=id_regla)
    except ReglaHomologacionSIESA.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Regla no encontrada"}, status=404)
    regla.delete()
    return JsonResponse({"ok": True})


@login_required(login_url="/login/")
def crear_normalizacion(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método no permitido"}, status=405)
    data = _json_post(request)
    if data is None:
        return JsonResponse({"ok": False, "error": "JSON inválido"}, status=400)

    valor_crudo = (data.get("valor_crudo") or "").strip()
    codigo = (data.get("codigo_normalizado") or "").strip()
    if not (valor_crudo and codigo):
        return JsonResponse(
            {"ok": False, "error": "Valor crudo y código normalizado son requeridos"},
            status=400,
        )

    fuente_id, err = _resolver_fuente_id(data)
    if err:
        return JsonResponse({"ok": False, "error": err}, status=400)

    dup_qs = NormalizacionTipoAfiliado.objects.filter(
        fuente_id=fuente_id, valor_crudo=valor_crudo,
    )
    if dup_qs.exists():
        scope = f"fuente {fuente_id}" if fuente_id else "global"
        return JsonResponse(
            {"ok": False, "error": f"Ya existe una normalización {scope} para '{valor_crudo}'"},
            status=400,
        )

    norm = NormalizacionTipoAfiliado.objects.create(
        fuente_id=fuente_id,
        valor_crudo=valor_crudo,
        codigo_normalizado=codigo,
    )
    return JsonResponse({"ok": True, "normalizacion": _serialize_normalizacion(norm)})


@login_required(login_url="/login/")
def editar_normalizacion(request, id_norm):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método no permitido"}, status=405)
    try:
        norm = NormalizacionTipoAfiliado.objects.get(id=id_norm)
    except NormalizacionTipoAfiliado.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Normalización no encontrada"}, status=404)

    data = _json_post(request)
    if data is None:
        return JsonResponse({"ok": False, "error": "JSON inválido"}, status=400)

    valor_crudo = (data.get("valor_crudo") or "").strip()
    codigo = (data.get("codigo_normalizado") or "").strip()
    if not (valor_crudo and codigo):
        return JsonResponse(
            {"ok": False, "error": "Valor crudo y código normalizado son requeridos"},
            status=400,
        )

    fuente_id, err = _resolver_fuente_id(data)
    if err:
        return JsonResponse({"ok": False, "error": err}, status=400)

    dup_qs = (
        NormalizacionTipoAfiliado.objects
        .filter(fuente_id=fuente_id, valor_crudo=valor_crudo)
        .exclude(id=norm.id)
    )
    if dup_qs.exists():
        scope = f"fuente {fuente_id}" if fuente_id else "global"
        return JsonResponse(
            {"ok": False, "error": f"Ya existe otra normalización {scope} para '{valor_crudo}'"},
            status=400,
        )

    norm.fuente_id = fuente_id
    norm.valor_crudo = valor_crudo
    norm.codigo_normalizado = codigo
    norm.save()
    return JsonResponse({"ok": True, "normalizacion": _serialize_normalizacion(norm)})


@login_required(login_url="/login/")
def eliminar_normalizacion(request, id_norm):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método no permitido"}, status=405)
    try:
        norm = NormalizacionTipoAfiliado.objects.get(id=id_norm)
    except NormalizacionTipoAfiliado.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Normalización no encontrada"}, status=404)
    norm.delete()
    return JsonResponse({"ok": True})

