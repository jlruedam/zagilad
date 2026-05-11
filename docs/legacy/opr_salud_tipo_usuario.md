# Fuente histórica OPR_SALUD para `tipo_usuario` (archivada)

> Esta fuente **ya no está activa**. Se conservaba como fallback del paquete
> `home.modules.tipo_usuario` cuando la fuente primaria era OPR_SALUD. El
> stack actual usa únicamente:
>
> 1. `MUTUALSER.dbo.DL_MS_AFILIADO_VIEW_CLEAN` (BD MUTUALSER, vista limpia)
> 2. API MUTUAL `validateRights` (FHIR Bundle)
>
> Si en el futuro se reincorpora OPR_SALUD, este documento contiene todo lo
> necesario para reactivarlo: conexión, tabla, query, código y comando de
> diagnóstico.

## Contexto

OPR_SALUD era originalmente la fuente primaria de homologación SIESA del
proyecto. La consulta llegaba al data lake (`SERVER_LAKE`) vía SQL Server, que
a su vez tenía un *linked server* llamado `OPR_SALUD` apuntando a la base
Oracle de OASIS. Por eso todas las queries usaban `OPENQUERY(OPR_SALUD, '...')`.

## Conexión

- Variables `.env`: `SERVER_LAKE`, `USERNAME_SERVER_LAKE`, `PASSWORD_SERVER_LAKE`
  (las mismas que usa hoy MUTUALSER — el linked server vive en el mismo SQL
  Server).
- Conector: `home.modules.conexionBD.conexionBD(query)`.
- Sin parámetros bindeados — las queries arman el SQL por interpolación
  (sanitizar el documento antes).

## Tabla origen

`OASIS.T_AFILIADO_MUTUALSER_EP` accedida exclusivamente vía OPENQUERY.

Columnas usadas:

| Columna                  | Uso                                                  |
|--------------------------|------------------------------------------------------|
| `NRO_TIPO_IDENTIFICACION`| Documento del afiliado (match exacto).               |
| `AFIC_REGIMEN`           | `'C'` Contributivo / `'S'` Subsidiado.               |
| `TIPO_AFILIADO`          | Texto largo (`'BENEFICIARIO'`, `'COTIZANTE'`, etc.). |
| `CODIGO_BDUA`            | Existía pero no se usaba en el flujo activo.         |

## Particularidades del SQL

- **OPENQUERY tiene un límite cercano a 8000 bytes** en la cadena interna
  pasada al linked server. El batch real estaba acotado a 200 documentos por
  chunk para no exceder ese límite.
- Las comillas simples se escapan duplicándolas (`''` dentro del literal).
- Existe un **typo histórico** en la fuente: aparece `'CABEZA DE FAMLIA'`
  (sin la `I`). La tabla de homologación SIESA (`homologacion.py`) lo
  reconoce explícitamente; cualquier reactivación debe mantenerlo.
- La homologación SIESA (régimen × tipo → `'01'/'02'/'03'/'04'`) ya estaba
  desacoplada en `home/modules/tipo_usuario/homologacion.py` y se sigue
  reutilizando tal cual con el resto de fuentes — no requiere cambios al
  reactivar OPR_SALUD.

## Código archivado

### `home/modules/tipo_usuario/source_sql.py`

```python
"""
Source SQL: consulta tipo de usuario en OPR_SALUD vía OPENQUERY.

Trae los valores crudos (regimen + tipo_afiliado) y delega la homologación
a `homologacion.py` para mantener una única tabla de reglas SIESA.
"""

from home.modules import conexionBD
from home.modules.tipo_usuario.homologacion import homologar_siesa, normalizar_tipo_afiliado

# Tamaño máximo de chunk para OPENQUERY (límite ~8000 bytes de SQL interno).
_BATCH_SIZE = 200


def obtener(documento) -> str:
    """
    Consulta un solo documento. Devuelve el código SIESA o `''` si no se
    encontró en OPR_SALUD o si el régimen/tipo no homologa.
    """
    query = f"""
        SELECT * FROM OPENQUERY(OPR_SALUD, '
        SELECT NRO_TIPO_IDENTIFICACION, AFIC_REGIMEN, TIPO_AFILIADO, CODIGO_BDUA
        FROM OASIS.T_AFILIADO_MUTUALSER_EP
        WHERE NRO_TIPO_IDENTIFICACION = ''{documento}''
        ')
        """
    rows = conexionBD.conexionBD(query) or []
    if not rows:
        return ""
    _doc, regimen, tipo_afiliado, *_ = list(rows[0]) + [None] * 4
    return homologar_siesa(regimen, normalizar_tipo_afiliado(tipo_afiliado))


def obtener_batch(documentos: list) -> dict:
    """
    Consulta múltiples documentos en lotes. Devuelve `{str(documento): codigo_siesa}`.
    Documentos no encontrados o sin homologación válida no aparecen en el dict.
    """
    if not documentos:
        return {}

    resultado: dict = {}

    for i in range(0, len(documentos), _BATCH_SIZE):
        chunk = documentos[i: i + _BATCH_SIZE]
        docs_in = ", ".join(f"''{str(doc)}''" for doc in chunk)

        query = f"""
            SELECT * FROM OPENQUERY(OPR_SALUD, '
            SELECT NRO_TIPO_IDENTIFICACION, AFIC_REGIMEN, TIPO_AFILIADO
            FROM OASIS.T_AFILIADO_MUTUALSER_EP
            WHERE NRO_TIPO_IDENTIFICACION IN ({docs_in})
            ')
            """

        rows = conexionBD.conexionBD(query) or []
        for row in rows:
            doc, regimen, tipo_afiliado, *_ = list(row) + [None] * 3
            siesa = homologar_siesa(regimen, normalizar_tipo_afiliado(tipo_afiliado))
            if siesa:
                resultado[str(doc)] = siesa

    return resultado
```

### Wrappers legacy en `home/modules/utils.py`

```python
from home.modules.tipo_usuario import source_sql

# Mantenido para compatibilidad con consumidores externos (ej: diag command).
_BATCH_SIZE_TIPO_USUARIO = source_sql._BATCH_SIZE


def obtener_tipo_usuario(documento):
    """
    Wrapper legacy: consulta SQL únicamente y devuelve un DataFrame
    con una sola columna (código SIESA) o vacío si no se encontró.
    """
    import pandas as pd
    siesa = source_sql.obtener(documento)
    if siesa:
        return pd.DataFrame([[siesa]])
    return pd.DataFrame()


def obtener_tipo_usuario_batch(documentos: list) -> dict:
    """
    Wrapper legacy: consulta SQL en batch. Devuelve `{str(doc): siesa}`.
    """
    return source_sql.obtener_batch(documentos)
```

### Comando de diagnóstico `home/management/commands/diag_tipo_usuario.py`

Se usaba con `python manage.py diag_tipo_usuario 1003562012 [docs...]`. Corría
9 TESTs contra OPR_SALUD para aislar fallas: query single, query batch,
SQL crudo con `IN`, SQL crudo con `=`, tamaño del SQL del batch real (con
CASE completo), columnas de la tabla, 3 filas de muestra, búsqueda LIKE,
COUNT(\*) total.

> El código completo del comando está versionado en git: para recuperarlo
> ver `home/management/commands/diag_tipo_usuario.py` en el commit que
> archivó esta fuente (`git log -- home/management/commands/diag_tipo_usuario.py`).

## Cómo reactivar OPR_SALUD

Si OPR_SALUD vuelve a estar disponible y se decide reincorporarlo:

1. Restaurar `home/modules/tipo_usuario/source_sql.py` desde este documento o
   desde git.
2. En `home/modules/tipo_usuario/__init__.py`:
   - `from home.modules.tipo_usuario import source_sql`
   - Agregar la rama OPR_SALUD en `obtener_tipo_usuario` y `obtener_tipo_usuario_batch`
     (la posición dependerá de la prioridad deseada — fallback final, primaria, etc).
3. Restaurar (opcional) los wrappers en `home/modules/utils.py` si se quiere
   volver a usar el comando de diagnóstico.
4. Restaurar (opcional) `home/management/commands/diag_tipo_usuario.py` desde git.
5. Actualizar el mensaje de inconsistencia en `home/modules/task.py` y
   `home/modules/revalidador.py` para nombrar las 3 fuentes.

## Por qué se archivó

OPR_SALUD presentaba inestabilidad intermitente — caídas del linked server y
errores de tipo `pyodbc.Error` que obligaban a depender del fallback API
MUTUAL en buena parte de las cargas. Cuando se sumó `MUTUALSER.dbo.DL_MS_AFILIADO_VIEW_CLEAN`
(misma información, BD local del data lake, sin OPENQUERY) la consulta
OPR_SALUD pasó a ser redundante y se removió del flujo activo para reducir
puntos de falla.
