"""
Re-validación de una Actividad existente tras edición manual.

Replica las mismas reglas que `procesar_cargue_actividades` pero para una
sola actividad (no batch). Tras llamar a `revalidar_actividad(actividad)`
el objeto queda con:
  - medico / tipo_actividad / contrato / parametros_programa recalculados
  - tipo_usuario consultado si vino vacío
  - inconsistencias actualizadas (None si todo OK)
  - admisionada_otra_carga marcada si aplica
y persistido en BD.
"""
import logging

from home.models import Actividad, ParametrosAreaPrograma, Regional
from home.modules import tipo_usuario as tipo_usuario_service
from zeus_mirror.models import Medico

logger = logging.getLogger(__name__)


def _validar_duplicado_admisionada(actividad):
    """True si existe OTRA actividad ya admisionada que coincide en la clave."""
    return (
        Actividad.objects.filter(
            regional=actividad.regional,
            fecha_servicio=actividad.fecha_servicio,
            nombre_actividad=actividad.nombre_actividad,
            tipo_actividad=actividad.tipo_actividad,
            diagnostico_p=actividad.diagnostico_p,
            tipo_documento=actividad.tipo_documento,
            documento_paciente=actividad.documento_paciente,
            medico=actividad.medico,
            admision__isnull=False,
        )
        .exclude(id=actividad.id)
        .exists()
    )


def _validar_duplicado_misma_carga(actividad):
    """True si existe OTRA actividad en la misma carga con la misma clave."""
    if not actividad.carga_id:
        return False
    return (
        Actividad.objects.filter(
            carga_id=actividad.carga_id,
            regional=actividad.regional,
            fecha_servicio=actividad.fecha_servicio,
            nombre_actividad=actividad.nombre_actividad,
            tipo_actividad=actividad.tipo_actividad,
            diagnostico_p=actividad.diagnostico_p,
            tipo_documento=actividad.tipo_documento,
            documento_paciente=actividad.documento_paciente,
            medico=actividad.medico,
        )
        .exclude(id=actividad.id)
        .exists()
    )


def revalidar_actividad(actividad):
    """
    Re-corre las validaciones de cargue para `actividad` y persiste el
    resultado. Devuelve la misma instancia ya guardada.

    Reglas en orden:
      1) Médico existe (por documento_medico)
      2) Tipo de actividad asignado
      3) Regional reconocida
      4) Parámetros área/programa existen para (área, regional)
      5) No duplicada vs admisionadas previas (otra carga)
      6) No duplicada en la misma carga
      7) tipo_usuario: si vacío, consultar OPR_SALUD + fallback API MUTUAL
    """
    actividad.inconsistencias = None
    # Reset del flag — si la edición lo limpia, debe poder volver a "OK".
    actividad.admisionada_otra_carga = False

    try:
        # 1. Médico
        doc_medico = (actividad.documento_medico or "").strip()
        if not doc_medico:
            raise Exception("Documento de médico vacío")
        medico = Medico.objects.filter(documento=doc_medico).first()
        if not medico:
            raise Exception("Medico no encontrado")
        actividad.medico = medico

        # 2. Tipo de actividad
        if not actividad.tipo_actividad_id:
            raise Exception("Tipo de actividad no encontrado")

        # 3. Snapshot de contrato desde el tipo
        actividad.contrato = actividad.tipo_actividad.contrato

        # 4. Regional + parámetros área/programa
        regional = Regional.objects.filter(regional=actividad.regional).first()
        if not regional:
            raise Exception("Regional no encontrada")

        params = ParametrosAreaPrograma.objects.filter(
            area_programa=actividad.tipo_actividad.area,
            regional=regional.id,
        ).first()
        if not params:
            raise Exception("Parametros del area/programa no encontrados")
        actividad.parametros_programa = params

        # 5. Duplicado vs admisionadas previas
        if _validar_duplicado_admisionada(actividad):
            actividad.admisionada_otra_carga = True
            raise Exception("Actividad ya fue admisionada")

        # 6. Duplicado en la misma carga
        if _validar_duplicado_misma_carga(actividad):
            raise Exception("Actividad repetida en la misma carga, validar.")

        # 7. tipo_usuario — solo consultar si el usuario no lo fijó manualmente
        if not (actividad.tipo_usuario or "").strip():
            try:
                tipo_usuario_codigo = tipo_usuario_service.obtener_tipo_usuario(
                    actividad.documento_paciente,
                    actividad.tipo_documento,
                )
            except Exception as e:
                raise Exception(f"Error consultando Tipo de Usuario: {e}")

            if tipo_usuario_codigo:
                actividad.tipo_usuario = tipo_usuario_codigo
            else:
                raise Exception(
                    f"Tipo de Usuario: documento {actividad.documento_paciente} "
                    f"no encontrado en OPR_SALUD ni en API MUTUAL"
                )

    except Exception as e:
        actividad.inconsistencias = ("⚠️" + str(e))[:500]
        logger.info(
            "Revalidación actividad %s con inconsistencia: %s",
            actividad.id, actividad.inconsistencias,
        )

    actividad.save()
    return actividad
