"""
Source API: consulta tipo de usuario contra el endpoint validateRights/ de
MUTUAL SER (autenticado vía Keycloak password grant).

Devuelve los valores crudos del Bundle FHIR (affiliateType + healthModality)
y los homologa al código SIESA usando la misma tabla que el path SQL.

Token cacheado en memoria del proceso. Renovación automática en 401.
"""

import logging
import time
import threading

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

# Token cacheado por proceso. Si Celery corre múltiples workers, cada uno
# obtendrá su propio token — aceptable, son baratos.
_token_lock = threading.Lock()
_cached_token: str | None = None


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
        raise PermissionError("Token expirado / inválido")
    if r.status_code >= 500:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")
    try:
        return r.json()
    except ValueError:
        return {}


def obtener(documento: str, tipo_documento: str = "CC") -> str:
    """
    Consulta un solo documento por API. Devuelve código SIESA o `''`.
    Levanta excepción si las credenciales no están configuradas o si la
    autenticación falla.
    """
    token = _obtener_token()
    try:
        payload = _validar_derechos(token, tipo_documento, documento)
    except PermissionError:
        token = _obtener_token(forzar=True)
        payload = _validar_derechos(token, tipo_documento, documento)
    regimen, affiliate = _parsear_respuesta(payload)
    return homologar_siesa(regimen, affiliate)


def obtener_batch(docs_tipos: list) -> dict:
    """
    Consulta múltiples (documento, tipo_documento) por API en serie.
    Devuelve `{(str(doc), tipo_doc): codigo_siesa}` solo para los resueltos.

    Si la autenticación falla → levanta excepción (no se intentan los demás).
    Errores por documento individual se loguean y se omiten del resultado.
    """
    resultado: dict = {}
    if not docs_tipos:
        return resultado

    if not _credenciales_disponibles():
        raise RuntimeError(
            "Credenciales MUTUAL no configuradas: setear MUTUAL_KEYCLOAK_USER y "
            "MUTUAL_KEYCLOAK_PASS en .env"
        )

    token = _obtener_token()

    for i, (documento, tipo_documento) in enumerate(docs_tipos):
        documento_str = str(documento)
        tipo_doc_str = (tipo_documento or "CC").strip().upper() or "CC"
        try:
            try:
                payload = _validar_derechos(token, tipo_doc_str, documento_str)
            except PermissionError:
                token = _obtener_token(forzar=True)
                payload = _validar_derechos(token, tipo_doc_str, documento_str)
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
