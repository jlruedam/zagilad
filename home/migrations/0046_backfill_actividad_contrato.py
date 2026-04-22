from django.db import migrations


def backfill_actividad_contrato(apps, schema_editor):
    Actividad = apps.get_model("home", "Actividad")
    TipoActividad = apps.get_model("home", "TipoActividad")

    tipos = TipoActividad.objects.filter(contrato__isnull=False).only("id", "contrato_id")
    for tipo in tipos.iterator(chunk_size=500):
        Actividad.objects.filter(
            tipo_actividad_id=tipo.id,
            contrato__isnull=True,
        ).update(contrato_id=tipo.contrato_id)


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0045_actividad_contrato"),
    ]

    operations = [
        migrations.RunPython(
            backfill_actividad_contrato,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
