# Generated manually to optimize massive activity admission queries.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0043_actividad_finalidad_alter_tipoactividad_finalidad"),
    ]

    operations = [
        migrations.AddIndex(
            model_name="actividad",
            index=models.Index(fields=["carga", "admision"], name="act_carga_adm_idx"),
        ),
        migrations.AddIndex(
            model_name="actividad",
            index=models.Index(
                fields=[
                    "documento_paciente",
                    "fecha_servicio",
                    "nombre_actividad",
                    "tipo_actividad",
                    "medico",
                    "admision",
                ],
                name="act_dup_adm_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="actividad",
            index=models.Index(
                fields=[
                    "carga",
                    "documento_paciente",
                    "fecha_servicio",
                    "nombre_actividad",
                    "tipo_actividad",
                    "medico",
                ],
                name="act_dup_carga_idx",
            ),
        ),
    ]
