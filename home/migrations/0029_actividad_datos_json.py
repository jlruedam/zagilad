# Generated by Django 4.1.4 on 2024-11-26 20:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0028_tokenapizeus_created_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='actividad',
            name='datos_json',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
