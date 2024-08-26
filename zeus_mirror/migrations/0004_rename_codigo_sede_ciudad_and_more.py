# Generated by Django 4.1.4 on 2024-08-16 14:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zeus_mirror', '0003_sede'),
    ]

    operations = [
        migrations.RenameField(
            model_name='sede',
            old_name='codigo',
            new_name='ciudad',
        ),
        migrations.RenameField(
            model_name='sede',
            old_name='nombre',
            new_name='codigo_eps',
        ),
        migrations.RemoveField(
            model_name='sede',
            name='municipio',
        ),
        migrations.AddField(
            model_name='sede',
            name='razon_social',
            field=models.CharField(default=1, max_length=150),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='sede',
            name='departamento',
            field=models.CharField(max_length=50),
        ),
    ]