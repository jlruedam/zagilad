"""
Agrega `campo_tipo_documento` a FuenteTipoUsuario.

Campo opcional (`blank=True`, `default=""`) — no rompe fuentes existentes.
Si se configura, las consultas SQL filtrarán por documento + tipo documento.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0050_seed_fuente_mutualser"),
    ]

    operations = [
        migrations.AddField(
            model_name="fuentetipousuario",
            name="campo_tipo_documento",
            field=models.CharField(
                blank=True,
                default="",
                help_text=(
                    "Opcional. Columna del tipo de documento (CC/TI/RC/…). "
                    "Si está configurada, la consulta filtra por documento + tipo doc."
                ),
                max_length=100,
            ),
        ),
    ]
