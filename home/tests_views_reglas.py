"""
Tests CRUD de reglas SIESA y normalizaciones (Fase 3).

Cubre:
  - Auth requerido
  - Listado renderiza
  - Crear regla/normalización global y con fuente (override)
  - Validación de campos requeridos
  - Validación de duplicados (UNIQUE parcial por scope)
  - Edit / delete
"""

import json
from unittest.mock import patch

from cryptography.fernet import Fernet
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from home.models import (
    FuenteTipoUsuario,
    NormalizacionTipoAfiliado,
    ReglaHomologacionSIESA,
)
from home.modules import crypto


_TEST_FERNET = Fernet(Fernet.generate_key())


def _fuente(nombre="F_TEST"):
    return FuenteTipoUsuario.objects.create(
        nombre=nombre,
        activa=True,
        prioridad=100,
        servidor="srv",
        usuario="u",
        password_encrypted="",
        driver="SQL Server",
        tabla="DB.dbo.T",
        campo_documento="doc",
        campo_regimen="reg",
        campo_tipo_afiliado="tip",
    )


class ReglasAuthTests(TestCase):

    def test_listado_requiere_login(self):
        resp = self.client.get(reverse("vista_reglas_homologacion"))
        self.assertEqual(resp.status_code, 302)


class ReglasCRUDTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._fernet_patcher = patch.object(crypto, "_get_fernet", return_value=_TEST_FERNET)
        cls._fernet_patcher.start()

    @classmethod
    def tearDownClass(cls):
        cls._fernet_patcher.stop()
        super().tearDownClass()

    def setUp(self):
        self.user = User.objects.create_user(username="admin", password="x")
        self.client = Client()
        self.client.force_login(self.user)
        from home.modules.tipo_usuario import homologacion
        homologacion.invalidar_cache()

    # ─── Reglas SIESA ───────────────────────────────────────────────────────

    def test_listado_render(self):
        resp = self.client.get(reverse("vista_reglas_homologacion"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Reglas SIESA")

    def test_crear_regla_global(self):
        resp = self.client.post(
            reverse("crear_regla_siesa"),
            data=json.dumps({
                "fuente_id": None,
                "regimen": "C",
                "tipo_afiliado_codigo": "C",
                "codigo_siesa": "01",
                "descripcion": "Cotizante",
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.json()["ok"])
        r = ReglaHomologacionSIESA.objects.get(regimen="C", tipo_afiliado_codigo="C", fuente=None)
        self.assertEqual(r.codigo_siesa, "01")

    def test_crear_regla_con_fuente_override(self):
        f = _fuente()
        resp = self.client.post(
            reverse("crear_regla_siesa"),
            data=json.dumps({
                "fuente_id": f.id,
                "regimen": "X",
                "tipo_afiliado_codigo": "Y",
                "codigo_siesa": "77",
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        r = ReglaHomologacionSIESA.objects.get(fuente=f, regimen="X", tipo_afiliado_codigo="Y")
        self.assertEqual(r.codigo_siesa, "77")

    def test_crear_regla_rechaza_duplicado_global(self):
        self.client.post(
            reverse("crear_regla_siesa"),
            data=json.dumps({"regimen": "C", "tipo_afiliado_codigo": "C", "codigo_siesa": "01"}),
            content_type="application/json",
        )
        resp = self.client.post(
            reverse("crear_regla_siesa"),
            data=json.dumps({"regimen": "C", "tipo_afiliado_codigo": "C", "codigo_siesa": "02"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("ya existe", resp.json()["error"].lower())

    def test_crear_regla_acepta_misma_clave_si_scope_distinto(self):
        # global (C,C) y override fuente (C,C) deben poder coexistir
        f = _fuente()
        r1 = self.client.post(
            reverse("crear_regla_siesa"),
            data=json.dumps({"regimen": "C", "tipo_afiliado_codigo": "C", "codigo_siesa": "01"}),
            content_type="application/json",
        )
        r2 = self.client.post(
            reverse("crear_regla_siesa"),
            data=json.dumps({"fuente_id": f.id, "regimen": "C", "tipo_afiliado_codigo": "C", "codigo_siesa": "99"}),
            content_type="application/json",
        )
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(ReglaHomologacionSIESA.objects.count(), 2)

    def test_crear_regla_rechaza_campos_faltantes(self):
        resp = self.client.post(
            reverse("crear_regla_siesa"),
            data=json.dumps({"regimen": "C"}),  # falta tipo y siesa
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_editar_regla(self):
        r = ReglaHomologacionSIESA.objects.create(
            fuente=None, regimen="C", tipo_afiliado_codigo="C", codigo_siesa="01",
        )
        resp = self.client.post(
            reverse("editar_regla_siesa", args=[r.id]),
            data=json.dumps({
                "regimen": "C", "tipo_afiliado_codigo": "C", "codigo_siesa": "02",
                "descripcion": "cambiada",
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        r.refresh_from_db()
        self.assertEqual(r.codigo_siesa, "02")
        self.assertEqual(r.descripcion, "cambiada")

    def test_eliminar_regla(self):
        r = ReglaHomologacionSIESA.objects.create(
            fuente=None, regimen="C", tipo_afiliado_codigo="C", codigo_siesa="01",
        )
        resp = self.client.post(reverse("eliminar_regla_siesa", args=[r.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(ReglaHomologacionSIESA.objects.filter(id=r.id).exists())

    def test_normaliza_a_mayusculas_regimen_y_tipo(self):
        # El backend hace .upper() en regimen y tipo
        self.client.post(
            reverse("crear_regla_siesa"),
            data=json.dumps({"regimen": "c", "tipo_afiliado_codigo": "b", "codigo_siesa": "02"}),
            content_type="application/json",
        )
        r = ReglaHomologacionSIESA.objects.get(regimen="C", tipo_afiliado_codigo="B")
        self.assertEqual(r.codigo_siesa, "02")

    # ─── Normalizaciones ────────────────────────────────────────────────────

    def test_crear_normalizacion_global(self):
        resp = self.client.post(
            reverse("crear_normalizacion"),
            data=json.dumps({
                "valor_crudo": "CABEZA DE FAMLIA",
                "codigo_normalizado": "F",
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        n = NormalizacionTipoAfiliado.objects.get(valor_crudo="CABEZA DE FAMLIA", fuente=None)
        self.assertEqual(n.codigo_normalizado, "F")

    def test_crear_normalizacion_rechaza_duplicado(self):
        self.client.post(
            reverse("crear_normalizacion"),
            data=json.dumps({"valor_crudo": "X", "codigo_normalizado": "Y"}),
            content_type="application/json",
        )
        resp = self.client.post(
            reverse("crear_normalizacion"),
            data=json.dumps({"valor_crudo": "X", "codigo_normalizado": "Z"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_editar_normalizacion(self):
        n = NormalizacionTipoAfiliado.objects.create(
            fuente=None, valor_crudo="X", codigo_normalizado="Y",
        )
        resp = self.client.post(
            reverse("editar_normalizacion", args=[n.id]),
            data=json.dumps({"valor_crudo": "X", "codigo_normalizado": "Z"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        n.refresh_from_db()
        self.assertEqual(n.codigo_normalizado, "Z")

    def test_eliminar_normalizacion(self):
        n = NormalizacionTipoAfiliado.objects.create(
            fuente=None, valor_crudo="X", codigo_normalizado="Y",
        )
        resp = self.client.post(reverse("eliminar_normalizacion", args=[n.id]))
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(NormalizacionTipoAfiliado.objects.filter(id=n.id).exists())

    def test_crear_normalizacion_con_fuente_inexistente_falla(self):
        resp = self.client.post(
            reverse("crear_normalizacion"),
            data=json.dumps({
                "fuente_id": 99999,
                "valor_crudo": "X",
                "codigo_normalizado": "Y",
            }),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("no encontrada", resp.json()["error"].lower())
