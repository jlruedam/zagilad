# Generated by Django 4.1.4 on 2024-09-09 19:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0014_carga_tiempo_procesamiento'),
    ]

    operations = [
        migrations.AddField(
            model_name='carga',
            name='cantidad_actividades_inconsistencias',
            field=models.IntegerField(default=0),
        ),
    ]