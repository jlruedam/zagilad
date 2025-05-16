# DJANGO
from django.shortcuts import render, redirect 
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect, JsonResponse, FileResponse
from django.core.serializers import json
from django.core import serializers
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q, Count
from django.db import transaction


# PYTHON
from datetime import datetime, date
import ast, time
import pandas as pd
import numpy as np
import json
import logging

# ZAGILAD
from home.models import TipoActividad, Actividad, ParametrosAreaPrograma
from home.models import Admision, AreaPrograma, Carga
from home.modules import peticiones_http, parametros_generales
from home.modules import generador_excel, utils
from home.modules import paginacion_actividades


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
    tipos_actividad = TipoActividad.objects.all()
    ctx = {"tipos_actividad":tipos_actividad}
    return render(request,"home/tiposActividad.html",ctx)

@login_required(login_url="/login/")
def parametros_area_programa(request):
    areas = ParametrosAreaPrograma.objects.all()
    ctx = {"areas":areas}
    return render(request,"home/parametrosPrograma.html",ctx)

@login_required(login_url="/login/")
def informe_cargas(request):
    cargas = Carga.objects.all()

    for carga in cargas:
        carga.actualizar_info_actividades()

    ctx = {"cargas":cargas}
    return render(request,"home/informeCargas.html",ctx)

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
            "regional", "fecha_gestion", "nombre", "ciex", "medico_id"
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
        
        # Procesar registros
        respuesta = []
        registros_vistos = set()  # Para controlar registros duplicados
        
        for _, fila in archivo_masivo.iterrows():
            # Crear una lista con los valores de la fila
            valores = fila.tolist()
            
            # Limpiar y formatear datos
            valores[1] = str(valores[1]).strip()  # numero_identificacion
            # Validar fechas - fecha_gestion, solo la fecha sin hora
            valores[7] = utils.validar_fecha(str(valores[7]).split(" ")[0])
            valores[9] = str(valores[9]).strip()  # ciex
            valores[10] = str(valores[10]).strip()  # medico_id
            # Agregar estado
            valores.append("A procesar")
            
            # Convertir a tupla para poder usar como clave en el conjunto
            registro_tupla = tuple(valores)
            
            # Evitar duplicados
            if registro_tupla not in registros_vistos:
                registros_vistos.add(registro_tupla)
                respuesta.append(valores)
        
        return JsonResponse(respuesta, safe=False)
    
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
    try:
        token = peticiones_http.obtener_token()
        print(token)
    except Exception as e:
        print(e)
        return HttpResponseBadRequest("No se pudo obtener el token de acceso", e)
    carga = Carga.objects.get(id = int(id_carga))
    carga.estado = "admisionando"
    carga.save()
    # task.tarea_admisionar_actividades_carga.delay(token, id_carga)
    async_task('home.modules.task.tarea_admisionar_actividades_carga', token, id_carga)
    
    return redirect(f'/informeCargas/')

@login_required(login_url="/login/")
def admisionar_actividad_individual(request, id_actividad, pagina):
    token = peticiones_http.obtener_token()
    actividad = Actividad.objects.get(id = id_actividad)
    # task.tarea_admisionar_actividades_carga.delay(token, actividad.carga.id, id_actividad)
    async_task('home.modules.task.tarea_admisionar_actividades_carga', token, actividad.carga.id, id_actividad)
    return redirect(f'/verCarga/{actividad.carga.id}/{pagina}')

@login_required(login_url="/login/")
def eliminar_actividades_inconsistencia_carga(request, id_carga, tipo_inconsistencia = None):
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

@login_required(login_url="/login/")    
def descargar_archivo(request, nombre_archivo):
    print("Archivo a descargar:",nombre_archivo)
    FOLDER_MEDIA = 'media/'    
    return FileResponse(open(FOLDER_MEDIA+nombre_archivo, 'rb'), as_attachment=True, filename = nombre_archivo)

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