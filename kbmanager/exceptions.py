class KBException(Exception):
    """Base exception for the OpenWebUI CLI."""

    pass


class APIError(KBException):
    """Raised when an API call returns an error status."""

    def __init__(self, message: str, status_code: int = None, response_content: str = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_content = response_content


class ConfigError(KBException):
    """Raised when there's an issue with configuration."""

    pass


class FileOperationError(KBException):
    """Raised when a local file operation fails."""

    pass
