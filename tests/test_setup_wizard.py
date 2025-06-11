# import pytest
# from unittest.mock import patch, MagicMock, mock_open
# from pathlib import Path
# import shutil
# import os
# import sys
# import json
# import yaml
# import requests
# import subprocess # Keep subprocess for mocking calls to external commands
#
# # Adjust import path if necessary based on your project structure
# from kbmanager.setup_wizard import SetupWizard
# from kbmanager.config_manager import APP_CONFIG_DIR, CONFIG_FILE_NAMES # Import APP_CONFIG_DIR for its value
#
#
# @pytest.fixture
# def mock_filesystem(tmp_path):
#     """
#     Mocks key filesystem interactions to isolate SetupWizard tests.
#     This includes:
#     - os.environ['HOME'] to redirect '~'
#     - pathlib.Path.cwd() to control current working directory
#     - pathlib.Path.exists() to control file/directory existence checks
#     - pathlib.Path.mkdir() to simulate directory creation without touching real disk
#     - pathlib.Path.is_file(), pathlib.Path.is_dir()
#     - pathlib.Path.write_text(), pathlib.Path.write_bytes(), Path.read_text(), Path.read_bytes()
#     - shutil.rmtree, shutil.move
#     - tempfile.mkdtemp (used by SetupWizard for client generation temp dir)
#     """
#     real_path_cwd = Path.cwd # Store real cwd
#     real_os_environ = os.environ.copy() # Store a copy of real environment
#
#     # Map real paths (as strings) to mocked in-memory representations or tmp_path
#     # This is a bit complex, but necessary for deep `Path` mocking.
#     # We'll use a dictionary to simulate our mocked filesystem.
#     mock_files = {}
#
#     def mock_path_exists(self):
#         return str(self) in mock_files or self == tmp_path # Basic check for roots
#
#     def mock_is_file(self):
#         return str(self) in mock_files and mock_files[str(self)]['type'] == 'file'
#
#     def mock_is_dir(self):
#         return str(self) in mock_files and mock_files[str(self)]['type'] == 'dir'
#
#     def mock_mkdir(self, parents=False, exist_ok=False):
#         p_str = str(self)
#         if p_str in mock_files and mock_files[p_str]['type'] == 'dir':
#             if exist_ok: return
#             raise FileExistsError(f"Directory already exists: {self}")
#         mock_files[p_str] = {'type': 'dir', 'contents': {}} # Simulate directory
#         # Also create parent dirs if needed
#         if parents:
#             parent = self.parent
#             while str(parent) != str(tmp_path.parent) and str(parent) not in mock_files:
#                 mock_files[str(parent)] = {'type': 'dir', 'contents': {}}
#                 parent = parent.parent
#
#     def mock_write_text(self, data, encoding='utf-8'):
#         mock_files[str(self)] = {'type': 'file', 'content': data.encode(encoding)}
#
#     def mock_write_bytes(self, data):
#         mock_files[str(self)] = {'type': 'file', 'content': data}
#
#     def mock_read_text(self, encoding='utf-8'):
#         if str(self) not in mock_files or mock_files[str(self)]['type'] != 'file':
#             raise FileNotFoundError(f"No such file: {self}")
#         return mock_files[str(self)]['content'].decode(encoding)
#
#     def mock_read_bytes(self):
#         if str(self) not in mock_files or mock_files[str(self)]['type'] != 'file':
#             raise FileNotFoundError(f"No such file: {self}")
#         return mock_files[str(self)]['content']
#
#     def mock_unlink(self, missing_ok=False):
#         if str(self) in mock_files and mock_files[str(self)]['type'] == 'file':
#             del mock_files[str(self)]
#         elif not missing_ok:
#             raise FileNotFoundError(f"No such file or directory: {self}")
#
#     def mock_shutil_rmtree(path):
#         # Simplistic mock: just remove the root from mock_files
#         path_str = str(path)
#         keys_to_delete = [k for k in mock_files if k.startswith(f"{path_str}/") or k == path_str]
#         for k in keys_to_delete:
#             del mock_files[k]
#
#     def mock_shutil_move(src, dst):
#         mock_files[str(dst)] = mock_files[str(src)]
#         mock_shutil_rmtree(Path(src)) # Remove source after move
#
#     def mock_tempfile_mkdtemp(suffix=None, prefix=None, dir=None):
#         # Create a unique temp path within tmp_path
#         temp_dir_path = tmp_path / f"mock_temp_dir_{len(mock_files)}"
#         mock_files[str(temp_dir_path)] = {'type': 'dir', 'contents': {}}
#         return str(temp_dir_path)
#
#     # Patch Path methods
#     with patch('pathlib.Path.exists', new=mock_path_exists), \
#          patch('pathlib.Path.is_file', new=mock_is_file), \
#          patch('pathlib.Path.is_dir', new=mock_is_dir), \
#          patch('pathlib.Path.mkdir', new=mock_mkdir), \
#          patch('pathlib.Path.write_text', new=mock_write_text), \
#          patch('pathlib.Path.write_bytes', new=mock_write_bytes), \
#          patch('pathlib.Path.read_text', new=mock_read_text), \
#          patch('pathlib.Path.read_bytes', new=mock_read_bytes), \
#          patch('pathlib.Path.unlink', new=mock_unlink), \
#          patch('pathlib.Path.cwd', return_value=tmp_path), \
#          patch('shutil.rmtree', new=mock_shutil_rmtree), \
#          patch('shutil.move', new=mock_shutil_move), \
#          patch('tempfile.mkdtemp', new=mock_tempfile_mkdtemp):
#
#         # Set up a fake home directory
#         os.environ['HOME'] = str(tmp_path)
#         # Ensure the .kbmanager config directory exists in our mock filesystem
#         mock_files[str(tmp_path / ".kbmanager")] = {'type': 'dir', 'contents': {}}
#
#
#         # Yield control to the test function
#         yield tmp_path
#
#     # Restore real environment and cwd after test
#     os.environ.clear()
#     os.environ.update(real_os_environ)
#     Path.cwd = real_path_cwd
#
#
# @pytest.fixture
# def wizard(mock_filesystem):
#     """Provides a SetupWizard instance for testing within the mocked filesystem."""
#     # SetupWizard initializes its internal paths on creation.
#     # With the mocked filesystem, these paths will now point to the isolated tmp_path.
#     return SetupWizard()
#
#
# class TestSetupWizard:
#     @patch('kbmanager.setup_wizard.requests.get')
#     @patch('kbmanager.setup_wizard.click.prompt')
#     @patch('kbmanager.setup_wizard.subprocess.run')
#     @patch('kbmanager.setup_wizard.SetupWizard.check_generator_installed', return_value=True)
#     def test_run_success(self, mock_check_generator, mock_subprocess_run,
#                          mock_click_prompt, mock_requests_get, wizard, mock_filesystem):
#         """Test a successful full run of the setup wizard."""
#         # Mock user prompts: URL, API Key
#         mock_click_prompt.side_effect = [
#             "http://mock-openwebui.com", # OpenWebUI Base URL
#             "mock_api_key_123"          # OpenWebUI API Key
#         ]
#
#         # Mock the OpenAPI spec download
#         mock_requests_get.return_value = MagicMock(
#             status_code=200,
#             content=json.dumps({"openapi": "3.0.0", "info": {"title": "Test API"}}).encode('utf-8'),
#             raise_for_status=MagicMock()
#         )
#
#         # Mock the subprocess.run call for client generation
#         # Ensure it 'creates' the expected client folder in the temp output path
#         def mock_generate_side_effect(*args, **kwargs):
#             if "openapi-python-client" in kwargs.get('args', args[0][0]):
#                 output_path_str = kwargs['args'][5] # Get output path from command line args
#                 generated_client_path = Path(output_path_str) / "open_web_ui_client"
#                 # Simulate creation of the generated client directory and a file inside
#                 generated_client_path.mkdir(parents=True, exist_ok=True)
#                 (generated_client_path / "__init__.py").touch()
#                 return MagicMock(returncode=0, stdout="Client generated.", stderr="")
#             return MagicMock(returncode=0) # For other subprocess calls if any
#
#         mock_subprocess_run.side_effect = mock_generate_side_effect
#
#         success = wizard.run()
#
#         assert success is True
#         mock_click_prompt.assert_any_call("Enter your OpenWebUI Base URL", default="http://localhost:8080", show_default=True)
#
#         config_file_path = wizard.config_dir / CONFIG_FILE_NAMES[0]
#         # Assert that the config file was created in the mock filesystem
#         assert config_file_path.is_file()
#         config = yaml.safe_load(config_file_path.read_text())
#         assert config['base_url'] == "http://mock-openwebui.com"
#         assert config['api_key'] == "mock_api_key_123"
#
#         # Verify calls for spec fetching and client generation
#         mock_requests_get.assert_called_once()
#         # Verify openapi-python-client generate command was attempted
#         assert any("openapi-python-client" in str(c) for c in mock_subprocess_run.call_args_list)
#
#         # Verify the final client directory exists (moved from temp to wizard.client_path)
#         assert wizard.client_path.is_dir()
#         assert (wizard.client_path / "__init__.py").is_file()
#
#     @patch('kbmanager.setup_wizard.requests.get')
#     @patch('kbmanager.setup_wizard.click.prompt')
#     @patch('kbmanager.setup_wizard.click.echo')
#     @patch('kbmanager.setup_wizard.subprocess.run')
#     @patch('kbmanager.setup_wizard.SetupWizard.check_generator_installed', return_value=True)
#     def test_run_fetch_spec_failure(self, mock_check_generator, mock_subprocess_run,
#                                      mock_click_echo, mock_click_prompt, mock_requests_get, wizard, mock_filesystem):
#         """Test wizard when fetching OpenAPI spec fails, and manual URL is not provided."""
#         mock_click_prompt.side_effect = [
#             "http://mock.fail",  # OpenWebUI Base URL
#             "mock_api_key",      # API Key
#             "",                   # No manual OpenAPI spec URL for the prompt
#         ]
#         # Mock all requests.get calls for possible_paths to fail
#         # This requires knowing how many paths fetch_openapi_spec tries
#         # For simplicity, we can mock it to always raise, or return a non-200.
#         # Here, returning a non-200 code for all attempts.
#         mock_requests_get.return_value = MagicMock(status_code=404)
#         mock_requests_get.return_value.raise_for_status.side_effect = lambda: requests.exceptions.HTTPError("404 Error")
#
#
#         success = wizard.run()
#
#         assert success is False
#         sys.stdout.flush()
#         sys.stderr.flush()
#         # Check output for specific error messages
#         assert "❌ Couldn't find OpenAPI spec automatically using common paths." in mock_click_echo.call_args_list[-2].args[0]
#         assert "Setup requires the OpenAPI specification. Exiting setup." in mock_click_echo.call_args_list[-1].args[0]
#
#     @patch('kbmanager.setup_wizard.requests.get')
#     @patch('kbmanager.setup_wizard.click.prompt')
#     @patch('kbmanager.setup_wizard.click.echo')
#     @patch('kbmanager.setup_wizard.subprocess.run')
#     @patch('kbmanager.setup_wizard.SetupWizard.check_generator_installed', return_value=False) # Generator not installed
#     def test_run_generator_install_failure(self, mock_check_generator, mock_subprocess_run,
#                                            mock_click_echo, mock_click_prompt, mock_requests_get, wizard, mock_filesystem):
#         """Test wizard when openapi-python-client installation fails."""
#         mock_click_prompt.side_effect = [
#             "http://test.com", # URL
#             "api_key_xyz",     # API Key
#         ]
#         mock_requests_get.return_value = MagicMock(
#             status_code=200,
#             content=json.dumps({"openapi": "3.0.0"}).encode('utf-8'),
#             raise_for_status=MagicMock(return_value=None)
#         )
#         # Mock generator install failure
#         mock_subprocess_run.side_effect = subprocess.CalledProcessError(1, "pip install", stderr="Install failed")
#
#         success = wizard.run()
#
#         assert success is False
#         assert "\n📦 Installing API generator (openapi-python-client)..." in mock_click_echo.call_args_list[-2].args[0]
#         assert "Failed to install openapi-python-client:   Install failed" in mock_click_echo.call_args_list[-1].args[0]
#
#     @patch('kbmanager.setup_wizard.click.prompt')
#     @patch('kbmanager.setup_wizard.requests.get')
#     @patch('kbmanager.setup_wizard.subprocess.run')
#     @patch('kbmanager.setup_wizard.SetupWizard.check_generator_installed', return_value=True)
#     def test_run_generate_client_failure(self, mock_check_generator, mock_subprocess_run,
#                                          mock_requests_get, mock_click_prompt, wizard, mock_filesystem):
#         """Test wizard when client generation command fails."""
#         mock_click_prompt.side_effect = [
#             "http://test.com",  # URL
#             "api_key_abc",      # API Key
#         ]
#         mock_requests_get.return_value = MagicMock(
#             status_code=200,
#             content=json.dumps({"openapi": "3.0.0"}).encode('utf-8'),
#             raise_for_status=MagicMock(return_value=None)
#         )
#         # Mock client generation failure
#         # Ensure that the mock side effect does NOT create the client folder
#         mock_subprocess_run.return_value = MagicMock(
#             returncode=1, stdout="Error", stderr="Generation failed"
#         )
#
#         success = wizard.run()
#
#         assert success is False # Should be False because the generated client folder won't exist in temp
#
#     @patch('kbmanager.setup_wizard.click.echo')
#     def test_save_config(self, mock_echo, wizard, mock_filesystem):
#         """Test _save_config method writes correct YAML to the config directory."""
#         mock_base_url = "http://test.server:8080"
#         mock_api_key = "test_123_abc"
#
#         wizard._save_config(mock_base_url, mock_api_key)
#
#         config_file_path = wizard.config_dir / CONFIG_FILE_NAMES[0]
#         assert config_file_path.is_file() # Check existence via mocked is_file
#         loaded_config = yaml.safe_load(config_file_path.read_text()) # Read via mocked read_text
#         assert loaded_config["base_url"] == mock_base_url
#         assert loaded_config["api_key"] == mock_api_key
#
#     @patch('kbmanager.setup_wizard.click.prompt')
#     @patch('kbmanager.setup_wizard.click.echo')
#     def test_load_existing_config_warning(self, mock_echo, mock_user_input, wizard, mock_filesystem):
#         """Test that a warning is issued if existing config file is unreadable/invalid."""
#         config_file_path = wizard.config_dir / CONFIG_FILE_NAMES[0]
#
#         # Simulate writing invalid YAML to the mock config file
#         # The 'read_text' mock will be called by safe_load eventually
#         config_file_path.write_text("invalid: yaml: content:") # Will raise YAMLError on load
#
#         mock_user_input.side_effect = [
#             "http://new.url",  # Base URL
#             "new_key",         # API Key
#         ]
#
#         # Mock HTTP requests and subprocess runs to prevent actual external calls
#         with patch('kbmanager.setup_wizard.requests.get', return_value=MagicMock(status_code=200, content=b'{}')), \
#              patch('kbmanager.setup_wizard.subprocess.run', return_value=MagicMock(returncode=0)):
#             wizard.run()
#
#         assert any("Warning: Could not read existing configuration" in call.args[0] for call in mock_echo.call_args_list)
