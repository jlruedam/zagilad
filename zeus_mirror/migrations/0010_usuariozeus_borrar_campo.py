# Generated by Django 4.1.4 on 2024-10-25 13:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zeus_mirror', '0009_usuariozeus'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuariozeus',
            name='borrar_campo',
            field=models.CharField(default='', max_length=250),
            preserve_default=False,
        ),
    ]
