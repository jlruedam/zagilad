# Generated by Django 4.1.4 on 2024-12-05 16:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0031_carga_num_tareas_en_proceso'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='carga',
            name='num_tareas_en_proceso',
        ),
    ]
