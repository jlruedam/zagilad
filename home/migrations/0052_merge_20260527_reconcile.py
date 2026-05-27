# Merge de reconciliación: une la rama de merges histórica de producción
# (tip 0049_merge_20260511_1048) con la rama del repo que agrega el módulo
# de fuentes de tipo de usuario (tip 0051). Sin operaciones de schema.
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0049_merge_20260511_1048"),
        ("home", "0051_fuentetipousuario_campo_tipo_documento"),
    ]

    operations = []
