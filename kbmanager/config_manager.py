# openwebui-cli/my_cli_app/config_manager.py

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from kbmanager.exceptions import ConfigError

logger = logging.getLogger(__name__)

# Define default configuration file paths
# Prioritize current working directory, then user's config directory
CONFIG_FILE_NAMES = ["config.yaml"]  # Search order
APP_CONFIG_DIR = Path.home() / ".kbmanager"  # ~/.kbmanager/


class ConfigManager:
    def __init__(self):
        self._config = {}
        self._loaded_file_path: Optional[Path] = None

    def _find_config_file(self) -> Optional[Path]:
        """Searches for a config file in predefined locations."""
        # Check current working directory first
        for name in CONFIG_FILE_NAMES:
            path = Path.cwd() / name
            if path.is_file():
                logger.debug(f"Found config file in CWD: {path}")
                return path

        # Check user's config directory
        for name in CONFIG_FILE_NAMES:
            path = APP_CONFIG_DIR / name
            if path.is_file():
                logger.debug(f"Found config file in user config dir: {path}")
                return path

        logger.debug("No config file found in expected locations.")
        return None

    def load_config(self, cli_args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Loads configuration from environment variables, config file, and CLI arguments.
        CLI arguments take precedence > Environment variables > Config file.
        """
        config_from_file = {}
        self._loaded_file_path = self._find_config_file()

        if self._loaded_file_path:
            try:
                with open(self._loaded_file_path) as f:
                    config_from_file = yaml.safe_load(f)
                if not isinstance(config_from_file, dict):
                    raise ConfigError(f"Config file '{self._loaded_file_path}' is not a valid YAML dictionary.")
                logger.info(f"Loaded configuration from: {self._loaded_file_path}")
            except yaml.YAMLError as e:
                raise ConfigError(f"Error parsing config file '{self._loaded_file_path}': {e}") from e
            except OSError as e:
                raise ConfigError(f"Error reading config file '{self._loaded_file_path}': {e}") from e
        else:
            logger.info("No config file found. Relying on environment variables or CLI arguments.")

        # Load from environment variables
        config_from_env = {
            "api_key": os.getenv("KB_MANAGER_API_KEY"),
            "base_url": os.getenv("KB_MANAGER_BASE_URL"),
        }
        # Filter out None values
        config_from_env = {k: v for k, v in config_from_env.items() if v is not None}
        if config_from_env:
            logger.debug(f"Loaded config from environment variables: {list(config_from_env.keys())}")

        # Merge configurations: Config file < Environment variables < CLI arguments
        self._config = {**config_from_file, **config_from_env, **cli_args}

        # Basic validation
        if not self.get("api_key"):
            raise ConfigError(
                "API key is missing. Please provide it via config file, environment variable (KB_MANAGER_API_KEY), or --api-key."
            )
        if not self.get("base_url"):
            raise ConfigError(
                "Base URL is missing. Please provide it via config file, environment variable (KB_MANAGER_BASE_URL), or --api-url."
            )

        logger.debug(f"Final merged configuration keys: {list(self._config.keys())}")
        return self._config

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieves a configuration value."""
        return self._config.get(key, default)

    @property
    def api_key(self) -> str:
        """Convenience property for API key."""
        return self.get("api_key")

    @property
    def base_url(self) -> str:
        """Convenience property for base URL."""
        return self.get("base_url")

    @property
    def loaded_file_path(self) -> Optional[Path]:
        """Returns the path of the loaded config file, if any."""
        return self._loaded_file_path
