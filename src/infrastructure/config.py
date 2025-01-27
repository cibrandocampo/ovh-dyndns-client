import os
import configparser
from domain.hostconfig import HostConfig
from threading import Lock

CONFIG_FILE_PATH = os.environ.get('DEFAULT_CONFIG_FILE_PATH', 'ovh-dyndns.config')


class Config:
    """
    A thread-safe Singleton class for managing application configuration.
    """
    _instance = None
    _lock = Lock()

    def __new__(cls, config_file=CONFIG_FILE_PATH) -> 'Config':
        """
        Ensure only one instance of the Config class is created (Singleton pattern).
        """
        if not cls._instance:
            with cls._lock:
                if not cls._instance:  # Double-checked locking
                    cls._instance = super().__new__(cls)
                    cls._instance._initialize(config_file)
        return cls._instance

    def _initialize(self, config_file) -> None:
        """
        Initialize the Config instance, reading the configuration file.
        
        :param config_file: The path to the configuration file.
        """
        from infrastructure.logger import Logger
        self.logger = Logger().get_logger()
        self.config = configparser.ConfigParser()
        try:
            self.config.read(config_file)
            self.logger.info(f"Configuration file '{config_file}' loaded successfully.")
        except Exception as e:
            self.logger.error(f"Failed to load configuration file '{config_file}': {e}")

    def get_section(self, section, fallback=None):
        """Retrieves all options from a specific section."""
        try:
            options = dict(self.config.items(section))
            self.logger.debug(f"Retrieved section '{section}': {options}")
            return options
        except configparser.NoSectionError:
            self.logger.warning(f"Section '{section}' not found. Returning fallback: {fallback}")
            return fallback

    def get(self, section, option, fallback=None):
        """Retrieves the value of a specific option from a section."""
        try:
            value = self.config.get(section, option)
            self.logger.debug(f"Retrieved '{option}' from section '{section}': {value}")
            return value
        except configparser.NoSectionError:
            self.logger.warning(f"Section '{section}' not found. Returning fallback for '{option}': {fallback}")
            return fallback
        except configparser.NoOptionError:
            self.logger.warning(f"Option '{option}' not found in section '{section}'. Returning fallback: {fallback}")
            return fallback

    def get_hosts_config(self) -> list:
        """Retrieve a list of HostConfig objects from the configuration."""
        hosts = []
        for section in self.config.sections():
            if section.startswith('hostconfig'):
                try:
                    host = HostConfig(
                        hostname=self.config.get(section=section, option='hostname'),
                        username=self.config.get(section=section, option='username'),
                        password=self.config.get(section=section, option='password')
                    )
                    hosts.append(host)
                    self.logger.debug(f"Host config loaded from section '{section}': {host}")
                except (configparser.NoOptionError, ValueError) as e:
                    self.logger.error(f"Failed to load host config from section '{section}': {e}")
        self.logger.info(f"Loaded {len(hosts)} host configurations.")
        return hosts

    def set(self, section, option, value):
        """Sets a value for a specific option in a section."""
        if not self.config.has_section(section):
            self.config.add_section(section)
            self.logger.info(f"Section '{section}' created.")
        self.config.set(section, option, value)
        self.logger.debug(f"Set '{option}' in section '{section}' to '{value}'.")

    def save(self, config_file):
        """Saves the current configuration to the specified file."""
        try:
            with open(config_file, 'w') as configfile:
                self.config.write(configfile)
            self.logger.info(f"Configuration saved to '{config_file}'.")
        except Exception as e:
            self.logger.error(f"Failed to save configuration to '{config_file}': {e}")
    
    @classmethod
    def get_config(cls, config_file=CONFIG_FILE_PATH) -> 'Config':
        """
        Returns the Singleton instance of the Config class.
        """
        return cls(config_file)


# Usage
#config_instance = Config()
