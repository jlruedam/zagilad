"""
Tests del módulo de homologación (`home/modules/tipo_usuario/homologacion.py`).

Cubre:
  - Defaults en memoria cuando la DB no tiene reglas
  - Prioridad de lookup: fuente_id override > global DB > defaults
  - Wildcard "*" en tipo_afiliado_codigo
  - Normalización por fuente / global / default / .upper()
  - Invalidación de cache vía signals (post_save / post_delete)
  - TTL: el cache se refresca tras el TTL
"""

import time
from unittest.mock import patch

from django.test import TestCase

from home.models import (
    FuenteTipoUsuario,
    NormalizacionTipoAfiliado,
    ReglaHomologacionSIESA,
)
from home.modules.tipo_usuario import homologacion


def _fuente(**overrides) -> FuenteTipoUsuario:
    defaults = {
        "nombre": "TEST_FUENTE",
        "activa": True,
        "prioridad": 100,
        "servidor": "srv-test",
        "usuario": "u",
        "password_encrypted": "",  # no se ejecutan queries reales en estos tests
        "driver": "SQL Server",
        "tabla": "TEST.dbo.FAKE",
        "campo_documento": "doc",
        "campo_regimen": "reg",
        "campo_tipo_afiliado": "tip",
    }
    defaults.update(overrides)
    return FuenteTipoUsuario.objects.create(**defaults)


class HomologarSiesaLookupTests(TestCase):
    def setUp(self):
        homologacion.invalidar_cache()

    def tearDown(self):
        homologacion.invalidar_cache()

    def test_default_se_usa_si_db_vacia(self):
        # Sin filas en DB, debe caer al DEFAULT_SIESA_RULES.
        self.assertEqual(homologacion.homologar_siesa("C", "C"), "01")
        self.assertEqual(homologacion.homologar_siesa("C", "B"), "02")
        self.assertEqual(homologacion.homologar_siesa("S", "C"), "04")  # wildcard '*'

    def test_regla_global_en_db_sobreescribe_default(self):
        ReglaHomologacionSIESA.objects.create(
            fuente=None, regimen="C", tipo_afiliado_codigo="C", codigo_siesa="99",
        )
        # post_save signal ya invalidó el cache → próxima lectura lee desde DB.
        self.assertEqual(homologacion.homologar_siesa("C", "C"), "99")

    def test_override_por_fuente_gana_a_global(self):
        f = _fuente()
        ReglaHomologacionSIESA.objects.create(
            fuente=None, regimen="C", tipo_afiliado_codigo="C", codigo_siesa="01",
        )
        ReglaHomologacionSIESA.objects.create(
            fuente=f, regimen="C", tipo_afiliado_codigo="C", codigo_siesa="77",
        )
        self.assertEqual(homologacion.homologar_siesa("C", "C", fuente_id=f.id), "77")
        # Sin fuente_id, vuelve a la global
        self.assertEqual(homologacion.homologar_siesa("C", "C"), "01")

    def test_wildcard_global(self):
        ReglaHomologacionSIESA.objects.create(
            fuente=None, regimen="X", tipo_afiliado_codigo="*", codigo_siesa="50",
        )
        self.assertEqual(homologacion.homologar_siesa("X", "ANY"), "50")
        self.assertEqual(homologacion.homologar_siesa("X", "OTRO"), "50")

    def test_regimen_no_existente_devuelve_vacio(self):
        self.assertEqual(homologacion.homologar_siesa("Z", "Z"), "")

    def test_regimen_vacio_devuelve_vacio(self):
        self.assertEqual(homologacion.homologar_siesa("", "C"), "")
        self.assertEqual(homologacion.homologar_siesa(None, "C"), "")

    def test_normaliza_mayusculas(self):
        # Aún sin reglas en DB, los defaults son case-insensitive en el lookup.
        self.assertEqual(homologacion.homologar_siesa("c", "c"), "01")


class NormalizarTipoAfiliadoTests(TestCase):
    def setUp(self):
        homologacion.invalidar_cache()

    def tearDown(self):
        homologacion.invalidar_cache()

    def test_default_se_usa_si_db_vacia(self):
        self.assertEqual(homologacion.normalizar_tipo_afiliado("BENEFICIARIO"), "B")
        self.assertEqual(homologacion.normalizar_tipo_afiliado("CABEZA DE FAMLIA"), "F")

    def test_db_global_sobreescribe_default(self):
        NormalizacionTipoAfiliado.objects.create(
            fuente=None, valor_crudo="BENEFICIARIO", codigo_normalizado="BNF",
        )
        self.assertEqual(homologacion.normalizar_tipo_afiliado("BENEFICIARIO"), "BNF")

    def test_override_por_fuente_gana(self):
        f = _fuente()
        NormalizacionTipoAfiliado.objects.create(
            fuente=None, valor_crudo="COTIZANTE", codigo_normalizado="C",
        )
        NormalizacionTipoAfiliado.objects.create(
            fuente=f, valor_crudo="COTIZANTE", codigo_normalizado="X",
        )
        self.assertEqual(
            homologacion.normalizar_tipo_afiliado("COTIZANTE", fuente_id=f.id), "X"
        )
        self.assertEqual(homologacion.normalizar_tipo_afiliado("COTIZANTE"), "C")

    def test_fallback_upper_si_no_match(self):
        self.assertEqual(homologacion.normalizar_tipo_afiliado("xyz"), "XYZ")

    def test_vacio_devuelve_vacio(self):
        self.assertEqual(homologacion.normalizar_tipo_afiliado(""), "")
        self.assertEqual(homologacion.normalizar_tipo_afiliado(None), "")


class CacheInvalidationTests(TestCase):
    """Signals de invalidación: editar/borrar reglas refresca el cache."""

    def setUp(self):
        homologacion.invalidar_cache()

    def tearDown(self):
        homologacion.invalidar_cache()

    def test_post_save_regla_invalida_cache(self):
        # Primera lectura: caen los defaults
        self.assertEqual(homologacion.homologar_siesa("C", "C"), "01")
        # Crear una regla global con valor distinto
        regla = ReglaHomologacionSIESA.objects.create(
            fuente=None, regimen="C", tipo_afiliado_codigo="C", codigo_siesa="88",
        )
        # El signal post_save debió haber limpiado el cache
        self.assertEqual(homologacion.homologar_siesa("C", "C"), "88")
        # Borrar → vuelve a defaults
        regla.delete()
        self.assertEqual(homologacion.homologar_siesa("C", "C"), "01")

    def test_post_save_normalizacion_invalida_cache(self):
        self.assertEqual(homologacion.normalizar_tipo_afiliado("COTIZANTE"), "C")
        n = NormalizacionTipoAfiliado.objects.create(
            fuente=None, valor_crudo="COTIZANTE", codigo_normalizado="XYZ",
        )
        self.assertEqual(homologacion.normalizar_tipo_afiliado("COTIZANTE"), "XYZ")
        n.delete()
        self.assertEqual(homologacion.normalizar_tipo_afiliado("COTIZANTE"), "C")


class CacheTTLTests(TestCase):
    """Si el TTL expira, el cache se refresca aunque no haya invalidación explícita."""

    def setUp(self):
        homologacion.invalidar_cache()

    def tearDown(self):
        homologacion.invalidar_cache()

    @patch.object(homologacion, "_CACHE_TTL_SEC", 0)
    def test_ttl_cero_siempre_refresca(self):
        # TTL=0 → cada lookup recarga desde DB
        self.assertEqual(homologacion.homologar_siesa("C", "C"), "01")
        ReglaHomologacionSIESA.objects.create(
            fuente=None, regimen="C", tipo_afiliado_codigo="C", codigo_siesa="44",
        )
        # El signal ya invalidó, pero aún sin signal TTL=0 debe refrescar igual
        homologacion._cache_loaded_at = time.time() - 100  # forzar expiración
        self.assertEqual(homologacion.homologar_siesa("C", "C"), "44")
