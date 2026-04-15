Gestiona las migraciones de Django para Zagilad.

Sigue estos pasos en orden:

**1. Ver estado actual de migraciones:**
```bash
python manage.py showmigrations
```
Revisa si hay migraciones pendientes (marcadas con `[ ]` en lugar de `[X]`).

**2. Detectar cambios en modelos:**
Lee los archivos de modelos modificados recientemente:
- `home/models.py` (modelos principales: Actividad, Carga, TipoActividad, etc.)
- `zeus_mirror/models.py` (modelos espejo de ZEUS: Contrato, Medico, Finalidad, etc.)

Compara con las últimas migraciones en `home/migrations/` y `zeus_mirror/migrations/`.

**3. Crear nuevas migraciones si hay cambios:**
```bash
python manage.py makemigrations
python manage.py makemigrations --check  # Solo verifica sin crear
```

**4. Aplicar migraciones:**
```bash
python manage.py migrate
```

**5. Verificar resultado:**
```bash
python manage.py showmigrations
```
Todos los items deben mostrar `[X]`.

**Consideraciones importantes para Zagilad:**
- La tabla `Actividad` tiene índices de rendimiento críticos (`act_carga_adm_idx`, `act_dup_adm_idx`, `act_dup_carga_idx`) — no eliminarlos
- La migración `0044` agrega índices de performance; si hay problemas de lentitud en cargas, verificar que esté aplicada
- La migración `0045` agrega el campo `contrato` (FK a ContratoMarco) en Actividad
- Si hay conflictos de migración entre `home` y `zeus_mirror`, resolver con `python manage.py makemigrations --merge`
