# Generated by Django 4.1.4 on 2024-10-25 14:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('zeus_mirror', '0012_alter_usuariozeus_full_name'),
        ('home', '0024_alter_carga_estado'),
    ]

    operations = [
        migrations.AddField(
            model_name='actividad',
            name='usuario_zeus',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='zeus_mirror.usuariozeus'),
        ),
    ]
