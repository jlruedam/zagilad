# Generated by Django 4.1.4 on 2024-10-25 13:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('zeus_mirror', '0010_usuariozeus_borrar_campo'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='usuariozeus',
            name='borrar_campo',
        ),
    ]
