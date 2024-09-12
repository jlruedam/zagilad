# Generated by Django 4.1.4 on 2024-09-12 19:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0017_carga_cantidad_actividades_admisionadas'),
    ]

    operations = [
        migrations.AlterField(
            model_name='carga',
            name='estado',
            field=models.CharField(choices=[('eliminada', 'Carga eliminada'), ('creada', 'Carga creada'), ('procesada', 'Carga procesada'), ('admisionando', 'Carga en proceso de crear admisiones')], default='creada', max_length=20),
        ),
    ]