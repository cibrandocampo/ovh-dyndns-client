import unittest
from unittest.mock import patch, MagicMock
from domain.hostconfig import HostConfig
from application.controller import UpdateDnsController
from infrastructure.config import Config


class TestUpdateDnsController(unittest.TestCase):
    
    def setUp(self):
        """
        Sets up test environment by resetting Config singleton and creating a controller instance.
        """
        Config._instance = None
        self.controller = UpdateDnsController()
    
    @patch('application.controller.IpifyClient')
    @patch('application.controller.OvhClient')
    def test_handler_ip_unchanged_no_failed_hosts(self, mock_ovh_client, mock_ipify_client):
        """
        Tests handler when IP hasn't changed and there are no failed hosts.
        Should skip update and not call update_hosts_ip.
        """
        # Setup mocks
        mock_ipify = mock_ipify_client.return_value
        mock_ipify.get_public_ip.return_value = "192.168.1.1"
        
        # Recreate controller after patches are applied
        self.controller = UpdateDnsController()
        
        config = Config()
        config.set_ip("192.168.1.1")
        
        # Execute
        self.controller.handler()
        
        # Assertions
        mock_ipify.get_public_ip.assert_called_once()
        mock_ovh_client.assert_not_called()
    
    @patch('application.controller.IpifyClient')
    @patch('application.controller.OvhClient')
    def test_handler_ip_unchanged_with_failed_hosts(self, mock_ovh_client, mock_ipify_client):
        """
        Tests handler when IP hasn't changed but there are failed hosts to retry.
        Should retry failed hosts.
        """
        # Setup mocks
        mock_ipify = mock_ipify_client.return_value
        mock_ipify.get_public_ip.return_value = "192.168.1.1"
        
        # Recreate controller after patches are applied
        self.controller = UpdateDnsController()
        
        config = Config()
        config.set_ip("192.168.1.1")
        
        # Add a failed host
        failed_host = HostConfig(hostname="example.com", username="user", password="pass")
        self.controller.failed_hosts = [failed_host]
        
        # Mock OVH client to return success
        mock_ovh_instance = MagicMock()
        mock_ovh_instance.update_ip.return_value = True
        mock_ovh_client.return_value = mock_ovh_instance
        
        # Execute
        self.controller.handler()
        
        # Assertions
        mock_ipify.get_public_ip.assert_called_once()
        mock_ovh_client.assert_called_once_with(host=failed_host)
        mock_ovh_instance.update_ip.assert_called_once_with("192.168.1.1")
    
    @patch('application.controller.IpifyClient')
    @patch('application.controller.OvhClient')
    def test_handler_ip_changed(self, mock_ovh_client, mock_ipify_client):
        """
        Tests handler when IP has changed.
        Should update all hosts with the new IP.
        """
        # Setup mocks
        mock_ipify = mock_ipify_client.return_value
        mock_ipify.get_public_ip.return_value = "192.168.1.2"
        
        # Recreate controller after patches are applied
        self.controller = UpdateDnsController()
        
        config = Config()
        config.set_ip("192.168.1.1")
        
        # Setup hosts config directly
        host1 = HostConfig(hostname="example.com", username="user1", password="pass1")
        host2 = HostConfig(hostname="example2.com", username="user2", password="pass2")
        config._hosts_config = [host1, host2]
        
        # Mock OVH client to return success
        mock_ovh_instance = MagicMock()
        mock_ovh_instance.update_ip.return_value = True
        mock_ovh_client.return_value = mock_ovh_instance
        
        # Execute
        self.controller.handler()
        
        # Assertions
        mock_ipify.get_public_ip.assert_called_once()
        self.assertEqual(config.ip, "192.168.1.2")
        self.assertEqual(mock_ovh_client.call_count, 2)
        mock_ovh_instance.update_ip.assert_called_with("192.168.1.2")
    
    @patch('application.controller.IpifyClient')
    def test_handler_ipify_exception(self, mock_ipify_client):
        """
        Tests handler when IpifyClient raises an exception.
        Should log error and raise RuntimeError.
        """
        # Setup mock to raise exception
        mock_ipify = mock_ipify_client.return_value
        mock_ipify.get_public_ip.side_effect = Exception("Network error")
        
        # Recreate controller after patches are applied
        self.controller = UpdateDnsController()
        
        # Execute and assert
        with self.assertRaises(RuntimeError) as context:
            self.controller.handler()
        
        self.assertEqual(str(context.exception), "DynDNS update failed")
    
    @patch('application.controller.OvhClient')
    def test_update_hosts_ip_success(self, mock_ovh_client):
        """
        Tests update_hosts_ip when all hosts update successfully.
        Should clear failed_hosts.
        """
        # Setup
        host1 = HostConfig(hostname="example.com", username="user1", password="pass1")
        host2 = HostConfig(hostname="example2.com", username="user2", password="pass2")
        hosts = [host1, host2]
        
        config = Config()
        config.set_ip("192.168.1.1")
        
        # Mock OVH client to return success
        mock_ovh_instance = MagicMock()
        mock_ovh_instance.update_ip.return_value = True
        mock_ovh_client.return_value = mock_ovh_instance
        
        # Execute
        self.controller.update_hosts_ip(hosts)
        
        # Assertions
        self.assertEqual(mock_ovh_client.call_count, 2)
        self.assertEqual(len(self.controller.failed_hosts), 0)
    
    @patch('application.controller.OvhClient')
    def test_update_hosts_ip_partial_failure(self, mock_ovh_client):
        """
        Tests update_hosts_ip when some hosts fail to update.
        Should track failed hosts.
        """
        # Setup
        host1 = HostConfig(hostname="example.com", username="user1", password="pass1")
        host2 = HostConfig(hostname="example2.com", username="user2", password="pass2")
        hosts = [host1, host2]
        
        config = Config()
        config.set_ip("192.168.1.1")
        
        # Mock OVH client to return mixed results
        mock_ovh_instance = MagicMock()
        mock_ovh_instance.update_ip.side_effect = [True, False]  # First succeeds, second fails
        mock_ovh_client.return_value = mock_ovh_instance
        
        # Execute
        self.controller.update_hosts_ip(hosts)
        
        # Assertions
        self.assertEqual(mock_ovh_client.call_count, 2)
        self.assertEqual(len(self.controller.failed_hosts), 1)
        self.assertEqual(self.controller.failed_hosts[0].hostname, "example2.com")
    
    @patch('application.controller.OvhClient')
    def test_update_hosts_ip_clears_previous_failures(self, mock_ovh_client):
        """
        Tests that update_hosts_ip clears previous failed hosts before processing.
        """
        # Setup - add previous failed host
        previous_failed = HostConfig(hostname="old.com", username="user", password="pass")
        self.controller.failed_hosts = [previous_failed]
        
        # Setup new hosts
        host1 = HostConfig(hostname="example.com", username="user1", password="pass1")
        hosts = [host1]
        
        config = Config()
        config.set_ip("192.168.1.1")
        
        # Mock OVH client to return success
        mock_ovh_instance = MagicMock()
        mock_ovh_instance.update_ip.return_value = True
        mock_ovh_client.return_value = mock_ovh_instance
        
        # Execute
        self.controller.update_hosts_ip(hosts)
        
        # Assertions - previous failed host should be cleared
        self.assertEqual(len(self.controller.failed_hosts), 0)
    
    @patch('application.controller.OvhClient')
    def test_update_hosts_ip_does_not_modify_input_list(self, mock_ovh_client):
        """
        Tests that update_hosts_ip creates a copy of the hosts list and doesn't modify the input.
        """
        # Setup
        host1 = HostConfig(hostname="example.com", username="user1", password="pass1")
        hosts = [host1]
        original_length = len(hosts)
        
        config = Config()
        config.set_ip("192.168.1.1")
        
        # Mock OVH client
        mock_ovh_instance = MagicMock()
        mock_ovh_instance.update_ip.return_value = True
        mock_ovh_client.return_value = mock_ovh_instance
        
        # Execute
        self.controller.update_hosts_ip(hosts)
        
        # Assertions - input list should not be modified
        self.assertEqual(len(hosts), original_length)


if __name__ == "__main__":
    unittest.main()

