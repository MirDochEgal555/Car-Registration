"""Small, dependency-free application settings for the initial backend."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Static settings until environment-based deployment configuration is added."""

    app_name: str = "CarTech API"
    app_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"


settings = Settings()
