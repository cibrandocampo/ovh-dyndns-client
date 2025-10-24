import json
import os
from pathlib import Path
from functools import lru_cache
from typing import List

from pydantic import ValidationError
from domain.hostconfig import HostConfig

DEFAULT_UPDATE_INTERVAL = 300
DEFAULT_HOST_FILE_PATH = Path("/app/hosts.json")  # Config path from Docker volume


class Config:
    """
    Handles application configuration, including:
    - Environment variables
    - Logger setup
    - IP state
    - Host config loading and validation
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # Only initialize once
        if not hasattr(self, '_initialized'):
            self.host_file_path = DEFAULT_HOST_FILE_PATH
            self._hosts_config = None
            self._ip = None
            self._initialized = True

    @property
    def ip(self) -> str:
        """Returns the stored IP address."""
        return self._ip

    def set_ip(self, new_ip: str) -> None:
        """Sets the current IP address."""
        self._ip = new_ip

    @property
    def logger_config(self) -> tuple:
        """
        Retrieves logger configuration from environment variables.

        Returns:
            tuple[str, str]: (logger name, logger level)
        """
        return (
            os.getenv("LOGGER_NAME", "ovh-dydns"),
            os.getenv("LOGGER_LEVEL", "INFO").upper(),
        )

    @property
    def update_ip_interval(self) -> int:
        """
        Retrieves update interval from env, or falls back to default.
        """
        raw_value = os.getenv("UPDATE_INTERVAL", DEFAULT_UPDATE_INTERVAL)
        try:
            return int(raw_value)
        except ValueError:
            # Use print instead of logger to avoid circular dependency
            print(f"Warning: Invalid UPDATE_INTERVAL: {raw_value}, using default {DEFAULT_UPDATE_INTERVAL}")
            return DEFAULT_UPDATE_INTERVAL

    @property
    def hosts_config(self) -> List[HostConfig]:
        """
        Returns cached list of valid HostConfig objects from file.
        """
        if self._hosts_config is None:
            self._hosts_config = self._load_hosts_config()
        return self._hosts_config

    @lru_cache(maxsize=1)
    def _load_hosts_config(self) -> List[HostConfig]:
        """
        Loads and validates hosts from JSON config file.
        Skips invalid or malformed entries with warning.

        Returns:
            List[HostConfig]: Valid host configurations.
        """
        try:
            with self.host_file_path.open("r", encoding="utf-8") as f:
                raw_hosts = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise RuntimeError(f"Failed to load host config: {e}")

        valid_hosts = []
        for raw_host in raw_hosts:
            host = HostConfig.model_validate(raw_host)
            valid_hosts.append(host)

        return valid_hosts
