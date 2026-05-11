"""
Normaliza los mensajes existentes de "Tipo de Usuario ... no encontrado en
OPR_SALUD ni en API MUTUAL" en Actividad.inconsistencias para que NO incluyan
el documento del afiliado.

Antes:
  "⚠️Tipo de Usuario: documento 6664771 no encontrado en OPR_SALUD ni en API MUTUAL"

Después:
  "⚠️Tipo de Usuario no encontrado en OPR_SALUD ni en API MUTUAL"

Así todas las actividades con este problema quedan con el MISMO texto y el
resumen de la carga las agrupa en una sola fila.
"""
import re

from django.db import migrations

PATRON = re.compile(
    r"Tipo de Usuario:\s*documento\s+\S+\s+no encontrado en OPR_SALUD ni en API MUTUAL",
    flags=re.IGNORECASE,
)

REEMPLAZO = "Tipo de Usuario no encontrado en OPR_SALUD ni en API MUTUAL"


def normalizar_mensajes(apps, schema_editor):
    Actividad = apps.get_model("home", "Actividad")

    qs = (
        Actividad.objects
        .filter(inconsistencias__icontains="no encontrado en OPR_SALUD")
        .only("id", "inconsistencias")
    )
    for actividad in qs.iterator(chunk_size=500):
        nuevo = PATRON.sub(REEMPLAZO, actividad.inconsistencias)
        if nuevo != actividad.inconsistencias:
            Actividad.objects.filter(id=actividad.id).update(inconsistencias=nuevo)


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0047_normalize_regimen_inconsistente_message"),
    ]

    operations = [
        migrations.RunPython(
            normalizar_mensajes,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
