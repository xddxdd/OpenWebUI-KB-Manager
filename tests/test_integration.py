# tests/test_integration.py
import pytest
from unittest.mock import patch, Mock
import tempfile
import shutil
from pathlib import Path
from kbmanager.config_manager import ConfigManager
from kbmanager.app_logic import AppLogic
from kbmanager.kbignore_parser import KBIgnoreParser


class TestIntegration:
    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace with config and test files."""
        workspace = tempfile.mkdtemp()
        workspace_path = Path(workspace)

        # Create config file
        config_file = workspace_path / "kb_config.yaml"
        config_file.write_text("""
api_key: test_api_key
base_url: http://localhost:8000
""")

        # Create .kbignore file
        ignore_file = workspace_path / ".kbignore"
        ignore_file.write_text("""
*.log
*.tmp
__pycache__/
""")

        # Create test files
        (workspace_path / "important.txt").write_text("Important content")
        (workspace_path / "debug.log").write_text("Debug logs")
        (workspace_path / "temp.tmp").write_text("Temporary file")

        yield workspace_path
        shutil.rmtree(workspace)

    def test_full_workflow(self, temp_workspace):
        """Test the integration of ConfigManager, KBIgnoreParser, and AppLogic."""
        # Change to temp workspace
        with patch('pathlib.Path.cwd', return_value=temp_workspace):
            # Initialize config manager
            config_manager = ConfigManager()
            config = config_manager.load_config({})

            assert config['api_key'] == 'test_api_key'
            assert config['base_url'] == 'http://localhost:8000'

            # Initialize ignore parser
            ignore_parser = KBIgnoreParser(temp_workspace / ".kbignore")

            # Test file filtering
            all_files = list(temp_workspace.glob("*"))
            filtered_files = [
                f for f in all_files
                if f.is_file() and not ignore_parser.is_ignored(f.relative_to(temp_workspace))
            ]

            # Should only include important.txt
            assert len(filtered_files) == 1
            assert filtered_files[0].name == "important.txt"