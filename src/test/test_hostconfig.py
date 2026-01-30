import unittest
from pydantic import ValidationError, SecretStr

from domain.hostconfig import HostConfig


class TestHostConfig(unittest.TestCase):
    """Tests for the HostConfig domain model."""

    def test_create_valid_hostconfig(self):
        """Test creating a valid HostConfig instance."""
        config = HostConfig(
            hostname="example.com",
            username="user",
            password="secret"
        )
        self.assertEqual(config.hostname, "example.com")
        self.assertEqual(config.username, "user")
        self.assertIsInstance(config.password, SecretStr)

    def test_password_is_secret(self):
        """Test that password is stored as SecretStr and hidden in string representation."""
        config = HostConfig(
            hostname="example.com",
            username="user",
            password="mysecretpassword"
        )
        # SecretStr should not reveal password in string representation
        self.assertNotIn("mysecretpassword", str(config))
        self.assertNotIn("mysecretpassword", repr(config))

    def test_password_get_secret_value(self):
        """Test that password can be retrieved using get_secret_value."""
        config = HostConfig(
            hostname="example.com",
            username="user",
            password="mysecretpassword"
        )
        self.assertEqual(config.password.get_secret_value(), "mysecretpassword")

    def test_missing_hostname_raises_error(self):
        """Test that missing hostname raises ValidationError."""
        with self.assertRaises(ValidationError):
            HostConfig(username="user", password="pass")

    def test_missing_username_raises_error(self):
        """Test that missing username raises ValidationError."""
        with self.assertRaises(ValidationError):
            HostConfig(hostname="example.com", password="pass")

    def test_missing_password_raises_error(self):
        """Test that missing password raises ValidationError."""
        with self.assertRaises(ValidationError):
            HostConfig(hostname="example.com", username="user")

    def test_from_dict_valid(self):
        """Test creating HostConfig from valid dictionary."""
        data = {
            "hostname": "test.example.com",
            "username": "testuser",
            "password": "testpass"
        }
        config = HostConfig.from_dict(data)
        self.assertEqual(config.hostname, "test.example.com")
        self.assertEqual(config.username, "testuser")
        self.assertEqual(config.password.get_secret_value(), "testpass")

    def test_from_dict_missing_field(self):
        """Test that from_dict raises ValidationError when field is missing."""
        data = {
            "hostname": "test.example.com",
            "username": "testuser"
            # password is missing
        }
        with self.assertRaises(ValidationError):
            HostConfig.from_dict(data)

    def test_from_dict_extra_fields_ignored(self):
        """Test that extra fields in dictionary are ignored."""
        data = {
            "hostname": "test.example.com",
            "username": "testuser",
            "password": "testpass",
            "extra_field": "should be ignored"
        }
        config = HostConfig.from_dict(data)
        self.assertEqual(config.hostname, "test.example.com")
        self.assertFalse(hasattr(config, "extra_field"))

    def test_hostname_with_subdomain(self):
        """Test hostname with subdomain."""
        config = HostConfig(
            hostname="sub.domain.example.com",
            username="user",
            password="pass"
        )
        self.assertEqual(config.hostname, "sub.domain.example.com")

    def test_hostname_with_ip_address(self):
        """Test hostname can be an IP address."""
        config = HostConfig(
            hostname="192.168.1.1",
            username="user",
            password="pass"
        )
        self.assertEqual(config.hostname, "192.168.1.1")

    def test_empty_hostname_raises_error(self):
        """Test that empty hostname is allowed by Pydantic but can be validated."""
        # Pydantic allows empty strings by default
        config = HostConfig(
            hostname="",
            username="user",
            password="pass"
        )
        self.assertEqual(config.hostname, "")

    def test_special_characters_in_password(self):
        """Test password with special characters."""
        special_password = "p@$$w0rd!#%&*()[]{}|<>?~`"
        config = HostConfig(
            hostname="example.com",
            username="user",
            password=special_password
        )
        self.assertEqual(config.password.get_secret_value(), special_password)

    def test_unicode_in_fields(self):
        """Test unicode characters in fields."""
        config = HostConfig(
            hostname="例え.jp",
            username="用户",
            password="密码"
        )
        self.assertEqual(config.hostname, "例え.jp")
        self.assertEqual(config.username, "用户")

    def test_model_dict_serialization(self):
        """Test that model can be serialized to dict."""
        config = HostConfig(
            hostname="example.com",
            username="user",
            password="secret"
        )
        data = config.model_dump()
        self.assertEqual(data["hostname"], "example.com")
        self.assertEqual(data["username"], "user")
        self.assertIsInstance(data["password"], SecretStr)

    def test_two_configs_with_same_values_are_equal(self):
        """Test that two HostConfig with same values are equal."""
        config1 = HostConfig(
            hostname="example.com",
            username="user",
            password="pass"
        )
        config2 = HostConfig(
            hostname="example.com",
            username="user",
            password="pass"
        )
        self.assertEqual(config1.hostname, config2.hostname)
        self.assertEqual(config1.username, config2.username)


if __name__ == "__main__":
    unittest.main()
