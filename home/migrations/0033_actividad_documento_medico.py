# Generated by Django 4.1.4 on 2024-12-05 21:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0032_remove_carga_num_tareas_en_proceso'),
    ]

    operations = [
        migrations.AddField(
            model_name='actividad',
            name='documento_medico',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
