# Generated by Django 4.1.4 on 2024-09-16 13:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0019_alter_carga_estado'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actividad',
            name='inconsistencias',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
    ]