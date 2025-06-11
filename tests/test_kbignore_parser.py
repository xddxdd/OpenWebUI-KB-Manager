# tests/test_kbignore_parser.py
import pytest
from pathlib import Path
from kbmanager.kbignore_parser import KBIgnoreParser
import tempfile
import shutil


class TestKBIgnoreParser:
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def kbignore_content(self):
        """Sample .kbignore content."""
        return """
# This is a comment
*.log
*.tmp
/build/
__pycache__/
!important.log
"""

    def test_parser_initialization(self, temp_dir, kbignore_content):
        """Test parser initialization with valid .kbignore file."""
        ignore_file = temp_dir / ".kbignore"
        ignore_file.write_text(kbignore_content)

        parser = KBIgnoreParser(ignore_file)
        assert parser.ignore_file == ignore_file
        assert len(parser.patterns) > 0

    def test_parser_no_ignore_file(self, temp_dir):
        """Test parser when .kbignore file doesn't exist."""
        ignore_file = temp_dir / ".kbignore"
        parser = KBIgnoreParser(ignore_file)
        assert len(parser.patterns) == 0

    def test_is_ignored_patterns(self, temp_dir, kbignore_content):
        """Test various ignore patterns."""
        ignore_file = temp_dir / ".kbignore"
        ignore_file.write_text(kbignore_content)
        parser = KBIgnoreParser(ignore_file)

        # Test cases
        assert parser.is_ignored("test.log") is True
        assert parser.is_ignored("subdir/test.log") is True
        assert parser.is_ignored("file.tmp") is True
        assert parser.is_ignored("test.txt") is False
        assert parser.is_ignored("build/output.bin") is True
        assert parser.is_ignored("__pycache__/file.pyc") is True
        assert parser.is_ignored("important.log") is False  # Negated pattern

    def test_empty_and_comment_lines(self, temp_dir):
        """Test handling of empty lines and comments."""
        ignore_content = """
# Comment line

*.log
   # Another comment
*.tmp
"""
        ignore_file = temp_dir / ".kbignore"
        ignore_file.write_text(ignore_content)
        parser = KBIgnoreParser(ignore_file)

        # Should only have 2 patterns (*.log and *.tmp)
        assert len(parser.patterns) == 2

    def test_path_normalization(self, temp_dir):
        """Test path normalization in pattern matching."""
        ignore_content = "subdir/*.txt"
        ignore_file = temp_dir / ".kbignore"
        ignore_file.write_text(ignore_content)
        parser = KBIgnoreParser(ignore_file)

        # Test with different path separators
        assert parser.is_ignored("subdir/file.txt") is True
        assert parser.is_ignored(Path("subdir") / "file.txt") is True
        assert parser.is_ignored("subdir\\file.txt") is True  # Windows path