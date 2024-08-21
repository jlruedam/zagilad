# Generated by Django 4.1.4 on 2024-08-15 20:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('zeus_mirror', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Admision',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('documento_paciente', models.IntegerField()),
                ('numero_estudio', models.IntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='ParametrosAreaPrograma',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('area_programa', models.CharField(blank=True, max_length=20, null=True)),
                ('unidad_funcional', models.CharField(max_length=5)),
                ('punto_atencion', models.CharField(max_length=5)),
                ('centro_costo', models.CharField(max_length=5)),
                ('regional', models.CharField(max_length=150)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='TipoActividad',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('grupo', models.CharField(max_length=150)),
                ('nombre', models.CharField(max_length=150)),
                ('cups', models.CharField(max_length=10)),
                ('responsable', models.CharField(max_length=150)),
                ('diagnostico', models.CharField(blank=True, max_length=10, null=True)),
                ('finalidad', models.CharField(blank=True, max_length=50, null=True)),
                ('fuente', models.CharField(max_length=50)),
                ('observacion', models.CharField(max_length=150)),
                ('entrega', models.CharField(max_length=150)),
                ('tipo_servicio', models.SmallIntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('contrato', models.ManyToManyField(related_name='contratos', to='zeus_mirror.contrato')),
            ],
        ),
        migrations.CreateModel(
            name='Actividad',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('tipo_fuente', models.CharField(max_length=10)),
                ('identificador', models.CharField(max_length=150)),
                ('regional', models.CharField(max_length=150)),
                ('fecha_servicio', models.DateField()),
                ('nombre_actividad', models.CharField(max_length=250)),
                ('diagnostico_p', models.CharField(default='', max_length=10)),
                ('diagnostico_1', models.CharField(default='', max_length=10)),
                ('diagnostico_2', models.CharField(default='', max_length=10)),
                ('diagnostico_3', models.CharField(default='', max_length=10)),
                ('tipo_documento', models.CharField(default='CC', max_length=10)),
                ('documento_paciente', models.CharField(max_length=50)),
                ('nombre_paciente', models.CharField(max_length=50)),
                ('sede', models.CharField(blank=True, default='1', max_length=10, null=True)),
                ('unidad_funcional', models.CharField(blank=True, max_length=150, null=True)),
                ('punto_atencion', models.CharField(blank=True, max_length=150, null=True)),
                ('centro_costo', models.CharField(blank=True, max_length=150, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('admision', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='home.admision')),
                ('tipo_actividad', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='home.tipoactividad')),
            ],
        ),
    ]
