"""
Tests de la carga masiva de tipos de actividad.

Cubre:
  - Auth requerido (302 a login)
  - Descarga de plantilla (200 + content-type xlsx)
  - Subida happy path: crea las filas válidas
  - Encabezados incorrectos -> 400
  - Resolución de FKs por valor legible (contrato=numero, tipo_servicio=id_zeus,
    area=nombre/identificador) y reporte de errores por fila
  - "Crear siempre": CUPS duplicado se inserta igual
  - Área ambigua por nombre -> error; resuelta por identificador -> ok
"""

import io
import json

import pandas as pd
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from home.models import AreaPrograma, ContratoMarco, TipoActividad
from home.views import ENCABEZADOS_TIPOS_ACTIVIDAD
from zeus_mirror.models import TipoServicio

XLSX_CT = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _fila(**kwargs):
    """Construye una fila completa con todas las columnas (vacías por defecto)."""
    return {col: kwargs.get(col, "") for col in ENCABEZADOS_TIPOS_ACTIVIDAD}


def _xlsx(filas, columns=None):
    """Genera un .xlsx en memoria como SimpleUploadedFile."""
    columns = columns or ENCABEZADOS_TIPOS_ACTIVIDAD
    df = pd.DataFrame(filas, columns=columns)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    buf.seek(0)
    return SimpleUploadedFile("carga.xlsx", buf.getvalue(), content_type=XLSX_CT)


class CargaMasivaTiposActividadTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="x")
        self.client = Client()
        self.client.force_login(self.user)

        self.contrato = ContratoMarco.objects.create(numero="CM-001")
        self.area = AreaPrograma.objects.create(identificador="A01", nombre="SALUD ORAL")
        self.servicio = TipoServicio.objects.create(
            fuente=1, id_zeus=500, nombre="ODONTOLOGIA", tipo="AMB", tipo_servicio="OD"
        )

        self.url_masivo = reverse("cargar_tipos_actividad_masivo")
        self.url_plantilla = reverse("descargar_plantilla_tipos_actividad")

    # ── auth ──
    def test_requiere_login(self):
        anon = Client()
        resp = anon.get(self.url_plantilla)
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.url)

    # ── plantilla ──
    def test_descarga_plantilla(self):
        resp = self.client.get(self.url_plantilla)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], XLSX_CT)
        self.assertIn("attachment", resp["Content-Disposition"])
        self.assertTrue(resp.content[:2] == b"PK")  # zip/xlsx magic

    # ── happy path ──
    def test_carga_valida_crea_tipos(self):
        archivo = _xlsx([
            _fila(nombre="CONSULTA OD", cups="890201", contrato="CM-001",
                  tipo_servicio="500", area="SALUD ORAL", finalidad="10"),
            _fila(nombre="CONTROL OD", cups="890202", contrato="CM-001",
                  tipo_servicio="500", area="A01"),  # área por identificador
        ])
        resp = self.client.post(self.url_masivo, {"adjunto": archivo})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data["ok"])
        self.assertEqual(data["creados"], 2)
        self.assertEqual(data["errores"], [])
        self.assertEqual(TipoActividad.objects.count(), 2)
        t = TipoActividad.objects.get(cups="890201")
        self.assertEqual(t.contrato_id, self.contrato.id)
        self.assertEqual(t.tipo_servicio_id, self.servicio.id)
        self.assertEqual(t.area_id, self.area.id)

    # ── encabezados ──
    def test_encabezados_invalidos(self):
        archivo = _xlsx([{"nombre": "x", "cups": "1"}], columns=["nombre", "cups"])
        resp = self.client.post(self.url_masivo, {"adjunto": archivo})
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(resp.json()["ok"])

    def test_sin_archivo(self):
        resp = self.client.post(self.url_masivo, {})
        self.assertEqual(resp.status_code, 400)

    # ── errores por fila ──
    def test_reporta_errores_y_crea_validas(self):
        archivo = _xlsx([
            _fila(nombre="OK", cups="1", contrato="CM-001", tipo_servicio="500", area="A01"),
            _fila(nombre="", cups="2", contrato="CM-001", tipo_servicio="500", area="A01"),       # falta nombre
            _fila(nombre="X", cups="3", contrato="NO-EXISTE", tipo_servicio="500", area="A01"),    # contrato malo
            _fila(nombre="X", cups="4", contrato="CM-001", tipo_servicio="999", area="A01"),       # servicio malo
            _fila(nombre="X", cups="5", contrato="CM-001", tipo_servicio="500", area="ZZZ"),       # area mala
        ])
        resp = self.client.post(self.url_masivo, {"adjunto": archivo})
        data = resp.json()
        self.assertEqual(data["creados"], 1)
        self.assertEqual(len(data["errores"]), 4)
        # filas del Excel: la 1 son encabezados, datos empiezan en 2
        filas_error = {e["fila"] for e in data["errores"]}
        self.assertEqual(filas_error, {3, 4, 5, 6})
        self.assertEqual(TipoActividad.objects.count(), 1)

    # ── crear siempre (sin dedupe por CUPS) ──
    def test_cups_duplicado_se_crea_igual(self):
        archivo = _xlsx([
            _fila(nombre="A", cups="MISMO", contrato="CM-001", tipo_servicio="500", area="A01"),
            _fila(nombre="B", cups="MISMO", contrato="CM-001", tipo_servicio="500", area="A01"),
        ])
        resp = self.client.post(self.url_masivo, {"adjunto": archivo})
        self.assertEqual(resp.json()["creados"], 2)
        self.assertEqual(TipoActividad.objects.filter(cups="MISMO").count(), 2)

    # ── área ambigua por nombre ──
    def test_area_ambigua_por_nombre(self):
        AreaPrograma.objects.create(identificador="A02", nombre="SALUD ORAL")  # nombre repetido
        archivo = _xlsx([
            _fila(nombre="X", cups="1", contrato="CM-001", tipo_servicio="500", area="SALUD ORAL"),
            _fila(nombre="Y", cups="2", contrato="CM-001", tipo_servicio="500", area="A02"),  # ok por id
        ])
        resp = self.client.post(self.url_masivo, {"adjunto": archivo})
        data = resp.json()
        self.assertEqual(data["creados"], 1)
        self.assertEqual(len(data["errores"]), 1)
        self.assertIn("ambigua", data["errores"][0]["motivo"])

    # ── filas vacías se ignoran ──
    def test_filas_vacias_se_ignoran(self):
        archivo = _xlsx([
            _fila(nombre="A", cups="1", contrato="CM-001", tipo_servicio="500", area="A01"),
            _fila(),  # fila totalmente vacía
        ])
        resp = self.client.post(self.url_masivo, {"adjunto": archivo})
        data = resp.json()
        self.assertEqual(data["creados"], 1)
        self.assertEqual(data["errores"], [])

    # ── nombre no se repite ──
    def test_nombre_existente_en_base(self):
        TipoActividad.objects.create(
            nombre="CONSULTA OD", cups="000", contrato=self.contrato,
            tipo_servicio=self.servicio, area=self.area,
        )
        archivo = _xlsx([
            # mismo nombre (distinta capitalización) -> debe rechazarse
            _fila(nombre="consulta od", cups="1", contrato="CM-001", tipo_servicio="500", area="A01"),
            _fila(nombre="NUEVO", cups="2", contrato="CM-001", tipo_servicio="500", area="A01"),
        ])
        resp = self.client.post(self.url_masivo, {"adjunto": archivo})
        data = resp.json()
        self.assertEqual(data["creados"], 1)
        self.assertEqual(len(data["errores"]), 1)
        self.assertIn("ya existe", data["errores"][0]["motivo"])

    def test_nombre_duplicado_en_archivo(self):
        archivo = _xlsx([
            _fila(nombre="REPETIDO", cups="1", contrato="CM-001", tipo_servicio="500", area="A01"),
            _fila(nombre="repetido", cups="2", contrato="CM-001", tipo_servicio="500", area="A01"),
        ])
        resp = self.client.post(self.url_masivo, {"adjunto": archivo})
        data = resp.json()
        self.assertEqual(data["creados"], 1)
        self.assertEqual(len(data["errores"]), 1)
        self.assertIn("duplicado en el archivo", data["errores"][0]["motivo"])
        self.assertEqual(TipoActividad.objects.filter(nombre__iexact="repetido").count(), 1)

    def test_nombre_normaliza_espacios(self):
        # Espacios internos múltiples y capitalización -> mismo nombre.
        archivo = _xlsx([
            _fila(nombre="CONSULTA  GENERAL", cups="1", contrato="CM-001", tipo_servicio="500", area="A01"),
            _fila(nombre="consulta general", cups="2", contrato="CM-001", tipo_servicio="500", area="A01"),
        ])
        resp = self.client.post(self.url_masivo, {"adjunto": archivo})
        data = resp.json()
        self.assertEqual(data["creados"], 1)
        self.assertEqual(len(data["errores"]), 1)
        self.assertIn("duplicado en el archivo", data["errores"][0]["motivo"])
        # se guarda con los espacios colapsados a uno
        self.assertTrue(TipoActividad.objects.filter(nombre="CONSULTA GENERAL").exists())

    # ── alta individual también valida nombre único ──
    def test_crear_individual_nombre_duplicado(self):
        url = reverse("crear_tipo_actividad")
        payload = {
            "nombre": "UNICO", "cups": "1",
            "contrato_id": self.contrato.id,
            "tipo_servicio_id": self.servicio.id,
            "area_id": self.area.id,
        }
        r1 = self.client.post(url, data=json.dumps(payload), content_type="application/json")
        self.assertTrue(r1.json()["ok"])
        # segundo intento con el mismo nombre -> 400
        r2 = self.client.post(url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(r2.status_code, 400)
        self.assertFalse(r2.json()["ok"])
        self.assertEqual(TipoActividad.objects.filter(nombre__iexact="UNICO").count(), 1)
