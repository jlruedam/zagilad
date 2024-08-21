# Generated by Django 4.1.4 on 2024-08-16 18:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('zeus_mirror', '0004_rename_codigo_sede_ciudad_and_more'),
        ('home', '0004_remove_actividad_centro_costo_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContratoMarco',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('numero', models.CharField(max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('contrato_contributivo', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='contributivo', to='zeus_mirror.contrato')),
                ('contrato_subsidiado', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='subsidado', to='zeus_mirror.contrato')),
            ],
        ),
    ]
