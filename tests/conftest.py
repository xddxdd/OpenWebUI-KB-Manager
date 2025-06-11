# tests/conftest.py
import pytest
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def mock_api_response():
    """Shared fixture for mocking API responses."""

    class MockResponse:
        def __init__(self, status_code=200, content=None, parsed=None):
            self.status_code = status_code
            self.content = content or b'{"success": true}'
            self.parsed = parsed

        def decode(self, *args, **kwargs):
            return self.content.decode(*args, **kwargs)

    return MockResponse