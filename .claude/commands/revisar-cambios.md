Revisa los cambios recientes del código de Zagilad para detectar problemas de calidad, seguridad y correctitud.

## Proceso de revisión

**1. Obtener el diff de cambios**

```bash
git diff HEAD
git diff --staged
git status
```

**2. Revisar cada archivo modificado**

Lee los archivos en los que hubo cambios. Enfócate en:

### Archivos críticos de Zagilad y qué revisar

**`home/models.py`**
- ¿Nuevos campos tienen `blank=True, null=True` apropiado?
- ¿Nuevas FKs usan `models.SET_NULL` (patrón del proyecto)?
- ¿Se necesita nueva migración?
- ¿Los `__str__` son informativos?

**`home/modules/task.py`**
- ¿Las funciones async manejan excepciones y registran en logger?
- ¿Se usa `bulk_create` con `batch_size` para inserciones masivas?
- ¿Los mensajes de inconsistencia se truncan a ≤500 chars (`[:500]`)?
- ¿Se actualiza `carga.actualizar_info_actividades()` después de cambios?
- ¿Los `update_fields` de `.save()` son correctos y completos?

**`home/modules/peticiones_http.py`**
- ¿Las peticiones manejan status codes != 200?
- ¿No se loguean tokens o passwords?
- ¿Se reutiliza el token vigente antes de pedir uno nuevo?

**`home/views.py`**
- ¿Todas las vistas tienen `@login_required(login_url="/login/")`?
- ¿Los endpoints JSON usan `JsonResponse` con `safe=False` cuando es lista?
- ¿Los archivos descargados validan la ruta (no path traversal)?
- ¿Las vistas de procesamiento retornan errores HTTP apropiados (400, 500)?

**`home/modules/validador_actividades.py`**
- ¿Las comparaciones de nombres son resistentes a espacios? (usar `.replace(" ", "")`)
- ¿Las queries de duplicados usan los índices correctos (`act_dup_adm_idx`, `act_dup_carga_idx`)?

**`zeus_mirror/views.py`**
- ¿Las sincronizaciones usan `update_or_create` con los campos únicos correctos?
- ¿Se manejan respuestas vacías de la API ZEUS?

### Checks generales Django

- ¿Queries N+1? (buscar `.all()` en loops — usar `select_related` o `prefetch_related`)
- ¿Transacciones faltantes? (operaciones multi-tabla sin `transaction.atomic()`)
- ¿`print()` que deberían ser `logger.info/debug/error()`?
- ¿Contraseñas/tokens en código hardcodeados?
- ¿Rutas de archivos construidas con concatenación en lugar de `os.path.join`?

**3. Revisar migraciones**

Si hay cambios en modelos, verificar:
```bash
python manage.py makemigrations --check
```

**4. Proporcionar feedback**

Genera un resumen con:
- Problemas críticos (seguridad, integridad de datos)
- Problemas de calidad (N+1, falta de manejo de errores)
- Mejoras menores (consistencia de estilo, logs)
- Confirmación de lo que está bien implementado
