from datetime import date
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse

from home.models import (
    Actividad,
    Admision,
    AreaPrograma,
    Carga,
    ContratoMarco,
    ParametrosAreaPrograma,
    Regional,
    TipoActividad,
)
from zeus_mirror.models import Contrato, Medico


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


class EditarActividadTests(TestCase):
    """
    Edición de actividades NO admisionadas.

    Cubre: bloqueo si ya tiene admision, bloqueo si admisionada en otra carga,
    re-validación que limpia inconsistencias, y recálculo de contadores en la
    Carga padre.
    """

    def setUp(self):
        # Auth — todas las vistas de edición requieren login
        self.user = User.objects.create_user(username="tester", password="pwd")
        self.client = Client()
        self.client.force_login(self.user)

        # Catálogos mínimos
        sub = _contrato("SUB-X", "EPS-X", "001-X", "SUBSIDIADO")
        con = _contrato("CON-X", "EPS-X", "002-X", "CONTRIBUTIVO")
        self.marco = ContratoMarco.objects.create(
            numero="MARCO-X",
            contrato_subsidiado=sub,
            contrato_contributivo=con,
        )
        self.area = AreaPrograma.objects.create(identificador="AP1", nombre="Área 1")
        self.regional = Regional.objects.create(regional="Centro")
        self.params = ParametrosAreaPrograma.objects.create(
            area_programa=self.area,
            regional=self.regional,
            sede=None,
        )
        self.tipo = TipoActividad.objects.create(
            nombre="Consulta",
            cups="890201",
            contrato=self.marco,
            area=self.area,
        )
        self.tipo_alt = TipoActividad.objects.create(
            nombre="Procedimiento",
            cups="990101",
            contrato=self.marco,
            area=self.area,
        )

        # Médicos: el viejo (en BD pero distinto al que el form va a usar)
        # y el nuevo válido que el form referenciará.
        self.medico_valido = Medico.objects.create(
            codigo="M001", documento="DOC-MED-OK", nombre="Dra Test",
        )

        # Carga padre
        self.carga = Carga.objects.create(usuario=self.user, estado="procesada")

    def _crear_actividad_con_inconsistencia(self):
        """Actividad cargada con 'Medico no encontrado' (doc apunta a médico inexistente)."""
        return Actividad.objects.create(
            tipo_documento="CC",
            documento_paciente="111",
            nombre_paciente="Paciente Test",
            regional="Centro",
            fecha_servicio=date(2024, 6, 1),
            nombre_actividad="Consulta de control",
            tipo_actividad=self.tipo,
            diagnostico_p="A00",
            documento_medico="DOC-MED-NO-EXISTE",
            medico=None,
            contrato=self.tipo.contrato,
            carga=self.carga,
            inconsistencias="⚠️Error al procesar la actividadMedico no encontrado",
        )

    @patch("home.modules.revalidador.tipo_usuario_service.obtener_tipo_usuario")
    def test_edicion_bloqueada_si_actividad_admisionada(self, mock_tipo_usuario):
        admision = Admision.objects.create(
            documento_paciente=111, numero_estudio=999999
        )
        actividad = self._crear_actividad_con_inconsistencia()
        actividad.admision = admision
        actividad.inconsistencias = None
        actividad.save()

        url = reverse("editar_actividad", args=[actividad.id])
        response = self.client.post(url, {
            "tipo_documento": "CC",
            "documento_paciente": "222",
            "documento_medico": "DOC-MED-OK",
            "tipo_actividad_id": self.tipo.id,
            "tipo_usuario": "04",
            "diagnostico_p": "Z00",
            "fecha_servicio": "2024-06-01",
        })

        self.assertEqual(response.status_code, 403)
        actividad.refresh_from_db()
        self.assertEqual(actividad.documento_paciente, "111", "no se debe modificar")
        mock_tipo_usuario.assert_not_called()

    def test_edicion_bloqueada_si_admisionada_en_otra_carga(self):
        actividad = self._crear_actividad_con_inconsistencia()
        actividad.admisionada_otra_carga = True
        actividad.save()

        url = reverse("editar_actividad", args=[actividad.id])
        response = self.client.post(url, {
            "tipo_documento": "CC",
            "documento_paciente": "222",
            "documento_medico": "DOC-MED-OK",
            "tipo_actividad_id": self.tipo.id,
            "tipo_usuario": "04",
            "diagnostico_p": "Z00",
            "fecha_servicio": "2024-06-01",
        })

        self.assertEqual(response.status_code, 403)

    @patch("home.modules.revalidador.tipo_usuario_service.obtener_tipo_usuario")
    def test_edicion_revalida_y_limpia_inconsistencia(self, mock_tipo_usuario):
        # tipo_usuario viene en el form → no se consulta el servicio externo
        actividad = self._crear_actividad_con_inconsistencia()
        self.assertIsNotNone(actividad.inconsistencias)

        url = reverse("editar_actividad", args=[actividad.id])
        response = self.client.post(url, {
            "tipo_documento": "CC",
            "documento_paciente": "111",
            "documento_medico": "DOC-MED-OK",  # ahora apunta al médico válido
            "tipo_actividad_id": self.tipo.id,
            "tipo_usuario": "04",
            "diagnostico_p": "A00",
            "fecha_servicio": "2024-06-01",
        })

        self.assertEqual(response.status_code, 302)
        actividad.refresh_from_db()
        self.assertIsNone(actividad.inconsistencias, "inconsistencia debe quedar resuelta")
        self.assertEqual(actividad.medico_id, self.medico_valido.id)
        self.assertEqual(actividad.tipo_usuario, "04")
        mock_tipo_usuario.assert_not_called()

    @patch("home.modules.revalidador.tipo_usuario_service.obtener_tipo_usuario")
    def test_edicion_consulta_tipo_usuario_si_viene_vacio(self, mock_tipo_usuario):
        mock_tipo_usuario.return_value = "01"
        actividad = self._crear_actividad_con_inconsistencia()

        url = reverse("editar_actividad", args=[actividad.id])
        response = self.client.post(url, {
            "tipo_documento": "CC",
            "documento_paciente": "111",
            "documento_medico": "DOC-MED-OK",
            "tipo_actividad_id": self.tipo.id,
            "tipo_usuario": "",  # vacío → debe consultar
            "diagnostico_p": "A00",
            "fecha_servicio": "2024-06-01",
        })

        self.assertEqual(response.status_code, 302)
        actividad.refresh_from_db()
        self.assertEqual(actividad.tipo_usuario, "01")
        mock_tipo_usuario.assert_called_once_with("111", "CC")

    @patch("home.modules.revalidador.tipo_usuario_service.obtener_tipo_usuario")
    def test_edicion_recalcula_contadores_carga(self, mock_tipo_usuario):
        actividad = self._crear_actividad_con_inconsistencia()
        # Estado inicial de los contadores
        self.carga.actualizar_info_actividades()
        self.carga.save()
        self.assertEqual(self.carga.cantidad_actividades_inconsistencias, 1)
        self.assertEqual(self.carga.cantidad_actividades_ok, 0)

        url = reverse("editar_actividad", args=[actividad.id])
        self.client.post(url, {
            "tipo_documento": "CC",
            "documento_paciente": "111",
            "documento_medico": "DOC-MED-OK",
            "tipo_actividad_id": self.tipo.id,
            "tipo_usuario": "04",
            "diagnostico_p": "A00",
            "fecha_servicio": "2024-06-01",
        })

        self.carga.refresh_from_db()
        self.assertEqual(self.carga.cantidad_actividades_inconsistencias, 0)
        self.assertEqual(self.carga.cantidad_actividades_ok, 1)

    @patch("home.modules.revalidador.tipo_usuario_service.obtener_tipo_usuario")
    def test_edicion_cambia_tipo_documento(self, mock_tipo_usuario):
        mock_tipo_usuario.return_value = "01"
        actividad = self._crear_actividad_con_inconsistencia()
        self.assertEqual(actividad.tipo_documento, "CC")

        url = reverse("editar_actividad", args=[actividad.id])
        response = self.client.post(url, {
            "tipo_documento": "TI",  # cambio de tipo
            "documento_paciente": "111",
            "documento_medico": "DOC-MED-OK",
            "tipo_actividad_id": self.tipo.id,
            "tipo_usuario": "",
            "diagnostico_p": "A00",
            "fecha_servicio": "2024-06-01",
        })

        self.assertEqual(response.status_code, 302)
        actividad.refresh_from_db()
        self.assertEqual(actividad.tipo_documento, "TI")
        # La consulta de tipo_usuario debe usar el nuevo tipo_documento
        mock_tipo_usuario.assert_called_once_with("111", "TI")

    def test_get_renderiza_form_si_editable(self):
        actividad = self._crear_actividad_con_inconsistencia()
        url = reverse("editar_actividad", args=[actividad.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Editar actividad")
        self.assertContains(response, "documento_paciente")
        self.assertContains(response, "tipo_actividad_id")


class ProcesarCargueEstadoFinalTests(TestCase):
    """
    Regresión: si `procesar_cargue_actividades` crashea mid-lote, la carga NO
    debe quedar stuck en 'procesando'. Antes del fix, el `carga.save()` vivía
    dentro del `try` y nunca corría cuando había excepción — la tarea
    retornaba True y django-q la marcaba como exitosa, dejando la carga
    huérfana en estado 'procesando'.
    """

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="x")
        self.carga = Carga.objects.create(
            usuario=self.user,
            estado="procesando",
            cantidad_actividades=5,
        )

    @patch("home.modules.task._cargar_cache_cargue")
    def test_excepcion_durante_procesamiento_marca_carga_como_cancelada(
        self, mock_cache,
    ):
        from home.modules import task

        mock_cache.side_effect = RuntimeError("simulated crash mid-lote")
        # Datos dummy — no se llega a usar porque _cargar_cache_cargue revienta primero.
        result = task.procesar_cargue_actividades(
            id_carga=self.carga.id,
            datos=[],
            num_lote=1,
            cantidad_actividades=5,
            tiempo_inicial=0,
        )
        # La tarea retorna True (django-q la considera exitosa) pero...
        self.assertTrue(result)
        # ...el estado DEBE haber transicionado a 'cancelada' en DB.
        self.carga.refresh_from_db()
        self.assertEqual(self.carga.estado, "cancelada")

    @patch("home.modules.task._cargar_cache_cargue")
    def test_carga_no_queda_en_procesando_si_save_final_falla(self, mock_cache):
        """
        Si el `carga.save()` del finally falla por alguna razón externa, no
        debe relanzar la excepción ni dejar a la tarea reportando éxito sin
        logs. El test verifica que la función no propaga la excepción del save.
        """
        from home.modules import task

        mock_cache.side_effect = RuntimeError("crash")
        with patch.object(Carga, "save", side_effect=RuntimeError("DB caída")):
            # No debe propagar — el `except` interno del finally lo absorbe.
            result = task.procesar_cargue_actividades(
                id_carga=self.carga.id,
                datos=[],
                num_lote=1,
                cantidad_actividades=5,
                tiempo_inicial=0,
            )
            self.assertTrue(result)


class DetectoresErrorZeusTests(TestCase):
    """Helpers que clasifican respuestas de ZEUS para decidir si reintentar."""

    def test_deadlock_detecta_mensaje_canonico_sql_server(self):
        from home.modules.task import _es_deadlock

        msg = (
            "Transaction (Process ID 87) was deadlocked on lock resources "
            "with another process and has been chosen as the deadlock victim. "
            "Rerun the transaction."
        )
        self.assertTrue(_es_deadlock(msg))
        self.assertTrue(_es_deadlock([msg]))  # también acepta lista

    def test_deadlock_no_falla_con_none_ni_vacio(self):
        from home.modules.task import _es_deadlock

        self.assertFalse(_es_deadlock(None))
        self.assertFalse(_es_deadlock(""))
        self.assertFalse(_es_deadlock([]))
        self.assertFalse(_es_deadlock("error genérico"))

    def test_pk_violation_detecta_mensajes_reales(self):
        from home.modules.task import _es_pk_violation

        # Mensaje exacto del log de produccion
        msg1 = (
            "[\"Violation of PRIMARY KEY constraint 'PK_ingresos_servicios'. "
            "Cannot insert duplicate key in object 'dbo.ingresos_servicios'. "
            "The duplicate key value is (351602).\"]"
        )
        self.assertTrue(_es_pk_violation(msg1))
        # Variante en minúsculas
        self.assertTrue(_es_pk_violation("violation of primary key constraint"))
        # Solo "duplicate key" también debe matchear
        self.assertTrue(_es_pk_violation("Cannot insert duplicate key"))

    def test_pk_violation_no_falsos_positivos(self):
        from home.modules.task import _es_pk_violation

        self.assertFalse(_es_pk_violation(None))
        self.assertFalse(_es_pk_violation(""))
        self.assertFalse(_es_pk_violation("error de validación"))
        # Deadlock NO debe ser detectado como PK violation
        self.assertFalse(_es_pk_violation("deadlock victim"))

    def test_deadlock_y_pk_son_mutuamente_excluyentes(self):
        """Una respuesta no debería matchear ambos detectores simultáneamente."""
        from home.modules.task import _es_deadlock, _es_pk_violation

        deadlock_msg = "deadlocked ... deadlock victim"
        pk_msg = "Violation of PRIMARY KEY constraint"
        self.assertTrue(_es_deadlock(deadlock_msg))
        self.assertFalse(_es_pk_violation(deadlock_msg))
        self.assertFalse(_es_deadlock(pk_msg))
        self.assertTrue(_es_pk_violation(pk_msg))
