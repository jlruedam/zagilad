from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zagilad.settings')
app = Celery('zagilad')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


# # Otras configuraciones que puedes agregar aquí
# app.conf.task_time_limit = 31622400000  # Sin límite de tiempo para las tareas
# app.conf.task_soft_time_limit = 31622400000  # Sin límite suave para las tareas
# app.conf.worker_concurrency = 4  # Número de tareas que se pueden ejecutar simultáneamente
# app.conf.task_retry_limit = 0  # Sin reintentos automáticos


# app.conf.update(
#     task_acks_late=True,  # Acknowledge solo después de completar la tarea
#     task_time_limit=31622400000,  # Timeout máximo de 30 minutos
#     task_soft_time_limit=31622400000  # Aviso de límite suave antes del timeout
# )

print(app.conf)