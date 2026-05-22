"""
Homologación de tipo de afiliado MUTUAL SER → código SIESA.

Fuente única de reglas para todos los paths de consulta (SQL dinámico y
API MUTUAL). A partir de Fase 2 las reglas viven en la DB (modelos
`ReglaHomologacionSIESA` y `NormalizacionTipoAfiliado`) y se editan desde
el admin, con un cache en memoria invalidado por signals.

Estrategia de lookup (prioridad descendente):
    1. Override por fuente en DB         (`fuente_id != NULL`)
    2. Regla global en DB                (`fuente_id IS NULL`)
    3. Fallback en memoria (`DEFAULT_*`) — para el caso de DB vacía o
       inaccesible (entornos de test, primer arranque sin seed).

Las constantes `SIESA_RULES` y `SQL_TIPO_AFILIADO_TO_CODIGO` se conservan
como alias de los defaults para compatibilidad con código que las importe
directamente.

Reglas SIESA (`DEFAULT_SIESA_RULES`):

    Régimen S (Subsidiado)   × *  (cualquier tipo)        → 04
    Régimen C (Contributivo) × C  (Cotizante)             → 01
    Régimen C (Contributivo) × ND                         → 01
    Régimen C (Contributivo) × SC (Segundo Cotizante)     → 01
    Régimen C (Contributivo) × F  (Cabeza de Familia)     → 01
    Régimen C (Contributivo) × B  (Beneficiario)          → 02
    Régimen C (Contributivo) × A  (Adicional)             → 03
"""

import logging
import threading
import time


logger = logging.getLogger(__name__)


# ─── Defaults en memoria (fallback) ───────────────────────────────────────────

DEFAULT_SIESA_RULES: dict = {
    "S": {"*": "04"},
    "C": {
        "C": "01",
        "ND": "01",
        "SC": "01",
        "F": "01",
        "B": "02",
        "A": "03",
    },
}

DEFAULT_SQL_TIPO_AFILIADO_TO_CODIGO: dict = {
    "BENEFICIARIO": "B",
    "COTIZANTE": "C",
    "SEGUNDO COTIZANTE": "SC",
    "CABEZA DE FAMILIA": "F",
    "CABEZA DE FAMLIA": "F",
    "ADICIONAL": "A",
    "ND": "ND",
    "F": "F",
    "f": "F",
    "O": "O",
}

# Aliases de compatibilidad — código que importa estos nombres sigue funcionando.
SIESA_RULES = DEFAULT_SIESA_RULES
SQL_TIPO_AFILIADO_TO_CODIGO = DEFAULT_SQL_TIPO_AFILIADO_TO_CODIGO

# Labels para mostrar al usuario — estáticos, los códigos SIESA son estables.
SIESA_LABELS: dict = {
    "01": "Cotizante",
    "02": "Beneficiario",
    "03": "Adicional",
    "04": "Subsidiado",
}


# ─── Cache thread-safe con TTL + invalidación por signal ──────────────────────

_CACHE_TTL_SEC = 60
_cache_lock = threading.Lock()
_cache_loaded_at: float = 0.0
_cache_reglas: dict | None = None             # {fuente_id_or_None: {regimen: {tipo: siesa}}}
_cache_normalizaciones: dict | None = None    # {fuente_id_or_None: {valor_crudo: codigo}}


def _cargar_desde_db() -> tuple[dict, dict]:
    """Lee reglas + normalizaciones desde la DB. Devuelve dicts vacíos si falla."""
    reglas: dict = {}
    normalizaciones: dict = {}

    try:
        # Import diferido para no romper en imports tempranos (apps loading, etc.)
        from home.models import ReglaHomologacionSIESA, NormalizacionTipoAfiliado

        for fuente_id, regimen, tipo, siesa in (
            ReglaHomologacionSIESA.objects
            .values_list("fuente_id", "regimen", "tipo_afiliado_codigo", "codigo_siesa")
        ):
            bucket = reglas.setdefault(fuente_id, {})
            bucket.setdefault((regimen or "").upper(), {})[(tipo or "").upper()] = siesa

        for fuente_id, valor_crudo, codigo in (
            NormalizacionTipoAfiliado.objects
            .values_list("fuente_id", "valor_crudo", "codigo_normalizado")
        ):
            normalizaciones.setdefault(fuente_id, {})[valor_crudo] = codigo

    except Exception as e:
        # Típicamente: tabla aún no migrada, DB inaccesible en tests, etc.
        logger.warning(
            "homologacion: lectura de DB falló (%s: %s), usando defaults",
            type(e).__name__, e,
        )

    return reglas, normalizaciones


def _get_cache() -> tuple[dict, dict]:
    """Devuelve `(reglas, normalizaciones)` desde cache. Refresca si está expirado."""
    global _cache_loaded_at, _cache_reglas, _cache_normalizaciones

    now = time.time()
    if (
        _cache_reglas is not None
        and _cache_normalizaciones is not None
        and (now - _cache_loaded_at) < _CACHE_TTL_SEC
    ):
        return _cache_reglas, _cache_normalizaciones

    with _cache_lock:
        # Double-checked locking
        now = time.time()
        if (
            _cache_reglas is not None
            and _cache_normalizaciones is not None
            and (now - _cache_loaded_at) < _CACHE_TTL_SEC
        ):
            return _cache_reglas, _cache_normalizaciones

        _cache_reglas, _cache_normalizaciones = _cargar_desde_db()
        _cache_loaded_at = time.time()
        return _cache_reglas, _cache_normalizaciones


def invalidar_cache() -> None:
    """Fuerza recarga en la próxima lectura. Llamado por signals al editar reglas."""
    global _cache_reglas, _cache_normalizaciones, _cache_loaded_at
    with _cache_lock:
        _cache_reglas = None
        _cache_normalizaciones = None
        _cache_loaded_at = 0.0


# ─── API pública ──────────────────────────────────────────────────────────────

def normalizar_tipo_afiliado(tipo_raw, fuente_id: int | None = None) -> str:
    """
    Normaliza un valor crudo de tipo de afiliado a su código corto
    (`'C'`, `'B'`, `'F'`, `'SC'`, `'A'`, `'ND'`, …).

    Orden de búsqueda: override por fuente → global DB → defaults → `.upper()`.
    """
    if not tipo_raw:
        return ""
    s = str(tipo_raw).strip()

    _, normalizaciones = _get_cache()

    # 1. Override por fuente
    if fuente_id is not None and fuente_id in normalizaciones:
        if s in normalizaciones[fuente_id]:
            return normalizaciones[fuente_id][s]

    # 2. Global en DB
    if None in normalizaciones and s in normalizaciones[None]:
        return normalizaciones[None][s]

    # 3. Default hardcoded
    if s in DEFAULT_SQL_TIPO_AFILIADO_TO_CODIGO:
        return DEFAULT_SQL_TIPO_AFILIADO_TO_CODIGO[s]

    # 4. Último recurso: upper. Útil cuando el valor ya viene en código corto.
    return s.upper()


def homologar_siesa(
    regimen,
    tipo_afiliado_codigo,
    fuente_id: int | None = None,
) -> str:
    """
    Devuelve el código SIESA (`'01'`/`'02'`/`'03'`/`'04'`) o `''` si no hay match.

    `regimen`: 'C' o 'S' (puede venir crudo del API o SQL).
    `tipo_afiliado_codigo`: código corto ya normalizado.

    Orden de búsqueda: override por fuente → global DB → defaults.
    """
    reg = (regimen or "").strip().upper()
    aff = (tipo_afiliado_codigo or "").strip().upper()
    if not reg:
        return ""

    reglas, _ = _get_cache()

    # Helper local para buscar en un set de reglas con soporte de wildcard '*'.
    def _lookup(reglas_set: dict) -> str:
        bucket = reglas_set.get(reg)
        if not bucket:
            return ""
        if aff in bucket:
            return bucket[aff]
        if "*" in bucket:
            return bucket["*"]
        return ""

    # 1. Override por fuente
    if fuente_id is not None and fuente_id in reglas:
        siesa = _lookup(reglas[fuente_id])
        if siesa:
            return siesa

    # 2. Global en DB
    if None in reglas:
        siesa = _lookup(reglas[None])
        if siesa:
            return siesa

    # 3. Default hardcoded
    return _lookup(DEFAULT_SIESA_RULES)
