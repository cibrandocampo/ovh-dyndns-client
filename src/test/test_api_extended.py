import os
import tempfile
import unittest
from datetime import timedelta
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from api.auth import create_access_token, hash_password
from api.main import create_app
from infrastructure.database.database import get_db_session, init_db
from infrastructure.database.models import History, Host, Settings, State, User


class TestAPIExtended(unittest.TestCase):
    """Extended tests for API edge cases and error handling."""

    @classmethod
    def setUpClass(cls):
        """Set up test database and FastAPI client."""
        cls.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        cls.temp_db.close()
        os.environ["DATABASE_PATH"] = cls.temp_db.name
        os.environ["JWT_SECRET"] = "test-secret-key-extended"
        from cryptography.fernet import Fernet

        os.environ["ENCRYPTION_KEY"] = Fernet.generate_key().decode("utf-8")
        init_db()
        cls.app = create_app()
        cls.client = TestClient(cls.app)

    @classmethod
    def tearDownClass(cls):
        """Clean up test database."""
        os.unlink(cls.temp_db.name)

    def setUp(self):
        """Clear all tables and create test user before each test."""
        with get_db_session() as db:
            db.query(History).delete()
            db.query(Host).delete()
            db.query(State).delete()
            db.query(Settings).delete()
            db.query(User).delete()

            user = User(username="testuser", password_hash=hash_password("testpass"), must_change_password=False)
            db.add(user)

    def get_auth_header(self):
        """Get authentication header with valid token."""
        response = self.client.post("/api/auth/login", json={"username": "testuser", "password": "testpass"})
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    # Token expiration tests

    def test_expired_token_rejected(self):
        """Test that expired tokens are rejected."""
        # Create token that expires immediately
        expired_token = create_access_token(data={"sub": "testuser"}, expires_delta=timedelta(seconds=-1))
        headers = {"Authorization": f"Bearer {expired_token}"}

        response = self.client.get("/api/hosts/", headers=headers)
        self.assertEqual(response.status_code, 401)

    def test_malformed_token_rejected(self):
        """Test that malformed tokens are rejected."""
        headers = {"Authorization": "Bearer not-a-valid-token"}
        response = self.client.get("/api/hosts/", headers=headers)
        self.assertEqual(response.status_code, 401)

    def test_missing_bearer_prefix_rejected(self):
        """Test that tokens without Bearer prefix are rejected."""
        response = self.client.post("/api/auth/login", json={"username": "testuser", "password": "testpass"})
        token = response.json()["access_token"]
        headers = {"Authorization": token}  # Missing "Bearer " prefix

        response = self.client.get("/api/hosts/", headers=headers)
        self.assertIn(response.status_code, [401, 403])

    # Login edge cases

    def test_login_nonexistent_user(self):
        """Test login with non-existent user."""
        response = self.client.post("/api/auth/login", json={"username": "nonexistent", "password": "anypass"})
        self.assertEqual(response.status_code, 401)

    def test_login_empty_credentials(self):
        """Test login with empty credentials."""
        response = self.client.post("/api/auth/login", json={"username": "", "password": ""})
        self.assertEqual(response.status_code, 401)

    def test_login_missing_username(self):
        """Test login with missing username field."""
        response = self.client.post("/api/auth/login", json={"password": "testpass"})
        self.assertEqual(response.status_code, 422)

    def test_login_missing_password(self):
        """Test login with missing password field."""
        response = self.client.post("/api/auth/login", json={"username": "testuser"})
        self.assertEqual(response.status_code, 422)

    # Password change edge cases

    def test_change_password_too_short(self):
        """Test password change with too short new password."""
        headers = self.get_auth_header()
        response = self.client.post(
            "/api/auth/change-password",
            json={
                "current_password": "testpass",
                "new_password": "short",  # Less than 6 characters
            },
            headers=headers,
        )
        self.assertEqual(response.status_code, 422)

    def test_change_password_same_as_current(self):
        """Test changing password to the same value."""
        headers = self.get_auth_header()
        response = self.client.post(
            "/api/auth/change-password",
            json={
                "current_password": "testpass",
                "new_password": "testpass",  # Same as current
            },
            headers=headers,
        )
        # This should still succeed as we don't prevent same passwords
        self.assertEqual(response.status_code, 200)

    # Host edge cases

    def test_create_host_empty_hostname(self):
        """Test creating host with empty hostname."""
        headers = self.get_auth_header()
        response = self.client.post(
            "/api/hosts/", json={"hostname": "", "username": "user", "password": "pass"}, headers=headers
        )
        # Pydantic validation may allow empty strings
        self.assertIn(response.status_code, [201, 422])

    def test_get_nonexistent_host(self):
        """Test getting a host that doesn't exist."""
        headers = self.get_auth_header()
        response = self.client.get("/api/hosts/99999", headers=headers)
        self.assertEqual(response.status_code, 404)

    def test_update_nonexistent_host(self):
        """Test updating a host that doesn't exist."""
        headers = self.get_auth_header()
        response = self.client.put("/api/hosts/99999", json={"hostname": "updated.example.com"}, headers=headers)
        self.assertEqual(response.status_code, 404)

    def test_delete_nonexistent_host(self):
        """Test deleting a host that doesn't exist."""
        headers = self.get_auth_header()
        response = self.client.delete("/api/hosts/99999", headers=headers)
        self.assertEqual(response.status_code, 404)

    def test_create_host_special_characters(self):
        """Test creating host with special characters in fields."""
        headers = self.get_auth_header()
        response = self.client.post(
            "/api/hosts/",
            json={"hostname": "test.example.com", "username": "user@domain.com", "password": "p@$$w0rd!#%"},
            headers=headers,
        )
        self.assertEqual(response.status_code, 201)

    def test_update_host_partial(self):
        """Test partial update of host (only some fields)."""
        headers = self.get_auth_header()

        # Create host
        response = self.client.post(
            "/api/hosts/",
            json={"hostname": "test.example.com", "username": "user", "password": "pass"},
            headers=headers,
        )
        host_id = response.json()["id"]

        # Update only username
        response = self.client.put(f"/api/hosts/{host_id}", json={"username": "newuser"}, headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["username"], "newuser")
        self.assertEqual(response.json()["hostname"], "test.example.com")

    # History edge cases

    def test_history_with_large_offset(self):
        """Test history with offset larger than total entries."""
        headers = self.get_auth_header()
        response = self.client.get("/api/history/?limit=10&offset=10000", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["entries"]), 0)

    def test_history_with_zero_limit(self):
        """Test history with zero limit returns validation error."""
        headers = self.get_auth_header()
        response = self.client.get("/api/history/?limit=0", headers=headers)
        # Zero limit is not valid, API returns 422
        self.assertEqual(response.status_code, 422)

    def test_history_negative_values_rejected(self):
        """Test that negative limit/offset are rejected."""
        headers = self.get_auth_header()
        response = self.client.get("/api/history/?limit=-1", headers=headers)
        self.assertEqual(response.status_code, 422)

    def test_history_filter_by_hostname(self):
        """`?hostname=foo` returns only entries that match, with the count adjusted."""
        from infrastructure.database import SqliteRepository

        repo = SqliteRepository()
        repo.create_host("alpha.example.com", "u", "p")
        repo.update_host_status("alpha.example.com", True)
        repo.create_host("beta.example.com", "u", "p")
        repo.update_host_status("beta.example.com", False, "boom")

        headers = self.get_auth_header()
        response = self.client.get("/api/history/?hostname=alpha.example.com", headers=headers)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        # Every returned row references the requested hostname.
        for entry in body["entries"]:
            self.assertEqual(entry["hostname"], "alpha.example.com")
        # `total` reflects the filtered count, not the global one.
        self.assertEqual(body["total"], len(body["entries"]))

    def test_history_hostnames_endpoint_returns_distinct_sorted(self):
        """`/api/history/hostnames` returns distinct hostnames in alpha order, NULLs excluded."""
        from infrastructure.database import SqliteRepository

        repo = SqliteRepository()
        # Two different hosts to exercise distinct ordering. `init_default_settings`
        # also writes a history row but with `hostname=None`, which must be filtered out.
        repo.create_host("zeta.example.com", "u", "p")
        repo.create_host("alpha.example.com", "u", "p")
        repo.init_default_settings()

        headers = self.get_auth_header()
        response = self.client.get("/api/history/hostnames", headers=headers)
        self.assertEqual(response.status_code, 200)
        names = response.json()
        self.assertIn("alpha.example.com", names)
        self.assertIn("zeta.example.com", names)
        # Sorted alpha — alpha < zeta in the response order.
        self.assertLess(names.index("alpha.example.com"), names.index("zeta.example.com"))
        # No NULLs surfaced as `null`/empty strings.
        self.assertNotIn(None, names)
        self.assertNotIn("", names)

    def test_history_hostnames_requires_auth(self):
        """The hostnames endpoint must reject unauthenticated requests."""
        response = self.client.get("/api/history/hostnames")
        # Same 401/403 tolerance as the existing `test_unauthorized_access`.
        self.assertIn(response.status_code, [401, 403])

    # Settings edge cases

    def test_settings_update_partial(self):
        """Test partial settings update."""
        headers = self.get_auth_header()

        from infrastructure.database import SqliteRepository

        SqliteRepository().init_default_settings()

        # Update only interval
        response = self.client.put("/api/settings/", json={"update_interval": 600}, headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["update_interval"], 600)

    def test_settings_invalid_log_level(self):
        """Test settings with invalid log level."""
        headers = self.get_auth_header()
        response = self.client.put(
            "/api/settings/",
            json={
                "logger_level": "TRACE"  # Not a valid level
            },
            headers=headers,
        )
        self.assertEqual(response.status_code, 422)

    def test_settings_interval_too_low(self):
        """Test settings with interval below minimum."""
        headers = self.get_auth_header()
        response = self.client.put(
            "/api/settings/",
            json={
                "update_interval": 5  # Too low
            },
            headers=headers,
        )
        self.assertEqual(response.status_code, 422)

    # Status endpoint

    def test_status_empty_hosts(self):
        """Test status when no hosts are configured."""
        headers = self.get_auth_header()
        response = self.client.get("/api/status/", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["hosts"]), 0)

    def test_status_with_ip_set(self):
        """Test status after IP has been set."""
        headers = self.get_auth_header()

        # Set IP in state
        from infrastructure.database import SqliteRepository

        repo = SqliteRepository()
        repo.set_ip("192.168.1.100")

        response = self.client.get("/api/status/", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["current_ip"], "192.168.1.100")

    # Trigger endpoint

    def test_trigger_endpoint_exists(self):
        """Test that trigger endpoint exists and requires auth."""
        # Without auth should return 401/403
        response = self.client.post("/api/status/trigger")
        self.assertIn(response.status_code, [401, 403])

        # With auth, endpoint should be accessible (may fail due to no controller)
        headers = self.get_auth_header()
        response = self.client.post("/api/status/trigger", headers=headers)
        # Accept 200 (success), 500 (controller error), or 503 (service unavailable)
        self.assertIn(response.status_code, [200, 500, 503])

    # Content-Type tests

    def test_login_wrong_content_type(self):
        """Test login with wrong content type."""
        response = self.client.post(
            "/api/auth/login",
            content="username=testuser&password=testpass",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        self.assertEqual(response.status_code, 422)

    # Trigger endpoint with controller set

    def test_trigger_update_with_controller_success(self):
        """Test trigger endpoint when controller is set and update succeeds."""
        from api.routers.status import set_controller

        mock_controller = MagicMock()
        set_controller(mock_controller)
        try:
            headers = self.get_auth_header()
            response = self.client.post("/api/status/trigger", headers=headers)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json()["success"])
            mock_controller.handler.assert_called_once()
        finally:
            set_controller(None)

    def test_trigger_update_with_controller_exception(self):
        """Test trigger endpoint when controller raises an exception."""
        from api.routers.status import set_controller

        mock_controller = MagicMock()
        mock_controller.handler.side_effect = Exception("Update failed")
        set_controller(mock_controller)
        try:
            headers = self.get_auth_header()
            response = self.client.post("/api/status/trigger", headers=headers)
            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.json()["success"])
            self.assertIn("Update failed", response.json()["message"])
        finally:
            set_controller(None)

    def test_trigger_host_update_with_controller(self):
        """Test per-host trigger endpoint when controller is set."""
        from api.routers.status import set_controller

        mock_controller = MagicMock()
        mock_controller.force_update_host.return_value = (True, "Host updated successfully")
        set_controller(mock_controller)
        try:
            headers = self.get_auth_header()
            response = self.client.post("/api/status/trigger/example.com", headers=headers)
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json()["success"])
            mock_controller.force_update_host.assert_called_once_with("example.com")
        finally:
            set_controller(None)

    def test_settings_change_callback_is_called(self):
        """Test that settings change callback is invoked when settings are updated."""
        from api.routers.settings import set_settings_change_callback

        callback = MagicMock()
        set_settings_change_callback(callback)
        try:
            from infrastructure.database import SqliteRepository

            SqliteRepository().init_default_settings()

            headers = self.get_auth_header()
            self.client.put("/api/settings/", json={"update_interval": 120}, headers=headers)
            callback.assert_called_once()
        finally:
            set_settings_change_callback(None)

    # init_admin_user tests

    def test_init_admin_user_creates_new_user(self):
        """Test init_admin_user creates user when it doesn't exist."""
        from api.main import init_admin_user

        with get_db_session() as db:
            db.query(User).delete()

        os.environ["ADMIN_USERNAME"] = "newadmin"
        os.environ["ADMIN_PASSWORD"] = "newadminpass"
        try:
            init_admin_user()
            from infrastructure.database import SqliteRepository

            self.assertTrue(SqliteRepository().user_exists("newadmin"))
        finally:
            del os.environ["ADMIN_USERNAME"]
            del os.environ["ADMIN_PASSWORD"]

    def test_init_admin_user_existing_user(self):
        """Test init_admin_user is a no-op when user already exists."""
        from api.main import init_admin_user

        # testuser already exists from setUp
        os.environ["ADMIN_USERNAME"] = "testuser"
        os.environ["ADMIN_PASSWORD"] = "testpass"
        try:
            init_admin_user()  # Should not raise
        finally:
            del os.environ["ADMIN_USERNAME"]
            del os.environ["ADMIN_PASSWORD"]

    # Token payload edge case

    def test_token_with_no_sub_rejected(self):
        """Test that a token without 'sub' claim is rejected."""
        from api.auth import create_access_token

        token = create_access_token(data={"user": "testuser"})  # No 'sub' field
        headers = {"Authorization": f"Bearer {token}"}
        response = self.client.get("/api/hosts/", headers=headers)
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
