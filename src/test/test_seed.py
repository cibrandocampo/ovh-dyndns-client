"""Tests for `scripts/seed.py`.

The seed lives outside ``src/`` (it's a developer tool, not production
code), so the test prepends the project's ``scripts/`` directory to
``sys.path`` before importing. Each test class isolates a tmp SQLite DB
and a generated ``ENCRYPTION_KEY`` so the seed's ``encrypt_password``
calls do not write to ``/app/data``.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

from cryptography.fernet import Fernet

# `scripts/seed.py` lives at <project>/scripts/seed.py. Inside the dev
# container that resolves to /scripts/seed.py via the bind mount. From
# `src/test/test_seed.py`, parents[2] is the project root in either
# context.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))


class TestSeed(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        cls.temp_db.close()
        os.environ["DATABASE_PATH"] = cls.temp_db.name
        os.environ["ENCRYPTION_KEY"] = Fernet.generate_key().decode("utf-8")

    @classmethod
    def tearDownClass(cls):
        os.unlink(cls.temp_db.name)

    def setUp(self):
        # Lazy import inside setUp so the engine binds to our tmp DB after
        # the env var has been set in setUpClass.
        from infrastructure.database.database import get_db_session, init_db
        from infrastructure.database.models import History, Host, Settings, State, User

        init_db()
        with get_db_session() as db:
            db.query(History).delete()
            db.query(Host).delete()
            db.query(State).delete()
            db.query(Settings).delete()
            db.query(User).delete()

    def _counts(self) -> dict:
        from infrastructure.database.database import get_db_session
        from infrastructure.database.models import History, Host, Settings, State, User

        with get_db_session() as db:
            return {
                "users": db.query(User).count(),
                "hosts": db.query(Host).count(),
                "history": db.query(History).count(),
                "state": db.query(State).count(),
                "settings": db.query(Settings).count(),
            }

    def test_seed_creates_expected_rows(self):
        import seed

        seed.seed(reset=False)
        counts = self._counts()
        self.assertEqual(counts["users"], 1)
        self.assertEqual(counts["hosts"], 5)
        self.assertEqual(counts["state"], 1)
        self.assertEqual(counts["settings"], 1)
        # set_ip + 5 host_created + 4 host_updated/failed + len(HISTORY_EVENTS)
        # ≥ 25 rows so the paginated view (limit=20) shows two pages.
        self.assertGreaterEqual(counts["history"], 25)

    def test_admin_must_change_password_is_false(self):
        import seed

        from infrastructure.database.database import get_db_session
        from infrastructure.database.models import User

        seed.seed(reset=False)
        with get_db_session() as db:
            admin = db.query(User).filter_by(username="admin").first()
            self.assertIsNotNone(admin)
            self.assertFalse(admin.must_change_password)

    def test_includes_failed_host(self):
        import seed

        from infrastructure.database.database import get_db_session
        from infrastructure.database.models import Host

        seed.seed(reset=False)
        with get_db_session() as db:
            failed = db.query(Host).filter_by(last_status=False).all()
            self.assertGreaterEqual(len(failed), 1)
            self.assertIsNotNone(failed[0].last_error)

    def test_includes_pending_host(self):
        import seed

        from infrastructure.database.database import get_db_session
        from infrastructure.database.models import Host

        seed.seed(reset=False)
        with get_db_session() as db:
            pending = db.query(Host).filter(Host.last_status.is_(None)).all()
            self.assertGreaterEqual(len(pending), 1)

    def test_refuses_to_overwrite_without_reset(self):
        import seed

        seed.seed(reset=False)
        with self.assertRaises(SystemExit):
            seed.seed(reset=False)

    def test_reset_wipes_and_reseeds(self):
        import seed

        seed.seed(reset=False)
        first = self._counts()
        seed.seed(reset=True)
        second = self._counts()
        # All counts identical after reset — no leftovers, no doubles.
        self.assertEqual(first["users"], second["users"])
        self.assertEqual(first["hosts"], second["hosts"])
        self.assertEqual(first["state"], second["state"])
        self.assertEqual(first["history"], second["history"])
        self.assertEqual(first["settings"], second["settings"])


if __name__ == "__main__":
    unittest.main()
