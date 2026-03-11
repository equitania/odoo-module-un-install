# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**odoo-module-un-install** is a command-line tool for managing Odoo modules across multiple server instances. It provides install, uninstall, and update operations with features like parallel processing, dependency analysis, and secure password management using system keyring.

**Key Features:**
- Multi-server operations from YAML configuration files
- Parallel processing for faster execution
- Dependency analysis to prevent breaking installations
- Secure credential storage with keyring support
- Detailed status reporting with colorful console output

## Development Setup

### Prerequisites
- Python >= 3.10
- UV package manager (NOT pip)

### Environment Setup
```bash
# Create and activate virtual environment
uv venv
source .venv/bin/activate.fish  # or use venv+ alias if available

# Install in editable/development mode
uv pip install -e .

# Install with dev dependencies
uv pip install -e ".[dev]"
```

## Essential Commands

### CLI Tool Commands
```bash
# Show help and version
odoo-un-install --help
odoo-un-install --version

# Run module operations
odoo-un-install run --server_path=./yaml_examples --module_path=./yaml_examples --install_modules
odoo-un-install run --server_path=./servers --module_path=./modules --uninstall_modules
odoo-un-install run --server_path=./servers --module_path=./modules --update_modules

# Show module status
odoo-un-install status --server_path=./yaml_examples

# Combined operations with all options
odoo-un-install run \
  --server_path=./servers \
  --module_path=./modules \
  --install_modules \
  --update_modules \
  --uninstall_modules \
  --check_dependencies \
  --parallel \
  --max_workers=10
```

### Development Commands
```bash
# Build package with UV (NOT python setup.py)
uv build

# Run single test (if tests exist)
pytest tests/test_specific.py -v

# Run all tests with coverage
pytest --cov=odoo_module_un_install tests/
```

## Architecture Overview

### Core Components

**Entry Point:**
- `odoo_module_un_install.py` - Click-based CLI with two main commands: `run` and `status`

**Key Modules:**
- `odoo_connection.py` - OdooRPC connection management and module operations
- `utils.py` - YAML parsing, parallel processing, dependency analysis
- `secure_login.py` - Keyring-based password management
- `exceptions.py` - Custom exception classes
- `version.py` - Version information (`__version__ = '1.2.0'`)

### Configuration System

The tool uses two types of YAML configuration files:

**Server Configuration (server_path):**
```yaml
Server:
  url: "https://your-odoo-server.com"
  port: 443
  user: "admin"
  password: "your-password"  # Optional with keyring
  database: "your-database"  # Optional, interactive selection
  use_keyring: true          # Store password in system keyring
```

**Module Configuration (module_path):**
```yaml
Install:
  - module_name_1
  - module_name_2
Uninstall:
  - module_name_3
  - module_name_4
```

### Operation Flow

1. **Connection Phase**: `collect_all_connections()` parses server YAML files and establishes OdooRPC connections
2. **Module Parsing**: `parse_yaml_folder()` reads module YAML files and separates Install/Uninstall lists
3. **Dependency Analysis** (optional): `analyze_dependencies()` checks module dependencies
4. **Execution Phase**: Either sequential or `process_modules_in_parallel()` with configurable workers
5. **Status Reporting**: `display_summary()` shows success/failure counts per server

### Parallel Processing

The tool supports parallel operations when `--parallel` flag is used:
- Default: 5 workers
- Configurable: `--max_workers=N`
- Uses ThreadPoolExecutor for concurrent server/module operations

## Version Management

**CRITICAL**: When updating the package:
1. Increment version in `odoo_module_un_install/version.py`
2. Use DD.MM.YYYY date format (e.g., 24.06.2025)
3. Update RELEASE_NOTES.md if exists
4. Use git commit prefix: `[CHG]` for version changes

Current version: `1.2.0`

## Package Management

**IMPORTANT**: This project uses UV package manager exclusively. All dependencies are managed in `pyproject.toml`.

```bash
# Install in editable mode
uv pip install -e .

# Install with dev dependencies
uv pip install -e ".[dev]"

# Build for PyPI distribution
uv build
```

## Dependencies

Core dependencies:
- **odoorpc-toolbox** (>=0.7.0) - Odoo server communication (Drop-in replacement for OdooRPC)
- **PyYAML** (>=6.0.2) - Configuration file parsing
- **click** (>=8.1.8) - CLI framework
- **colorama** (>=0.4.4) - Colored console output
- **tqdm** (>=4.62.0) - Progress bars
- **keyring** (>=23.0.0) - Secure password storage
- **python-dateutil** (>=2.8.2) - Date handling utilities

## Security Considerations

Password management priority:
1. System keyring (recommended, set `use_keyring: true`)
2. Environment variable `ODOO_PASSWORD`
3. YAML file (not recommended for production)
4. Interactive prompt

## Testing Single Components

```bash
# Test connection to specific server
odoo-un-install status --server_path=./yaml_examples

# Test single module installation
odoo-un-install run --server_path=./test_server --module_path=./test_module --install_modules

# Test with verbose logging
odoo-un-install run --verbose --server_path=./servers --module_path=./modules
```
