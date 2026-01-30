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
        self._results: List[bool] = []
        self._default_result = True

    def update_ip(self, host: HostConfig, ip: IPvAnyAddress) -> bool:
        self.calls.append((host, ip))
        if self._results:
            return self._results.pop(0)
        return self._default_result

    def set_results(self, results: List[bool]) -> None:
        self._results = results.copy()

    def set_default_result(self, result: bool) -> None:
        self._default_result = result


class FakeIpStateStore(IpStateStore):
    def __init__(self, ip: Optional[str] = None):
        self._ip: Optional[IPvAnyAddress] = IPvAnyAddress(ip) if ip else None

    def get_ip(self) -> Optional[IPvAnyAddress]:
        return self._ip

    def set_ip(self, ip: IPvAnyAddress) -> None:
        self._ip = ip


class FakeHostsRepository(HostsRepository):
    def __init__(self, hosts: Optional[List[HostConfig]] = None):
        self._hosts = hosts or []

    def get_hosts(self) -> List[HostConfig]:
        return self._hosts

    def set_hosts(self, hosts: List[HostConfig]) -> None:
        self._hosts = hosts


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

    def test_handler_ip_unchanged_no_failed_hosts(self):
        """
        Tests handler when IP hasn't changed and there are no failed hosts.
        Should skip update and not call dns_updater.
        """
        self.ip_provider.set_ip("192.168.1.1")
        self.ip_state.set_ip(IPvAnyAddress("192.168.1.1"))

        self.controller.handler()

        self.assertEqual(self.ip_provider.call_count, 1)
        self.assertEqual(len(self.dns_updater.calls), 0)

    def test_handler_ip_unchanged_with_failed_hosts(self):
        """
        Tests handler when IP hasn't changed but there are failed hosts to retry.
        Should retry failed hosts.
        """
        self.ip_provider.set_ip("192.168.1.1")
        self.ip_state.set_ip(IPvAnyAddress("192.168.1.1"))

        failed_host = HostConfig(hostname="example.com", username="user", password="pass")
        self.controller.failed_hosts = [failed_host]

        self.controller.handler()

        self.assertEqual(self.ip_provider.call_count, 1)
        self.assertEqual(len(self.dns_updater.calls), 1)
        self.assertEqual(self.dns_updater.calls[0][0], failed_host)
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

    def test_handler_ip_changed_with_update_failure(self):
        """
        Tests handler when IP changes but some hosts fail to update.
        Failed hosts should be tracked for retry on next run.
        """
        self.ip_provider.set_ip("192.168.1.2")
        self.ip_state.set_ip(IPvAnyAddress("192.168.1.1"))

        host1 = HostConfig(hostname="example.com", username="user1", password="pass1")
        host2 = HostConfig(hostname="example2.com", username="user2", password="pass2")
        self.hosts_repo.set_hosts([host1, host2])

        # First host succeeds, second fails
        self.dns_updater.set_results([True, False])

        self.controller.handler()

        # IP should be stored
        self.assertEqual(str(self.ip_state.get_ip()), "192.168.1.2")
        # Second host should be in failed_hosts
        self.assertEqual(len(self.controller.failed_hosts), 1)
        self.assertEqual(self.controller.failed_hosts[0].hostname, "example2.com")

    def test_handler_retry_failed_hosts_success(self):
        """
        Tests that failed hosts are successfully retried when IP hasn't changed.
        """
        self.ip_provider.set_ip("192.168.1.1")
        self.ip_state.set_ip(IPvAnyAddress("192.168.1.1"))

        failed_host = HostConfig(hostname="failed.com", username="user", password="pass")
        self.controller.failed_hosts = [failed_host]

        # Retry succeeds
        self.dns_updater.set_default_result(True)

        self.controller.handler()

        # failed_hosts should be cleared after successful retry
        self.assertEqual(len(self.controller.failed_hosts), 0)

    def test_handler_retry_failed_hosts_still_fails(self):
        """
        Tests that failed hosts remain in the list if retry fails.
        """
        self.ip_provider.set_ip("192.168.1.1")
        self.ip_state.set_ip(IPvAnyAddress("192.168.1.1"))

        failed_host = HostConfig(hostname="failed.com", username="user", password="pass")
        self.controller.failed_hosts = [failed_host]

        # Retry fails again
        self.dns_updater.set_default_result(False)

        self.controller.handler()

        # Host should still be in failed_hosts
        self.assertEqual(len(self.controller.failed_hosts), 1)
        self.assertEqual(self.controller.failed_hosts[0].hostname, "failed.com")

    def test_handler_multiple_failed_hosts_partial_retry_success(self):
        """
        Tests retry with multiple failed hosts where only some succeed.
        """
        self.ip_provider.set_ip("192.168.1.1")
        self.ip_state.set_ip(IPvAnyAddress("192.168.1.1"))

        failed_host1 = HostConfig(hostname="failed1.com", username="user1", password="pass1")
        failed_host2 = HostConfig(hostname="failed2.com", username="user2", password="pass2")
        self.controller.failed_hosts = [failed_host1, failed_host2]

        # First succeeds, second fails
        self.dns_updater.set_results([True, False])

        self.controller.handler()

        # Only second host should remain failed
        self.assertEqual(len(self.controller.failed_hosts), 1)
        self.assertEqual(self.controller.failed_hosts[0].hostname, "failed2.com")

    def test_update_hosts_ip_success(self):
        """
        Tests update_hosts_ip when all hosts update successfully.
        Should clear failed_hosts.
        """
        host1 = HostConfig(hostname="example.com", username="user1", password="pass1")
        host2 = HostConfig(hostname="example2.com", username="user2", password="pass2")
        hosts = [host1, host2]

        ip = IPvAnyAddress("192.168.1.1")
        self.controller.update_hosts_ip(hosts, ip)

        self.assertEqual(len(self.dns_updater.calls), 2)
        self.assertEqual(len(self.controller.failed_hosts), 0)

    def test_update_hosts_ip_partial_failure(self):
        """
        Tests update_hosts_ip when some hosts fail to update.
        Should track failed hosts.
        """
        host1 = HostConfig(hostname="example.com", username="user1", password="pass1")
        host2 = HostConfig(hostname="example2.com", username="user2", password="pass2")
        hosts = [host1, host2]

        self.dns_updater.set_results([True, False])

        ip = IPvAnyAddress("192.168.1.1")
        self.controller.update_hosts_ip(hosts, ip)

        self.assertEqual(len(self.dns_updater.calls), 2)
        self.assertEqual(len(self.controller.failed_hosts), 1)
        self.assertEqual(self.controller.failed_hosts[0].hostname, "example2.com")

    def test_update_hosts_ip_all_fail(self):
        """
        Tests update_hosts_ip when all hosts fail to update.
        """
        host1 = HostConfig(hostname="example.com", username="user1", password="pass1")
        host2 = HostConfig(hostname="example2.com", username="user2", password="pass2")
        hosts = [host1, host2]

        self.dns_updater.set_default_result(False)

        ip = IPvAnyAddress("192.168.1.1")
        self.controller.update_hosts_ip(hosts, ip)

        self.assertEqual(len(self.dns_updater.calls), 2)
        self.assertEqual(len(self.controller.failed_hosts), 2)

    def test_update_hosts_ip_clears_previous_failures(self):
        """
        Tests that update_hosts_ip clears previous failed hosts before processing.
        """
        previous_failed = HostConfig(hostname="old.com", username="user", password="pass")
        self.controller.failed_hosts = [previous_failed]

        host1 = HostConfig(hostname="example.com", username="user1", password="pass1")
        hosts = [host1]

        ip = IPvAnyAddress("192.168.1.1")
        self.controller.update_hosts_ip(hosts, ip)

        self.assertEqual(len(self.controller.failed_hosts), 0)

    def test_update_hosts_ip_does_not_modify_input_list(self):
        """
        Tests that update_hosts_ip creates a copy of the hosts list and doesn't modify the input.
        """
        host1 = HostConfig(hostname="example.com", username="user1", password="pass1")
        hosts = [host1]
        original_length = len(hosts)

        ip = IPvAnyAddress("192.168.1.1")
        self.controller.update_hosts_ip(hosts, ip)

        self.assertEqual(len(hosts), original_length)

    def test_update_hosts_ip_empty_list(self):
        """
        Tests update_hosts_ip with an empty host list.
        """
        hosts = []
        ip = IPvAnyAddress("192.168.1.1")
        self.controller.update_hosts_ip(hosts, ip)

        self.assertEqual(len(self.dns_updater.calls), 0)
        self.assertEqual(len(self.controller.failed_hosts), 0)

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
