import os
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from infrastructure.database.database import init_db, get_db_session
from infrastructure.database.models import User, Host, State, History, Settings
from api.auth import hash_password
from api.main import create_app


class TestAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Set up test database and FastAPI client."""
        cls.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        cls.temp_db.close()
        os.environ['DATABASE_PATH'] = cls.temp_db.name
        os.environ['JWT_SECRET'] = 'test-secret-key'
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

            # Create test user (not requiring password change for tests)
            user = User(
                username="testuser",
                password_hash=hash_password("testpass"),
                must_change_password=False
            )
            db.add(user)

    def get_auth_header(self):
        """Get authentication header with valid token."""
        response = self.client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "testpass"
        })
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    def test_login_success(self):
        """Test successful login."""
        response = self.client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "testpass"
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["token_type"], "bearer")
        self.assertFalse(data["must_change_password"])

    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        response = self.client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "wrongpass"
        })
        self.assertEqual(response.status_code, 401)

    def test_login_must_change_password(self):
        """Test login with user that must change password."""
        with get_db_session() as db:
            user = db.query(User).filter(User.username == "testuser").first()
            user.must_change_password = True

        response = self.client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "testpass"
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["must_change_password"])

    def test_change_password(self):
        """Test password change."""
        headers = self.get_auth_header()
        response = self.client.post("/api/auth/change-password", json={
            "current_password": "testpass",
            "new_password": "newpassword123"
        }, headers=headers)
        self.assertEqual(response.status_code, 200)

        # Try login with new password
        response = self.client.post("/api/auth/login", json={
            "username": "testuser",
            "password": "newpassword123"
        })
        self.assertEqual(response.status_code, 200)

    def test_change_password_wrong_current(self):
        """Test password change with wrong current password."""
        headers = self.get_auth_header()
        response = self.client.post("/api/auth/change-password", json={
            "current_password": "wrongpass",
            "new_password": "newpassword123"
        }, headers=headers)
        self.assertEqual(response.status_code, 400)

    def test_hosts_crud(self):
        """Test hosts CRUD operations."""
        headers = self.get_auth_header()

        # Create host
        response = self.client.post("/api/hosts/", json={
            "hostname": "test.example.com",
            "username": "dnsuser",
            "password": "dnspass"
        }, headers=headers)
        self.assertEqual(response.status_code, 201)
        host_id = response.json()["id"]

        # List hosts
        response = self.client.get("/api/hosts/", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

        # Get host
        response = self.client.get(f"/api/hosts/{host_id}", headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["hostname"], "test.example.com")

        # Update host
        response = self.client.put(f"/api/hosts/{host_id}", json={
            "hostname": "updated.example.com"
        }, headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["hostname"], "updated.example.com")

        # Delete host
        response = self.client.delete(f"/api/hosts/{host_id}", headers=headers)
        self.assertEqual(response.status_code, 204)

        # Verify deleted
        response = self.client.get(f"/api/hosts/{host_id}", headers=headers)
        self.assertEqual(response.status_code, 404)

    def test_hosts_duplicate(self):
        """Test creating duplicate host."""
        headers = self.get_auth_header()

        self.client.post("/api/hosts/", json={
            "hostname": "test.example.com",
            "username": "user",
            "password": "pass"
        }, headers=headers)

        response = self.client.post("/api/hosts/", json={
            "hostname": "test.example.com",
            "username": "user2",
            "password": "pass2"
        }, headers=headers)
        self.assertEqual(response.status_code, 409)

    def test_status(self):
        """Test status endpoint."""
        headers = self.get_auth_header()

        # Create a host first
        self.client.post("/api/hosts/", json={
            "hostname": "test.example.com",
            "username": "user",
            "password": "pass"
        }, headers=headers)

        response = self.client.get("/api/status/", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("current_ip", data)
        self.assertIn("hosts", data)
        self.assertEqual(len(data["hosts"]), 1)

    def test_history(self):
        """Test history endpoint."""
        headers = self.get_auth_header()

        # Create some history by creating a host
        self.client.post("/api/hosts/", json={
            "hostname": "test.example.com",
            "username": "user",
            "password": "pass"
        }, headers=headers)

        response = self.client.get("/api/history/", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("entries", data)
        self.assertIn("total", data)
        self.assertGreater(len(data["entries"]), 0)

    def test_history_pagination(self):
        """Test history pagination."""
        headers = self.get_auth_header()

        response = self.client.get("/api/history/?limit=10&offset=0", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["limit"], 10)
        self.assertEqual(data["offset"], 0)

    def test_settings(self):
        """Test settings endpoints."""
        headers = self.get_auth_header()

        # Initialize settings
        from infrastructure.database import SqliteRepository
        SqliteRepository().init_default_settings()

        # Get settings
        response = self.client.get("/api/settings/", headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("update_interval", data)
        self.assertIn("logger_level", data)

        # Update settings
        response = self.client.put("/api/settings/", json={
            "update_interval": 600,
            "logger_level": "DEBUG"
        }, headers=headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["update_interval"], 600)
        self.assertEqual(data["logger_level"], "DEBUG")

    def test_settings_validation(self):
        """Test settings validation."""
        headers = self.get_auth_header()

        # Invalid interval (too low)
        response = self.client.put("/api/settings/", json={
            "update_interval": 10
        }, headers=headers)
        self.assertEqual(response.status_code, 422)

        # Invalid log level
        response = self.client.put("/api/settings/", json={
            "logger_level": "INVALID"
        }, headers=headers)
        self.assertEqual(response.status_code, 422)

    def test_unauthorized_access(self):
        """Test accessing protected endpoints without auth."""
        response = self.client.get("/api/hosts/")
        self.assertEqual(response.status_code, 403)

        response = self.client.get("/api/status/")
        self.assertEqual(response.status_code, 403)

        response = self.client.get("/api/history/")
        self.assertEqual(response.status_code, 403)

    def test_health_check(self):
        """Test health check endpoint."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")


if __name__ == "__main__":
    unittest.main()
