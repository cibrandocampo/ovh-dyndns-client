"""Tests for ``infrastructure.crypto``.

Each test class isolates ``ENCRYPTION_KEY`` via env var so the module's
``_fernet()`` builds against a known key without touching any persisted
file under ``DATA_DIR``.
"""

import os
import unittest

from cryptography.fernet import Fernet

from infrastructure.crypto import (
    ENCRYPTED_PREFIX,
    decrypt_password,
    encrypt_password,
    is_encrypted,
)


class _IsolatedFernet(unittest.TestCase):
    """Provide a deterministic ENCRYPTION_KEY for the duration of each test."""

    def setUp(self):
        self._previous = os.environ.get("ENCRYPTION_KEY")
        os.environ["ENCRYPTION_KEY"] = Fernet.generate_key().decode("utf-8")

    def tearDown(self):
        if self._previous is None:
            os.environ.pop("ENCRYPTION_KEY", None)
        else:
            os.environ["ENCRYPTION_KEY"] = self._previous


class TestIsEncrypted(unittest.TestCase):
    def test_true_for_prefixed_value(self):
        self.assertTrue(is_encrypted(f"{ENCRYPTED_PREFIX}whatever"))

    def test_false_for_bare_string(self):
        self.assertFalse(is_encrypted("plaintext"))

    def test_false_for_empty(self):
        self.assertFalse(is_encrypted(""))


class TestEncryptPassword(_IsolatedFernet):
    def test_returns_prefixed_value(self):
        result = encrypt_password("my-password")
        self.assertTrue(result.startswith(ENCRYPTED_PREFIX))
        self.assertNotIn("my-password", result)

    def test_two_calls_produce_different_ciphertext(self):
        """Fernet embeds a random nonce/timestamp — same plaintext, different output."""
        a = encrypt_password("same-input")
        b = encrypt_password("same-input")
        self.assertNotEqual(a, b)
        self.assertEqual(decrypt_password(a), "same-input")
        self.assertEqual(decrypt_password(b), "same-input")


class TestDecryptPassword(_IsolatedFernet):
    def test_round_trip(self):
        self.assertEqual(decrypt_password(encrypt_password("foo")), "foo")

    def test_round_trip_unicode(self):
        secret = "contraseña-日本語-🔐"
        self.assertEqual(decrypt_password(encrypt_password(secret)), secret)

    def test_passthrough_for_legacy_plaintext(self):
        """Values without the prefix come back untouched (migration handles them)."""
        self.assertEqual(decrypt_password("legacy-plain"), "legacy-plain")

    def test_raises_on_corrupted_payload(self):
        with self.assertRaises(RuntimeError) as ctx:
            decrypt_password(f"{ENCRYPTED_PREFIX}not-a-valid-fernet-token")
        self.assertIn("Failed to decrypt", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
