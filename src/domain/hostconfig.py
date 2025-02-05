class HostConfig:
    def __init__(self, hostname: str, username: str, password: str):
        """
        Initializes the HostConfig instance.

        Parameters:
        - hostname (str): The hostname for the configuration.
        - username (str): The username for the configuration.
        - password (str): The password for the configuration.
        """
        self.hostname = hostname
        self.username = username
        self.password = password

    @classmethod
    def from_dict(cls, config_dict: dict):
        """
        Creates a HostConfig instance directly from a dictionary.

        Parameters:
        - config_dict (dict): A dictionary containing the configuration data.
          It should include the keys: 'hostname', 'username', and 'password'.

        Returns:
        - HostConfig: A new instance of HostConfig initialized with the values
          from the dictionary.
        """
        return cls(
            hostname=config_dict.get('hostname'),
            username=config_dict.get('username'),
            password=config_dict.get('password')
        )
