"""
Cifrado de credenciales sensibles para fuentes externas (módulo tipo_usuario).

Usa Fernet (clave simétrica derivada de URL-safe base64 de 32 bytes). La clave
vive en `.env` como `FUENTES_FERNET_KEY` y nunca debe commitearse.

Generar una clave nueva:
    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

Si la clave no está configurada, `encrypt`/`decrypt` lanzan `ImproperlyConfigured`
con un mensaje accionable. La carga de la clave es perezosa (no se evalúa al
importar) para no romper migraciones ni tests en entornos sin la clave.
"""
import logging
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken
from decouple import config
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_fernet() -> Fernet:
    key = config("FUENTES_FERNET_KEY", default="")
    if not key:
        raise ImproperlyConfigured(
            "FUENTES_FERNET_KEY no configurada en .env. Generala con:\n"
            '  python -c "from cryptography.fernet import Fernet; '
            'print(Fernet.generate_key().decode())"\n'
            "y agregala al .env como FUENTES_FERNET_KEY=<clave>"
        )
    try:
        return Fernet(key.encode() if isinstance(key, str) else key)
    except (ValueError, TypeError) as e:
        raise ImproperlyConfigured(
            f"FUENTES_FERNET_KEY inválida ({e}). Debe ser una clave Fernet "
            "(base64 url-safe de 32 bytes)."
        ) from e


def encrypt(plaintext: str) -> str:
    """Cifra un string. Devuelve ciphertext como str (base64 url-safe).

    `None` o `''` → `''` (no se cifra una cadena vacía).
    """
    if not plaintext:
        return ""
    return _get_fernet().encrypt(str(plaintext).encode("utf-8")).decode("ascii")


def decrypt(ciphertext: str) -> str:
    """Descifra un string. `''` o `None` → `''`. Lanza InvalidToken si está corrupto."""
    if not ciphertext:
        return ""
    try:
        return _get_fernet().decrypt(ciphertext.encode("ascii")).decode("utf-8")
    except InvalidToken:
        logger.error(
            "Fernet InvalidToken al desencriptar credencial — clave rotada o dato corrupto"
        )
        raise
