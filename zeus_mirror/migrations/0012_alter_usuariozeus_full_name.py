# Generated by Django 4.1.4 on 2024-10-25 13:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('zeus_mirror', '0011_remove_usuariozeus_borrar_campo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usuariozeus',
            name='full_name',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
    ]
