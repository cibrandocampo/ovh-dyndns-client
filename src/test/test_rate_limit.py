"""Rate-limit tests for ``/api/auth/login`` and ``/api/auth/change-password`` (T010).

slowapi keeps in-memory counters keyed by the client IP that
``get_remote_address`` returns. Under FastAPI ``TestClient`` every request
comes from the same loopback address, so the bucket fills up exactly the
same way as a real attacker hammering one source. The autouse fixture in
``conftest.py`` resets counters between tests.
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


class TestLoginRateLimit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        cls.temp_db.close()
        os.environ["DATABASE_PATH"] = cls.temp_db.name
        os.environ["JWT_SECRET"] = "test-secret-rl"
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
            db.add(
                User(
                    username="alice",
                    password_hash=hash_password("right-password"),
                    must_change_password=False,
                )
            )

    def _login(self, password: str) -> int:
        return self.client.post(
            "/api/auth/login",
            json={"username": "alice", "password": password},
        ).status_code

    def test_login_first_5_attempts_not_rate_limited(self):
        """The 5/minute budget allows the first five attempts to reach the auth check."""
        for _ in range(5):
            self.assertEqual(self._login("wrong"), 401)

    def test_login_6th_attempt_is_429(self):
        for _ in range(5):
            self._login("wrong")
        self.assertEqual(self._login("wrong"), 429)

    def test_login_correct_credentials_still_consume_budget(self):
        """Successful logins also count — the limiter is unaware of outcome."""
        for _ in range(5):
            self.assertEqual(self._login("right-password"), 200)
        self.assertEqual(self._login("right-password"), 429)


class TestChangePasswordRateLimit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        cls.temp_db.close()
        os.environ["DATABASE_PATH"] = cls.temp_db.name
        os.environ["JWT_SECRET"] = "test-secret-rl-cp"
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
            db.add(
                User(
                    username="alice",
                    password_hash=hash_password("right-password"),
                    must_change_password=False,
                )
            )

    def _token(self) -> str:
        response = self.client.post(
            "/api/auth/login",
            json={"username": "alice", "password": "right-password"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()["access_token"]

    def test_change_password_11th_attempt_is_429(self):
        """The 10/minute budget allows ten requests before throttling kicks in."""
        token = self._token()
        headers = {"Authorization": f"Bearer {token}"}

        # 10 attempts with the wrong current password — each returns 400
        # and consumes one slot of the rate-limit bucket.
        for _ in range(10):
            r = self.client.post(
                "/api/auth/change-password",
                headers=headers,
                json={"current_password": "wrong", "new_password": "valid-newpw"},
            )
            self.assertEqual(r.status_code, 400)

        r = self.client.post(
            "/api/auth/change-password",
            headers=headers,
            json={"current_password": "wrong", "new_password": "valid-newpw"},
        )
        self.assertEqual(r.status_code, 429)


if __name__ == "__main__":
    unittest.main()
