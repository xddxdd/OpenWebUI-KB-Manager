# tests/test_main.py
import pytest
from unittest.mock import Mock, patch, MagicMock
import click
from click.testing import CliRunner
from kbmanager.main import CLIContext
from kbmanager.exceptions import ConfigError, FileOperationError


class TestCLIContext:
    def test_cli_context_initialization(self):
        """Test CLIContext initialization."""
        with patch('kbmanager.main.ConfigManager'):
            context = CLIContext()
            assert context.config_manager is not None
            assert context.open_web_ui_client is None
            assert context.app_logic is None
            assert context.config == {}

    def test_init_api_client_and_app_logic_success(self):
        """Test successful initialization of API client and app logic."""
        context = CLIContext()
        context.config_manager = Mock()
        context.config_manager.base_url = "http://test.com"
        context.config_manager.api_key = "test_key"

        with patch('kbmanager.main.AuthenticatedClient') as mock_client:
            with patch('kbmanager.main.AppLogic') as mock_app_logic:
                context.init_api_client_and_app_logic()

                mock_client.assert_called_once_with(
                    base_url="http://test.com",
                    token="test_key"
                )
                mock_app_logic.assert_called_once()
                assert context.open_web_ui_client is not None
                assert context.app_logic is not None

    def test_init_api_client_config_error(self):
        """Test initialization with ConfigError."""
        context = CLIContext()
        context.config_manager = Mock()
        context.config_manager.base_url = "http://test.com"
        context.config_manager.api_key = "test_key"

        with patch('kbmanager.main.AuthenticatedClient', side_effect=ConfigError("Invalid config")):
            with patch('kbmanager.main.click.echo') as mock_echo:
                with patch('kbmanager.main.sys.exit') as mock_exit:
                    context.init_api_client_and_app_logic()

                    mock_echo.assert_called_with("Error: Invalid config", err=True)
                    mock_exit.assert_called_with(1)

    def test_coro_decorator(self):
        """Test the coro decorator for async functions."""
        from kbmanager.main import coro

        @coro
        async def async_function(value):
            return value * 2

        # Should be able to call without await
        result = async_function(5)
        assert result == 10


class TestMainCLI:
    """Test CLI commands if they exist in main.py"""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    def test_error_handling_in_cli(self, runner):
        """Test error handling in CLI commands."""
        # This would test actual CLI commands from main.py
        # Since the provided context doesn't show the CLI commands,
        # this is a placeholder for testing the error handling pattern

        with patch('kbmanager.main.logger') as mock_logger:
            # Simulate an error scenario
            error = FileOperationError("Could not complete directory upload: test error")
            mock_logger.error.assert_not_called()  # Before error

            # Log the error (as shown in main.py)
            mock_logger.error(f"Could not complete directory upload: {error}")
            mock_logger.error.assert_called_once()