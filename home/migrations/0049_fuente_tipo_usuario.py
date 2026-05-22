"""
Schema para el módulo configurable de fuentes de tipo de usuario.

Crea 3 tablas:
  - FuenteTipoUsuario: conexión + mapeo de tabla/columnas
  - ReglaHomologacionSIESA: régimen + tipo → código SIESA (con override por fuente)
  - NormalizacionTipoAfiliado: valor crudo → código corto (con override por fuente)

El seed inicial (fuente MUTUAL_VIEW + reglas + normalizaciones) va en
`0050_seed_fuente_mutualser.py`.
"""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0048_normalize_tipo_usuario_inconsistencia"),
    ]

    operations = [
        migrations.CreateModel(
            name="FuenteTipoUsuario",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("nombre", models.CharField(max_length=100, unique=True, help_text="Identificador único (ej. MUTUAL_VIEW)")),
                ("descripcion", models.CharField(blank=True, default="", max_length=250)),
                ("activa", models.BooleanField(default=True)),
                ("prioridad", models.IntegerField(default=100, help_text="Menor número = mayor prioridad en la cascada")),
                ("servidor", models.CharField(max_length=200)),
                ("base_datos", models.CharField(blank=True, default="", max_length=100, help_text="Opcional si la tabla incluye DB.schema.tabla")),
                ("usuario", models.CharField(max_length=100)),
                ("password_encrypted", models.TextField(help_text="Cifrado con Fernet — no editar manualmente")),
                ("driver", models.CharField(default="SQL Server", max_length=100)),
                ("tabla", models.CharField(max_length=200, help_text="Nombre completo, ej: MUTUALSER.dbo.DL_MS_AFILIADO_VIEW_CLEAN")),
                ("campo_documento", models.CharField(max_length=100)),
                ("campo_regimen", models.CharField(max_length=100)),
                ("campo_tipo_afiliado", models.CharField(max_length=100)),
                (
                    "estado_validacion",
                    models.CharField(
                        choices=[("ok", "OK"), ("error", "Error"), ("pendiente", "Pendiente")],
                        default="pendiente",
                        max_length=20,
                    ),
                ),
                ("mensaje_validacion", models.TextField(blank=True, default="")),
                ("ultima_validacion_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Fuente de tipo de usuario",
                "verbose_name_plural": "Fuentes de tipo de usuario",
                "ordering": ["prioridad", "nombre"],
            },
        ),
        migrations.CreateModel(
            name="ReglaHomologacionSIESA",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("regimen", models.CharField(max_length=10)),
                (
                    "tipo_afiliado_codigo",
                    models.CharField(max_length=10, help_text='Código corto. "*" = cualquier tipo bajo ese régimen'),
                ),
                ("codigo_siesa", models.CharField(max_length=10)),
                ("descripcion", models.CharField(blank=True, default="", max_length=150)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "fuente",
                    models.ForeignKey(
                        blank=True,
                        help_text="NULL = regla global",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="home.fuentetipousuario",
                    ),
                ),
            ],
            options={
                "verbose_name": "Regla de homologación SIESA",
                "verbose_name_plural": "Reglas de homologación SIESA",
                "ordering": ["fuente_id", "regimen", "tipo_afiliado_codigo"],
            },
        ),
        migrations.CreateModel(
            name="NormalizacionTipoAfiliado",
            fields=[
                ("id", models.AutoField(primary_key=True, serialize=False)),
                ("valor_crudo", models.CharField(help_text="Tal cual lo devuelve la fuente", max_length=100)),
                ("codigo_normalizado", models.CharField(max_length=10)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "fuente",
                    models.ForeignKey(
                        blank=True,
                        help_text="NULL = mapeo global",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="home.fuentetipousuario",
                    ),
                ),
            ],
            options={
                "verbose_name": "Normalización de tipo de afiliado",
                "verbose_name_plural": "Normalizaciones de tipo de afiliado",
                "ordering": ["fuente_id", "valor_crudo"],
            },
        ),
        migrations.AddConstraint(
            model_name="reglahomologacionsiesa",
            constraint=models.UniqueConstraint(
                condition=models.Q(("fuente__isnull", False)),
                fields=("fuente", "regimen", "tipo_afiliado_codigo"),
                name="uniq_regla_siesa_fuente_reg_tipo",
            ),
        ),
        migrations.AddConstraint(
            model_name="reglahomologacionsiesa",
            constraint=models.UniqueConstraint(
                condition=models.Q(("fuente__isnull", True)),
                fields=("regimen", "tipo_afiliado_codigo"),
                name="uniq_regla_siesa_global_reg_tipo",
            ),
        ),
        migrations.AddConstraint(
            model_name="normalizaciontipoafiliado",
            constraint=models.UniqueConstraint(
                condition=models.Q(("fuente__isnull", False)),
                fields=("fuente", "valor_crudo"),
                name="uniq_normalizacion_fuente_valor",
            ),
        ),
        migrations.AddConstraint(
            model_name="normalizaciontipoafiliado",
            constraint=models.UniqueConstraint(
                condition=models.Q(("fuente__isnull", True)),
                fields=("valor_crudo",),
                name="uniq_normalizacion_global_valor",
            ),
        ),
    ]
