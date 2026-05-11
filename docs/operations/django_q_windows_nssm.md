# Django Q en producción (Windows + NSSM)

Django Q se ejecuta en el servidor de producción como un **servicio de
Windows** registrado mediante [NSSM](https://nssm.cc/) (the Non-Sucking
Service Manager). NSSM envuelve al proceso `qcluster` y le da el ciclo de
vida estándar de un servicio Windows (autostart, restart on failure, logs,
etc.).

## Nombre del servicio

```
django-qcluster
```

## Comandos operativos

Todos se ejecutan desde una consola **con privilegios de administrador**
en el servidor donde corre Django Q.

| Acción          | Comando                          |
|-----------------|----------------------------------|
| Iniciar         | `net start django-qcluster`      |
| Detener         | `net stop django-qcluster`       |
| Consultar estado| `sc query django-qcluster`       |
| Reiniciar       | `net stop django-qcluster && net start django-qcluster` |

> El reinicio con `net stop && net start` es la forma estándar — NSSM
> también acepta `nssm restart django-qcluster` si está en el PATH.

## Cuándo es **obligatorio** reiniciar el servicio

Django Q carga los módulos Python **una sola vez** al arrancar cada
worker. Cualquier cambio que modifique código que se ejecute dentro de
una tarea no tiene efecto hasta que el servicio recicle. Casos típicos:

- Cambios en `home/modules/task.py` (la lógica de las tareas asíncronas).
- Cambios en módulos importados por las tareas:
  `home/modules/admision.py`, `home/modules/revalidador.py`,
  `home/modules/tipo_usuario/*`, `home/modules/peticiones_http.py`,
  `home/modules/notificaciones_email.py`, `home/modules/conexionBD.py`,
  `home/models.py` (cuando una tarea instancia modelos).
- Cambios de variables de entorno consumidas por las tareas
  (`SERVER_LAKE`, credenciales del API MUTUAL, SMTP, etc.).
- Migraciones de base de datos que cambien el shape de tablas tocadas
  desde las tareas.

> El servidor web (Django request/response) se recicla por separado en su
> propio servicio/IIS — reiniciar `django-qcluster` **no** reinicia el
> servidor web ni viceversa.

## Verificar que el reinicio surtió efecto

1. `sc query django-qcluster` → debe devolver `STATE: 4 RUNNING`.
2. Tail al log de Q (path configurado en `settings.py → Q_CLUSTER`). Debe
   aparecer una línea de arranque tipo:
   ```
   INFO Q Cluster <id> running.
   ```
3. Disparar una tarea de prueba pequeña (p.ej. revalidar una actividad)
   y confirmar que se procesa.

## Troubleshooting rápido

| Síntoma                                            | Causa probable                                |
|----------------------------------------------------|-----------------------------------------------|
| `sc query` devuelve `STATE: 1 STOPPED`             | El servicio cayó — revisar log NSSM y log Q.  |
| Cambios de código no surten efecto                 | Falta reiniciar el servicio.                  |
| Tareas se encolan pero no se procesan              | Servicio detenido, cluster con 0 workers, o DB caída. |
| Servicio se reinicia solo en loop                  | Excepción al importar un módulo — ver log de NSSM (`stderr`). |

## Cómo está configurado NSSM (referencia)

NSSM se configuró apuntando al `python.exe` del venv del proyecto con
`manage.py qcluster` como argumento. Para inspeccionar la configuración
actual:

```
nssm edit django-qcluster
```

(abre el editor gráfico — sirve para ver/editar path del ejecutable,
parámetros, working directory, redirección de stdout/stderr y políticas
de restart automático).
