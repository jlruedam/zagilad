"""
Normaliza los mensajes existentes de "Régimen inconsistente" en
Actividad.inconsistencias para que NO incluyan el documento del afiliado.

Antes:
  "⚠️Error al crear la admisión: Régimen inconsistente: Zeus dice
   Contributivo pero tipo_usuario es '04' (Subsidiado) según OPR_SALUD/API.
   Revisar afiliado 64705603."

Después:
  "⚠️Error al crear la admisión: Régimen inconsistente: Zeus dice
   Contributivo pero tipo_usuario es '04' (Subsidiado) según OPR_SALUD/API."

Así todas las actividades con este problema quedan con el MISMO texto y
el resumen de la carga las agrupa en una sola fila.
"""
import re

from django.db import migrations

PATRON = re.compile(
    r"(Régimen inconsistente:.*?(?:OPR_SALUD/API)\.)\s*Revisar afiliado\s+\S+\.?",
    flags=re.IGNORECASE | re.DOTALL,
)


def normalizar_mensajes(apps, schema_editor):
    Actividad = apps.get_model("home", "Actividad")

    # Solo tocamos las que contienen el patrón, para no escanear todo el set.
    qs = (
        Actividad.objects
        .filter(inconsistencias__icontains="Régimen inconsistente")
        .only("id", "inconsistencias")
    )
    for actividad in qs.iterator(chunk_size=500):
        nuevo = PATRON.sub(r"\1", actividad.inconsistencias)
        if nuevo != actividad.inconsistencias:
            Actividad.objects.filter(id=actividad.id).update(inconsistencias=nuevo)


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0046_backfill_actividad_contrato"),
    ]

    operations = [
        migrations.RunPython(
            normalizar_mensajes,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
