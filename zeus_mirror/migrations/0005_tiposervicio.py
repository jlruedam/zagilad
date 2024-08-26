# Generated by Django 4.1.4 on 2024-08-16 20:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zeus_mirror', '0004_rename_codigo_sede_ciudad_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='TipoServicio',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('fuente', models.IntegerField()),
                ('id_zeus', models.IntegerField()),
                ('nombre', models.CharField(max_length=150)),
                ('tipo', models.CharField(max_length=150)),
                ('tipo_servicio', models.CharField(max_length=5)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]