"""
Signals para invalidación de cachés del módulo `tipo_usuario`.

Cuando el admin edita una regla SIESA, una normalización o una fuente, los
caches en memoria del proceso quedan desincronizados con la DB. Estos signals
los limpian inmediatamente en el proceso que ejecutó el cambio. Otros workers
(Django Q) ven el cambio a más tardar tras el TTL de cache (60s) en
`homologacion._CACHE_TTL_SEC`.
"""

import logging

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from home.models import (
    FuenteTipoUsuario,
    NormalizacionTipoAfiliado,
    ReglaHomologacionSIESA,
)


logger = logging.getLogger(__name__)


@receiver([post_save, post_delete], sender=ReglaHomologacionSIESA)
@receiver([post_save, post_delete], sender=NormalizacionTipoAfiliado)
def _invalidar_cache_homologacion(sender, instance, **kwargs):
    """Reglas o normalizaciones cambiadas → recarga inmediata en próximo lookup."""
    from home.modules.tipo_usuario.homologacion import invalidar_cache
    invalidar_cache()
    logger.debug(
        "Cache de homologación invalidado por cambio en %s (id=%s)",
        sender.__name__, getattr(instance, "id", "?"),
    )


@receiver([post_save, post_delete], sender=FuenteTipoUsuario)
def _invalidar_conexion_fuente(sender, instance, **kwargs):
    """Fuente editada/borrada → cerrar la conexión cacheada (puede tener
    credenciales viejas).

    Best-effort: solo afecta al proceso que ejecutó el cambio. Otros workers
    detectan el cambio en su próxima consulta porque el pool versiona por
    `fuente.updated_at`.
    """
    from home.modules.tipo_usuario.source_dinamica import invalidar_conexion
    if getattr(instance, "id", None) is not None:
        invalidar_conexion(instance.id)
