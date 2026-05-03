"""Tests for ``infrastructure.secrets``.

Each test isolates ``DATA_DIR`` to a ``tmp_path`` so generated secret files
land outside ``/app/data``. Env vars (``JWT_SECRET``, ``ENCRYPTION_KEY``,
``DATA_DIR``) are scrubbed in ``tearDown`` to avoid leaking between tests.
"""

import os
import tempfile
import unittest
from pathlib import Path

from infrastructure import secrets as secrets_mod


class _IsolatedTempDir(unittest.TestCase):
    """Base class that points DATA_DIR at a fresh tmp dir per test."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        os.environ["DATA_DIR"] = self._tmp.name
        # Make sure no leftovers from earlier tests survive.
        for var in ("JWT_SECRET", "ENCRYPTION_KEY"):
            os.environ.pop(var, None)

    def tearDown(self):
        for var in ("DATA_DIR", "JWT_SECRET", "ENCRYPTION_KEY"):
            os.environ.pop(var, None)
        self._tmp.cleanup()

    @property
    def data_dir(self) -> Path:
        return Path(self._tmp.name)


class TestJwtSecret(_IsolatedTempDir):
    def test_env_var_takes_precedence(self):
        os.environ["JWT_SECRET"] = "env-supplied"
        self.assertEqual(secrets_mod.get_or_create_jwt_secret(), "env-supplied")
        # File must not be created when env var wins.
        self.assertFalse((self.data_dir / secrets_mod.JWT_SECRET_FILENAME).exists())

    def test_reads_persisted_file(self):
        path = self.data_dir / secrets_mod.JWT_SECRET_FILENAME
        path.write_text("file-supplied\n")
        # Trailing whitespace must be trimmed.
        self.assertEqual(secrets_mod.get_or_create_jwt_secret(), "file-supplied")

    def test_generates_persists_and_returns(self):
        secret = secrets_mod.get_or_create_jwt_secret()
        path = self.data_dir / secrets_mod.JWT_SECRET_FILENAME
        self.assertTrue(path.exists())
        self.assertEqual(path.read_text(), secret)
        # token_urlsafe(32) produces ~43 chars of url-safe base64.
        self.assertGreaterEqual(len(secret), 32)

    def test_idempotent_across_calls(self):
        first = secrets_mod.get_or_create_jwt_secret()
        second = secrets_mod.get_or_create_jwt_secret()
        self.assertEqual(first, second)

    def test_generated_file_is_chmod_600(self):
        secrets_mod.get_or_create_jwt_secret()
        path = self.data_dir / secrets_mod.JWT_SECRET_FILENAME
        self.assertEqual(oct(path.stat().st_mode & 0o777), "0o600")


class TestEncryptionKey(_IsolatedTempDir):
    def test_env_var_takes_precedence(self):
        os.environ["ENCRYPTION_KEY"] = "env-supplied-key"
        self.assertEqual(secrets_mod.get_or_create_encryption_key(), b"env-supplied-key")
        self.assertFalse((self.data_dir / secrets_mod.ENCRYPTION_KEY_FILENAME).exists())

    def test_reads_persisted_file(self):
        from cryptography.fernet import Fernet

        existing = Fernet.generate_key()
        path = self.data_dir / secrets_mod.ENCRYPTION_KEY_FILENAME
        path.write_bytes(existing)
        self.assertEqual(secrets_mod.get_or_create_encryption_key(), existing)

    def test_generates_valid_fernet_key(self):
        from cryptography.fernet import Fernet

        key = secrets_mod.get_or_create_encryption_key()
        # Must be a valid Fernet key (constructor will raise otherwise).
        Fernet(key)
        path = self.data_dir / secrets_mod.ENCRYPTION_KEY_FILENAME
        self.assertTrue(path.exists())
        self.assertEqual(path.read_bytes(), key)

    def test_idempotent_across_calls(self):
        first = secrets_mod.get_or_create_encryption_key()
        second = secrets_mod.get_or_create_encryption_key()
        self.assertEqual(first, second)

    def test_generated_file_is_chmod_600(self):
        secrets_mod.get_or_create_encryption_key()
        path = self.data_dir / secrets_mod.ENCRYPTION_KEY_FILENAME
        self.assertEqual(oct(path.stat().st_mode & 0o777), "0o600")


class TestEncryptionKeyExists(_IsolatedTempDir):
    def test_false_when_neither_env_nor_file(self):
        self.assertFalse(secrets_mod.encryption_key_exists())

    def test_true_when_env_var_set(self):
        os.environ["ENCRYPTION_KEY"] = "anything"
        self.assertTrue(secrets_mod.encryption_key_exists())

    def test_true_when_file_present(self):
        (self.data_dir / secrets_mod.ENCRYPTION_KEY_FILENAME).write_bytes(b"placeholder")
        self.assertTrue(secrets_mod.encryption_key_exists())


if __name__ == "__main__":
    unittest.main()
