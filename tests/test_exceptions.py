# tests/test_exceptions.py
import pytest
from kbmanager.exceptions import KBException, APIError, ConfigError, FileOperationError


class TestExceptions:
    def test_kb_exception(self):
        """Test base KBException."""
        with pytest.raises(KBException) as exc_info:
            raise KBException("Base exception")
        assert str(exc_info.value) == "Base exception"

    def test_api_error(self):
        """Test APIError with all attributes."""
        error = APIError("API failed", status_code=404, response_content="Not found")
        assert str(error) == "API failed"
        assert error.status_code == 404
        assert error.response_content == "Not found"

    def test_api_error_minimal(self):
        """Test APIError with only message."""
        error = APIError("API failed")
        assert str(error) == "API failed"
        assert error.status_code is None
        assert error.response_content is None

    def test_config_error(self):
        """Test ConfigError."""
        with pytest.raises(ConfigError) as exc_info:
            raise ConfigError("Invalid configuration")
        assert str(exc_info.value) == "Invalid configuration"

    def test_file_operation_error(self):
        """Test FileOperationError."""
        with pytest.raises(FileOperationError) as exc_info:
            raise FileOperationError("File not found")
        assert str(exc_info.value) == "File not found"