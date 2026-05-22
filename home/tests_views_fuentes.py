"""
Tests de las views CRUD de fuentes (Fase 3).

Cubre:
  - Auth requerido (302 a login si no autenticado)
  - GET listado renderiza
  - POST crear: happy path, validación de identificadores SQL, password requerida
  - POST editar: actualiza campos, password opcional, conserva password si vacío
  - POST toggle_activa, eliminar
  - AJAX: probar_conexion, listar_tablas, listar_columnas (con pyodbc mockeado)
"""

import json
from unittest.mock import MagicMock, patch

from cryptography.fernet import Fernet
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from home.models import FuenteTipoUsuario
from home.modules import crypto


_TEST_FERNET = Fernet(Fernet.generate_key())


def _make_pyodbc_mock(query_to_rows=None, raise_exc=None):
    """Reemplazo de pyodbc.connect para los tests de admin helpers."""
    if query_to_rows is None:
        query_to_rows = lambda q: []

    def _connect(*args, **kwargs):
        conn = MagicMock()
        cursor = MagicMock()
        if raise_exc is not None:
            cursor.execute.side_effect = raise_exc
        else:
            def _execute(query, *params):
                cursor._last_query = query
                cursor._rows = query_to_rows(query)
            cursor.execute.side_effect = _execute
            cursor.fetchall.side_effect = lambda: cursor._rows
            cursor.fetchone.side_effect = lambda: (cursor._rows[0] if cursor._rows else None)
        conn.cursor.return_value = cursor
        return conn

    return _connect


class FuentesAuthTests(TestCase):
    """Sin autenticar, todas las views redirigen a login."""

    def test_listado_requiere_login(self):
        resp = self.client.get(reverse("vista_fuentes_tipo_usuario"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login/", resp.url)

    def test_crear_requiere_login(self):
        resp = self.client.post(
            reverse("crear_fuente_tipo_usuario"),
            data=json.dumps({"nombre": "X"}),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 302)


class FuentesCRUDTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._fernet_patcher = patch.object(crypto, "_get_fernet", return_value=_TEST_FERNET)
        cls._fernet_patcher.start()
        crypto._get_fernet.cache_clear()

    @classmethod
    def tearDownClass(cls):
        cls._fernet_patcher.stop()
        crypto._get_fernet.cache_clear()
        super().tearDownClass()

    def setUp(self):
        self.user = User.objects.create_user(username="admin", password="x")
        self.client = Client()
        self.client.force_login(self.user)

    def _payload_valido(self, **overrides):
        base = {
            "nombre": "TEST_FUENTE",
            "descripcion": "desc",
            "activa": True,
            "prioridad": 50,
            "servidor": "srv1",
            "usuario": "u1",
            "password": "secret123",
            "driver": "SQL Server",
            "base_datos": "DB1",
            "tabla": "DB1.dbo.afiliados",
            "campo_documento": "doc",
            "campo_regimen": "reg",
            "campo_tipo_afiliado": "tip",
        }
        base.update(overrides)
        return base

    # ─── listado ────────────────────────────────────────────────────────────
    def test_listado_render(self):
        resp = self.client.get(reverse("vista_fuentes_tipo_usuario"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Fuentes de Tipo de Usuario")

    # ─── crear ──────────────────────────────────────────────────────────────
    def test_crear_happy_path(self):
        resp = self.client.post(
            reverse("crear_fuente_tipo_usuario"),
            data=json.dumps(self._payload_valido()),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["ok"])
        f = FuenteTipoUsuario.objects.get(nombre="TEST_FUENTE")
        # Password cifrado, no en plano
        self.assertNotEqual(f.password_encrypted, "secret123")
        self.assertEqual(crypto.decrypt(f.password_encrypted), "secret123")

    def test_crear_rechaza_nombre_duplicado(self):
        self.client.post(
            reverse("crear_fuente_tipo_usuario"),
            data=json.dumps(self._payload_valido()),
            content_type="application/json",
        )
        resp = self.client.post(
            reverse("crear_fuente_tipo_usuario"),
            data=json.dumps(self._payload_valido()),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("ya existe", resp.json()["error"].lower())

    def test_crear_rechaza_tabla_con_inyeccion(self):
        resp = self.client.post(
            reverse("crear_fuente_tipo_usuario"),
            data=json.dumps(self._payload_valido(tabla="afil; DROP TABLE x;--")),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("inválido", resp.json()["error"].lower())
        self.assertFalse(FuenteTipoUsuario.objects.filter(nombre="TEST_FUENTE").exists())

    def test_crear_rechaza_password_vacia(self):
        resp = self.client.post(
            reverse("crear_fuente_tipo_usuario"),
            data=json.dumps(self._payload_valido(password="")),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_crear_rechaza_campo_invalido(self):
        resp = self.client.post(
            reverse("crear_fuente_tipo_usuario"),
            data=json.dumps(self._payload_valido(campo_documento="doc; DROP")),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)

    def test_crear_con_campo_tipo_documento_opcional(self):
        resp = self.client.post(
            reverse("crear_fuente_tipo_usuario"),
            data=json.dumps(self._payload_valido(campo_tipo_documento="tipo_doc_col")),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        f = FuenteTipoUsuario.objects.get(nombre="TEST_FUENTE")
        self.assertEqual(f.campo_tipo_documento, "tipo_doc_col")

    def test_crear_acepta_campo_tipo_documento_vacio(self):
        # Campo opcional — la creación debe funcionar sin él (default '')
        resp = self.client.post(
            reverse("crear_fuente_tipo_usuario"),
            data=json.dumps(self._payload_valido()),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        f = FuenteTipoUsuario.objects.get(nombre="TEST_FUENTE")
        self.assertEqual(f.campo_tipo_documento, "")

    def test_crear_rechaza_campo_tipo_documento_invalido(self):
        resp = self.client.post(
            reverse("crear_fuente_tipo_usuario"),
            data=json.dumps(self._payload_valido(campo_tipo_documento="td; DROP")),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo documento", resp.json()["error"].lower())
        self.assertFalse(FuenteTipoUsuario.objects.filter(nombre="TEST_FUENTE").exists())

    # ─── editar ─────────────────────────────────────────────────────────────
    def test_editar_conserva_password_si_vacio(self):
        resp = self.client.post(
            reverse("crear_fuente_tipo_usuario"),
            data=json.dumps(self._payload_valido()),
            content_type="application/json",
        )
        f_id = resp.json()["fuente"]["id"]
        cipher_original = FuenteTipoUsuario.objects.get(id=f_id).password_encrypted

        # editar SIN password
        resp = self.client.post(
            reverse("editar_fuente_tipo_usuario", args=[f_id]),
            data=json.dumps(self._payload_valido(descripcion="cambiada", password="")),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        f = FuenteTipoUsuario.objects.get(id=f_id)
        self.assertEqual(f.descripcion, "cambiada")
        self.assertEqual(f.password_encrypted, cipher_original)

    def test_editar_actualiza_password_si_se_provee(self):
        resp = self.client.post(
            reverse("crear_fuente_tipo_usuario"),
            data=json.dumps(self._payload_valido()),
            content_type="application/json",
        )
        f_id = resp.json()["fuente"]["id"]

        resp = self.client.post(
            reverse("editar_fuente_tipo_usuario", args=[f_id]),
            data=json.dumps(self._payload_valido(password="nuevoSecreto")),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        f = FuenteTipoUsuario.objects.get(id=f_id)
        self.assertEqual(crypto.decrypt(f.password_encrypted), "nuevoSecreto")

    # ─── toggle / eliminar ──────────────────────────────────────────────────
    def test_toggle_activa(self):
        resp = self.client.post(
            reverse("crear_fuente_tipo_usuario"),
            data=json.dumps(self._payload_valido()),
            content_type="application/json",
        )
        f_id = resp.json()["fuente"]["id"]
        self.assertTrue(FuenteTipoUsuario.objects.get(id=f_id).activa)

        resp = self.client.post(reverse("toggle_activa_fuente", args=[f_id]))
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(FuenteTipoUsuario.objects.get(id=f_id).activa)

        # toggle de vuelta
        self.client.post(reverse("toggle_activa_fuente", args=[f_id]))
        self.assertTrue(FuenteTipoUsuario.objects.get(id=f_id).activa)

    def test_eliminar(self):
        resp = self.client.post(
            reverse("crear_fuente_tipo_usuario"),
            data=json.dumps(self._payload_valido()),
            content_type="application/json",
        )
        f_id = resp.json()["fuente"]["id"]

        resp = self.client.post(reverse("eliminar_fuente_tipo_usuario", args=[f_id]))
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(FuenteTipoUsuario.objects.filter(id=f_id).exists())


class FuentesAjaxTests(TestCase):
    """AJAX endpoints con pyodbc mockeado."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._fernet_patcher = patch.object(crypto, "_get_fernet", return_value=_TEST_FERNET)
        cls._fernet_patcher.start()
        crypto._get_fernet.cache_clear()

    @classmethod
    def tearDownClass(cls):
        cls._fernet_patcher.stop()
        crypto._get_fernet.cache_clear()
        super().tearDownClass()

    def setUp(self):
        self.user = User.objects.create_user(username="admin", password="x")
        self.client = Client()
        self.client.force_login(self.user)

    def _creds_payload(self):
        return {
            "servidor": "srv1",
            "usuario": "u1",
            "password": "secret",
            "driver": "SQL Server",
            "base_datos": "DB1",
        }

    def test_probar_conexion_ok(self):
        mock_connect = _make_pyodbc_mock(query_to_rows=lambda q: [(1,)])
        with patch("home.modules.tipo_usuario.source_admin_helpers.pyodbc.connect",
                   side_effect=mock_connect):
            resp = self.client.post(
                reverse("probar_conexion_fuente"),
                data=json.dumps(self._creds_payload()),
                content_type="application/json",
            )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["ok"])

    def test_probar_conexion_falla(self):
        import pyodbc
        with patch("home.modules.tipo_usuario.source_admin_helpers.pyodbc.connect",
                   side_effect=pyodbc.OperationalError("login failed")):
            resp = self.client.post(
                reverse("probar_conexion_fuente"),
                data=json.dumps(self._creds_payload()),
                content_type="application/json",
            )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertFalse(data["ok"])
        self.assertIn("login failed", data["mensaje"])

    def test_listar_tablas_devuelve_lista(self):
        rows = [("dbo", "tabla_a"), ("dbo", "tabla_b")]
        mock_connect = _make_pyodbc_mock(query_to_rows=lambda q: rows)
        with patch("home.modules.tipo_usuario.source_admin_helpers.pyodbc.connect",
                   side_effect=mock_connect):
            resp = self.client.post(
                reverse("listar_tablas_fuente"),
                data=json.dumps(self._creds_payload()),
                content_type="application/json",
            )
        data = resp.json()
        self.assertTrue(data["ok"])
        # Las tablas vienen con prefijo de DB
        self.assertEqual(data["tablas"], ["DB1.dbo.tabla_a", "DB1.dbo.tabla_b"])

    def test_listar_tablas_requiere_base_datos(self):
        payload = self._creds_payload()
        payload.pop("base_datos")
        resp = self.client.post(
            reverse("listar_tablas_fuente"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertIn("base de datos", resp.json()["error"].lower())

    def test_listar_columnas_devuelve_columnas(self):
        rows = [("doc", "varchar", "YES"), ("reg", "char", "NO"), ("tip", "varchar", "YES")]
        mock_connect = _make_pyodbc_mock(query_to_rows=lambda q: rows)
        with patch("home.modules.tipo_usuario.source_admin_helpers.pyodbc.connect",
                   side_effect=mock_connect):
            payload = self._creds_payload()
            payload["tabla"] = "DB1.dbo.afiliados"
            resp = self.client.post(
                reverse("listar_columnas_fuente"),
                data=json.dumps(payload),
                content_type="application/json",
            )
        data = resp.json()
        self.assertTrue(data["ok"])
        self.assertEqual(len(data["columnas"]), 3)
        self.assertEqual(data["columnas"][0]["nombre"], "doc")
        self.assertTrue(data["columnas"][0]["nullable"])
        self.assertFalse(data["columnas"][1]["nullable"])
