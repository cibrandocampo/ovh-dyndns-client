from pydantic import BaseModel, Field, SecretStr, ValidationError


class HostConfig(BaseModel):
    """
    Represents host connection configuration with automatic validation.
    """
    hostname: str = Field(..., description="The hostname or IP address of the host.")
    username: str = Field(..., description="Username for authentication.")
    password: SecretStr = Field(..., description="Password for authentication.")

    @classmethod
    def from_dict(cls, config_dict: dict):
        """
        Creates a HostConfig instance from a dictionary.
        Raises ValidationError if required fields are missing or invalid.
        """
        return cls(**config_dict)
