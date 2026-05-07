"""
Diagnóstico API MUTUAL validateRights/ — prueba A/B para aislar la causa
de los HTTP 500 intermitentes que aparecen en logs durante la carga.

  MODO A: requests.post() standalone (replica exacta de source_api.py actual)
  MODO B: requests.Session() — propaga cookies recibidas (sticky session)

Detalle completo (headers, bodies) se escribe a un archivo .log y la consola
muestra solo un resumen con status codes por llamada.

Uso:
    python manage.py diag_api_mutual 1007691763
    python manage.py diag_api_mutual 1007691763 --tipo CC --repeat 10
    python manage.py diag_api_mutual 1007691763 --output mi_log.txt
"""
import datetime as dt
import json
import os

import requests
from decouple import config
from django.core.management.base import BaseCommand


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

SEP = "=" * 70


def _payload_validate(tipo, documento):
    return {
        "resourceType": "Parameters",
        "id": "CorrelationId",
        "parameter": [
            {"name": "documentType", "valueString": tipo},
            {"name": "documentId", "valueString": str(documento)},
            {"name": "contractValidate", "valueBoolean": False},
        ],
    }


def _data_token():
    return {
        "grant_type": "password",
        "client_id": _CLIENT_ID,
        "username": _USERNAME,
        "password": _PASSWORD,
    }


def _headers_validate(access_token):
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }


def _resumir_issue(body):
    """Si la respuesta es OperationOutcome (error FHIR), extrae diagnostics/details."""
    try:
        entries = body.get("entry") or []
        for e in entries:
            res = e.get("resource") or {}
            if res.get("resourceType") == "OperationOutcome":
                msgs = []
                for issue in res.get("issue") or []:
                    sev = issue.get("severity", "?")
                    code = issue.get("code", "?")
                    diag = issue.get("diagnostics") or (issue.get("details") or {}).get("text") or ""
                    msgs.append(f"[{sev}/{code}] {diag}")
                if msgs:
                    return " | ".join(msgs)
    except Exception:
        pass
    return ""


class _Logger:
    """Escribe detalle completo al archivo, resumen al stdout."""
    def __init__(self, file_path):
        self.f = open(file_path, "w", encoding="utf-8")
        self.path = file_path

    def file(self, msg=""):
        self.f.write(msg + "\n")

    def both(self, msg=""):
        self.f.write(msg + "\n")
        print(msg)

    def header_file(self, titulo):
        self.f.write("\n" + SEP + "\n" + titulo + "\n" + SEP + "\n")

    def close(self):
        self.f.close()

    def write_response(self, r):
        self.f.write(f"  Status:        {r.status_code}\n")
        self.f.write(f"  Set-Cookie:    {r.headers.get('Set-Cookie', '(ninguna)')}\n")
        self.f.write(f"  Content-Type:  {r.headers.get('Content-Type')}\n")
        self.f.write("  Body:\n")
        try:
            body = r.json()
            out = json.dumps(body, indent=2, ensure_ascii=False)
        except ValueError:
            body = None
            out = r.text
        for line in out.splitlines():
            self.f.write(f"    {line}\n")
        return body


class Command(BaseCommand):
    help = "Diagnostica MUTUAL validateRights/ con prueba A/B (sin/con Session)."

    def add_arguments(self, parser):
        parser.add_argument("documento", help="Documento a consultar (ej: 1007691763)")
        parser.add_argument("--tipo", default="CC", help="Tipo de documento (default: CC)")
        parser.add_argument(
            "--repeat", type=int, default=3,
            help="Veces a llamar validateRights/ con el mismo token (default: 3).",
        )
        parser.add_argument(
            "--output", default=None,
            help="Ruta del archivo de log. Default: diag_api_mutual_<timestamp>.log en cwd.",
        )

    def handle(self, *args, **options):
        documento = options["documento"]
        tipo = options["tipo"].strip().upper()
        repeat = options["repeat"]
        output = options["output"]

        if not _USERNAME or not _PASSWORD:
            self.stderr.write(
                "ERROR: setear MUTUAL_KEYCLOAK_USER y MUTUAL_KEYCLOAK_PASS en .env"
            )
            return

        if not output:
            ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
            output = os.path.join(os.getcwd(), f"diag_api_mutual_{ts}.log")

        log = _Logger(output)
        try:
            log.both(f"Documento:    {tipo}|{documento}")
            log.both(f"Repeticiones: {repeat}")
            log.both(f"Log detalle:  {output}")
            log.file(f"Token URL:    {_TOKEN_URL}")
            log.file(f"Validate URL: {_VALIDATE_URL}")

            body_validate = _payload_validate(tipo, documento)

            self._correr_modo(
                log, "MODO A · requests.post() standalone (sin Session)",
                use_session=False, body_validate=body_validate, repeat=repeat,
            )
            self._correr_modo(
                log, "MODO B · requests.Session() (cookies persistentes)",
                use_session=True, body_validate=body_validate, repeat=repeat,
            )

            log.both("")
            log.both(SEP)
            log.both("CÓMO LEER")
            log.both(SEP)
            log.both("• A falla intermitente y B OK → sticky session (cookie JSESSIONID).")
            log.both("• A y B fallan igual          → no es la cookie. Token o rate limit.")
            log.both("• A y B funcionan ambos       → solo bajo concurrencia (workers Django Q).")
            log.both("")
            log.both(f"Detalle completo: {output}")
        finally:
            log.close()

    def _correr_modo(self, log, titulo, *, use_session, body_validate, repeat):
        log.both("")
        log.both(SEP)
        log.both(titulo)
        log.both(SEP)
        log.header_file(titulo)

        sess = requests.Session() if use_session else None
        post = sess.post if sess else requests.post

        try:
            r_tok = post(_TOKEN_URL, data=_data_token(), timeout=30)
            log.both(f"Token status: {r_tok.status_code}")
            log.file(f"  Set-Cookie del /token: {r_tok.headers.get('Set-Cookie', '(ninguna)')}")
            if sess is not None:
                log.file(f"  Cookies en sess: {dict(sess.cookies)}")
            r_tok.raise_for_status()
            access = r_tok.json()["access_token"]
            log.file(f"  access_token (...{access[-20:]})")
        except Exception as e:
            log.both(f"  EXCEPCIÓN obteniendo token: {type(e).__name__}: {e}")
            return

        # Resumen por línea: " #N: 200" o " #N: 500 [...diagnostics...]"
        for i in range(1, repeat + 1):
            log.file(f"\n  ─── validateRights/ #{i} ───")
            try:
                r = post(
                    _VALIDATE_URL,
                    json=body_validate,
                    headers=_headers_validate(access),
                    timeout=60,
                )
                if sess is not None:
                    log.file(f"  Cookies en sess: {dict(sess.cookies)}")
                body = log.write_response(r)
                resumen = f"  #{i:>2}: {r.status_code}"
                if r.status_code >= 400 and body:
                    issue = _resumir_issue(body)
                    if issue:
                        resumen += f"  {issue}"
                log.both(resumen)
            except Exception as e:
                log.both(f"  #{i:>2}: EXCEPCIÓN {type(e).__name__}: {e}")
