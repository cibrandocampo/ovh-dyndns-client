"""Security headers on every response, and a strict CSP on the app's own pages."""

import os
import tempfile
import unittest

from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

from api.main import create_app
from infrastructure.database.database import init_db


class TestSecurityHeaders(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        cls.temp_db.close()
        os.environ["DATABASE_PATH"] = cls.temp_db.name
        os.environ["JWT_SECRET"] = "test-secret-headers"
        os.environ["ENCRYPTION_KEY"] = Fernet.generate_key().decode("utf-8")
        init_db()
        cls.client = TestClient(create_app())

    @classmethod
    def tearDownClass(cls):
        os.unlink(cls.temp_db.name)

    def _csp(self, path):
        directives = self.client.get(path).headers["Content-Security-Policy"].split(";")
        return {d.split()[0]: d.split()[1:] for d in (d.strip() for d in directives) if d}

    def test_dashboard_only_runs_its_own_scripts(self):
        csp = self._csp("/")
        self.assertEqual(csp["default-src"], ["'self'"])
        self.assertEqual(csp["script-src"], ["'self'"])
        self.assertEqual(csp["object-src"], ["'none'"])

    def test_dashboard_cannot_be_framed(self):
        response = self.client.get("/")
        self.assertEqual(response.headers["X-Frame-Options"], "DENY")
        self.assertEqual(self._csp("/")["frame-ancestors"], ["'none'"])

    def test_every_response_disables_sniffing_and_referrer(self):
        for path in ("/", "/health", "/api/hosts/", "/static/js/app.js", "/missing"):
            with self.subTest(path=path):
                headers = self.client.get(path).headers
                self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
                self.assertEqual(headers["Referrer-Policy"], "no-referrer")

    def test_api_docs_keep_working_without_the_strict_csp(self):
        """Swagger UI loads its assets from a CDN and uses an inline script."""
        response = self.client.get("/docs")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("Content-Security-Policy", response.headers)
        self.assertEqual(response.headers["X-Frame-Options"], "DENY")


if __name__ == "__main__":
    unittest.main()
