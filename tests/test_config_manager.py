# tests/test_config_manager.py
import pytest
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path
import yaml
from kbmanager.config_manager import ConfigManager, ConfigError


class TestConfigManager:
    @pytest.fixture
    def mock_env(self):
        """Mock environment variables."""
        with patch.dict('os.environ', {
            'OPENWEBUI_API_KEY': 'env_api_key',
            'OPENWEBUI_BASE_URL': 'http://env.example.com'
        }):
            yield

    @pytest.fixture
    def sample_config_yaml(self):
        """Sample YAML configuration content."""
        return """
api_key: file_api_key
base_url: http://file.example.com
extra_setting: value
"""

    def test_find_config_file_not_found(self):
        """Test when no config file is found."""
        manager = ConfigManager()
        with patch('pathlib.Path.is_file', return_value=False):
            result = manager._find_config_file()
            assert result is None

    def test_find_config_file_in_current_dir(self):
        """Test finding config file in current directory."""
        manager = ConfigManager()
        with patch('pathlib.Path.is_file') as mock_is_file:
            mock_is_file.side_effect = lambda: mock_is_file.call_count == 1
            result = manager._find_config_file()
            assert result is not None
            assert result.name in ['config.yaml']

    def test_load_config_cli_precedence(self, mock_env, sample_config_yaml):
        """Test that CLI arguments take precedence over environment and file config."""
        manager = ConfigManager()

        # Mock file operations
        with patch('pathlib.Path.is_file', return_value=True):
            with patch('builtins.open', mock_open(read_data=sample_config_yaml)):
                cli_args = {
                    'api_key': 'cli_api_key',
                    'base_url': 'http://cli.example.com'
                }
                config = manager.load_config(cli_args)

                assert config['api_key'] == 'cli_api_key'
                assert config['base_url'] == 'http://cli.example.com'

    def test_load_config_env_precedence(self, mock_env, sample_config_yaml):
        """Test that environment variables take precedence over file config."""
        manager = ConfigManager()

        with patch('pathlib.Path.is_file', return_value=True):
            with patch('builtins.open', mock_open(read_data=sample_config_yaml)):
                config = manager.load_config({})

                assert config['api_key'] == 'env_api_key'
                assert config['base_url'] == 'http://env.example.com'
                assert config['extra_setting'] == 'value'

    def test_load_config_file_only(self, sample_config_yaml):
        """Test loading config from file when no env vars or CLI args."""
        manager = ConfigManager()

        with patch('pathlib.Path.is_file', return_value=True):
            with patch('builtins.open', mock_open(read_data=sample_config_yaml)):
                with patch.dict('os.environ', {}, clear=True):
                    config = manager.load_config({})

                    assert config['api_key'] == 'file_api_key'
                    assert config['base_url'] == 'http://file.example.com'

    def test_load_config_invalid_yaml(self):
        """Test handling of invalid YAML file."""
        manager = ConfigManager()
        invalid_yaml = "invalid: yaml: content:"

        with patch('pathlib.Path.is_file', return_value=True):
            with patch('builtins.open', mock_open(read_data=invalid_yaml)):
                with pytest.raises(ConfigError) as exc_info:
                    manager.load_config({})
                assert "Error parsing config file" in str(exc_info.value)

    def test_load_config_non_dict_yaml(self):
        """Test handling of YAML that doesn't parse to a dictionary."""
        manager = ConfigManager()
        non_dict_yaml = "just a string"

        with patch('pathlib.Path.is_file', return_value=True):
            with patch('builtins.open', mock_open(read_data=non_dict_yaml)):
                with pytest.raises(ConfigError) as exc_info:
                    manager.load_config({})
                assert "not a valid YAML dictionary" in str(exc_info.value)

    def test_get_method(self, mock_env):
        """Test the get method."""
        manager = ConfigManager()
        manager.load_config({})

        assert manager.get('api_key') == 'env_api_key'
        assert manager.get('non_existent') is None
        assert manager.get('non_existent', 'default') == 'default'

    def test_properties(self, mock_env):
        """Test convenience properties."""
        manager = ConfigManager()
        manager.load_config({})

        assert manager.api_key == 'env_api_key'
        assert manager.base_url == 'http://env.example.com'

    def test_loaded_file_path(self, sample_config_yaml):
        """Test loaded_file_path property."""
        manager = ConfigManager()

        with patch('pathlib.Path.is_file', return_value=True):
            with patch('builtins.open', mock_open(read_data=sample_config_yaml)):
                manager.load_config({})
                assert manager.loaded_file_path is not None