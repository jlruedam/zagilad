"""
Source API: consulta tipo de usuario contra el endpoint validateRights/ de
MUTUAL SER (autenticado vía Keycloak password grant).

Devuelve los valores crudos del Bundle FHIR (affiliateType + healthModality)
y los homologa al código SIESA usando la misma tabla que el path SQL.

Token cacheado en memoria del proceso. Renovación automática en 401.
Reintentos con backoff exponencial en 5xx (transient/saturación de MUTUAL).
"""

import logging
import threading
import time

import requests
from decouple import config

from home.modules.tipo_usuario.homologacion import homologar_siesa

logger = logging.getLogger(__name__)

_TOKEN_URL = config(
    "MUTUAL_KEYCLOAK_URL",
    default="https://rino.mutualser.com/realms/right-validation/protocol/openid-connect/token",
)
_VALIDATE_URL = config(
    "MUTUAL_VALIDATE_URL",
    default="https://guacamayaazul.mutualser.com/validateRights/",
)
_CLIENT_ID = config("MUTUAL_KEYCLOAK_CLIENT", default="right-validation")
_USERNAME = config("MUTUAL_KEYCLOAK_USER", default="")
_PASSWORD = config("MUTUAL_KEYCLOAK_PASS", default="")

_RATE_LIMIT_SLEEP_SEC = 0.15  # cortesía hacia el servicio
_REQUEST_TIMEOUT_SEC = 60
_TOKEN_TIMEOUT_SEC = 30

_MAX_INTENTOS_5XX = 3       # 1 inicial + 2 reintentos
_BACKOFF_BASE_SEC = 1.0     # 1s, 2s, 4s entre reintentos
_BODY_LOG_MAX_CHARS = 2000  # cuánto del body se incluye en logs/excepciones

# Token cacheado por proceso. Si Django Q corre múltiples workers, cada uno
# obtendrá su propio token — aceptable, son baratos.
_token_lock = threading.Lock()
_cached_token: str | None = None


class _TokenInvalido(Exception):
    """401 — token expirado o rechazado por el servidor."""


class _ErrorTransientServidor(Exception):
    """5xx — encapsula la respuesta completa para logging detallado."""

    def __init__(self, status_code: int, body_text: str, body_json):
        self.status_code = status_code
        self.body_text = body_text
        self.body_json = body_json
        super().__init__(f"HTTP {status_code}")


def _credenciales_disponibles() -> bool:
    return bool(_USERNAME and _PASSWORD)


def _obtener_token(forzar: bool = False) -> str:
    global _cached_token
    with _token_lock:
        if _cached_token and not forzar:
            return _cached_token
        if not _credenciales_disponibles():
            raise RuntimeError(
                "Credenciales MUTUAL no configuradas: setear MUTUAL_KEYCLOAK_USER y "
                "MUTUAL_KEYCLOAK_PASS en .env"
            )
        r = requests.post(
            _TOKEN_URL,
            data={
                "grant_type": "password",
                "client_id": _CLIENT_ID,
                "username": _USERNAME,
                "password": _PASSWORD,
            },
            timeout=_TOKEN_TIMEOUT_SEC,
        )
        r.raise_for_status()
        _cached_token = r.json()["access_token"]
        return _cached_token


def _extraer_extension(extensions, key):
    """Busca extensión por su URL y devuelve (code, display) o (string, '')."""
    target = f"mutualSER/hl7/patient/{key}"
    for ext in extensions or []:
        if ext.get("url") == target:
            if "valueCoding" in ext:
                vc = ext["valueCoding"]
                return vc.get("code", ""), vc.get("display", "")
            if "valueString" in ext:
                return ext["valueString"], ""
    return "", ""


def _parsear_respuesta(payload: dict) -> tuple[str, str]:
    """Devuelve (regimen_code, affiliate_type_code) extraídos del Bundle FHIR."""
    entries = payload.get("entry") or []
    if not entries:
        return "", ""
    extensions = entries[0].get("resource", {}).get("extension", [])
    aff_code, _ = _extraer_extension(extensions, "affiliateType")
    reg_code, _ = _extraer_extension(extensions, "healthModality")
    return reg_code, aff_code


def _resumir_operation_outcome(body_json) -> str:
    """Extrae issue.diagnostics / details.text si la respuesta es OperationOutcome FHIR."""
    if not body_json:
        return ""
    try:
        for entry in body_json.get("entry") or []:
            res = entry.get("resource") or {}
            if res.get("resourceType") == "OperationOutcome":
                msgs = []
                for issue in res.get("issue") or []:
                    sev = issue.get("severity", "?")
                    code = issue.get("code", "?")
                    diag = issue.get("diagnostics") or (issue.get("details") or {}).get("text") or ""
                    msgs.append(f"[{sev}/{code}] {diag}".strip())
                if msgs:
                    return " | ".join(msgs)
    except Exception:
        pass
    return ""


def _validar_derechos(token: str, tipo_documento: str, documento: str) -> dict:
    body = {
        "resourceType": "Parameters",
        "id": "CorrelationId",
        "parameter": [
            {"name": "documentType", "valueString": tipo_documento},
            {"name": "documentId", "valueString": str(documento)},
            {"name": "contractValidate", "valueBoolean": False},
        ],
    }
    r = requests.post(
        _VALIDATE_URL,
        json=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        timeout=_REQUEST_TIMEOUT_SEC,
    )
    if r.status_code == 401:
        raise _TokenInvalido()
    if r.status_code >= 500:
        try:
            body_json = r.json()
        except ValueError:
            body_json = None
        raise _ErrorTransientServidor(r.status_code, r.text, body_json)
    try:
        return r.json()
    except ValueError:
        return {}


def _consultar_con_retry(documento: str, tipo_documento: str) -> dict:
    """
    Política de reintentos para una consulta a validateRights/:
      - 401 → refresh de token + retry una vez (sin contar contra el límite)
      - 5xx → backoff 1s/2s/4s, máx _MAX_INTENTOS_5XX intentos. Tras el primer
        5xx se fuerza refresh del token (cubre el caso "token cerca de expirar
        que MUTUAL devuelve como 500 en vez de 401").
    """
    token = _obtener_token()
    ultimo: _ErrorTransientServidor | None = None

    for intento in range(1, _MAX_INTENTOS_5XX + 1):
        try:
            try:
                return _validar_derechos(token, tipo_documento, documento)
            except _TokenInvalido:
                token = _obtener_token(forzar=True)
                return _validar_derechos(token, tipo_documento, documento)
        except _ErrorTransientServidor as e:
            ultimo = e
            if intento == 1:
                # primer 5xx → refrescar token por las dudas (token-near-expiry)
                token = _obtener_token(forzar=True)
            if intento < _MAX_INTENTOS_5XX:
                espera = _BACKOFF_BASE_SEC * (2 ** (intento - 1))
                logger.info(
                    "API MUTUAL %s|%s: HTTP %s intento %s/%s, reintentando en %.1fs",
                    tipo_documento, documento, e.status_code, intento, _MAX_INTENTOS_5XX, espera,
                )
                time.sleep(espera)
                continue
            # último intento agotado → re-raise con detalle del OperationOutcome
            diag = _resumir_operation_outcome(e.body_json)
            cuerpo = (e.body_text or "")[:_BODY_LOG_MAX_CHARS]
            mensaje = f"HTTP {e.status_code} tras {_MAX_INTENTOS_5XX} intentos"
            if diag:
                mensaje += f" | {diag}"
            if cuerpo:
                mensaje += f" | body: {cuerpo}"
            raise RuntimeError(mensaje) from e

    # rama defensiva — no debería alcanzarse
    raise RuntimeError(f"Sin respuesta tras {_MAX_INTENTOS_5XX} intentos") from ultimo


def obtener(documento: str, tipo_documento: str = "CC") -> str:
    """
    Consulta un solo documento por API. Devuelve código SIESA o `''`.
    Levanta excepción si las credenciales no están configuradas, si la
    autenticación falla o si MUTUAL devuelve 5xx tras todos los reintentos.
    """
    payload = _consultar_con_retry(str(documento), tipo_documento)
    regimen, affiliate = _parsear_respuesta(payload)
    return homologar_siesa(regimen, affiliate)


def obtener_batch(docs_tipos: list) -> dict:
    """
    Consulta múltiples (documento, tipo_documento) por API en serie.
    Devuelve `{(str(doc), tipo_doc): codigo_siesa}` solo para los resueltos.

    Si la autenticación falla → levanta excepción (no se intentan los demás).
    Errores por documento individual (incluyendo 5xx tras reintentos) se
    loguean y se omiten del resultado.
    """
    resultado: dict = {}
    if not docs_tipos:
        return resultado

    if not _credenciales_disponibles():
        raise RuntimeError(
            "Credenciales MUTUAL no configuradas: setear MUTUAL_KEYCLOAK_USER y "
            "MUTUAL_KEYCLOAK_PASS en .env"
        )

    # Fail-fast: si no podemos obtener token, no iteramos.
    _obtener_token()

    for i, (documento, tipo_documento) in enumerate(docs_tipos):
        documento_str = str(documento)
        tipo_doc_str = (tipo_documento or "CC").strip().upper() or "CC"
        try:
            payload = _consultar_con_retry(documento_str, tipo_doc_str)
            regimen, affiliate = _parsear_respuesta(payload)
            siesa = homologar_siesa(regimen, affiliate)
            if siesa:
                resultado[(documento_str, tipo_doc_str)] = siesa
        except Exception as e:
            logger.warning(
                "API MUTUAL: error consultando %s|%s: %s: %s",
                tipo_doc_str, documento_str, type(e).__name__, e,
            )

        if i < len(docs_tipos) - 1:
            time.sleep(_RATE_LIMIT_SLEEP_SEC)

    return resultado
