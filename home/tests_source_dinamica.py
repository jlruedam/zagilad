"""
Tests del módulo `source_dinamica` con pyodbc mockeado.

Cubre:
  - Sanitización de documento (regex `_RX_DOC`)
  - Validación de identificadores SQL (whitelist regex)
  - Cascada de fuentes activas por prioridad
  - Batch resolución progresiva
  - Manejo de excepciones cuando todas las fuentes fallan
  - Pool versionado por `updated_at`
"""

from unittest.mock import MagicMock, patch

import pyodbc

from django.test import TestCase

from home.models import (
    FuenteTipoUsuario,
    ReglaHomologacionSIESA,
)
from home.modules.tipo_usuario import source_dinamica


def _fuente(nombre="F1", prioridad=10, activa=True,
            tabla="DB.dbo.T",
            campo_documento="doc",
            campo_regimen="reg",
            campo_tipo_afiliado="tip"):
    return FuenteTipoUsuario.objects.create(
        nombre=nombre,
        activa=activa,
        prioridad=prioridad,
        servidor="srv",
        usuario="u",
        password_encrypted="",
        driver="SQL Server",
        tabla=tabla,
        campo_documento=campo_documento,
        campo_regimen=campo_regimen,
        campo_tipo_afiliado=campo_tipo_afiliado,
    )


def _fake_pyodbc_with_rows(rows_por_query=None, raise_on_call=None):
    """
    Devuelve un mock que reemplaza `pyodbc.connect`. Acepta:
      - `rows_por_query`: callable(query_str) -> list[tuple] que decide qué
        rows devolver. Si no se provee, devuelve [].
      - `raise_on_call`: excepción a lanzar al ejecutar cursor.execute.
    """
    if rows_por_query is None:
        rows_por_query = lambda q: []

    def _make_connection(*args, **kwargs):
        conn = MagicMock()
        cursor = MagicMock()
        if raise_on_call is not None:
            cursor.execute.side_effect = raise_on_call
        else:
            def _execute(query):
                cursor._last_query = query
                cursor._rows = rows_por_query(query)
            cursor.execute.side_effect = _execute
            cursor.fetchall.side_effect = lambda: cursor._rows
        conn.cursor.return_value = cursor
        return conn

    return _make_connection


class SanitizeAndValidateTests(TestCase):

    def test_sanitize_doc_quita_no_alfanum(self):
        self.assertEqual(source_dinamica._sanitize_doc("123-456"), "123456")
        self.assertEqual(source_dinamica._sanitize_doc("CC 123"), "CC123")
        self.assertEqual(source_dinamica._sanitize_doc("'; DROP--"), "DROP")
        self.assertEqual(source_dinamica._sanitize_doc(None), "")
        self.assertEqual(source_dinamica._sanitize_doc(""), "")

    def test_validar_identificadores_acepta_validos(self):
        f = _fuente()
        # No debe lanzar
        source_dinamica._validar_identificadores(f)

    def test_validar_identificadores_rechaza_inyeccion(self):
        casos_malos = [
            "T; DROP TABLE x",
            "T'",
            "[T]",
            "T--",
            "T WHERE 1=1",
            "a.b.c.d",   # > 2 puntos
            ".",
            "1tabla",    # arranca con dígito
        ]
        for tabla_mala in casos_malos:
            f = _fuente(nombre=f"f_{hash(tabla_mala)}", tabla=tabla_mala)
            with self.assertRaises(ValueError, msg=f"tabla={tabla_mala!r} debió rechazarse"):
                source_dinamica._validar_identificadores(f)

    def test_validar_identificadores_rechaza_campo_invalido(self):
        f = _fuente(campo_documento="doc; DROP")
        with self.assertRaises(ValueError):
            source_dinamica._validar_identificadores(f)


class ObtenerCascadaTests(TestCase):
    """`obtener` itera fuentes en orden de prioridad y devuelve el primer SIESA."""

    def setUp(self):
        from home.modules.tipo_usuario import homologacion
        homologacion.invalidar_cache()
        # Limpia pool entre tests
        source_dinamica._thread_local.conns = {}
        # Limpia fuentes sembradas por la migración 0050 — los tests
        # construyen su propio escenario.
        FuenteTipoUsuario.objects.all().delete()

    def test_sin_fuentes_devuelve_vacio(self):
        # No hay fuentes activas → no se llama a pyodbc
        with patch.object(source_dinamica.pyodbc, "connect") as mock_connect:
            result = source_dinamica.obtener("123")
            self.assertEqual(result, "")
            mock_connect.assert_not_called()

    def test_primera_fuente_resuelve(self):
        f1 = _fuente(nombre="F1", prioridad=10)
        _fuente(nombre="F2", prioridad=20)

        def rows(query):
            # f1 query trae la fila; f2 no debe ser consultada
            return [("C", "COTIZANTE")]

        with patch.object(source_dinamica.pyodbc, "connect",
                          side_effect=_fake_pyodbc_with_rows(rows_por_query=rows)) as mock_connect:
            result = source_dinamica.obtener("123")
            self.assertEqual(result, "01")
            # Solo una conexión abierta (f1)
            self.assertEqual(mock_connect.call_count, 1)

    def test_fallback_a_segunda_fuente_si_primera_no_encuentra(self):
        _fuente(nombre="F1", prioridad=10)
        _fuente(nombre="F2", prioridad=20)

        calls = []

        def rows(query):
            calls.append(query)
            # primera consulta → vacía; segunda → match
            if len(calls) == 1:
                return []
            return [("C", "B")]

        with patch.object(source_dinamica.pyodbc, "connect",
                          side_effect=_fake_pyodbc_with_rows(rows_por_query=rows)):
            result = source_dinamica.obtener("123")
            self.assertEqual(result, "02")
            self.assertEqual(len(calls), 2)

    def test_fallback_a_segunda_si_primera_lanza_excepcion(self):
        _fuente(nombre="F1", prioridad=10)
        _fuente(nombre="F2", prioridad=20)

        # Conexión 1 lanza, conexión 2 devuelve filas.
        intentos = {"n": 0}

        def fake_connect(*args, **kwargs):
            intentos["n"] += 1
            if intentos["n"] == 1:
                raise pyodbc.OperationalError("simulated")
            return _fake_pyodbc_with_rows(rows_por_query=lambda q: [("C", "C")])()

        with patch.object(source_dinamica.pyodbc, "connect", side_effect=fake_connect):
            # source_dinamica reintenta una vez al detectar pyodbc.Error
            # (lo hace dentro de _ejecutar), por eso connect se llama más veces.
            result = source_dinamica.obtener("123")
            self.assertEqual(result, "01")

    def test_si_todas_fallan_propaga_primera_excepcion(self):
        _fuente(nombre="F1", prioridad=10)
        _fuente(nombre="F2", prioridad=20)

        with patch.object(source_dinamica.pyodbc, "connect",
                          side_effect=ValueError("boom")):
            with self.assertRaises(ValueError):
                source_dinamica.obtener("123")


class ObtenerBatchTests(TestCase):

    def setUp(self):
        from home.modules.tipo_usuario import homologacion
        homologacion.invalidar_cache()
        source_dinamica._thread_local.conns = {}
        FuenteTipoUsuario.objects.all().delete()

    def test_batch_vacio(self):
        self.assertEqual(source_dinamica.obtener_batch([]), {})

    def test_batch_resuelve_y_deja_pendientes_para_siguiente_fuente(self):
        _fuente(nombre="F1", prioridad=10)
        _fuente(nombre="F2", prioridad=20)

        def rows(query):
            # F1 resuelve solo '111'; F2 resuelve '222'.
            if "F2" in query or "tabla_f2" in query:
                pass
            if "'111'" in query and "'222'" in query:
                # 1er query (F1, ambos docs) — devuelve solo 111
                return [("111", "C", "COTIZANTE")]
            elif "'222'" in query and "'111'" not in query:
                # 2do query (F2, solo el pendiente)
                return [("222", "C", "BENEFICIARIO")]
            return []

        with patch.object(source_dinamica.pyodbc, "connect",
                          side_effect=_fake_pyodbc_with_rows(rows_por_query=rows)):
            res = source_dinamica.obtener_batch(["111", "222"])
            self.assertEqual(res, {"111": "01", "222": "02"})

    def test_batch_dedupe_y_sanitiza(self):
        _fuente(nombre="F1", prioridad=10)

        def rows(query):
            return [("123", "C", "COTIZANTE")]

        with patch.object(source_dinamica.pyodbc, "connect",
                          side_effect=_fake_pyodbc_with_rows(rows_por_query=rows)):
            # "123" y "1-2-3" se sanitizan al mismo doc "123" → un solo IN.
            res = source_dinamica.obtener_batch(["123", "1-2-3"])
            self.assertIn("123", res)
            self.assertEqual(res["123"], "01")

    def test_batch_propaga_si_todas_fallan_y_nada_resuelto(self):
        _fuente(nombre="F1", prioridad=10)
        _fuente(nombre="F2", prioridad=20)

        with patch.object(source_dinamica.pyodbc, "connect",
                          side_effect=RuntimeError("conexión rota")):
            with self.assertRaises(RuntimeError):
                source_dinamica.obtener_batch(["123"])


class FiltroTipoDocumentoTests(TestCase):
    """`campo_tipo_documento` opcional — si está configurado, filtra por tipo doc."""

    def setUp(self):
        from home.modules.tipo_usuario import homologacion
        homologacion.invalidar_cache()
        source_dinamica._thread_local.conns = {}
        FuenteTipoUsuario.objects.all().delete()

    def test_sin_campo_tipo_doc_no_agrega_and(self):
        """Si la fuente no tiene `campo_tipo_documento` → query legacy (sin AND)."""
        _fuente(nombre="F1", prioridad=10)
        capturado = {}

        def rows(query):
            capturado["q"] = query
            return [("C", "COTIZANTE")]

        with patch.object(source_dinamica.pyodbc, "connect",
                          side_effect=_fake_pyodbc_with_rows(rows_por_query=rows)):
            siesa = source_dinamica.obtener("123", "CC")
            self.assertEqual(siesa, "01")
            self.assertIn("WHERE doc = '123'", capturado["q"])
            self.assertNotIn(" AND ", capturado["q"])

    def test_con_campo_tipo_doc_agrega_and(self):
        f = _fuente(nombre="F1", prioridad=10)
        f.campo_tipo_documento = "doc_tipo"
        f.save()
        capturado = {}

        def rows(query):
            capturado["q"] = query
            return [("C", "COTIZANTE")]

        with patch.object(source_dinamica.pyodbc, "connect",
                          side_effect=_fake_pyodbc_with_rows(rows_por_query=rows)):
            siesa = source_dinamica.obtener("123", "CC")
            self.assertEqual(siesa, "01")
            self.assertIn("WHERE doc = '123' AND doc_tipo = 'CC'", capturado["q"])

    def test_con_campo_tipo_doc_pero_caller_no_pasa_tipo(self):
        """Si la fuente tiene `campo_tipo_documento` pero no se pasa tipo → no filtra."""
        f = _fuente(nombre="F1", prioridad=10)
        f.campo_tipo_documento = "doc_tipo"
        f.save()
        capturado = {}

        def rows(query):
            capturado["q"] = query
            return [("C", "COTIZANTE")]

        with patch.object(source_dinamica.pyodbc, "connect",
                          side_effect=_fake_pyodbc_with_rows(rows_por_query=rows)):
            source_dinamica.obtener("123")
            self.assertNotIn(" AND ", capturado["q"])

    def test_tipo_documento_sanitizado(self):
        """Caracteres no alfanuméricos en tipo_documento se eliminan."""
        f = _fuente(nombre="F1", prioridad=10)
        f.campo_tipo_documento = "doc_tipo"
        f.save()
        capturado = {}

        def rows(query):
            capturado["q"] = query
            return [("C", "COTIZANTE")]

        with patch.object(source_dinamica.pyodbc, "connect",
                          side_effect=_fake_pyodbc_with_rows(rows_por_query=rows)):
            source_dinamica.obtener("123", "C'C--; DROP")
            self.assertIn("doc_tipo = 'CCDROP'", capturado["q"])

    def test_campo_tipo_documento_invalido_lanza(self):
        f = _fuente(nombre="F1", prioridad=10)
        f.campo_tipo_documento = "td; DROP TABLE x"
        f.save()
        with self.assertRaises(ValueError):
            source_dinamica._validar_identificadores(f)

    def test_batch_agrupa_por_tipo_doc(self):
        f = _fuente(nombre="F1", prioridad=10)
        f.campo_tipo_documento = "doc_tipo"
        f.save()
        queries = []

        def rows(query):
            queries.append(query)
            if "CC" in query:
                return [("111", "C", "COTIZANTE")]
            if "TI" in query:
                return [("222", "C", "BENEFICIARIO")]
            return []

        with patch.object(source_dinamica.pyodbc, "connect",
                          side_effect=_fake_pyodbc_with_rows(rows_por_query=rows)):
            res = source_dinamica.obtener_batch(
                [("111", "CC"), ("222", "TI")]
            )
            self.assertEqual(res, {("111", "CC"): "01", ("222", "TI"): "02"})
            # Una query por grupo de tipo_doc
            self.assertEqual(len(queries), 2)


class PoolVersionadoTests(TestCase):
    """Si `fuente.updated_at` cambia, la conexión cacheada se descarta."""

    def setUp(self):
        source_dinamica._thread_local.conns = {}
        FuenteTipoUsuario.objects.all().delete()

    def test_pool_reabre_si_updated_at_cambia(self):
        f = _fuente(nombre="F1", prioridad=10)

        def rows(query):
            return [("C", "COTIZANTE")]

        with patch.object(source_dinamica.pyodbc, "connect",
                          side_effect=_fake_pyodbc_with_rows(rows_por_query=rows)) as mock_connect:
            source_dinamica.obtener("123")
            self.assertEqual(mock_connect.call_count, 1)

            # Misma fuente → misma conexión cacheada (no reabre)
            source_dinamica.obtener("456")
            self.assertEqual(mock_connect.call_count, 1)

            # Cambia updated_at → el pool detecta versión vieja y reabre
            f.refresh_from_db()
            f.descripcion = "cambiada"
            f.save()
            source_dinamica.obtener("789")
            self.assertEqual(mock_connect.call_count, 2)
