# Generated by Django 4.1.4 on 2024-08-08 14:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0006_actividad_centro_costo_actividad_unidad_funcional_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actividad',
            name='diagnostico_1',
            field=models.CharField(default='', max_length=10),
        ),
        migrations.AlterField(
            model_name='actividad',
            name='diagnostico_2',
            field=models.CharField(default='', max_length=10),
        ),
        migrations.AlterField(
            model_name='actividad',
            name='diagnostico_3',
            field=models.CharField(default='', max_length=10),
        ),
        migrations.AlterField(
            model_name='actividad',
            name='diagnostico_p',
            field=models.CharField(default='', max_length=10),
        ),
    ]
