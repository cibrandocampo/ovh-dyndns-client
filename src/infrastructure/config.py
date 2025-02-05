import json
import os
from functools import lru_cache
from domain.hostconfig import HostConfig

DEFAULT_UPDATE_INTERVAL = 300
DEFAULT_HOST_FILE_PATH = "/app/hosts.json" # Config from Docker compose volume
REQUIRED_HOST_KEYS = {"hostname", "username", "password"}

class Config:
    """
    Singleton Configuration class responsible for handling environment variables, 
    retrieving the host configuration, and providing logger settings.
    """

    _instance = None  # Singleton instance

    def __new__(cls, *args, **kwargs):
        """
        Ensures only one instance of Config is created.
        If an instance already exists, it returns the existing one.

        Returns:
            Config: The singleton instance of Config.
        """
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()  # Initialize only once
        return cls._instance

    def _initialize(self):
        """
        Initializes the configuration class.
        This method runs only once per instance creation.
        """
        self.host_file_path = DEFAULT_HOST_FILE_PATH
        self._hosts_config = None
        self._ip = None

    @property
    def ip(self) -> str:
        """
        Retrieves the stored IP address.

        Returns:
            str: The current IP address.
        """
        return self._ip
    
    def set_ip(self, new_ip: str) -> None:
        """
        Updates the stored IP address.

        Args:
            new_ip (str): The new IP address to store.
        """
        self._ip = new_ip

    @property
    def logger_config(self) -> tuple:
        """
        Retrieves the logger configuration from environment variables.

        Returns:
            tuple: A tuple containing (logger_name, logger_level).
        """
        return (
            os.getenv("LOGGER_NAME", "ovh-dydns"),
            os.getenv("LOGGER_LEVEL", "INFO").upper(),
        )

    @property
    def update_ip_interval(self) -> int:
        """
        Retrieves the interval for updating the IP address from the environment variable.
        If the value is not a valid integer, it defaults to `DEFAULT_UPDATE_INTERVAL`.

        Returns:
            int: The update interval in seconds.
        """
        update_ip_interval = os.getenv("UPDATE_INTERVAL", DEFAULT_UPDATE_INTERVAL)
        try:
            return int(update_ip_interval)
        except ValueError:
            return DEFAULT_UPDATE_INTERVAL

    @property
    def hosts_config(self) -> list:
        """
        Retrieves the list of host configurations.
        The configuration is loaded once and cached in `_hosts_config`.

        Returns:
            list: A list of `HostConfig` objects.
        """
        if self._hosts_config is None:
            self._hosts_config = self.get_hosts_config()
        return self._hosts_config

    @lru_cache(maxsize=1)
    def get_hosts_config(self) -> list:
        """
        Loads and parses the hosts configuration file.
        Only hosts containing the required keys (`REQUIRED_HOST_KEYS`) are included.

        Returns:
            list: A list of `HostConfig` objects parsed from the JSON file.
        """
        with open(self.host_file_path, "r", encoding="utf-8") as f:
            raw_hosts_config = json.load(f)

        return [
            HostConfig.from_dict(host_config)
            for host_config in raw_hosts_config
            if REQUIRED_HOST_KEYS <= host_config.keys()
        ]
