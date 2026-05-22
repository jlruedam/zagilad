"""
Tests del helper Fernet (`home/modules/crypto.py`).

Verifica el roundtrip, manejo de vacíos, ausencia de clave y detección de
ciphertext corrupto. La clave se inyecta vía mock de `_get_fernet` para no
depender del .env del entorno de tests.
"""

from unittest.mock import patch

from cryptography.fernet import Fernet, InvalidToken
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase

from home.modules import crypto


_TEST_KEY = Fernet.generate_key()
_TEST_FERNET = Fernet(_TEST_KEY)


class CryptoRoundtripTests(SimpleTestCase):
    """Con la clave inyectada, encrypt+decrypt debe devolver el original."""

    def setUp(self):
        self._patcher = patch.object(crypto, "_get_fernet", return_value=_TEST_FERNET)
        self._patcher.start()
        # Limpiar lru_cache por si tests previos cachearon una instancia distinta
        crypto._get_fernet.cache_clear()

    def tearDown(self):
        self._patcher.stop()
        crypto._get_fernet.cache_clear()

    def test_roundtrip_ascii(self):
        original = "MiPasswordSecreto123"
        cipher = crypto.encrypt(original)
        self.assertNotEqual(cipher, original)
        self.assertEqual(crypto.decrypt(cipher), original)

    def test_roundtrip_utf8(self):
        original = "contraseña con ñ y á ✓"
        cipher = crypto.encrypt(original)
        self.assertEqual(crypto.decrypt(cipher), original)

    def test_encrypt_empty_returns_empty(self):
        self.assertEqual(crypto.encrypt(""), "")
        self.assertEqual(crypto.encrypt(None), "")

    def test_decrypt_empty_returns_empty(self):
        self.assertEqual(crypto.decrypt(""), "")
        self.assertEqual(crypto.decrypt(None), "")

    def test_decrypt_corrupted_raises_invalid_token(self):
        with self.assertRaises(InvalidToken):
            crypto.decrypt("gAAAAA-garbage-not-a-real-token")


class CryptoMissingKeyTests(SimpleTestCase):
    """Sin FUENTES_FERNET_KEY, las funciones deben fallar con un mensaje accionable."""

    def setUp(self):
        # Limpiar el cache de la clave; el config('FUENTES_FERNET_KEY', default='')
        # devolverá '' y _get_fernet levantará ImproperlyConfigured.
        crypto._get_fernet.cache_clear()

    def tearDown(self):
        crypto._get_fernet.cache_clear()

    @patch("home.modules.crypto.config", return_value="")
    def test_missing_key_raises(self, _mock_config):
        with self.assertRaises(ImproperlyConfigured) as ctx:
            crypto.encrypt("foo")
        self.assertIn("FUENTES_FERNET_KEY", str(ctx.exception))
        self.assertIn("Fernet.generate_key", str(ctx.exception))

    @patch("home.modules.crypto.config", return_value="not-a-valid-fernet-key")
    def test_invalid_key_raises(self, _mock_config):
        with self.assertRaises(ImproperlyConfigured) as ctx:
            crypto.decrypt("dummy")
        self.assertIn("inválida", str(ctx.exception).lower())
