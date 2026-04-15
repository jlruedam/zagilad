Ayuda a iniciar el entorno de desarrollo de Zagilad.

El proyecto requiere DOS procesos corriendo en terminales separadas:

**Terminal 1 — Servidor Django:**
```bash
# Activar el entorno virtual
venv\Scripts\activate

# Iniciar servidor de desarrollo
python manage.py runserver
```

**Terminal 2 — Worker de tareas (OBLIGATORIO para procesar cargas):**
```bash
# Activar el entorno virtual
venv\Scripts\activate

# Iniciar el cluster de django-q (procesa cargas y admisiones en background)
python manage.py qcluster
```

Verifica que el archivo `.env` exista en la raíz del proyecto con las variables:
- `DATABASE_*` (conexión MySQL)
- `URL_API_ZEUS` (URL de la API ZEUS)
- `USUARIO_API_ZEUS` y `PASSWORD_API_ZEUS`
- `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`

Si el servidor no arranca, revisa el archivo `.env` y que la BD MySQL esté disponible.
Si el qcluster no arranca, revisa los logs en `logs/zagilad.log`.

**Importante:** Sin el qcluster corriendo, las cargas de actividades quedarán en estado "procesando" indefinidamente y no se procesarán.
