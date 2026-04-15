Analiza y depura una Carga de actividades de Zagilad para diagnosticar problemas.

El argumento es el ID de la Carga a analizar: $ARGUMENTS

## Pasos de diagnóstico

**1. Leer el estado actual de la carga**

Revisa el modelo `Carga` en [home/models.py](home/models.py) y el flujo de procesamiento en [home/modules/task.py](home/modules/task.py).

Busca en el código las actividades de esa carga usando la vista `ver_carga` en [home/views.py](home/views.py):
- URL: `/verCarga/{ID_CARGA}/1`

**2. Identificar el patrón de inconsistencias**

Las inconsistencias más comunes en Zagilad y sus causas:

| Mensaje de inconsistencia | Causa probable | Solución |
|---|---|---|
| `Medico no encontrado` | Documento del médico no está en `zeus_mirror.Medico` | Sincronizar médicos desde `/consultasZeus/` |
| `Finalidad no encontrada` | Valor de finalidad no está en `zeus_mirror.Finalidad` | Sincronizar finalidades desde `/consultasZeus/` |
| `Regional no encontrada` | Nombre de regional no coincide exactamente con `home.Regional` | Verificar ortografía exacta (ej: "BOLIVAR NORTE") |
| `Tipo de actividad no encontrado` | Nombre de actividad en Excel no coincide con `TipoActividad.nombre` | Revisar TipoActividad en BD; el match es por substring |
| `Parametros del area/programa no encontrados` | No existe `ParametrosAreaPrograma` para esa combinación area+regional | Configurar en `/parametrosAreaPrograma/` |
| `Actividad ya fue admisionada` | Duplicado histórico — ya existe una Admision para ese paciente+actividad+fecha+médico | Normal; eliminar de la carga |
| `Actividad repetida en la misma carga` | Fila duplicada en el Excel | Eliminar duplicados del Excel origen |
| `Error al consultar el Tipo de Usuario` | Falla en conexión a BD OPR_SALUD | Verificar `conexionBD.py` y conectividad a MSSQL |

**3. Revisar los archivos relevantes según el error**

- Validaciones de actividades: [home/modules/validador_actividades.py](home/modules/validador_actividades.py)
- Procesamiento de lote: [home/modules/task.py](home/modules/task.py) función `procesar_cargue_actividades`
- Conexión BD externa: [home/modules/conexionBD.py](home/modules/conexionBD.py)
- Parámetros generales: [home/modules/parametros_generales.py](home/modules/parametros_generales.py)

**4. Opciones de resolución**

- Eliminar actividades con un tipo específico de inconsistencia: `DELETE /eliminarActividadesInconsistenciaCarga/{ID}/{tipo}`
- Eliminar todas las inconsistencias: `DELETE /eliminarActividadesInconsistenciaCarga/{ID}/all`
- Exportar inconsistencias a Excel para revisión: `/exportarCargaExcel/{ID}/inconsistencias`
- Re-admisionar una actividad individual: `/admisionarActividadIndividual/{ID_ACTIVIDAD}/{PAGINA}`

Proporciona un diagnóstico claro con el conteo de cada tipo de inconsistencia y las acciones recomendadas.
