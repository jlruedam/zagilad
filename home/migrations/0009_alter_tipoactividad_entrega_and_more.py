# Generated by Django 4.1.4 on 2024-08-16 20:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0008_alter_tipoactividad_contrato_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tipoactividad',
            name='entrega',
            field=models.CharField(blank=True, max_length=150, null=True),
        ),
        migrations.AlterField(
            model_name='tipoactividad',
            name='fuente',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='tipoactividad',
            name='grupo',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='tipoactividad',
            name='observacion',
            field=models.CharField(blank=True, max_length=150, null=True),
        ),
        migrations.AlterField(
            model_name='tipoactividad',
            name='responsable',
            field=models.CharField(blank=True, max_length=150, null=True),
        ),
    ]