from __future__ import absolute_import
# PYTHON
import ast,time
import collections
import json
import logging
import os
import random

# DJANGO Q
from django_q.models import Task
from django_q.models import OrmQ
from django.conf import settings
from django.db import transaction
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
from home.modules import tipo_usuario as tipo_usuario_service

logger = logging.getLogger(__name__)


def _valor_limpio(valor):
    return "" if valor is None else str(valor).strip()


def _clave_json(valor):
    return json.dumps(valor, default=str, ensure_ascii=False, separators=(",", ":"))


def _valor_clave(valor):
    return "" if valor is None else str(valor)


def _clave_actividad(actividad):
    tipo_actividad_id = actividad.tipo_actividad_id
    if tipo_actividad_id is None and actividad.tipo_actividad:
        tipo_actividad_id = actividad.tipo_actividad.id

    medico_id = actividad.medico_id
    if medico_id is None and actividad.medico:
        medico_id = actividad.medico.id

    return (
        _valor_clave(actividad.regional),
        _valor_clave(actividad.fecha_servicio),
        _valor_clave(actividad.nombre_actividad),
        tipo_actividad_id,
        _valor_clave(actividad.diagnostico_p),
        _valor_clave(actividad.diagnostico_1),
        _valor_clave(actividad.diagnostico_2),
        _valor_clave(actividad.diagnostico_3),
        _valor_clave(actividad.tipo_documento),
        _valor_clave(actividad.documento_paciente),
        _valor_clave(actividad.nombre_paciente),
        medico_id,
    )


def _clave_actividad_desde_bd(fila):
    return (
        _valor_clave(fila[0]),
        _valor_clave(fila[1]),
        _valor_clave(fila[2]),
        fila[3],
        _valor_clave(fila[4]),
        _valor_clave(fila[5]),
        _valor_clave(fila[6]),
        _valor_clave(fila[7]),
        _valor_clave(fila[8]),
        _valor_clave(fila[9]),
        _valor_clave(fila[10]),
        fila[11],
    )


def _es_deadlock(error_response):
    """
    Detecta el patrón canónico de deadlock de SQL Server en una respuesta
    de ZEUS. ZEUS puede devolverlo como str o list[str]; lo tratamos como
    texto plano. SQL Server siempre incluye 'deadlocked' y 'victim' en la
    misma frase y el mensaje es retry-friendly por diseño.
    """
    if not error_response:
        return False
    text = str(error_response).lower()
    return "deadlocked" in text and "victim" in text


def _es_pk_violation(error_response):
    """
    Detecta violación de PRIMARY KEY en respuesta de ZEUS. Suele venir como:
    "Violation of PRIMARY KEY constraint 'PK_xxx'. Cannot insert duplicate key".
    Indica que ZEUS ya tiene la fila — no es retry-friendly, requiere
    reconciliación manual.
    """
    if not error_response:
        return False
    text = str(error_response).lower()
    return "violation of primary key" in text or "duplicate key" in text


def _categorizar_inconsistencia(texto):
    """
    Mapea el texto final de Actividad.inconsistencias a una categoría corta
    para el resumen del lote. Si el texto no matchea ningún patrón conocido
    cae en 'otros' — sirve como detector de mensajes nuevos.
    """
    if not texto:
        return "otros"
    t = texto.lower()

    if "no se obtuvieron datos del paciente" in t:
        return "sin_paciente"
    if "ya fue admisionada" in t:
        return "duplicada"
    if "tipo de actividad" in t and "no encontrado" in t:
        return "tipo_actividad_no_encontrado"
    if "regional" in t and "no encontrada" in t:
        return "regional_no_encontrada"
    if "médico" in t and "no encontrado" in t:
        return "medico_no_encontrado"
    if "parámetros" in t and ("no configurados" in t or "área/programa" in t):
        return "parametros_no_configurados"
    if "régimen inconsistente" in t:
        return "regimen_inconsistente"
    if "no tiene regimen relacionado" in t:
        return "sin_regimen"
    if "tipo de usuario" in t and "obligatorio" in t:
        return "zeus_rechazo_tipo_usuario"
    if "tipo de usuario" in t:
        return "sin_tipo_usuario"
    # Errores ZEUS / SQL Server específicos
    if "deadlocked" in t and "victim" in t:
        return "deadlock_zeus"
    if "violation of primary key" in t or "duplicate key" in t:
        return "pk_violation_zeus"
    if "error al enviar admisión" in t:
        return "rechazo_zeus_otro"
    if "error al crear la admisión" in t:
        return "error_creacion_admision"
    return "otros"


def _validar_tipo_actividad_cached(nombre_actividad, tipos_actividad):
    nombre_limpio = nombre_actividad.replace(" ", "")
    for tipo in tipos_actividad:
        if tipo.nombre.replace(" ", "") in nombre_limpio:
            return tipo
    return None


def _cargar_cache_cargue(datos):
    documentos_medicos = set()
    finalidades = set()
    regionales = set()

    for valores in datos:
        documentos_medicos.add(_valor_limpio(valores[10]))
        finalidades.add(_valor_limpio(valores[11]))
        regionales.add(_valor_limpio(valores[6]))

    medicos = {
        medico.documento: medico
        for medico in Medico.objects.filter(documento__in=documentos_medicos)
    }
    finalidades_cache = {
        finalidad.valor: finalidad
        for finalidad in Finalidad.objects.filter(valor__in=finalidades)
    }
    regionales_cache = {
        regional.regional: regional
        for regional in Regional.objects.filter(regional__in=regionales)
    }
    tipos_actividad = list(
        TipoActividad.objects.select_related("contrato", "area").all()
    )
    parametros_programa = {
        (parametro.area_programa_id, parametro.regional_id): parametro
        for parametro in ParametrosAreaPrograma.objects.select_related(
            "area_programa", "regional"
        )
    }

    return {
        "medicos": medicos,
        "finalidades": finalidades_cache,
        "regionales": regionales_cache,
        "tipos_actividad": tipos_actividad,
        "parametros_programa": parametros_programa,
    }


def _buscar_claves_actividades(actividades, carga=None, admisionadas=False):
    candidatas = [
        actividad
        for actividad in actividades
        if actividad.tipo_actividad and actividad.medico
    ]
    if not candidatas:
        return set()

    consulta = Actividad.objects.filter(
        regional__in={actividad.regional for actividad in candidatas},
        fecha_servicio__in={actividad.fecha_servicio for actividad in candidatas},
        nombre_actividad__in={actividad.nombre_actividad for actividad in candidatas},
        tipo_actividad_id__in={
            actividad.tipo_actividad_id or actividad.tipo_actividad.id
            for actividad in candidatas
        },
        tipo_documento__in={actividad.tipo_documento for actividad in candidatas},
        documento_paciente__in={actividad.documento_paciente for actividad in candidatas},
        medico_id__in={actividad.medico_id or actividad.medico.id for actividad in candidatas},
    )
    if carga:
        consulta = consulta.filter(carga=carga)
    if admisionadas:
        consulta = consulta.filter(admision__isnull=False)

    campos_clave = (
        "regional",
        "fecha_servicio",
        "nombre_actividad",
        "tipo_actividad_id",
        "diagnostico_p",
        "diagnostico_1",
        "diagnostico_2",
        "diagnostico_3",
        "tipo_documento",
        "documento_paciente",
        "nombre_paciente",
        "medico_id",
    )
    return {
        _clave_actividad_desde_bd(fila)
        for fila in consulta.values_list(*campos_clave).iterator(chunk_size=1000)
    }

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
        actividad.contrato = tipo.contrato
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
            tipo_usuario_codigo = tipo_usuario_service.obtener_tipo_usuario(
                actividad.documento_paciente,
                actividad.tipo_documento,
            )
            if tipo_usuario_codigo:
                actividad.tipo_usuario = tipo_usuario_codigo
            else:
                actividad.inconsistencias = (
                    f"⚠️Tipo de Usuario: documento {actividad.documento_paciente} "
                    f"no encontrado en OPR_SALUD ni en API MUTUAL"
                )[:500]
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
    carga = Carga.objects.select_related("usuario").get(id= id_carga)
    try:
        cache = _cargar_cache_cargue(datos)
        datos_json_existentes = {
            _clave_json(datos_json)
            for datos_json in Actividad.objects.filter(carga=carga).values_list("datos_json", flat=True)
        }
        datos_json_lote = set()
        actividades_crear = []
        tipo_usuario_cache = {}

        for valores in datos:
            clave_json = _clave_json(valores)
            if clave_json in datos_json_existentes or clave_json in datos_json_lote:
                continue
            datos_json_lote.add(clave_json)

            actividad = Actividad()
            actividad.datos_json = valores
            actividad.carga = carga
            actividad.tipo_fuente = "EXCEL"
            actividad.tipo_documento = valores[0]
            actividad.documento_paciente = _valor_limpio(valores[1])
            actividad.nombre_paciente = f'{valores[4]} {valores[5]} {valores[2]} {valores[3]}'
            actividad.regional = _valor_limpio(valores[6])
            actividad.fecha_servicio = str(valores[7])
            actividad.nombre_actividad = _valor_limpio(valores[8])
            actividad.diagnostico_p = _valor_limpio(valores[9])
            actividad.documento_medico = _valor_limpio(valores[10])

            try:
                actividad.medico = cache["medicos"].get(actividad.documento_medico)
                if not actividad.medico:
                    raise Exception("Medico no encontrado")

                numero_finalidad = _valor_limpio(valores[11])
                actividad.finalidad = cache["finalidades"].get(numero_finalidad)
                if not actividad.finalidad:
                    raise Exception("Finalidad no encontrada")

                regional = cache["regionales"].get(actividad.regional)
                if not regional:
                    raise Exception("Regional no encontrada")

                tipo = _validar_tipo_actividad_cached(
                    actividad.nombre_actividad,
                    cache["tipos_actividad"],
                )
                if not tipo:
                    raise Exception("Tipo de actividad no encontrado")

                actividad.tipo_actividad = tipo
                actividad.contrato = tipo.contrato
                actividad.parametros_programa = cache["parametros_programa"].get(
                    (tipo.area_id, regional.id)
                )
                if not actividad.parametros_programa:
                    raise Exception("Parametros del area/programa no encontrados")
            except Exception as e:
                actividad.inconsistencias = ("⚠️Error al procesar la actividad" + str(e))[:500]

            actividades_crear.append(actividad)

        claves_admisionadas = _buscar_claves_actividades(
            actividades_crear,
            admisionadas=True,
        )
        claves_carga = _buscar_claves_actividades(
            actividades_crear,
            carga=carga,
        )
        claves_lote = set()

        # 1ª pasada: validar duplicados y recopilar (doc, tipo_doc) que necesitan tipo_usuario
        docs_tipos_a_consultar = set()
        for actividad in actividades_crear:
            if actividad.inconsistencias:
                continue

            clave_actividad = _clave_actividad(actividad)
            if clave_actividad in claves_admisionadas:
                actividad.admisionada_otra_carga = True
                actividad.inconsistencias = "⚠️Error al procesar la actividadActividad ya fue admisionada"
                continue

            if clave_actividad in claves_carga or clave_actividad in claves_lote:
                actividad.inconsistencias = "⚠️Error al procesar la actividadActividad repetida en la misma carga, validar."
                continue

            claves_lote.add(clave_actividad)
            tipo_doc_norm = (actividad.tipo_documento or "CC").strip().upper() or "CC"
            docs_tipos_a_consultar.add((str(actividad.documento_paciente), tipo_doc_norm))

        # Consulta batch: SQL primero, fallback API MUTUAL para los no resueltos
        batch_error = None
        tipo_usuario_cache = {}
        if docs_tipos_a_consultar:
            try:
                tipo_usuario_cache = tipo_usuario_service.obtener_tipo_usuario_batch(
                    list(docs_tipos_a_consultar)
                )
            except Exception as e:
                batch_error = e
                logger.exception("Error en batch tipo_usuario para carga %s", id_carga)

        # Diagnóstico: si había documentos por consultar pero el cache quedó vacío,
        # ambas fuentes (SQL + API) fallaron — mensaje único para todas.
        fuente_caida = bool(docs_tipos_a_consultar) and not tipo_usuario_cache
        if fuente_caida:
            if batch_error is not None:
                mensaje_fuente = (
                    f"⚠️Error consultando tipo_usuario (SQL+API): "
                    f"{type(batch_error).__name__}: {batch_error}"
                )
            else:
                mensaje_fuente = (
                    "⚠️Tipo de Usuario no resuelto por OPR_SALUD ni por API MUTUAL. "
                    "Contactar al equipo de datos."
                )
            logger.error("Carga %s: %s", id_carga, mensaje_fuente)

        # 2ª pasada: asignar tipo_usuario a las actividades válidas
        for actividad in actividades_crear:
            if actividad.inconsistencias:
                continue

            tipo_doc_norm = (actividad.tipo_documento or "CC").strip().upper() or "CC"
            tipo_usuario = tipo_usuario_cache.get(
                (str(actividad.documento_paciente), tipo_doc_norm)
            )
            if tipo_usuario:
                actividad.tipo_usuario = tipo_usuario
            elif fuente_caida:
                actividad.inconsistencias = mensaje_fuente[:500]
            else:
                actividad.inconsistencias = (
                    f"⚠️Tipo de Usuario: documento {actividad.documento_paciente} "
                    f"no encontrado en OPR_SALUD ni en API MUTUAL"
                )[:500]

        if actividades_crear:
            Actividad.objects.bulk_create(actividades_crear, batch_size=500)
                
        # Validar si se completa la carga
        numero_actividades_carga = Actividad.objects.filter(carga = id_carga).count() 
        if numero_actividades_carga == cantidad_actividades:
            estado = "procesada"
            final = time.time()
            carga.tiempo_procesamiento = (final - tiempo_inicial)/60
            
            if carga.usuario and carga.usuario.email:
                notificaciones_email.notificar_carga_procesada(carga, [carga.usuario.email])

        carga.estado = estado
        carga.actualizar_info_actividades()
        # Preservar el total objetivo mientras la carga no esté finalizada,
        # para que el cálculo de porcentaje de avance sea correcto.
        if estado != "procesada":
            carga.cantidad_actividades = cantidad_actividades
        carga.save()

    except Exception as e:
        logger.exception("Error al procesar la carga %s", id_carga)
        estado = "cancelada"
    finally:
        logger.info(
            "Lote: %s - num_actividades_tarea: %s - Total Actividades Carga: %s - Estado: %s",
            num_lote,
            len(datos),
            cantidad_actividades,
            estado,
        )
            
    return True

def tarea_admisionar_actividades_carga(id_carga, ids_actividades, num_lote=0):
    relaciones_admision = [
        "tipo_actividad",
        "tipo_actividad__contrato",
        "tipo_actividad__contrato__contrato_subsidiado",
        "tipo_actividad__contrato__contrato_contributivo",
        "tipo_actividad__tipo_servicio",
        "tipo_actividad__area",
        "contrato",
        "contrato__contrato_subsidiado",
        "contrato__contrato_contributivo",
        "parametros_programa",
        "parametros_programa__unidad_funcional",
        "parametros_programa__punto_atencion",
        "parametros_programa__centro_costo",
        "parametros_programa__sede",
        "medico",
        "finalidad",
    ]

    try:
        token = peticiones_http.obtener_token()
    except Exception as e:
        logger.exception(
            "Carga %s lote %s: no se pudo obtener token ZEUS",
            id_carga, num_lote,
        )
        return f"ERROR_TOKEN_LOTE_{num_lote}: {type(e).__name__}: {e}"

    carga = Carga.objects.select_related("usuario").get(id=int(id_carga))

    actividades_carga = (
        Actividad.objects
        .filter(id__in=ids_actividades, admision__isnull=True, admisionada_otra_carga=False)
        .select_related(*relaciones_admision)
        .order_by("id")
    )

    total_actividades = actividades_carga.count()
    logger.info(
        "Admision carga %s lote %s: iniciando con %s actividades",
        carga.id, num_lote, total_actividades,
    )

    # ── Pre-cargar tipo_usuario batch (SQL→API fallback, evita N queries en el loop) ──
    docs_tipos_sin_tipo_usuario = list(
        actividades_carga
        .filter(tipo_usuario__isnull=True)
        .values_list("documento_paciente", "tipo_documento")
        .distinct()
    )
    tipo_usuario_preload = {}
    tipo_usuario_preload_error = None
    if docs_tipos_sin_tipo_usuario:
        try:
            tipo_usuario_preload = tipo_usuario_service.obtener_tipo_usuario_batch(
                docs_tipos_sin_tipo_usuario
            )
            logger.info("tipo_usuario pre-cargados: %s documentos", len(tipo_usuario_preload))
        except Exception as e:
            tipo_usuario_preload_error = e
            logger.exception("Error en batch tipo_usuario pre-carga admision %s", carga.id)

    # Si el preload trajo 0 docs habiendo pedido varios → ambas fuentes caídas
    fuente_tipo_usuario_caida = bool(docs_tipos_sin_tipo_usuario) and not tipo_usuario_preload
    if fuente_tipo_usuario_caida:
        if tipo_usuario_preload_error is not None:
            logger.error(
                "Carga %s: tipo_usuario inaccesible (SQL+API) (%s: %s)",
                carga.id, type(tipo_usuario_preload_error).__name__, tipo_usuario_preload_error,
            )
        else:
            logger.error(
                "Carga %s: SQL+API devolvieron 0 afiliados para %s documentos",
                carga.id, len(docs_tipos_sin_tipo_usuario),
            )

    # ── Caches de fallback (evitan queries individuales dentro del loop) ──
    tipos_actividad_cache = {
        ta.nombre: ta
        for ta in TipoActividad.objects.select_related(
            "contrato", "contrato__contrato_subsidiado",
            "contrato__contrato_contributivo", "tipo_servicio", "area",
        ).all()
    }
    medicos_cache = {m.documento: m for m in Medico.objects.all()}
    regionales_cache = {r.regional: r for r in Regional.objects.all()}
    parametros_cache = {
        (p.area_programa_id, p.regional_id): p
        for p in ParametrosAreaPrograma.objects.select_related(
            "unidad_funcional", "punto_atencion", "centro_costo", "sede"
        ).all()
    }

    # ── Cache de datos de afiliado ZEUS (evita GET duplicados por mismo paciente) ──
    afiliado_cache = {}

    # ── Contador de resultados del lote (resumen al cierre) ──
    contadores = collections.Counter()

    for posicion, actividad in enumerate(actividades_carga.iterator(chunk_size=500), start=1):
        update_fields = {"updated_at"}
        try:
            # Reutilizar datos del afiliado si el mismo paciente ya fue consultado
            cache_key = (actividad.documento_paciente, actividad.tipo_documento)
            if cache_key not in afiliado_cache:
                ruta = (
                    f"/api/SisDeta/GetDatosBasicosPaciente"
                    f"?NumeroIdentificacion={actividad.documento_paciente}"
                    f"&TipoIdentificacion={actividad.tipo_documento}"
                )
                afiliado_cache[cache_key] = peticiones_http.consultar_data(ruta)
            datos_afiliado = afiliado_cache[cache_key]

            actividad.id_usuario = '1'
            actividad.nombre_usuario = 'admin'
            actividad.cedula_usuario = '123'
            actividad.nombre_persona_usuario = 'admin'

            if not len(datos_afiliado['Datos']):
                raise Exception("No se obtuvieron datos del paciente")

            if validador_actividades.valida_actividad_repetida_paciente(actividad):
                raise Exception("Esta actividad ya fue admisionada")

            # ── Fallback: tipo_actividad desde caché en memoria ──
            if not actividad.tipo_actividad:
                tipo_act = tipos_actividad_cache.get(actividad.nombre_actividad)
                if not tipo_act:
                    raise Exception(f"Tipo de actividad '{actividad.nombre_actividad}' no encontrado")
                actividad.tipo_actividad = tipo_act
                update_fields.add("tipo_actividad")

            try:
                # ── Fallback: parametros_programa desde caché en memoria ──
                if actividad.parametros_programa is None:
                    regional = regionales_cache.get(actividad.regional)
                    if not regional:
                        raise Exception(f"Regional '{actividad.regional}' no encontrada")
                    tipo_act = tipos_actividad_cache.get(actividad.nombre_actividad)
                    if tipo_act:
                        actividad.tipo_actividad = tipo_act
                    if not actividad.tipo_actividad:
                        raise Exception("Tipo de actividad no definido para obtener parámetros")
                    actividad.parametros_programa = parametros_cache.get(
                        (actividad.tipo_actividad.area_id, regional.id)
                    )
                    if not actividad.parametros_programa:
                        raise Exception("Parámetros del área/programa no configurados")
                    update_fields.update({"tipo_actividad", "parametros_programa"})

                # ── Fallback: médico desde caché en memoria ──
                if actividad.medico is None:
                    medico = medicos_cache.get(actividad.documento_medico)
                    if not medico:
                        raise Exception(f"Médico '{actividad.documento_medico}' no encontrado")
                    actividad.medico = medico
                    update_fields.add("medico")

                auto_id = datos_afiliado['Datos'][0]['autoid']
                regimen = datos_afiliado['Datos'][0]['NombreRegimen']

                if not regimen:
                    raise Exception("No tiene regimen relacionado")

                # ── tipo_usuario: pre-cargado o fallback individual (SQL→API) ──
                tipo_usuario = actividad.tipo_usuario
                if not tipo_usuario:
                    tipo_doc_norm = (actividad.tipo_documento or "CC").strip().upper() or "CC"
                    tipo_usuario = tipo_usuario_preload.get(
                        (str(actividad.documento_paciente), tipo_doc_norm)
                    )
                    if tipo_usuario:
                        actividad.tipo_usuario = tipo_usuario
                        update_fields.add("tipo_usuario")
                    elif fuente_tipo_usuario_caida:
                        update_fields.add("inconsistencias")
                        if tipo_usuario_preload_error is not None:
                            actividad.inconsistencias = (
                                f"⚠️Tipo de Usuario inaccesible (SQL+API): "
                                f"{type(tipo_usuario_preload_error).__name__}: {tipo_usuario_preload_error}"
                            )[:500]
                        else:
                            actividad.inconsistencias = (
                                "⚠️Tipo de Usuario sin datos en OPR_SALUD ni en API MUTUAL. "
                                "Contactar al equipo de datos."
                            )[:500]
                    else:
                        try:
                            siesa = tipo_usuario_service.obtener_tipo_usuario(
                                actividad.documento_paciente,
                                actividad.tipo_documento,
                            )
                            if siesa:
                                actividad.tipo_usuario = siesa
                                tipo_usuario = siesa
                                update_fields.add("tipo_usuario")
                            else:
                                update_fields.add("inconsistencias")
                                actividad.inconsistencias = (
                                    f"⚠️Tipo de Usuario: documento {actividad.documento_paciente} "
                                    f"no encontrado en OPR_SALUD ni en API MUTUAL"
                                )[:500]
                        except Exception as e:
                            update_fields.add("inconsistencias")
                            actividad.inconsistencias = (
                                f"⚠️Error consultando Tipo de Usuario para {actividad.documento_paciente}: "
                                f"{type(e).__name__}: {e}"
                            )[:500]

                # ── Reconciliar tipo_usuario contra el regimen de Zeus ──
                # Zeus es la fuente de verdad para la admisión. Si OPR_SALUD/API
                # dijeron un regimen distinto al que Zeus tiene, el tipo_usuario
                # quedó mal homologado. Reglas SIESA absolutas:
                #   Subsidiado → SIEMPRE 04 (cualquier tipo_afiliado).
                #   Contributivo → 01/02/03 (no 04).
                if regimen == "Subsidiado" and tipo_usuario != "04":
                    logger.info(
                        "Reconciliando tipo_usuario actividad %s: Zeus=%r → forzando '04' (era %r de OPR_SALUD/API)",
                        actividad.id, regimen, tipo_usuario,
                    )
                    actividad.tipo_usuario = "04"
                    tipo_usuario = "04"
                    update_fields.add("tipo_usuario")
                elif regimen == "Contributivo" and tipo_usuario == "04":
                    raise Exception(
                        f"Régimen inconsistente: Zeus dice Contributivo pero tipo_usuario es '04' "
                        f"(Subsidiado) según OPR_SALUD/API. Revisar afiliado {actividad.documento_paciente}."
                    )

                admision_actividad = admision.crear_admision(
                    autoid=auto_id,
                    regimen=regimen,
                    tipo_usuario=tipo_usuario,
                    codigo_entidad=parametros_generales.CODIGO_ENTIDAD[regimen],
                    tipo_diag=parametros_generales.TIPO_DIAGNOSTICO,
                    actividad=actividad
                )

                try:
                    # Retry con backoff+jitter cuando ZEUS devuelve deadlock de SQL Server.
                    # Otros errores (PK violation, validaciones) NO se reintentan: o no
                    # son recuperables o requieren reconciliación manual.
                    respuesta = None
                    for intento in range(1, settings.ADMISIONADO_MAX_RETRIES + 1):
                        respuesta = peticiones_http.crear_admision(admision_actividad, token)

                        if not respuesta:
                            raise Exception("Error en la petición a Zeus")

                        if _es_deadlock(respuesta.get('Errores')) and intento < settings.ADMISIONADO_MAX_RETRIES:
                            backoff = 0.2 + random.random() * 0.5 * intento
                            logger.warning(
                                "Deadlock ZEUS actividad %s reintento %s/%s (espera %.2fs)",
                                actividad.id, intento, settings.ADMISIONADO_MAX_RETRIES, backoff,
                            )
                            time.sleep(backoff)
                            continue
                        break

                    if respuesta['Errores']:
                        raise Exception(respuesta['Errores'])

                    respuesta_admision = ast.literal_eval(respuesta['Datos'][0]['infoTrasaction'])
                    datos_error = respuesta_admision[0]['DatosEnError']
                    datos_guardados = respuesta_admision[0]['DatosGuardados']

                    if datos_error:
                        raise Exception(datos_error[0])

                    if datos_guardados:
                        numero_estudio = datos_guardados[0]['Estudio']
                        nueva_admision = Admision.objects.create(
                            documento_paciente=actividad.documento_paciente,
                            numero_estudio=numero_estudio,
                            json=json.dumps(admision_actividad),
                        )
                        actividad.admision = nueva_admision
                        actividad.inconsistencias = None
                        update_fields.update({"admision", "inconsistencias"})
                    else:
                        # Zeus respondió OK pero sin datos_guardados ni datos_error.
                        # Hacer visible este path silencioso para diagnosticar.
                        logger.warning(
                            "Admision actividad %s: Zeus devolvió respuesta vacía "
                            "(tipo_usuario=%r, regimen=%r). Respuesta cruda: %r",
                            actividad.id, tipo_usuario, regimen, respuesta_admision,
                        )
                        raise Exception(
                            f"Zeus respondió sin datos_guardados ni datos_error "
                            f"(tipo_usuario={tipo_usuario!r}, regimen={regimen!r})"
                        )
                except Exception as e:
                    logger.exception("Error al enviar admision de actividad %s", actividad.id)
                    actividad.inconsistencias = ("⚠️Error al enviar admisión: " + str(e))[:500]
                    update_fields.add("inconsistencias")

            except Exception as e:
                logger.exception("Error al crear admision de actividad %s", actividad.id)
                actividad.inconsistencias = ("⚠️Error al crear la admisión: " + str(e))[:500]
                update_fields.add("inconsistencias")

        except Exception as e:
            logger.exception("Error al admisionar actividad %s", actividad.id)
            actividad.inconsistencias = ("⚠️" + str(e))[:500]
            update_fields.add("inconsistencias")

        actividad.save(update_fields=list(update_fields))

        # Categorizar resultado de esta actividad para el resumen del lote
        if "admision" in update_fields:
            contadores["admisionadas"] += 1
        else:
            contadores[_categorizar_inconsistencia(actividad.inconsistencias)] += 1

    # Actualización del contador al cierre del lote (1 save por tarea)
    carga.actualizar_info_actividades()
    carga.save(update_fields=[
        "cantidad_actividades",
        "cantidad_actividades_ok",
        "cantidad_actividades_inconsistencias",
        "cantidad_actividades_admisionadas",
        "updated_at",
    ])
    # Resumen del lote ordenado por frecuencia (admisionadas primero por convención)
    resumen_partes = [f"admisionadas={contadores.get('admisionadas', 0)}"]
    resumen_partes += [
        f"{categoria}={cantidad}"
        for categoria, cantidad in sorted(
            ((k, v) for k, v in contadores.items() if k != "admisionadas"),
            key=lambda kv: -kv[1],
        )
    ]
    logger.info(
        "Admision carga %s lote %s: %s/%s procesadas | %s",
        carga.id, num_lote, total_actividades, total_actividades,
        " ".join(resumen_partes),
    )

    # Transición a 'procesada' solo cuando ya no quedan actividades pendientes.
    # select_for_update evita que dos lotes finalizando en simultáneo dupliquen
    # la transición de estado o el envío del email.
    es_ultimo_lote = False
    with transaction.atomic():
        carga_locked = Carga.objects.select_for_update().get(id=int(id_carga))
        pendientes = Actividad.objects.filter(
            carga=carga_locked,
            admision__isnull=True,
            inconsistencias__isnull=True,
            admisionada_otra_carga=False,
        ).count()

        if pendientes == 0 and carga_locked.estado != "procesada":
            carga_locked.estado = "procesada"
            carga_locked.actualizar_info_actividades()
            carga_locked.save()
            es_ultimo_lote = True

    if es_ultimo_lote and carga.usuario and carga.usuario.email:
        logger.info("Enviar notificacion de admision a: %s", carga.usuario.email)
        notificaciones_email.notificar_carga_admisionada(carga, [carga.usuario.email])

    return f"LOTE_{num_lote}_OK ({total_actividades} actividades)"

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
