# Generated manually to align Actividad.contrato with the database schema.

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0044_actividad_performance_indexes"),
    ]

    operations = [
        migrations.AddField(
            model_name="actividad",
            name="contrato",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="home.contratomarco",
            ),
        ),
    ]
