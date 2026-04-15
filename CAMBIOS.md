# Registro de Cambios - Zagilad

> Documento para rastrear cambios realizados en el proyecto, decisiones técnicas y contexto relevante.

---

## Contexto del Proyecto

**Zagilad** es un sistema Django para Fundación SERSOCIAL (Colombia) que automatiza el procesamiento masivo de actividades de salud y su envío a **ZEUS** (sistema hospitalario externo) vía REST API.

### Flujo principal
1. Usuario carga Excel con actividades de salud
2. `procesarCargue()` crea un objeto `Carga` y lanza tareas async via **django-q** en bloques de 2000
3. `procesar_cargue_actividades()` (`task.py`) valida cada actividad contra BD local
4. Usuario revisa inconsistencias en UI y las corrige o elimina
5. `admisionar_actividades_carga()` envía actividades válidas a ZEUS API → crea registros `Admision`

### Modelos clave
| Modelo | Descripción |
|---|---|
| `Carga` | Lote de actividades cargado. Estados: `creada → procesando → procesada → admisionando` |
| `Actividad` | Actividad individual; tiene campo `inconsistencias` si hay error |
| `Admision` | Registro creado exitosamente en ZEUS; tiene `numero_estudio` |
| `TipoActividad` | Catálogo de actividades válidas con CUPS, diagnóstico, contrato, área |
| `ParametrosAreaPrograma` | Configuración regional × área-programa |
| `ContratoMarco` | Contratos marco mapeando subsidiado/contributivo en `zeus_mirror.Contrato` |

### Bases de datos
- **Django DB (MySQL)**: datos del sistema Zagilad
- **OPR_SALUD (MSSQL via OPENQUERY)**: consulta tipo de afiliado (subsidiado/contributivo)
- **ZEUS API (REST)**: sistema externo donde se crean las admisiones

---

## Cambios Pendientes de Commit (rama `main`, 2026-04-15)

Estos cambios están en el working tree pero aún no tienen commit.

### `home/models.py` — Modelo `Actividad`

**Cambios:**
- Se añadió campo `contrato = ForeignKey(ContratoMarco, SET_NULL, null=True)` al modelo `Actividad`
- Se añadieron 3 índices de base de datos en `Meta.indexes`:
  - `act_carga_adm_idx`: sobre `(carga, admision)` — acelera filtros por carga y estado de admisión
  - `act_dup_adm_idx`: sobre `(documento_paciente, fecha_servicio, nombre_actividad, tipo_actividad, medico, admision)` — detección de duplicados históricos
  - `act_dup_carga_idx`: sobre `(carga, documento_paciente, fecha_servicio, nombre_actividad, tipo_actividad, medico)` — detección de duplicados dentro de la misma carga

**Migraciones asociadas (sin trackear):**
- `0044_actividad_performance_indexes.py` — crea los índices
- `0045_actividad_contrato.py` — añade el campo `contrato`

---

### `home/modules/task.py` — Refactoring mayor de procesamiento

Este es el cambio más grande. Se refactorizó completamente la lógica de procesamiento masivo.

#### Nuevas funciones auxiliares (helpers privados)
- `_valor_limpio(valor)` / `_clave_json(valor)` / `_valor_clave(valor)`: normalización de valores para comparaciones
- `_clave_actividad(actividad)`: genera una tupla única que identifica una actividad (evita duplicados)
- `_clave_actividad_desde_bd(fila)`: misma clave pero desde una fila de BD
- `_validar_tipo_actividad_cached(nombre, tipos)`: busca tipo de actividad en lista en memoria
- `_cargar_cache_cargue(datos)`: precarga en memoria todos los catálogos necesarios (médicos, finalidades, regionales, tipos de actividad, parámetros) antes de procesar el lote — **evita N queries individuales**
- `_buscar_claves_actividades(actividades, carga, admisionadas)`: consulta en batch las claves de actividades ya existentes en BD para detección de duplicados

#### `procesar_cargue_actividades()` — refactorizado
- **Antes**: una query a BD por cada validación (médico, finalidad, regional, tipo actividad, parámetros)
- **Ahora**:
  1. Se precarga todo en memoria con `_cargar_cache_cargue()` al inicio del lote
  2. Detección de duplicados en 2 pasadas: primero se acumulan claves del lote, luego se consulta BD una sola vez
  3. Consulta batch de `tipo_usuario` a OPR_SALUD via `obtener_tipo_usuario_batch()` — una sola query por lote en lugar de una por actividad
  4. `Actividad.objects.bulk_create()` con `batch_size=500` en lugar de `.save()` individual
  5. Se preserva `cantidad_actividades` en la carga mientras el estado no sea "procesada" (para cálculo correcto del porcentaje de avance)
  6. `print()` reemplazados por `logger.exception()` / `logger.info()`

#### `tarea_admisionar_actividades_carga()` — refactorizado
- **Antes**: N queries individuales a BD por actividad (tipo_actividad, medico, regional, parametros), N GET a ZEUS por paciente, N queries a OPR_SALUD por tipo_usuario
- **Ahora**:
  - Pre-carga de caches en memoria: `tipos_actividad_cache`, `medicos_cache`, `regionales_cache`, `parametros_cache`
  - Cache de datos de afiliado ZEUS por `(documento, tipo_documento)` — si el mismo paciente aparece varias veces, solo se hace 1 GET
  - Pre-carga de `tipo_usuario` en batch para documentos sin tipo asignado
  - Fallback individual a `obtener_tipo_usuario()` si el batch no encontró el documento
  - `.save(update_fields=[...])` en lugar de `.save()` completo — solo escribe los campos que cambiaron
  - Progreso cada 500 actividades: `carga.actualizar_info_actividades()` + `carga.save(update_fields=[...])`
  - Iteración con `.iterator(chunk_size=500)` para no cargar todo en memoria
  - `Admision.objects.create()` en lugar de instanciar + `.save()`
  - `print()` reemplazados por `logger`

---

### `home/modules/utils.py` — Nueva función batch

**Cambio principal:** Nueva función `obtener_tipo_usuario_batch(documentos: list) -> dict`

- Recibe una lista de documentos y retorna `{str(documento): id_tipo_afiliado}`
- Ejecuta la consulta en lotes de 200 documentos (constante `_BATCH_SIZE_TIPO_USUARIO`) para no superar el límite de ~8000 bytes de SQL en OPENQUERY
- Usa `WHERE NRO_TIPO_IDENTIFICACION IN (...)` en lugar de una query por documento
- **Motivación**: en cargas de 2000+ actividades, la función individual generaba 2000+ queries seriales a OPR_SALUD, causando timeouts

---

### `home/modules/conexionBD.py` — Pool de conexiones thread-local

**Cambio:** La función `conexionBD()` ahora reutiliza conexiones por hilo en lugar de abrir/cerrar en cada llamada.

- Se añadió `threading.local()` para almacenar la conexión por hilo
- `_get_conn()`: retorna la conexión existente del hilo o crea una nueva
- Manejo de reconexión automática: si la conexión falla (caída), la cierra, limpia y reconecta una vez antes de propagar el error
- **Motivación**: con el procesamiento batch, la misma conexión se abría y cerraba cientos de veces por lote

---

### `home/modules/peticiones_http.py` — Limpieza de logs

- Eliminados todos los `print()` de depuración que exponían tokens, URLs y respuestas completas en los logs de producción

---

### `home/modules/validador_actividades.py` — Mejoras menores

- `valida_actividad_repetida_paciente()`: parámetro `carga_actual=None` en lugar de `[]` (mutable default)
- `validador_tipo_actividad()`: ahora acepta `tipos_actividad=None` (lista pre-cargada opcional) para evitar query a BD cuando se llama en bucle

---

### `home/views.py` — Nueva vista y mejoras

**Nueva vista:** `listar_resumen_cargas()` — endpoint JSON (`GET /listarResumenCargas/`)
- Retorna resumen de todas las cargas con porcentajes calculados:
  - `porcentaje_procesamiento`: progreso durante estado "procesando"
  - `porcentaje_admisionado`: progreso durante estado "admisionando"
- Usa `select_related("usuario")` para evitar N+1

**Mejoras en `cargar_actividades()`:**
- Filtrado de columnas del Excel al conjunto esperado antes de iterar (`archivo_masivo[encabezados_esperados]`)
- Iteración con `itertuples()` en lugar de `iterrows()` (más eficiente)
- `cantidad_actividades` se guarda en la `Carga` al momento de crearla (antes no se guardaba hasta terminar)

**Mejoras en `procesarCargue()`:**
- Se asigna `cantidad_actividades=cant_act` al crear la `Carga`

---

### `home/urls.py`

- Nueva ruta: `path('listarResumenCargas/', views.listar_resumen_cargas, name='listar_resumen_cargas')`

---

### `home/templates/home/informeCargas.html` + `home/static/assets/js/informeCargas.js`

- Refactorización de la página de informe de cargas (detalles en los archivos)

---

## Historial de Commits Recientes

| Hash | Fecha | Descripción |
|---|---|---|
| `bdc5f70` | 2025-08-19 | `feat: save a contract when it dont exist in db` (zeus_mirror/views.py) |
| `222acc3` | 2025-06-11 | Add error handling for user type retrieval in `tarea_admisionar_actividades_carga` |
| `0824fde` | 2025-06-11 | Handle user type retrieval errors in `procesar_actividad` + update SQL query en `obtener_tipo_usuario` |
| `0c622cd` | 2025-06-09 | Refactor cargaActividades page: layout, file upload, observation fields |
| `9e86d5d` | — | Update finalidad assignment en `crear_admision` para usar `actividad.finalidad.valor` |

---

## Notas Técnicas

### Inconsistencias más comunes en actividades
- `⚠️Error al procesar la actividad` + `Actividad ya fue admisionada`
- `⚠️Error al procesar la actividad` + `Actividad repetida en la misma carga, validar.`
- `⚠️Error el consultar el Tipo de Usuario: documento no encontrado en OPR_SALUD`
- `⚠️Error al crear la admisión: ...`
- `⚠️Error al enviar admisión: ...`

### Variables de entorno requeridas (`.env`)
- `SERVER_LAKE` — servidor SQL Server (OPR_SALUD)
- `USERNAME_SERVER_LAKE` / `PASSWORD_SERVER_LAKE` — credenciales
- `URL_API_ZEUS` — URL base de la API ZEUS
- `USERNAME` / `PASSWORD` — credenciales ZEUS

### Patrón de caché en procesamiento masivo
El patrón establecido para evitar N+1 queries en lotes grandes:
1. Pre-cargar catálogos completos en dicts en memoria al inicio del lote
2. Consultar la BD una sola vez para claves de duplicados
3. Consultar OPR_SALUD en batch (chunks de 200)
4. Usar `bulk_create()` / `save(update_fields=[...])` en lugar de saves individuales
