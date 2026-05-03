"""End-to-end tests for the must_change_password enforcement (T009).

Each test sets up a temporary SQLite DB with a user whose
``must_change_password`` flag is configurable. Authenticates via the real
``/api/auth/login`` endpoint, then exercises every protected route to
confirm that the dependency split correctly blocks (403) or allows (200/204)
based on the flag.
"""

import os
import tempfile
import unittest

from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

from api.auth import hash_password
from api.main import create_app
from infrastructure.database.database import get_db_session, init_db
from infrastructure.database.models import History, Host, Settings, State, User


class TestMustChangePasswordEnforcement(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        cls.temp_db.close()
        os.environ["DATABASE_PATH"] = cls.temp_db.name
        os.environ["JWT_SECRET"] = "test-secret-mcp"
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

    def _create_user(self, must_change: bool) -> None:
        with get_db_session() as db:
            db.add(
                User(
                    username="alice",
                    password_hash=hash_password("initial-pass"),
                    must_change_password=must_change,
                )
            )

    def _login(self, password: str = "initial-pass") -> str:
        response = self.client.post(
            "/api/auth/login",
            json={"username": "alice", "password": password},
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()["access_token"]

    def _auth(self, token: str) -> dict:
        return {"Authorization": f"Bearer {token}"}

    # ── Blocked endpoints when flag is True ───────────────────────────

    def test_hosts_endpoint_blocked_when_must_change_password(self):
        self._create_user(must_change=True)
        token = self._login()

        response = self.client.get("/api/hosts/", headers=self._auth(token))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], "Password change required")

    def test_status_endpoint_blocked_when_must_change_password(self):
        self._create_user(must_change=True)
        token = self._login()

        response = self.client.get("/api/status/", headers=self._auth(token))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], "Password change required")

    def test_settings_put_blocked_when_must_change_password(self):
        self._create_user(must_change=True)
        token = self._login()

        response = self.client.put(
            "/api/settings/",
            headers=self._auth(token),
            json={"update_interval": 600},
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], "Password change required")

    def test_history_endpoint_blocked_when_must_change_password(self):
        self._create_user(must_change=True)
        token = self._login()

        response = self.client.get("/api/history/", headers=self._auth(token))
        self.assertEqual(response.status_code, 403)

    # ── Change-password endpoint MUST stay accessible ─────────────────

    def test_change_password_allowed_when_flag_true(self):
        self._create_user(must_change=True)
        token = self._login()

        response = self.client.post(
            "/api/auth/change-password",
            headers=self._auth(token),
            json={"current_password": "initial-pass", "new_password": "rotated-pass"},
        )
        self.assertEqual(response.status_code, 200, response.text)

    def test_change_password_clears_flag_and_token_unblocks(self):
        """After change, the SAME token (still within TTL) must work everywhere."""
        self._create_user(must_change=True)
        token = self._login()

        change = self.client.post(
            "/api/auth/change-password",
            headers=self._auth(token),
            json={"current_password": "initial-pass", "new_password": "rotated-pass"},
        )
        self.assertEqual(change.status_code, 200)

        # Same token, previously blocked endpoint, now allowed.
        response = self.client.get("/api/hosts/", headers=self._auth(token))
        self.assertEqual(response.status_code, 200)

    # ── Regression: user without the flag operates normally ──────────

    def test_user_without_flag_passes_all_endpoints(self):
        self._create_user(must_change=False)
        token = self._login()

        for path in ("/api/hosts/", "/api/status/", "/api/history/", "/api/settings/"):
            response = self.client.get(path, headers=self._auth(token))
            self.assertEqual(
                response.status_code,
                200,
                f"{path} expected 200, got {response.status_code}: {response.text}",
            )


if __name__ == "__main__":
    unittest.main()
