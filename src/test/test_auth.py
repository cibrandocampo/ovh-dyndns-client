import os
import unittest
from datetime import timedelta
from unittest.mock import patch

from api.auth import (
    hash_password,
    verify_password,
    create_access_token,
    decode_token,
    get_jwt_secret,
    get_jwt_expiration_hours,
    get_admin_credentials,
    DEFAULT_JWT_SECRET,
    DEFAULT_JWT_EXPIRATION_HOURS
)


class TestPasswordHashing(unittest.TestCase):
    """Tests for password hashing and verification functions."""

    def test_hash_password_returns_different_hash_each_time(self):
        """Test that hashing the same password returns different hashes due to salt."""
        password = "test_password123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        self.assertNotEqual(hash1, hash2)

    def test_hash_password_returns_string(self):
        """Test that hash_password returns a string."""
        result = hash_password("mypassword")
        self.assertIsInstance(result, str)

    def test_verify_password_correct(self):
        """Test that verify_password returns True for correct password."""
        password = "secure_password"
        hashed = hash_password(password)
        self.assertTrue(verify_password(password, hashed))

    def test_verify_password_incorrect(self):
        """Test that verify_password returns False for incorrect password."""
        password = "secure_password"
        hashed = hash_password(password)
        self.assertFalse(verify_password("wrong_password", hashed))

    def test_verify_password_empty_password(self):
        """Test verify_password with empty password."""
        hashed = hash_password("actual_password")
        self.assertFalse(verify_password("", hashed))

    def test_hash_password_with_special_characters(self):
        """Test hashing password with special characters."""
        password = "p@$$w0rd!#%&*()[]{}|"
        hashed = hash_password(password)
        self.assertTrue(verify_password(password, hashed))

    def test_hash_password_with_unicode(self):
        """Test hashing password with unicode characters."""
        password = "contraseña_日本語_🔐"
        hashed = hash_password(password)
        self.assertTrue(verify_password(password, hashed))


class TestJWTToken(unittest.TestCase):
    """Tests for JWT token creation and decoding."""

    def setUp(self):
        """Set up test environment variables."""
        os.environ['JWT_SECRET'] = 'test-jwt-secret-key'

    def tearDown(self):
        """Clean up environment variables."""
        if 'JWT_SECRET' in os.environ:
            del os.environ['JWT_SECRET']

    def test_create_access_token_contains_subject(self):
        """Test that created token contains the subject claim."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        decoded = decode_token(token)
        self.assertEqual(decoded["sub"], "testuser")

    def test_create_access_token_contains_expiration(self):
        """Test that created token contains expiration claim."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        decoded = decode_token(token)
        self.assertIn("exp", decoded)

    def test_create_access_token_with_custom_expiration(self):
        """Test creating token with custom expiration delta."""
        data = {"sub": "testuser"}
        expires = timedelta(hours=1)
        token = create_access_token(data, expires_delta=expires)
        decoded = decode_token(token)
        self.assertIsNotNone(decoded)

    def test_create_access_token_preserves_additional_data(self):
        """Test that additional data is preserved in token."""
        data = {"sub": "testuser", "role": "admin", "custom_field": "value"}
        token = create_access_token(data)
        decoded = decode_token(token)
        self.assertEqual(decoded["role"], "admin")
        self.assertEqual(decoded["custom_field"], "value")

    def test_decode_token_invalid_token(self):
        """Test that decode_token returns None for invalid token."""
        result = decode_token("invalid.token.here")
        self.assertIsNone(result)

    def test_decode_token_tampered_token(self):
        """Test that decode_token returns None for tampered token."""
        data = {"sub": "testuser"}
        token = create_access_token(data)
        # Tamper with the token
        tampered = token[:-5] + "xxxxx"
        result = decode_token(tampered)
        self.assertIsNone(result)

    def test_decode_token_empty_string(self):
        """Test that decode_token returns None for empty string."""
        result = decode_token("")
        self.assertIsNone(result)

    def test_decode_token_wrong_secret(self):
        """Test that decode_token fails with wrong secret."""
        data = {"sub": "testuser"}
        token = create_access_token(data)

        # Change the secret
        os.environ['JWT_SECRET'] = 'different-secret'
        result = decode_token(token)
        self.assertIsNone(result)


class TestJWTConfiguration(unittest.TestCase):
    """Tests for JWT configuration functions."""

    def tearDown(self):
        """Clean up environment variables after each test."""
        for var in ['JWT_SECRET', 'JWT_EXPIRATION_HOURS']:
            if var in os.environ:
                del os.environ[var]

    def test_get_jwt_secret_from_env(self):
        """Test getting JWT secret from environment variable."""
        os.environ['JWT_SECRET'] = 'my-custom-secret'
        self.assertEqual(get_jwt_secret(), 'my-custom-secret')

    def test_get_jwt_secret_default(self):
        """Test getting default JWT secret when not set."""
        if 'JWT_SECRET' in os.environ:
            del os.environ['JWT_SECRET']
        self.assertEqual(get_jwt_secret(), DEFAULT_JWT_SECRET)

    def test_get_jwt_expiration_hours_from_env(self):
        """Test getting JWT expiration from environment variable."""
        os.environ['JWT_EXPIRATION_HOURS'] = '48'
        self.assertEqual(get_jwt_expiration_hours(), 48)

    def test_get_jwt_expiration_hours_default(self):
        """Test getting default JWT expiration when not set."""
        if 'JWT_EXPIRATION_HOURS' in os.environ:
            del os.environ['JWT_EXPIRATION_HOURS']
        self.assertEqual(get_jwt_expiration_hours(), DEFAULT_JWT_EXPIRATION_HOURS)

    def test_get_jwt_expiration_hours_invalid_value(self):
        """Test that invalid expiration value returns default."""
        os.environ['JWT_EXPIRATION_HOURS'] = 'not-a-number'
        self.assertEqual(get_jwt_expiration_hours(), DEFAULT_JWT_EXPIRATION_HOURS)

    def test_get_jwt_expiration_hours_float_value(self):
        """Test that float value returns default."""
        os.environ['JWT_EXPIRATION_HOURS'] = '24.5'
        self.assertEqual(get_jwt_expiration_hours(), DEFAULT_JWT_EXPIRATION_HOURS)


class TestAdminCredentials(unittest.TestCase):
    """Tests for admin credentials function."""

    def tearDown(self):
        """Clean up environment variables."""
        for var in ['ADMIN_USERNAME', 'ADMIN_PASSWORD']:
            if var in os.environ:
                del os.environ[var]

    def test_get_admin_credentials_from_env(self):
        """Test getting admin credentials from environment variables."""
        os.environ['ADMIN_USERNAME'] = 'custom_admin'
        os.environ['ADMIN_PASSWORD'] = 'custom_pass'
        username, password = get_admin_credentials()
        self.assertEqual(username, 'custom_admin')
        self.assertEqual(password, 'custom_pass')

    def test_get_admin_credentials_defaults(self):
        """Test getting default admin credentials."""
        if 'ADMIN_USERNAME' in os.environ:
            del os.environ['ADMIN_USERNAME']
        if 'ADMIN_PASSWORD' in os.environ:
            del os.environ['ADMIN_PASSWORD']
        username, password = get_admin_credentials()
        self.assertEqual(username, 'admin')
        self.assertEqual(password, 'admin')

    def test_get_admin_credentials_partial_env(self):
        """Test getting credentials when only username is set."""
        os.environ['ADMIN_USERNAME'] = 'myuser'
        if 'ADMIN_PASSWORD' in os.environ:
            del os.environ['ADMIN_PASSWORD']
        username, password = get_admin_credentials()
        self.assertEqual(username, 'myuser')
        self.assertEqual(password, 'admin')


if __name__ == "__main__":
    unittest.main()
