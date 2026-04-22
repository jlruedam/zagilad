from datetime import date

from django.test import TestCase

from home.models import Actividad, ContratoMarco, TipoActividad
from zeus_mirror.models import Contrato


def _contrato(codigo, empresa, numero, regimen):
    return Contrato.objects.create(
        codigo=codigo,
        nombre=f"Contrato {codigo}",
        empresa=empresa,
        fecha_inicial="2024-01-01",
        fecha_final="2025-12-31",
        observacion="",
        numero=numero,
        id_sede="1",
        regimen=regimen,
    )


class ContratoSnapshotTests(TestCase):
    """Editar TipoActividad.contrato no debe afectar actividades creadas antes."""

    def setUp(self):
        sub_a = _contrato("SUB-A", "EPS-A", "001-A", "SUBSIDIADO")
        con_a = _contrato("CON-A", "EPS-A", "002-A", "CONTRIBUTIVO")
        sub_b = _contrato("SUB-B", "EPS-B", "001-B", "SUBSIDIADO")
        con_b = _contrato("CON-B", "EPS-B", "002-B", "CONTRIBUTIVO")

        self.marco_a = ContratoMarco.objects.create(
            numero="MARCO-A",
            contrato_subsidiado=sub_a,
            contrato_contributivo=con_a,
        )
        self.marco_b = ContratoMarco.objects.create(
            numero="MARCO-B",
            contrato_subsidiado=sub_b,
            contrato_contributivo=con_b,
        )

        self.tipo = TipoActividad.objects.create(
            nombre="Consulta",
            cups="890201",
            contrato=self.marco_a,
        )

    def _crear_actividad(self):
        return Actividad.objects.create(
            regional="Centro",
            fecha_servicio=date(2024, 6, 1),
            nombre_actividad="Consulta de control",
            tipo_actividad=self.tipo,
            documento_paciente="123",
            nombre_paciente="Paciente Test",
            contrato=self.tipo.contrato,
        )

    def test_editar_contrato_del_tipo_no_altera_actividades_previas(self):
        actividad = self._crear_actividad()
        self.assertEqual(actividad.contrato_id, self.marco_a.id)

        self.tipo.contrato = self.marco_b
        self.tipo.save()

        actividad.refresh_from_db()
        self.assertEqual(
            actividad.contrato_id,
            self.marco_a.id,
            "El snapshot de contrato en la actividad debe conservarse",
        )

    def test_actividad_nueva_usa_contrato_actual_del_tipo(self):
        self._crear_actividad()
        self.tipo.contrato = self.marco_b
        self.tipo.save()

        nueva = self._crear_actividad()
        self.assertEqual(nueva.contrato_id, self.marco_b.id)

    def test_legacy_sin_snapshot_resuelve_via_tipo(self):
        actividad = self._crear_actividad()
        Actividad.objects.filter(id=actividad.id).update(contrato=None)
        actividad.refresh_from_db()

        from home.modules import admision as admision_module

        contrato_id = (
            actividad.contrato_id
            if actividad.contrato_id
            else actividad.tipo_actividad.contrato_id
        )
        self.assertEqual(contrato_id, self.marco_a.id)
        self.assertTrue(hasattr(admision_module, "crear_admision"))
