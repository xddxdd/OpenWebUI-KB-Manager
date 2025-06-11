# kbmanager/setup_wizard.py

import json
import os
import shutil  # For rmtree
import tempfile
import subprocess
import sys
from pathlib import Path
from typing import Optional

import click
import requests
import yaml  # NEW: Import yaml

# Import ConfigManager components for saving config
from kbmanager.config_manager import APP_CONFIG_DIR, CONFIG_FILE_NAMES


class SetupWizard:
    def __init__(self):
        self.client_path = Path(__file__).parent / "open_web_ui_client"
        self.spec_filename = "openapi.json"

        # Ensure the config directory exists
        self.config_dir = APP_CONFIG_DIR
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def run(self) -> bool:
        """Run the setup wizard."""
        click.echo("🚀 KB-Manager Setup Wizard\n")

        # --- NEW STEP 1: Prompt for OpenWebUI URL and API Key ---
        click.echo("First, let's configure your OpenWebUI connection.")

        # Attempt to load existing config for defaults
        existing_url = ""
        existing_api_key = ""
        config_file_path = self._get_config_file_path()
        if config_file_path.exists():
            try:
                with open(config_file_path) as f:
                    existing_config = yaml.safe_load(f) or {}
                    existing_url = existing_config.get("base_url", "")
                    existing_api_key = existing_config.get("api_key", "")
            except Exception as e:
                click.echo(f"  Warning: Could not read existing configuration from {config_file_path}: {e}")

        openwebui_url = click.prompt(
            "Enter your OpenWebUI Base URL",
            default=existing_url if existing_url else "http://localhost:8080",
            show_default=True,
        ).rstrip("/")  # Ensure no trailing slash

        # Provide guidance for getting API key
        click.echo("\nTo get your OpenWebUI API Key:")
        click.echo("1. Log into your OpenWebUI instance (at the URL you just provided).")
        click.echo("2. Go to 'Settings' (gear icon) -> 'Account' -> 'API Keys' (tab).")
        click.echo("3. Click 'Create New Key' and copy the generated key.")

        api_key = click.prompt(
            "Enter your OpenWebUI API Key",
            default=existing_api_key if existing_api_key else "Paste your API Key here",
            hide_input=True,  # Mask input for security
            show_default=False,  # Don't show default for API key
        )

        # Save the collected config
        self._save_config(openwebui_url, api_key)
        click.echo(f"✅ Configuration saved to {config_file_path}\n")

        # --- Original Step 1 (now Step 2): Fetch OpenAPI Spec ---
        click.echo("Next, we'll fetch the OpenAPI specification to generate the API client.")
        spec_path = self.fetch_openapi_spec(openwebui_url)

        if not spec_path:
            click.echo("❌ Couldn't find OpenAPI spec automatically using common paths.")
            manual_url = click.prompt(
                "\nPlease enter the direct URL to your OpenAPI spec (e.g., from your browser's dev tools).\n"
                + f"(Hint: Check {openwebui_url}/docs or {openwebui_url}/api/docs for the spec link)",
                default="",
            )
            if manual_url:
                with_http_prefix = (
                    manual_url if manual_url.startswith(("http://", "https://")) else f"http://{manual_url}"
                )
                spec_path = self._download_file(with_http_prefix, self.spec_filename)

        if not spec_path:
            click.echo("\nSetup requires the OpenAPI specification. Exiting setup.")
            return False

        # --- Original Step 2 (now Step 3): Install generator if needed ---
        if not self.check_generator_installed():
            click.echo("\n📦 Installing API generator (openapi-python-client)...")
            try:
                subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "pip",
                        "install",
                        "openapi-python-client",
                        "--quiet",
                        "--disable-pip-version-check",
                    ],
                    check=True,
                    capture_output=True,
                )
                click.echo("Generator installed.")
            except subprocess.CalledProcessError as e:
                click.echo(f"  ❌ Failed to install openapi-python-client: {e.stdout.decode()} {e.stderr.decode()}")
                click.echo("    Please install it manually: pip install openapi-python-client")
                return False
            except FileNotFoundError:
                click.echo("  ❌ Python's pip executable not found. Please ensure Python is installed correctly.")
                return False

        # --- Original Step 3 (now Step 4): Generate client ---
        click.echo("\n🔨 Generating API client...")
        success = self.generate_client(spec_path)

        if success:
            click.echo("\n✅ KB-Manager setup complete!")
            click.echo("You can now start using 'kb-manager' commands.")
        return success

    # --- New Helper Methods for Co
    def _get_config_file_path(self) -> Path:
        """Determines the path for the config.yaml."""
        # Prioritize existing config files if they follow the naming convention
        for name in CONFIG_FILE_NAMES:
            path = self.config_dir / name
            if path.exists():
                return path
        # Default to the first name if no existing file found
        return self.config_dir / CONFIG_FILE_NAMES[0]

    def _save_config(self, base_url: str, api_key: str):
        """Saves base_url and api_key to ~/.kbmanager/config.yaml."""
        config_file = self._get_config_file_path()  # Use the determined path

        config_data = {"base_url": base_url, "api_key": api_key}

        try:
            with open(config_file, "w") as f:
                yaml.safe_dump(config_data, f)
        except Exception as e:
            click.echo(f"  ❌ Failed to save configuration to {config_file}: {e}", err=True)
            sys.exit(1)  # Exit if cannot save config

    # --- Existing Helper Methods (with minor adjustments) ---

    def _download_file(self, url: str, target_filename: str) -> Optional[Path]:
        # ... (same as before) ...
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            temp_path = Path.cwd() / target_filename
            with open(temp_path, "wb") as f:
                f.write(response.content)
            click.echo(f"  Downloaded: {url} to {temp_path}")
            return temp_path
        except requests.exceptions.RequestException as e:
            click.echo(f"  ❌ Failed to download {url}: {e}")
            return None
        except Exception as e:
            click.echo(f"  ❌ An unexpected error occurred during download: {e}")
            return None

    def fetch_openapi_spec(self, base_url: str) -> Optional[Path]:
        # ... (same as before, but ensure it calls self._download_file) ...
        # Ensure base_url passed here is the one collected from prompt
        possible_paths = [
            "/openapi.json",
            "/api/openapi.json",
            "/api/v1/openapi.json",
            "/docs/openapi.json",
            "/swagger.json",
            "/api/swagger.json",
        ]

        for path in possible_paths:
            full_url = base_url.rstrip("/") + path
            spec_path = self._download_file(full_url, self.spec_filename)  # Corrected to self._download_file
            if spec_path and spec_path.exists():
                click.echo(f"  Found OpenAPI spec at: {full_url}")
                try:
                    with open(spec_path) as f:
                        json.load(f)
                    return spec_path
                except json.JSONDecodeError:
                    click.echo(f"  Warning: Downloaded file at {spec_path} is not valid JSON. Trying next URL.")
                    spec_path.unlink(missing_ok=True)
                except Exception as e:
                    click.echo(f"  Warning: Could not read spec file {spec_path}: {e}. Trying next URL.")
                    spec_path.unlink(missing_ok=True)

        return None

    def check_generator_installed(self) -> bool:
        # ... (same as before) ...
        return bool(os.system("openapi-python-client --version > /dev/null 2>&1") == 0)

    def generate_client(self, spec_path: Path) -> bool:
        """Generates the API client using openapi-python-client."""

        # Clean up existing client directory first
        if self.client_path.exists():
            click.echo(f"  Deleting existing client at {self.client_path}...")
            try:
                shutil.rmtree(self.client_path)
            except OSError as e:
                click.echo(f"  ❌ Failed to delete existing client: {e}. Please delete manually.")
                return False

        # Create a temporary directory for generation
        temp_generate_dir = None
        try:
            temp_generate_dir = tempfile.mkdtemp()
            temp_output_path = Path(temp_generate_dir)  # This is where the "open_web_ui_client" folder will first appear

            # Create a basic config file for openapi-python-client
            config_content = """
            project_name: "open_web_ui_client"
            package_name: "open_web_ui_client"
            """
            config_file = Path(temp_generate_dir) / ".openapi-generator-config.yml"  # Put config file in temp dir
            with open(config_file, 'w') as f:
                f.write(config_content)

            cmd = [
                'openapi-python-client', 'generate',
                '--path', str(spec_path),
                '--output-path', str(temp_output_path),  # Output to the temp directory
                '--config', str(config_file),
                '--overwrite'
            ]
            click.echo(f"  Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)  # check=False for robustness

            ###
            # TODO: I am purposely suppressing the error here because the OWUI client generation fails for the full client
            # but the parts we need (like FileModelResponse, KnowledgeBaseResponse) are generated correctly.
            # Will need to discuss with OpenWebUI team to fix this in the future.
            ###

            if result.returncode != 0:
                # click.echo(
                #     f"\n--- WARNING: API client generation completed with non-zero exit code ({result.returncode}) ---")
                # click.echo("    This might mean there were issues generating parts of the client.")
                # click.echo(
                #     "    Check the stdout/stderr below for details. If the parts you need work, you can proceed.")
                # click.echo(f"    Command: {' '.join(cmd)}")
                # click.echo("    Stdout:")
                # click.echo(result.stdout)
                # if result.stderr:
                #     click.echo("    Stderr:")
                #     click.echo(result.stderr)
                # click.echo("--- End of Generation Warning ---\n")
                # # Even with warnings, if the crucial "open_web_ui_client" folder exists, we proceed to move it
                if not (temp_output_path / "open_web_ui_client").exists():
                    click.echo("❌ API client directory was not created even with warnings. Generation failed.")
                    return False
            # else:
            #     click.echo("  Generation output:")
            #     click.echo(result.stdout)
            #     if result.stderr:
            #         click.echo("  Generation warnings:")
            #         click.echo(result.stderr)

            # --- Move the generated "open_web_ui_client" folder ---
            # The generator creates a folder named after package_name inside output-path
            generated_client_folder = temp_output_path / "open_web_ui_client"
            if generated_client_folder.exists():
                click.echo(f"  Moving generated client from {generated_client_folder} to {self.client_path}...")
                shutil.move(str(generated_client_folder), str(self.client_path))
                click.echo("  Client moved successfully.")
                return True
            else:
                click.echo(
                    f"❌ Expected 'open_web_ui_client' folder not found in temporary directory: {temp_output_path}. Generation failed.")
                return False

        except FileNotFoundError:
            click.echo("  ❌ 'openapi-python-client' command not found. Ensure it's installed and in your PATH.")
            return False
        except Exception as e:
            click.echo(f"  ❌ An unexpected error occurred during client generation or move: {e}")
            return False
        finally:
            # Clean up the temporary directory generated by mkdtemp
            if temp_generate_dir and Path(temp_generate_dir).exists():
                shutil.rmtree(temp_generate_dir)
            # Clean up the downloaded spec file if it exists (it's in CWD by design)
            spec_path.unlink(missing_ok=True)
