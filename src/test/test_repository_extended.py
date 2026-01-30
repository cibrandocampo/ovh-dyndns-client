import os
import tempfile
import unittest
from datetime import datetime, timezone

from infrastructure.database.database import init_db, get_db_session
from infrastructure.database.repository import SqliteRepository
from infrastructure.database.models import User, Host, State, History, Settings


class TestSqliteRepositoryExtended(unittest.TestCase):
    """Extended tests for SqliteRepository edge cases."""

    @classmethod
    def setUpClass(cls):
        """Set up test database."""
        cls.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        cls.temp_db.close()
        os.environ['DATABASE_PATH'] = cls.temp_db.name
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

    # IP State tests

    def test_set_ip_creates_history_entry(self):
        """Test that setting IP creates a history entry."""
        repo = SqliteRepository()
        repo.set_ip("192.168.1.1")

        history = repo.get_history(limit=10)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["action"], "ip_changed")
        self.assertIn("192.168.1.1", history[0]["details"])

    def test_set_ip_same_value_no_history(self):
        """Test that setting same IP doesn't create duplicate history."""
        repo = SqliteRepository()
        repo.set_ip("192.168.1.1")
        repo.set_ip("192.168.1.1")

        history = repo.get_history(limit=10)
        ip_changed_entries = [h for h in history if h["action"] == "ip_changed"]
        self.assertEqual(len(ip_changed_entries), 1)

    def test_set_ip_ipv6(self):
        """Test setting IPv6 address."""
        repo = SqliteRepository()
        repo.set_ip("2001:db8::1")

        ip = repo.get_ip()
        self.assertEqual(str(ip), "2001:db8::1")

    def test_get_state_initial(self):
        """Test get_state with no state set."""
        repo = SqliteRepository()
        state = repo.get_state()
        self.assertIsNone(state["current_ip"])
        self.assertIsNone(state["last_check"])

    def test_get_state_with_ip(self):
        """Test get_state after IP is set."""
        repo = SqliteRepository()
        repo.set_ip("10.0.0.1")
        state = repo.get_state()
        self.assertEqual(state["current_ip"], "10.0.0.1")
        self.assertIsNotNone(state["last_check"])

    # Host tests

    def test_get_host_by_hostname_not_found(self):
        """Test getting host that doesn't exist."""
        repo = SqliteRepository()
        host = repo.get_host_by_id(99999)
        self.assertIsNone(host)

    def test_create_host_creates_history(self):
        """Test that creating host creates history entry."""
        repo = SqliteRepository()
        repo.create_host("test.com", "user", "pass")

        history = repo.get_history(limit=10)
        host_created = [h for h in history if h["action"] == "host_created"]
        self.assertEqual(len(host_created), 1)

    def test_delete_host_creates_history(self):
        """Test that deleting host creates history entry."""
        repo = SqliteRepository()
        host = repo.create_host("test.com", "user", "pass")
        repo.delete_host(host["id"])

        history = repo.get_history(limit=10)
        host_deleted = [h for h in history if h["action"] == "host_deleted"]
        self.assertEqual(len(host_deleted), 1)

    def test_update_host_creates_history(self):
        """Test that updating host creates history entry."""
        repo = SqliteRepository()
        host = repo.create_host("test.com", "user", "pass")
        repo.update_host(host["id"], hostname="updated.com")

        history = repo.get_history(limit=10)
        host_updated = [h for h in history if h["action"] == "host_updated"]
        self.assertEqual(len(host_updated), 1)

    def test_update_host_nonexistent(self):
        """Test updating non-existent host returns None."""
        repo = SqliteRepository()
        result = repo.update_host(99999, hostname="test.com")
        self.assertIsNone(result)

    def test_update_host_password_only(self):
        """Test updating only password."""
        repo = SqliteRepository()
        host = repo.create_host("test.com", "user", "oldpass")
        updated = repo.update_host(host["id"], password="newpass")
        self.assertIsNotNone(updated)

        # Verify password was updated via get_hosts
        hosts = repo.get_hosts()
        self.assertEqual(hosts[0].password.get_secret_value(), "newpass")

    def test_update_host_status_success(self):
        """Test updating host status on success."""
        repo = SqliteRepository()
        repo.create_host("test.com", "user", "pass")
        repo.update_host_status("test.com", True)

        hosts = repo.get_all_hosts()
        self.assertTrue(hosts[0]["last_status"])
        self.assertIsNone(hosts[0]["last_error"])

    def test_update_host_status_failure(self):
        """Test updating host status on failure."""
        repo = SqliteRepository()
        repo.create_host("test.com", "user", "pass")
        repo.update_host_status("test.com", False, "Connection refused")

        hosts = repo.get_all_hosts()
        self.assertFalse(hosts[0]["last_status"])
        self.assertEqual(hosts[0]["last_error"], "Connection refused")

    def test_update_host_status_nonexistent(self):
        """Test updating status for non-existent host does nothing."""
        repo = SqliteRepository()
        # Should not raise
        repo.update_host_status("nonexistent.com", True)

    def test_get_hosts_returns_hostconfig(self):
        """Test that get_hosts returns HostConfig objects."""
        repo = SqliteRepository()
        repo.create_host("test.com", "user", "pass")

        hosts = repo.get_hosts()
        self.assertEqual(len(hosts), 1)
        self.assertEqual(hosts[0].hostname, "test.com")
        self.assertEqual(hosts[0].username, "user")
        # Password should be SecretStr
        self.assertEqual(hosts[0].password.get_secret_value(), "pass")

    def test_get_all_hosts_returns_dicts(self):
        """Test that get_all_hosts returns dictionaries."""
        repo = SqliteRepository()
        repo.create_host("test.com", "user", "pass")

        hosts = repo.get_all_hosts()
        self.assertEqual(len(hosts), 1)
        self.assertIsInstance(hosts[0], dict)
        self.assertIn("id", hosts[0])
        self.assertIn("hostname", hosts[0])
        # Password should NOT be in get_all_hosts
        self.assertNotIn("password", hosts[0])

    # History tests

    def test_get_history_ordering(self):
        """Test that history is ordered by timestamp descending."""
        repo = SqliteRepository()
        repo.set_ip("192.168.1.1")
        repo.set_ip("192.168.1.2")
        repo.set_ip("192.168.1.3")

        history = repo.get_history(limit=10)
        # Most recent should be first
        self.assertIn("192.168.1.3", history[0]["details"])

    def test_get_history_pagination(self):
        """Test history pagination."""
        repo = SqliteRepository()
        # Create multiple entries
        for i in range(10):
            repo.set_ip(f"192.168.1.{i}")

        # Get first page
        page1 = repo.get_history(limit=3, offset=0)
        self.assertEqual(len(page1), 3)

        # Get second page
        page2 = repo.get_history(limit=3, offset=3)
        self.assertEqual(len(page2), 3)

        # Entries should be different
        self.assertNotEqual(page1[0]["id"], page2[0]["id"])

    def test_get_history_count(self):
        """Test history count."""
        repo = SqliteRepository()
        repo.set_ip("192.168.1.1")
        repo.create_host("test.com", "user", "pass")

        count = repo.get_history_count()
        self.assertEqual(count, 2)

    # User tests

    def test_create_user_must_change_password_default(self):
        """Test that new users must change password by default."""
        repo = SqliteRepository()
        repo.create_user("testuser", "hashedpass")

        user = repo.get_user_by_username("testuser")
        self.assertTrue(user["must_change_password"])

    def test_get_user_by_username_not_found(self):
        """Test getting non-existent user."""
        repo = SqliteRepository()
        user = repo.get_user_by_username("nonexistent")
        self.assertIsNone(user)

    def test_update_user_password_clears_must_change(self):
        """Test that updating password clears must_change_password."""
        repo = SqliteRepository()
        repo.create_user("testuser", "oldhash")

        # Initially must change
        self.assertTrue(repo.get_user_must_change_password("testuser"))

        # After update, should be False
        repo.update_user_password("testuser", "newhash")
        self.assertFalse(repo.get_user_must_change_password("testuser"))

    def test_get_user_must_change_password_nonexistent(self):
        """Test must_change_password for non-existent user."""
        repo = SqliteRepository()
        result = repo.get_user_must_change_password("nonexistent")
        self.assertFalse(result)

    # Settings tests

    def test_get_settings_default(self):
        """Test getting default settings."""
        repo = SqliteRepository()
        settings = repo.get_settings()
        self.assertEqual(settings["update_interval"], 300)
        self.assertEqual(settings["logger_level"], "INFO")

    def test_update_settings_creates_if_not_exists(self):
        """Test that update_settings creates settings if they don't exist."""
        repo = SqliteRepository()
        settings = repo.update_settings(update_interval=600)
        self.assertEqual(settings["update_interval"], 600)

    def test_update_settings_partial(self):
        """Test partial settings update."""
        repo = SqliteRepository()
        repo.init_default_settings()

        # Update only interval
        settings = repo.update_settings(update_interval=900)
        self.assertEqual(settings["update_interval"], 900)
        self.assertEqual(settings["logger_level"], "INFO")

        # Update only level
        settings = repo.update_settings(logger_level="DEBUG")
        self.assertEqual(settings["update_interval"], 900)
        self.assertEqual(settings["logger_level"], "DEBUG")

    def test_update_settings_creates_history(self):
        """Test that updating settings creates history entry."""
        repo = SqliteRepository()
        repo.update_settings(update_interval=600)

        history = repo.get_history(limit=10)
        settings_updated = [h for h in history if h["action"] == "settings_updated"]
        self.assertEqual(len(settings_updated), 1)

    def test_init_default_settings_idempotent(self):
        """Test that init_default_settings is idempotent."""
        repo = SqliteRepository()
        repo.init_default_settings()
        repo.update_settings(update_interval=600)
        repo.init_default_settings()  # Should not overwrite

        settings = repo.get_settings()
        self.assertEqual(settings["update_interval"], 600)


if __name__ == "__main__":
    unittest.main()
