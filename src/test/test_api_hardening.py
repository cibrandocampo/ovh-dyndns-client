"""API hardening tests: input validation, error handling, auth edge cases
and non-blocking trigger endpoints."""

import os
import tempfile
import threading
import unittest
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from api.auth import hash_password
from api.main import create_app
from infrastructure.database.database import get_db_session, init_db
from infrastructure.database.models import History, Host, Settings, State, User


class _ApiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        cls.temp_db.close()
        os.environ["DATABASE_PATH"] = cls.temp_db.name
        os.environ["JWT_SECRET"] = "test-secret-key-hardening"
        from cryptography.fernet import Fernet

        os.environ["ENCRYPTION_KEY"] = Fernet.generate_key().decode("utf-8")
        init_db()
        cls.app = create_app()
        cls.client = TestClient(cls.app)

    @classmethod
    def tearDownClass(cls):
        os.unlink(cls.temp_db.name)

    def setUp(self):
        with get_db_session() as db:
            db.query(History).delete()
            db.query(Host).delete()
            db.query(State).delete()
            db.query(Settings).delete()
            db.query(User).delete()
            db.add(User(username="testuser", password_hash=hash_password("testpass"), must_change_password=False))

    def login(self, password="testpass"):
        return self.client.post("/api/auth/login", json={"username": "testuser", "password": password})

    def auth_header(self):
        return {"Authorization": f"Bearer {self.login().json()['access_token']}"}

    def create_host(self, headers, hostname="a.example.com"):
        response = self.client.post(
            "/api/hosts/", json={"hostname": hostname, "username": "user", "password": "pass"}, headers=headers
        )
        self.assertEqual(response.status_code, 201)
        return response.json()


class TestHostInputValidation(_ApiTestCase):
    INVALID_HOSTNAMES = [
        "",
        "a.example.com&myip=1.2.3.4",
        "a.example.com#frag",
        "a.example.com/path",
        "has space.example.com",
        "-leading.example.com",
        "trailing-.example.com",
        "nodot",
        "x');alert(1)//.example.com",
        "a" * 64 + ".example.com",
    ]

    def test_create_rejects_invalid_hostnames(self):
        headers = self.auth_header()
        for hostname in self.INVALID_HOSTNAMES:
            with self.subTest(hostname=hostname):
                response = self.client.post(
                    "/api/hosts/", json={"hostname": hostname, "username": "user", "password": "pass"}, headers=headers
                )
                self.assertEqual(response.status_code, 422)

    def test_update_rejects_invalid_hostnames(self):
        headers = self.auth_header()
        host_id = self.create_host(headers)["id"]
        for hostname in self.INVALID_HOSTNAMES:
            with self.subTest(hostname=hostname):
                response = self.client.put(f"/api/hosts/{host_id}", json={"hostname": hostname}, headers=headers)
                self.assertEqual(response.status_code, 422)

    def test_create_accepts_valid_hostnames(self):
        headers = self.auth_header()
        for hostname in ["home.example.com", "Sub-1.My-Domain.es", "xn--bcher-kva.example"]:
            with self.subTest(hostname=hostname):
                self.create_host(headers, hostname=hostname)

    def test_create_rejects_empty_credentials(self):
        headers = self.auth_header()
        for field in ("username", "password"):
            with self.subTest(field=field):
                body = {"hostname": "a.example.com", "username": "user", "password": "pass", field: ""}
                response = self.client.post("/api/hosts/", json=body, headers=headers)
                self.assertEqual(response.status_code, 422)

    def test_update_rejects_empty_credentials(self):
        headers = self.auth_header()
        host_id = self.create_host(headers)["id"]
        for field in ("username", "password"):
            with self.subTest(field=field):
                response = self.client.put(f"/api/hosts/{host_id}", json={field: ""}, headers=headers)
                self.assertEqual(response.status_code, 422)


class TestHostConflicts(_ApiTestCase):
    def test_rename_to_existing_hostname_returns_409(self):
        headers = self.auth_header()
        self.create_host(headers, hostname="a.example.com")
        second_id = self.create_host(headers, hostname="b.example.com")["id"]

        response = self.client.put(f"/api/hosts/{second_id}", json={"hostname": "a.example.com"}, headers=headers)

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["detail"], "Host with hostname 'a.example.com' already exists")

    def test_unexpected_create_error_does_not_leak_details(self):
        from unittest.mock import patch

        headers = self.auth_header()
        with patch("api.routers.hosts.SqliteRepository.create_host", side_effect=RuntimeError("db at /secret/path")):
            response = self.client.post(
                "/api/hosts/",
                json={"hostname": "a.example.com", "username": "user", "password": "pass"},
                headers=headers,
            )

        self.assertEqual(response.status_code, 500)
        self.assertNotIn("/secret/path", response.text)


class TestTriggerDoesNotBlockServer(_ApiTestCase):
    """A slow DNS update must not freeze the rest of the API."""

    def _assert_health_responds_while_blocked(self, path, controller):
        from api.routers.status import set_controller

        set_controller(controller)
        try:
            with TestClient(self.app) as client:
                headers = self.auth_header()
                trigger = threading.Thread(target=lambda: client.post(path, headers=headers))
                trigger.start()
                self.assertTrue(self.entered.wait(5), "controller was never called")

                health_status = []
                probe = threading.Thread(target=lambda: health_status.append(client.get("/health").status_code))
                probe.start()
                probe.join(timeout=2)
                health_answered = not probe.is_alive()

                self.release.set()
                trigger.join(timeout=10)
                probe.join(timeout=10)

            self.assertTrue(health_answered, "/health was blocked while the DNS update was running")
            self.assertEqual(health_status, [200])
        finally:
            set_controller(None)

    def setUp(self):
        super().setUp()
        self.entered = threading.Event()
        self.release = threading.Event()

    def _slow(self, *result):
        def call(*_args):
            self.entered.set()
            self.release.wait(10)
            return result or None

        return call

    def test_trigger_all_runs_off_the_event_loop(self):
        controller = MagicMock()
        controller.handler.side_effect = self._slow()
        self._assert_health_responds_while_blocked("/api/status/trigger", controller)

    def test_trigger_host_runs_off_the_event_loop(self):
        controller = MagicMock()
        controller.force_update_host.side_effect = self._slow(True, "ok")
        self._assert_health_responds_while_blocked("/api/status/trigger/a.example.com", controller)


class TestLongPasswords(_ApiTestCase):
    """bcrypt rejects inputs over 72 bytes; the API must not turn that into a 500."""

    def test_login_with_password_over_72_bytes_returns_401(self):
        response = self.login(password="x" * 73)
        self.assertEqual(response.status_code, 401)

    def test_change_password_rejects_new_password_over_72_bytes(self):
        response = self.client.post(
            "/api/auth/change-password",
            json={"current_password": "testpass", "new_password": "ñ" * 37},  # 74 bytes in UTF-8
            headers=self.auth_header(),
        )
        self.assertEqual(response.status_code, 422)

    def test_change_password_with_current_password_over_72_bytes_returns_400(self):
        response = self.client.post(
            "/api/auth/change-password",
            json={"current_password": "x" * 73, "new_password": "newpass123"},
            headers=self.auth_header(),
        )
        self.assertEqual(response.status_code, 400)


class TestPasswordChangeRevokesTokens(_ApiTestCase):
    def _change_password(self, headers):
        response = self.client.post(
            "/api/auth/change-password",
            json={"current_password": "testpass", "new_password": "newpass123"},
            headers=headers,
        )
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_old_token_is_rejected_after_password_change(self):
        headers = self.auth_header()
        self._change_password(headers)

        response = self.client.get("/api/hosts/", headers=headers)
        self.assertEqual(response.status_code, 401)

    def test_change_password_returns_a_working_token(self):
        body = self._change_password(self.auth_header())

        response = self.client.get("/api/hosts/", headers={"Authorization": f"Bearer {body['access_token']}"})
        self.assertEqual(response.status_code, 200)

    def test_token_for_deleted_user_is_rejected(self):
        headers = self.auth_header()
        with get_db_session() as db:
            db.query(User).delete()

        response = self.client.get("/api/hosts/", headers=headers)
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
