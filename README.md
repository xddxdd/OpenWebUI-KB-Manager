# KB-Manager

A command-line interface (CLI) tool for managing files and knowledge bases in OpenWebUI.

## Features

-   **Knowledge Base Management**: Create new knowledge bases and list existing ones.
-   **File Operations**: Upload, update, delete, and list files.
-   **Batch Directory Uploads**: Upload entire directories, with support for ignore patterns via `.kbignore` files.
-   **Flexible Configuration**: Configure via a local `config.yaml`, environment variables, or CLI arguments.
-   **JSON Output**: Optional JSON output for programmatic use and scripting.

## Installation

### Prerequisites

-   Python 3.11 or higher.
-   An active OpenWebUI instance.

### Install from Source 

```bash
git clone https://github.com/dubh3124/kb-manager.git
cd kb-manager
pip install -e .
```

## Getting Started

Because this tool no longer generates its own client, getting started is as simple as providing your API credentials. KB-Manager can be configured through multiple methods, which are loaded in the following order of precedence:

1.  **CLI Arguments** (`--api-key`, `--api-url`)
2.  **Environment Variables**
3.  **Configuration File**

### Step 1: Obtain Your API Key

Log in to your OpenWebUI instance, navigate to **Settings -> Account -> API Keys**, and create a new key.

### Step 2: Configure the Tool

Choose **one** of the following methods to configure `kb-manager`.

#### Method A: Configuration File (Recommended for Regular Use)

Create a configuration file at `~/.kbmanager/config.yaml`.

```bash
# Create the directory
mkdir -p ~/.kbmanager

# Create and edit the config file
nano ~/.kbmanager/config.yaml
```

Add the following content to the file:

```yaml
# ~/.kbmanager/config.yaml
api_key: "your_api_key_here"
base_url: "http://your-open-webui-instance:8080"
```

*You can also place a `config.yaml` file in your current working directory.*

#### Method B: Environment Variables

Set the following environment variables in your terminal session:

```bash
export KB_MANAGER_API_KEY="your_api_key_here"
export KB_MANAGER_BASE_URL="http://your-open-webui-instance:8080"
```

### Step 3: Verify Your Setup

Run the `list-kbs` command to check your connection.

```bash
kb-manager list-kbs
```

If successful, you will see a list of your existing knowledge bases.

## Usage

### Global Options

-   `--debug`: Enable verbose debug logging.
-   `--api-key`: Override the API key from config/environment.
-   `--api-url`: Override the base URL from config/environment.

### Commands

| Command | Description | Example Usage |
| :--- | :--- | :--- |
| `list-kbs` | Lists all knowledge bases. | `kb-manager list-kbs` <br> `kb-manager list-kbs --json` |
| `create-kb <name>` | Creates a new knowledge base. | `kb-manager create-kb "My Research Notes"` |
| `upload-file <path>` | Uploads a single file to a KB. | `kb-manager upload-file doc.pdf --kb-id <id>` |
| `upload-dir <path>` | Uploads a directory to a KB. | `kb-manager upload-dir my-project --kb-id <id>` <br> `kb-manager upload-dir . --kb-id <id> --prefix-paths` |
| `update-file <file_id>` | Updates an existing file's content. | `kb-manager update-file <id> new-doc.pdf` |
| `delete-file <file_id>` | Deletes a file by its ID. | `kb-manager delete-file <id>` |
| `list-files <kb_id>` | Lists files in a specific KB. | `kb-manager list-files <id> --search "report"` |
| `delete-all-files <kb_id>`| Deletes ALL files from a specific KB. | `kb-manager delete-all-files <id> --yes` |

## `.kbignore` Files

To exclude files during `upload-dir` operations, place a `.kbignore` file in the root of the directory you are uploading. The syntax is the same as `.gitignore`.

Example `.kbignore` content:

```gitignore
# Ignore all log files
*.log

# Ignore specific directories
__pycache__/
build/
.git/
.idea/

# Ignore this file itself
.kbignore
```

## Development and Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Running Tests

```bash
# Install test dependencies
pip install -e ".[test]"

# Run tests
pytest
```

### Versioning and Releases

This project uses **[python-semantic-release](https://python-semantic-release.readthedocs.io/en/latest/)** to automate versioning and releases based on the **[Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/)** specification.

Releases are automatically triggered when commits are merged into the `main` branch.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

Built for seamless integration with [OpenWebUI](https://github.com/open-webui/open-webui).