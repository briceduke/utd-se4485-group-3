# VS Code Extension Update Utility

A set of utilities for managing VS Code extensions in airgapped environments. The toolkit consists of two main utilities: a **Downloader** for packaging extensions and a **Deployer** for installing them, along with a lightweight **File Server** for distribution.


## Overview

This toolkit solves the challenge of updating VS Code extensions in airgapped (network-isolated) environments. Instead of requiring direct internet access on target machines, you can:

1. **Download** extensions on an internet-connected machine
2. **Package** them into a transferable archive with integrity verification
3. **Transfer** the archive to the airgapped environment
4. **Deploy** extensions to target VS Code installations

All operations are logged to syslog for audit and troubleshooting purposes.

## Features
- **Batch Extension Management**: Download and deploy multiple extensions at once
- **Version Control**: Specify exact versions or use "latest"
- **Integrity Verification**: SHA-256 checksums ensure file integrity
- **Flexible Deployment**: Multiple replace modes (NONE, REPLACE, CLEAN)
- **Backup Support**: Automatically backup existing extensions before deployment
- **Retry Logic**: Configurable retry attempts for network operations
- **Comprehensive Logging**: Logs to file, console, and/or syslog
- **Dry Run Mode**: Test deployments without making changes
- **Include/Exclude Filters**: Fine-grained control over which extensions to deploy

## Prerequisites

- **Python 3.8+**
- **Linux-based operating system** (for full syslog support)
- **Internet connection** (for the Downloader utility only)
- **VS Code** installed on target machines

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/briceduke/utd-se4485-group-3.git
cd utd-se4485-group-3
```

### 2. Set Up Development Environment

Use the provided Makefile to install dependencies and set up the virtual environment:

```bash
make dev-install
```

This command will:
- Create a Python virtual environment
- Install all required dependencies
- Build the utilities

### 3. Configure Environment Variables

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` to set your preferences:

```env
CORS_ORIGINS = "*"
PORT = 5000
HOST = "0.0.0.0"
DEBUG = false
```

## Quick Start

### Download Extensions

```bash
make run-dl
# or
python -m downloader --config downloader.yaml
```

### Deploy Extensions

```bash
make run-dp
# or
python -m deployer --config deployer.yaml
```

### Start File Server

```bash
python server/main.py
```

## Utilities

### Downloader

The Downloader utility fetches VS Code extensions from the Visual Studio Marketplace and packages them into a ZIP archive with a manifest file for integrity verification.

**Key Features:**
- Downloads VSIX packages for specified extensions
- Generates SHA-256 checksums for each file
- Creates a dated ZIP archive and JSON manifest
- Supports retry logic for failed downloads
- Logs all operations to syslog

**Output:**
- `everfox-extensions-YYYYMMDD.zip` - Archive containing all extensions
- `everfox-extensions-YYYYMMDD.json` - Manifest with checksums and metadata

### Deployer

The Deployer utility extracts and installs extensions from a downloaded archive to target VS Code installations.

**Key Features:**
- Fetches archives from a file server or URL
- Verifies file integrity using manifest checksums
- Multiple deployment modes (replace/skip existing extensions)
- Automatic backup of existing extensions
- Include/exclude filters for selective deployment
- Dry-run mode for testing

### File Server

A lightweight Flask-based HTTP server for distributing extension archives in airgapped environments.

**Key Features:**
- Serves ZIP archives and manifest files
- Lists available files via REST API
- CORS support for web-based tools
- Configurable via environment variables

**Endpoints:**
- `GET /` - List all available files
- `GET /zip/<filename>` - Download a specific ZIP archive
- `GET /manifest/<filename>` - Download a specific manifest file

## Configuration

### Downloader Configuration

Create a `downloader.yaml` file:

```yaml
# List of extensions to download
extensions:
  - name: "ms-python.python"
    version: latest
  - name: "ms-vscode.cpptools"
    version: latest
  - name: "redhat.java"
    version: "1.14.0"  # Specific version

# Output configuration
output:
  directory: "./server/files"
  name_template: "everfox-extensions-{{date}}.zip"

# Download configuration
download:
  retries: 3
  skip_failed: true

# Logging configuration
logging:
  level: INFO
  file: "./downloader.log"
  to_console: true
  to_syslog: true
```

#### Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `extensions` | List of extensions to download | Required |
| `extensions[].name` | Extension identifier (publisher.extension) | Required |
| `extensions[].version` | Version number or "latest" | Required |
| `output.directory` | Directory for output files | `./server/files` |
| `output.name_template` | ZIP filename template ({{date}} = YYYYMMDD) | `everfox-extensions-{{date}}.zip` |
| `download.retries` | Number of retry attempts | `3` |
| `download.skip_failed` | Continue if a download fails | `true` |
| `logging.level` | Log level (DEBUG, INFO, WARNING, ERROR) | `INFO` |
| `logging.file` | Log file path | `./downloader.log` |
| `logging.to_console` | Log to console | `false` |
| `logging.to_syslog` | Log to syslog | `true` |

### Deployer Configuration

Create a `deployer.yaml` file:

```yaml
# Plan configuration
plan:
  replace_mode: NONE  # NONE, REPLACE, or CLEAN
  backup_dir: "./backup"
  temp_dir: "./temp"
  include_extensions:
    - name: "ms-python.python"
      version: latest
  exclude_extensions:
    - name: "ms-vscode.vscode-json"
      version: latest

# Source configuration
source:
  archive_url: "http://localhost:5000/zip/everfox-extensions-20251031.zip"
  manifest_url: "http://localhost:5000/manifest/everfox-extensions-20251031.json"
  retries: 3

# Deployment configuration
deployment:
  target_dir: "~/.vscode/extensions"  # Linux/Mac
  # target_dir: "C:/Users/Username/.vscode/extensions"  # Windows
  verify_integrity: ERROR  # NONE, WARN, or ERROR
  dry_run: false

# Logging configuration
logging:
  level: INFO
  file: "./deployer.log"
  to_console: true
  to_syslog: true
```

#### Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `plan.replace_mode` | NONE (skip existing), REPLACE (update different versions), CLEAN (remove all and reinstall) | `NONE` |
| `plan.backup_dir` | Directory for backing up existing extensions | `./backup` |
| `plan.temp_dir` | Temporary directory for extraction | `./temp` |
| `plan.include_extensions` | Only deploy these extensions | `[]` (all) |
| `plan.exclude_extensions` | Skip these extensions | `[]` (none) |
| `source.archive_url` | URL to the ZIP archive | Required |
| `source.manifest_url` | URL to the manifest file | Required |
| `source.retries` | Number of retry attempts | `3` |
| `deployment.target_dir` | VS Code extensions directory | Required |
| `deployment.verify_integrity` | NONE (skip), WARN (log), ERROR (fail) | `ERROR` |
| `deployment.dry_run` | Test without making changes | `false` |
| `logging.level` | Log level (DEBUG, INFO, WARNING, ERROR) | `INFO` |
| `logging.file` | Log file path | `./deployer.log` |
| `logging.to_console` | Log to console | `true` |
| `logging.to_syslog` | Log to syslog | `false` |

## Usage

### Using YAML Configuration

This is the recommended approach for production use.

#### Download Extensions

```bash
# Using Makefile
make run-dl

# Using Python directly
python -m downloader --config downloader.yaml
```

#### Deploy Extensions

```bash
# Using Makefile
make run-dp

# Using Python directly
python -m deployer --config deployer.yaml
```

### Using CLI Flags

CLI flags override YAML configuration values.

#### Downloader CLI Flags

```bash
everfox-downloader \
  --config ./downloader.yaml \
  --extensions ms-python.python:latest ms-vscode.vscode-json:1.5.0 \
  --output ./downloads
```

**Available Flags:**

| Flag | Description | Example |
|------|-------------|---------|
| `--config` | Path to YAML config file | `--config downloader.yaml` |
| `--extensions` | Space-separated list of extensions (name:version) | `--extensions ms-python.python:latest` |
| `--output` | Output directory | `--output ./downloads` |

#### Deployer CLI Flags

```bash
everfox-deployer \
  --config ./deployer.yaml \
  --archive-url https://example.com/vscode-extensions.zip \
  --target-dir ~/.vscode/extensions \
  --verify-integrity error \
  --dry-run
```

**Available Flags:**

| Flag | Description | Example |
|------|-------------|---------|
| `--config` | Path to YAML config file | `--config deployer.yaml` |
| `--archive-url` | URL to ZIP archive | `--archive-url http://localhost:5000/zip/...` |
| `--manifest-url` | URL to manifest file | `--manifest-url http://localhost:5000/manifest/...` |
| `--target-dir` | VS Code extensions directory | `--target-dir ~/.vscode/extensions` |
| `--verify-integrity` | Integrity check mode (none/warn/error) | `--verify-integrity error` |
| `--dry-run` | Test without making changes | `--dry-run` |

## Examples

### Example 1: Basic Download and Deploy

**Step 1: Download Extensions**

```bash
# Create a simple downloader config
cat > downloader.yaml << EOF
extensions:
  - name: "ms-python.python"
    version: latest
  - name: "dbaeumer.vscode-eslint"
    version: latest
output:
  directory: "./server/files"
  name_template: "extensions-{{date}}.zip"
download:
  retries: 3
  skip_failed: true
logging:
  level: INFO
  file: "./downloader.log"
  to_syslog: true
EOF

# Run the downloader
python -m downloader --config downloader.yaml
```

**Step 2: Start File Server**

```bash
# In a new terminal
python server/main.py
```

**Step 3: Deploy Extensions**

```bash
# Create deployer config
cat > deployer.yaml << EOF
plan:
  replace_mode: REPLACE
  backup_dir: "./backup"
source:
  archive_url: "http://localhost:5000/zip/extensions-20251204.zip"
  manifest_url: "http://localhost:5000/manifest/extensions-20251204.json"
deployment:
  target_dir: "~/.vscode/extensions"
  verify_integrity: ERROR
  dry_run: false
logging:
  level: INFO
  to_console: true
EOF

# Run the deployer
python -m deployer --config deployer.yaml
```

### Example 2: Testing with Dry Run

```bash
# Test deployment without making changes
python -m deployer --config deployer.yaml --dry-run

# Review the logs
cat deployer.log
```

### Viewing Logs

**Syslog (Linux):**
```bash
# View recent logs
tail -f /var/log/syslog | grep everfox

# Search for errors
grep -i error /var/log/syslog
```

**Log Files:**
```bash
# View downloader logs
tail -f downloader.log

# View deployer logs
tail -f deployer.log

# View with colors (if installed)
ccze -A < downloader.log
```

### Debug Mode

Enable debug logging for detailed output:

```yaml
logging:
  level: DEBUG
  to_console: true
  to_syslog: true
```