import unittest
import logging
from typing import List, Optional
from pydantic import IPvAnyAddress

from domain.hostconfig import HostConfig
from application.controller import UpdateDnsController
from application.ports import IpProvider, DnsUpdater, IpStateStore, HostsRepository


# Fake implementations of the ports for testing
class FakeIpProvider(IpProvider):
    def __init__(self, ip: str = "192.168.1.1"):
        self._ip = IPvAnyAddress(ip)
        self.call_count = 0

    def get_public_ip(self) -> IPvAnyAddress:
        self.call_count += 1
        return self._ip

    def set_ip(self, ip: str) -> None:
        self._ip = IPvAnyAddress(ip)


class FakeIpProviderWithException(IpProvider):
    def __init__(self, exception: Exception):
        self._exception = exception

    def get_public_ip(self) -> IPvAnyAddress:
        raise self._exception


class FakeDnsUpdater(DnsUpdater):
    def __init__(self):
        self.calls: List[tuple] = []
        self._results: List[tuple] = []
        self._default_result = (True, None)

    def update_ip(self, host: HostConfig, ip: IPvAnyAddress) -> tuple:
        self.calls.append((host, ip))
        if self._results:
            return self._results.pop(0)
        return self._default_result

    def set_results(self, results: List[tuple]) -> None:
        """Set results as list of (success, error_message) tuples."""
        self._results = results.copy()

    def set_default_result(self, success: bool, error: str = None) -> None:
        self._default_result = (success, error)


class FakeIpStateStore(IpStateStore):
    def __init__(self, ip: Optional[str] = None):
        self._ip: Optional[IPvAnyAddress] = IPvAnyAddress(ip) if ip else None
        self.last_check_updated = False

    def get_ip(self) -> Optional[IPvAnyAddress]:
        return self._ip

    def set_ip(self, ip: IPvAnyAddress) -> None:
        self._ip = ip

    def update_last_check(self) -> None:
        self.last_check_updated = True


class FakeHostsRepository(HostsRepository):
    def __init__(self, hosts: Optional[List[HostConfig]] = None, pending_hosts: Optional[List[HostConfig]] = None):
        self._hosts = hosts or []
        self._pending_hosts = pending_hosts or []
        self.status_updates: List[tuple] = []

    def get_hosts(self) -> List[HostConfig]:
        return self._hosts

    def get_pending_hosts(self) -> List[HostConfig]:
        return self._pending_hosts

    def get_host_by_hostname(self, hostname: str) -> Optional[HostConfig]:
        for host in self._hosts:
            if host.hostname == hostname:
                return host
        return None

    def update_host_status(self, hostname: str, success: bool, error: str = None) -> None:
        self.status_updates.append((hostname, success, error))

    def set_hosts(self, hosts: List[HostConfig]) -> None:
        self._hosts = hosts

    def set_pending_hosts(self, hosts: List[HostConfig]) -> None:
        self._pending_hosts = hosts


class TestUpdateDnsController(unittest.TestCase):

    def setUp(self):
        """
        Sets up test environment with fake implementations.
        """
        self.ip_provider = FakeIpProvider()
        self.dns_updater = FakeDnsUpdater()
        self.ip_state = FakeIpStateStore()
        self.hosts_repo = FakeHostsRepository()
        self.logger = logging.getLogger("test")
        self.logger.setLevel(logging.DEBUG)

        self.controller = UpdateDnsController(
            ip_provider=self.ip_provider,
            dns_updater=self.dns_updater,
            ip_state=self.ip_state,
            hosts_repo=self.hosts_repo,
            logger=self.logger
        )

    def test_handler_ip_unchanged_no_pending_hosts(self):
        """
        Tests handler when IP hasn't changed and there are no pending hosts.
        Should skip update and not call dns_updater.
        """
        self.ip_provider.set_ip("192.168.1.1")
        self.ip_state.set_ip(IPvAnyAddress("192.168.1.1"))
        self.hosts_repo.set_pending_hosts([])

        self.controller.handler()

        self.assertEqual(self.ip_provider.call_count, 1)
        self.assertEqual(len(self.dns_updater.calls), 0)

    def test_handler_ip_unchanged_with_pending_hosts(self):
        """
        Tests handler when IP hasn't changed but there are pending hosts.
        Should update pending hosts.
        """
        self.ip_provider.set_ip("192.168.1.1")
        self.ip_state.set_ip(IPvAnyAddress("192.168.1.1"))

        pending_host = HostConfig(hostname="example.com", username="user", password="pass")
        self.hosts_repo.set_pending_hosts([pending_host])

        self.controller.handler()

        self.assertEqual(self.ip_provider.call_count, 1)
        self.assertEqual(len(self.dns_updater.calls), 1)
        self.assertEqual(self.dns_updater.calls[0][0], pending_host)
        self.assertEqual(str(self.dns_updater.calls[0][1]), "192.168.1.1")

    def test_handler_ip_changed(self):
        """
        Tests handler when IP has changed.
        Should update all hosts with the new IP.
        """
        self.ip_provider.set_ip("192.168.1.2")
        self.ip_state.set_ip(IPvAnyAddress("192.168.1.1"))

        host1 = HostConfig(hostname="example.com", username="user1", password="pass1")
        host2 = HostConfig(hostname="example2.com", username="user2", password="pass2")
        self.hosts_repo.set_hosts([host1, host2])

        self.controller.handler()

        self.assertEqual(self.ip_provider.call_count, 1)
        self.assertEqual(str(self.ip_state.get_ip()), "192.168.1.2")
        self.assertEqual(len(self.dns_updater.calls), 2)
        self.assertEqual(str(self.dns_updater.calls[0][1]), "192.168.1.2")

    def test_handler_first_run_no_stored_ip(self):
        """
        Tests handler on first run when no IP is stored yet.
        Should detect IP change and update all hosts.
        """
        self.ip_provider.set_ip("192.168.1.1")
        # ip_state has no IP (None by default)

        host1 = HostConfig(hostname="example.com", username="user1", password="pass1")
        self.hosts_repo.set_hosts([host1])

        self.controller.handler()

        self.assertEqual(str(self.ip_state.get_ip()), "192.168.1.1")
        self.assertEqual(len(self.dns_updater.calls), 1)

    def test_handler_ipify_exception(self):
        """
        Tests handler when IpProvider raises an exception.
        Should log error and raise RuntimeError.
        """
        ip_provider = FakeIpProviderWithException(Exception("Network error"))
        controller = UpdateDnsController(
            ip_provider=ip_provider,
            dns_updater=self.dns_updater,
            ip_state=self.ip_state,
            hosts_repo=self.hosts_repo,
            logger=self.logger
        )

        with self.assertRaises(RuntimeError) as context:
            controller.handler()

        self.assertEqual(str(context.exception), "DynDNS update failed")

    def test_handler_ip_changed_calls_all_hosts(self):
        """
        Tests handler when IP changes calls update on all hosts.
        """
        self.ip_provider.set_ip("192.168.1.2")
        self.ip_state.set_ip(IPvAnyAddress("192.168.1.1"))

        host1 = HostConfig(hostname="example.com", username="user1", password="pass1")
        host2 = HostConfig(hostname="example2.com", username="user2", password="pass2")
        self.hosts_repo.set_hosts([host1, host2])

        self.dns_updater.set_results([(True, None), (False, "Test error")])

        self.controller.handler()

        # IP should be stored
        self.assertEqual(str(self.ip_state.get_ip()), "192.168.1.2")
        # Both hosts should be called
        self.assertEqual(len(self.dns_updater.calls), 2)

    def test_handler_updates_pending_hosts_when_ip_unchanged(self):
        """
        Tests that pending hosts are updated when IP hasn't changed.
        """
        self.ip_provider.set_ip("192.168.1.1")
        self.ip_state.set_ip(IPvAnyAddress("192.168.1.1"))

        pending_host = HostConfig(hostname="pending.com", username="user", password="pass")
        self.hosts_repo.set_pending_hosts([pending_host])

        self.dns_updater.set_default_result(True, None)

        self.controller.handler()

        self.assertEqual(len(self.dns_updater.calls), 1)
        self.assertEqual(self.dns_updater.calls[0][0].hostname, "pending.com")

    def test_handler_multiple_pending_hosts(self):
        """
        Tests handler with multiple pending hosts.
        """
        self.ip_provider.set_ip("192.168.1.1")
        self.ip_state.set_ip(IPvAnyAddress("192.168.1.1"))

        pending_host1 = HostConfig(hostname="pending1.com", username="user1", password="pass1")
        pending_host2 = HostConfig(hostname="pending2.com", username="user2", password="pass2")
        self.hosts_repo.set_pending_hosts([pending_host1, pending_host2])

        self.controller.handler()

        self.assertEqual(len(self.dns_updater.calls), 2)

    def test_update_hosts_ip_success(self):
        """
        Tests update_hosts_ip when all hosts update successfully.
        """
        host1 = HostConfig(hostname="example.com", username="user1", password="pass1")
        host2 = HostConfig(hostname="example2.com", username="user2", password="pass2")
        hosts = [host1, host2]

        ip = IPvAnyAddress("192.168.1.1")
        self.controller.update_hosts_ip(hosts, ip)

        self.assertEqual(len(self.dns_updater.calls), 2)

    def test_update_hosts_ip_calls_updater_for_each_host(self):
        """
        Tests update_hosts_ip calls dns_updater for each host.
        """
        host1 = HostConfig(hostname="example.com", username="user1", password="pass1")
        host2 = HostConfig(hostname="example2.com", username="user2", password="pass2")
        hosts = [host1, host2]

        self.dns_updater.set_results([(True, None), (False, "Test error")])

        ip = IPvAnyAddress("192.168.1.1")
        self.controller.update_hosts_ip(hosts, ip)

        self.assertEqual(len(self.dns_updater.calls), 2)

    def test_update_hosts_ip_empty_list(self):
        """
        Tests update_hosts_ip with an empty host list.
        """
        hosts = []
        ip = IPvAnyAddress("192.168.1.1")
        self.controller.update_hosts_ip(hosts, ip)

        self.assertEqual(len(self.dns_updater.calls), 0)

    def test_update_hosts_ip_passes_correct_ip_to_updater(self):
        """
        Tests that update_hosts_ip passes the correct IP to the dns_updater.
        """
        host = HostConfig(hostname="example.com", username="user", password="pass")
        ip = IPvAnyAddress("10.0.0.1")
        self.controller.update_hosts_ip([host], ip)

        self.assertEqual(len(self.dns_updater.calls), 1)
        self.assertEqual(str(self.dns_updater.calls[0][1]), "10.0.0.1")

    def test_handler_with_ipv6(self):
        """
        Tests handler with IPv6 address.
        """
        self.ip_provider.set_ip("2001:db8::1")
        # No stored IP yet

        host = HostConfig(hostname="example.com", username="user", password="pass")
        self.hosts_repo.set_hosts([host])

        self.controller.handler()

        self.assertEqual(str(self.ip_state.get_ip()), "2001:db8::1")
        self.assertEqual(str(self.dns_updater.calls[0][1]), "2001:db8::1")


if __name__ == "__main__":
    unittest.main()
