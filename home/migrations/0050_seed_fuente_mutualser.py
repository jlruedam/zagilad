"""
Seed inicial del módulo configurable de fuentes de tipo de usuario.

Crea:
  1. La fuente `MUTUAL_VIEW` con los valores que hoy viven hardcoded en
     `source_mutualser.py` + .env (`SERVER_LAKE`, `USERNAME_SERVER_LAKE`,
     `PASSWORD_SERVER_LAKE`). El password se cifra con Fernet.
  2. Las reglas SIESA globales que viven hoy en `homologacion.SIESA_RULES`.
  3. Los mapeos de normalización globales que viven hoy en
     `homologacion.SQL_TIPO_AFILIADO_TO_CODIGO`.

Esta migración es **defensiva**: si `FUENTES_FERNET_KEY` o las variables
`SERVER_LAKE`/`USERNAME_SERVER_LAKE`/`PASSWORD_SERVER_LAKE` no están
configuradas, se loguea un warning y se omite la creación de la fuente
(pero las reglas + normalizaciones globales sí se siembran para que el
admin tenga datos iniciales).

Idempotente: usa `get_or_create`, se puede correr varias veces sin duplicar.
"""

import logging

from decouple import config
from django.core.exceptions import ImproperlyConfigured
from django.db import migrations


logger = logging.getLogger(__name__)


# Reglas globales — extraídas de home/modules/tipo_usuario/homologacion.py:SIESA_RULES
# Formato: (regimen, tipo_afiliado_codigo, codigo_siesa, descripcion)
REGLAS_SIESA_GLOBALES = [
    ("S", "*", "04", "Subsidiado — cualquier tipo"),
    ("C", "C", "01", "Contributivo — Cotizante"),
    ("C", "ND", "01", "Contributivo — No definido (tratado como cotizante)"),
    ("C", "SC", "01", "Contributivo — Segundo Cotizante"),
    ("C", "F", "01", "Contributivo — Cabeza de Familia"),
    ("C", "B", "02", "Contributivo — Beneficiario"),
    ("C", "A", "03", "Contributivo — Adicional"),
]

# Normalizaciones globales — extraídas de SQL_TIPO_AFILIADO_TO_CODIGO.
# Se omite la entrada 'f' minúscula porque colisiona con 'F' en collations
# case-insensitive (SQL Server default). El fallback `s.upper()` ya cubre
# minúsculas en el código de runtime.
NORMALIZACIONES_GLOBALES = [
    ("BENEFICIARIO", "B"),
    ("COTIZANTE", "C"),
    ("SEGUNDO COTIZANTE", "SC"),
    ("CABEZA DE FAMILIA", "F"),
    ("CABEZA DE FAMLIA", "F"),  # typo histórico en MUTUAL SER
    ("ADICIONAL", "A"),
    ("ND", "ND"),
    ("F", "F"),
    ("O", "O"),
]


def _encrypt_password(plaintext: str) -> str | None:
    """Cifra con Fernet. Retorna None si la clave no está configurada."""
    try:
        from home.modules.crypto import encrypt

        return encrypt(plaintext)
    except ImproperlyConfigured as e:
        logger.warning(
            "Seed MUTUAL_VIEW omitido: %s. Configurá FUENTES_FERNET_KEY y "
            "ejecutá el management command de re-seed o creá la fuente manualmente "
            "desde el admin.",
            e,
        )
        return None


def sembrar(apps, schema_editor):
    FuenteTipoUsuario = apps.get_model("home", "FuenteTipoUsuario")
    ReglaHomologacionSIESA = apps.get_model("home", "ReglaHomologacionSIESA")
    NormalizacionTipoAfiliado = apps.get_model("home", "NormalizacionTipoAfiliado")

    # 1. Reglas SIESA globales (no requieren cifrado)
    for regimen, tipo, siesa, descripcion in REGLAS_SIESA_GLOBALES:
        ReglaHomologacionSIESA.objects.get_or_create(
            fuente=None,
            regimen=regimen,
            tipo_afiliado_codigo=tipo,
            defaults={"codigo_siesa": siesa, "descripcion": descripcion},
        )

    # 2. Normalizaciones globales
    for valor_crudo, codigo in NORMALIZACIONES_GLOBALES:
        NormalizacionTipoAfiliado.objects.get_or_create(
            fuente=None,
            valor_crudo=valor_crudo,
            defaults={"codigo_normalizado": codigo},
        )

    # 3. Fuente MUTUAL_VIEW — solo si están todas las env vars
    servidor = config("SERVER_LAKE", default="")
    usuario = config("USERNAME_SERVER_LAKE", default="")
    password = config("PASSWORD_SERVER_LAKE", default="")

    if not (servidor and usuario and password):
        logger.warning(
            "Seed MUTUAL_VIEW omitido: faltan env vars (SERVER_LAKE/"
            "USERNAME_SERVER_LAKE/PASSWORD_SERVER_LAKE). Creá la fuente "
            "manualmente desde el admin cuando estén configuradas."
        )
        return

    password_encrypted = _encrypt_password(password)
    if password_encrypted is None:
        return  # Sin clave Fernet — ya logueó el warning

    FuenteTipoUsuario.objects.get_or_create(
        nombre="MUTUAL_VIEW",
        defaults={
            "descripcion": "Vista limpia de afiliados de MUTUAL SER en el data lake",
            "activa": True,
            "prioridad": 10,
            "servidor": servidor,
            "base_datos": "",  # incluida en `tabla` (MUTUALSER.dbo.<tabla>)
            "usuario": usuario,
            "password_encrypted": password_encrypted,
            "driver": "SQL Server",
            "tabla": "MUTUALSER.dbo.DL_MS_AFILIADO_VIEW_CLEAN",
            "campo_documento": "AFIC_DOCUMENTO",
            "campo_regimen": "AFIC_REGIMEN",
            "campo_tipo_afiliado": "AFIC_TIPO",
            "estado_validacion": "pendiente",
            "mensaje_validacion": "Fuente creada por seed inicial — pendiente de validar",
        },
    )


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0049_fuente_tipo_usuario"),
    ]

    operations = [
        # reverse_code=noop: si se hace rollback la tabla se dropea en 0049.
        migrations.RunPython(sembrar, reverse_code=migrations.RunPython.noop),
    ]
