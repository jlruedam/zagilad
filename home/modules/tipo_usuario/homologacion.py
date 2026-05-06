"""
Homologación de tipo de afiliado MUTUAL SER → código SIESA.

Fuente única de reglas para los dos paths (SQL OPR_SALUD y API MUTUAL).
Antes vivían embebidas en el CASE del SQL en utils.py — ahora se aplican en
Python después de extraer los valores crudos.

Reglas (tomadas de homologacion_tipoAfiliado_siesa.xlsx):

    Régimen S (Subsidiado)   × *  (cualquier tipo)        → 04
    Régimen C (Contributivo) × C  (Cotizante)             → 01
    Régimen C (Contributivo) × ND                         → 01
    Régimen C (Contributivo) × SC (Segundo Cotizante)     → 01
    Régimen C (Contributivo) × F  (Cabeza de Familia)     → 01
    Régimen C (Contributivo) × B  (Beneficiario)          → 02
    Régimen C (Contributivo) × A  (Adicional)             → 03
"""

# Reglas SIESA: {regimen: {tipo_afiliado_corto: codigo_siesa}}
SIESA_RULES: dict = {
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

# Mapeo de nombres largos (formato OPR_SALUD) → códigos cortos (formato API).
# Incluye el typo histórico "FAMLIA" presente en OPR_SALUD para no perder filas.
SQL_TIPO_AFILIADO_TO_CODIGO: dict = {
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


def normalizar_tipo_afiliado(tipo_raw) -> str:
    """Normaliza un tipo de afiliado crudo de OPR_SALUD a código corto."""
    if not tipo_raw:
        return ""
    s = str(tipo_raw).strip()
    if s in SQL_TIPO_AFILIADO_TO_CODIGO:
        return SQL_TIPO_AFILIADO_TO_CODIGO[s]
    return s.upper()


def homologar_siesa(regimen, tipo_afiliado_codigo) -> str:
    """
    Devuelve el código SIESA (`'01'/'02'/'03'/'04'`) o `''` si no hay match.

    `regimen`: 'C' o 'S' (puede venir crudo del API o SQL).
    `tipo_afiliado_codigo`: código corto ya normalizado ('C', 'B', 'F', 'SC', 'A', 'ND', ...).
    """
    reg = (regimen or "").strip().upper()
    aff = (tipo_afiliado_codigo or "").strip().upper()
    if reg in SIESA_RULES:
        if aff in SIESA_RULES[reg]:
            return SIESA_RULES[reg][aff]
        if "*" in SIESA_RULES[reg]:
            return SIESA_RULES[reg]["*"]
    return ""
