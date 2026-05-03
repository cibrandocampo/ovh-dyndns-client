import os
import tempfile
import unittest

from cryptography.fernet import Fernet

from infrastructure.crypto import ENCRYPTED_PREFIX, encrypt_password
from infrastructure.database.database import (
    get_db_session,
    has_encrypted_hosts,
    init_db,
    migrate_plaintext_passwords,
)
from infrastructure.database.models import History, Host, Settings, State, User
from infrastructure.database.repository import SqliteRepository


class TestSqliteRepository(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up test database."""
        cls.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        cls.temp_db.close()
        os.environ["DATABASE_PATH"] = cls.temp_db.name
        os.environ["ENCRYPTION_KEY"] = Fernet.generate_key().decode("utf-8")
        init_db()

    @classmethod
    def tearDownClass(cls):
        """Clean up test database."""
        os.unlink(cls.temp_db.name)

    def setUp(self):
        """Clear all tables before each test."""
        with get_db_session() as db:
            db.query(History).delete()
            db.query(Host).delete()
            db.query(State).delete()
            db.query(Settings).delete()
            db.query(User).delete()

    def test_set_and_get_ip(self):
        """Test setting and getting IP address."""
        repo = SqliteRepository()

        # Initially no IP
        self.assertIsNone(repo.get_ip())

        # Set IP
        repo.set_ip("192.168.1.1")
        ip = repo.get_ip()
        self.assertEqual(str(ip), "192.168.1.1")

        # Update IP
        repo.set_ip("192.168.1.2")
        ip = repo.get_ip()
        self.assertEqual(str(ip), "192.168.1.2")

    def test_create_and_get_host(self):
        """Test creating and retrieving a host."""
        repo = SqliteRepository()

        # Create host
        host = repo.create_host("test.example.com", "testuser", "testpass")
        self.assertEqual(host["hostname"], "test.example.com")
        self.assertEqual(host["username"], "testuser")
        self.assertIsNotNone(host["id"])

        # Get host by ID
        retrieved = repo.get_host_by_id(host["id"])
        self.assertEqual(retrieved["hostname"], "test.example.com")
        self.assertEqual(retrieved["username"], "testuser")

    def test_get_hosts_for_controller(self):
        """Test get_hosts returns HostConfig objects."""
        repo = SqliteRepository()

        repo.create_host("host1.example.com", "user1", "pass1")
        repo.create_host("host2.example.com", "user2", "pass2")

        hosts = repo.get_hosts()
        self.assertEqual(len(hosts), 2)
        self.assertEqual(hosts[0].hostname, "host1.example.com")
        self.assertEqual(hosts[0].username, "user1")

    def test_update_host(self):
        """Test updating a host."""
        repo = SqliteRepository()

        host = repo.create_host("test.example.com", "testuser", "testpass")
        host_id = host["id"]

        # Update hostname
        updated = repo.update_host(host_id, hostname="updated.example.com")
        self.assertEqual(updated["hostname"], "updated.example.com")
        self.assertEqual(updated["username"], "testuser")

        # Update username
        updated = repo.update_host(host_id, username="newuser")
        self.assertEqual(updated["username"], "newuser")

    def test_delete_host(self):
        """Test deleting a host."""
        repo = SqliteRepository()

        host = repo.create_host("test.example.com", "testuser", "testpass")
        host_id = host["id"]

        # Delete host
        result = repo.delete_host(host_id)
        self.assertTrue(result)

        # Should not find host anymore
        retrieved = repo.get_host_by_id(host_id)
        self.assertIsNone(retrieved)

        # Delete non-existent host
        result = repo.delete_host(9999)
        self.assertFalse(result)

    def test_get_all_hosts(self):
        """Test getting all hosts."""
        repo = SqliteRepository()

        repo.create_host("host1.example.com", "user1", "pass1")
        repo.create_host("host2.example.com", "user2", "pass2")

        hosts = repo.get_all_hosts()
        self.assertEqual(len(hosts), 2)

    def test_update_host_status(self):
        """Test updating host status after DNS update."""
        repo = SqliteRepository()

        repo.create_host("test.example.com", "testuser", "testpass")

        # Update status - success
        repo.update_host_status("test.example.com", True)
        host = repo.get_all_hosts()[0]
        self.assertTrue(host["last_status"])
        self.assertIsNone(host["last_error"])

        # Update status - failure
        repo.update_host_status("test.example.com", False, "Connection timeout")
        host = repo.get_all_hosts()[0]
        self.assertFalse(host["last_status"])
        self.assertEqual(host["last_error"], "Connection timeout")

    def test_get_state(self):
        """Test getting state."""
        repo = SqliteRepository()

        # Initially empty
        state = repo.get_state()
        self.assertIsNone(state["current_ip"])

        # After setting IP
        repo.set_ip("10.0.0.1")
        state = repo.get_state()
        self.assertEqual(state["current_ip"], "10.0.0.1")
        self.assertIsNotNone(state["last_check"])

    def test_history(self):
        """Test history logging and retrieval."""
        repo = SqliteRepository()

        # Create some history entries
        repo.set_ip("192.168.1.1")
        repo.create_host("test.example.com", "user", "pass")
        repo.update_host_status("test.example.com", True)

        # Get history
        history = repo.get_history(limit=10)
        self.assertGreater(len(history), 0)

        # Check pagination
        count = repo.get_history_count()
        self.assertGreater(count, 0)

    def test_user_crud(self):
        """Test user creation and retrieval."""
        repo = SqliteRepository()

        # Initially no user
        self.assertFalse(repo.user_exists("testuser"))

        # Create user
        repo.create_user("testuser", "hashedpassword")
        self.assertTrue(repo.user_exists("testuser"))

        # Get user
        user = repo.get_user_by_username("testuser")
        self.assertIsNotNone(user)
        self.assertEqual(user["username"], "testuser")
        self.assertTrue(user["must_change_password"])

    def test_update_user_password(self):
        """Test updating user password."""
        repo = SqliteRepository()

        repo.create_user("testuser", "oldhash")

        # Update password
        result = repo.update_user_password("testuser", "newhash")
        self.assertTrue(result)

        # Verify must_change_password is now False
        self.assertFalse(repo.get_user_must_change_password("testuser"))

        # Update non-existent user
        result = repo.update_user_password("nonexistent", "hash")
        self.assertFalse(result)

    def test_settings(self):
        """Test settings management."""
        repo = SqliteRepository()

        # Get default settings
        repo.init_default_settings()
        settings = repo.get_settings()
        self.assertEqual(settings["update_interval"], 300)
        self.assertEqual(settings["logger_level"], "INFO")

        # Update settings
        updated = repo.update_settings(update_interval=600, logger_level="DEBUG")
        self.assertEqual(updated["update_interval"], 600)
        self.assertEqual(updated["logger_level"], "DEBUG")

        # Verify persistence
        settings = repo.get_settings()
        self.assertEqual(settings["update_interval"], 600)
        self.assertEqual(settings["logger_level"], "DEBUG")

    # ── Encryption + migration tests (T008) ───────────────────────────

    def test_create_host_persists_encrypted(self):
        """Stored password must carry the ciphertext prefix, not plaintext."""
        repo = SqliteRepository()
        repo.create_host("enc.example.com", "user", "plain-pass")

        with get_db_session() as db:
            row = db.query(Host).filter_by(hostname="enc.example.com").first()
            self.assertTrue(row.password.startswith(ENCRYPTED_PREFIX))
            self.assertNotIn("plain-pass", row.password)

    def test_get_hosts_returns_decrypted(self):
        """`get_hosts` must materialise the original password in HostConfig."""
        repo = SqliteRepository()
        repo.create_host("rt.example.com", "u", "round-trip-pass")

        hosts = repo.get_hosts()
        self.assertEqual(len(hosts), 1)
        self.assertEqual(hosts[0].password.get_secret_value(), "round-trip-pass")

    def test_update_host_re_encrypts(self):
        """`update_host` with a new password must replace the ciphertext."""
        repo = SqliteRepository()
        host = repo.create_host("upd.example.com", "u", "old-pass")
        with get_db_session() as db:
            old_ciphertext = db.query(Host).filter_by(id=host["id"]).first().password

        repo.update_host(host["id"], password="new-pass")

        with get_db_session() as db:
            new_ciphertext = db.query(Host).filter_by(id=host["id"]).first().password
        self.assertNotEqual(new_ciphertext, old_ciphertext)
        self.assertTrue(new_ciphertext.startswith(ENCRYPTED_PREFIX))

        # And the new value round-trips correctly.
        cfg = repo.get_host_by_hostname("upd.example.com")
        self.assertEqual(cfg.password.get_secret_value(), "new-pass")

    def test_migrate_plaintext_passwords_encrypts_legacy(self):
        """Rows with bare plaintext are upgraded; reads then return the original value."""
        # Insert a legacy plaintext row directly, bypassing the repository.
        with get_db_session() as db:
            db.add(Host(hostname="legacy.example.com", username="u", password="legacy-pass"))

        migrated = migrate_plaintext_passwords()
        self.assertEqual(migrated, 1)

        with get_db_session() as db:
            row = db.query(Host).filter_by(hostname="legacy.example.com").first()
            self.assertTrue(row.password.startswith(ENCRYPTED_PREFIX))

        cfg = SqliteRepository().get_host_by_hostname("legacy.example.com")
        self.assertEqual(cfg.password.get_secret_value(), "legacy-pass")

    def test_migrate_plaintext_passwords_idempotent(self):
        """Running the migration twice in a row leaves nothing extra to do."""
        with get_db_session() as db:
            db.add(Host(hostname="idem.example.com", username="u", password="x"))
            db.add(Host(hostname="already.example.com", username="u", password=encrypt_password("y")))

        first = migrate_plaintext_passwords()
        second = migrate_plaintext_passwords()
        self.assertEqual(first, 1)  # only the plaintext row migrated
        self.assertEqual(second, 0)

    # ── has_encrypted_hosts() (boot-time consistency check) ───────────

    def test_has_encrypted_hosts_empty_db(self):
        """Fresh database with no host rows returns False."""
        self.assertFalse(has_encrypted_hosts())

    def test_has_encrypted_hosts_only_plaintext(self):
        """Legacy plaintext-only rows do not trip the check."""
        with get_db_session() as db:
            db.add(Host(hostname="plain.example.com", username="u", password="plaintext"))
        self.assertFalse(has_encrypted_hosts())

    def test_has_encrypted_hosts_with_encrypted_row(self):
        """Any row carrying the `enc:v1:` prefix flips the check to True."""
        with get_db_session() as db:
            db.add(Host(hostname="enc.example.com", username="u", password=encrypt_password("p")))
        self.assertTrue(has_encrypted_hosts())


if __name__ == "__main__":
    unittest.main()
