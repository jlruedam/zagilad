# Generated by Django 4.1.4 on 2024-08-15 20:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('zeus_mirror', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='puntoatencion',
            old_name='Municipio',
            new_name='municipio',
        ),
    ]
