# Generated by Django 4.1.4 on 2024-09-13 18:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0018_alter_carga_estado'),
    ]

    operations = [
        migrations.AlterField(
            model_name='carga',
            name='estado',
            field=models.CharField(choices=[('eliminada', 'Carga eliminada'), ('creada', 'Carga creada'), ('procesando', 'Carga en proceso'), ('procesada', 'Carga procesada'), ('admisionando', 'Carga en proceso de creación de admisiones')], default='creada', max_length=20),
        ),
    ]
