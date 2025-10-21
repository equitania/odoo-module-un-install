# Odoo Module (Un)Install Tool

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://pypi.org/project/odoo-module-un-install-equitania/)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-AGPL--3.0-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-production-brightgreen.svg)](RELEASE_NOTES.md)

A powerful command-line tool for managing Odoo modules across multiple server instances.

**Version 1.0.0 - Production Ready** 🚀

## Features

- Install, uninstall, and update Odoo modules
- Export installed modules to YAML configuration files
- Process multiple Odoo servers in a single operation
- Secure password management with keyring support
- Dependencies analysis to prevent breaking installations
- Parallel processing for faster operations
- Detailed status reporting
- Colorful and informative console output
- Comprehensive logging system

## Installation

### Requirements:

- Python (>= 3.8)
- OdooRPC (>= 0.10.1)
- PyYaml (>= 6.0.2)
- python-dotenv (>= 1.0.0)
- click (>= 8.1.8)
- colorama (>= 0.4.4)
- tqdm (>= 4.62.0)
- keyring (>= 23.0.0)
- python-dateutil (>= 2.8.2)

Use pip to install the package:

```bash
pip install odoo-module-un-install-equitania
```

## Usage

### Command Line Interface

The tool provides three main commands:

1. `run` - Execute module operations (install, uninstall, update)
2. `status` - Display module status information
3. `export` - Export installed modules to YAML file

```bash
# Run operations
odoo-un-install run [OPTIONS]

# Show version
odoo-un-install --version

# Show module status
odoo-un-install status [OPTIONS]

# Export installed modules
odoo-un-install export [OPTIONS]
```

### Available Options:

#### Run Command Options:

```bash
$ odoo-un-install run --help

Options:
  --server_path DIRECTORY  Path to folder containing .env server configuration files
  --module_path DIRECTORY  Path to folder containing module configuration files
  --uninstall_modules      Uninstall modules defined in "Uninstall" section
  --install_modules        Install modules defined in "Install" section
  --update_modules         Update modules defined in "Install" section
  --check_dependencies     Check module dependencies before operations (recommended)
  --parallel               Process modules in parallel for faster execution
  --max_workers INTEGER    Maximum number of parallel workers [default: 5]
  --show_status            Show detailed module status report after operations
  -v, --verbose            Enable verbose output for debugging
  --help                   Show this message and exit
```

#### Status Command Options:

```bash
$ odoo-un-install status --help

Options:
  --server_path DIRECTORY  Path to folder containing .env server configuration files
  -v, --verbose            Enable verbose output for debugging
  --help                   Show this message and exit
```

#### Export Command Options:

```bash
$ odoo-un-install export --help

Options:
  --server_path DIRECTORY  Path to folder containing .env server configuration files
  --output FILE            Output YAML file path
  --include-base           Include base Odoo modules (default: exclude)
  --states TEXT            Module states to export (comma-separated)
                           Options: installed,to upgrade,to install,to remove
  -v, --verbose            Enable verbose output for debugging
  --help                   Show this message and exit
```
---

## Quick Start Example
```bash
# Basic usage with .env configuration
odoo-un-install run --server_path=./env_configs --module_path=./modules_yaml --install_modules --uninstall_modules

# Using custom configuration paths
odoo-un-install run --server_path=$HOME/configs/servers --module_path=$HOME/configs/modules --install_modules --update_modules
```

## Module Update Guide

### How to Update Modules

To update existing modules, use the `--update_modules` flag:

```bash
odoo-un-install run --server_path=./servers --module_path=./modules --update_modules
```

The tool will use the modules listed in the `Install` section of your YAML files:

```yaml
Install:
  - module_to_update_1
  - module_to_update_2
```

### Update Process

When running with the `--update_modules` flag:

1. The tool connects to each configured Odoo server
2. For each module in the `Install` section:
   - If the module is already installed, it will be updated to the latest version
   - If the module is not installed, it will be skipped (unless `--install_modules` is also specified)

### Combined Operations

You can combine update with installation and dependency checking:

```bash
odoo-un-install run --server_path=./servers --module_path=./modules --update_modules --install_modules --check_dependencies
```

This will:
- Install modules that are not yet installed
- Update modules that are already installed
- Check dependencies before performing operations

### Configuration Files

#### Server Configuration (.env)

Create .env files in your server configuration folder:

```bash
# Required fields
ODOO_URL=https://your-odoo-server.com
ODOO_USER=admin

# Optional fields
ODOO_PORT=443
ODOO_PASSWORD=your-password
ODOO_DATABASE=your-database
ODOO_USE_KEYRING=true
```

**Benefits of .env format:**
- Industry-standard configuration format
- Better IDE support and syntax highlighting
- Easier integration with environment variables
- Compatible with Docker and CI/CD pipelines

**File naming:** `production.env`, `staging.env`, `localhost.env`, etc.

For complete .env examples and documentation, see the [env_examples/](env_examples/) directory.

#### Module Configuration (YAML)

Create YAML files in your module configuration folder:

```yaml
Install:
  - module_name_1
  - module_name_2
Uninstall:
  - module_name_3
  - module_name_4
```

### Examples

Basic usage:

```bash
# Install modules
odoo-un-install run --server_path=./env_configs --module_path=./modules_yaml --install_modules

# Uninstall modules
odoo-un-install run --server_path=./env_configs --module_path=./modules_yaml --uninstall_modules

# Update modules
odoo-un-install run --server_path=./env_configs --module_path=./modules_yaml --update_modules

# Install and update modules with dependency checking
odoo-un-install run --server_path=./env_configs --module_path=./modules_yaml --install_modules --update_modules --check_dependencies

# Check module status
odoo-un-install status --server_path=./env_configs

# Export installed modules to YAML
odoo-un-install export --server_path=./env_configs --output=my_modules.yaml
```

Export examples:

```bash
# Export only installed modules (excluding base Odoo modules)
odoo-un-install export --server_path=./env_configs --output=installed_modules.yaml

# Export all modules including base Odoo modules
odoo-un-install export --server_path=./env_configs --output=all_modules.yaml --include-base

# Export modules that need upgrade
odoo-un-install export --server_path=./env_configs --output=upgrade_modules.yaml --states="to upgrade"

# Export multiple states (installed + to upgrade)
odoo-un-install export --server_path=./env_configs --output=multi_state.yaml --states="installed,to upgrade"
```

**Export Output Format:**

The export command generates a structured YAML file with modules organized by category:

```yaml
# Server: https://example.odoo.com
# Database: production_db
# Odoo Version: 18
# Export Date: 2025-06-24 10:30:45
# Total Modules: 45

Install:
  # Accounting (12 modules)
  - account
  - account_invoicing
  - account_payment
  - account_reports

  # CRM (5 modules)
  - crm
  - crm_livechat
  - crm_phone_validation

  # Human Resources (8 modules)
  - hr
  - hr_attendance
  - hr_holidays
  - hr_recruitment

  # Sales (10 modules)
  - sale
  - sale_management
  - sale_crm
  - sale_stock

  # Website (10 modules)
  - website
  - website_blog
  - website_crm
  - website_sale

Uninstall: []
```

**Features:**
- Modules grouped and sorted by English category names
- German category names automatically translated to English
- Module count displayed for each category
- Server and database information in header comments
- Base Odoo modules excluded by default (use `--include-base` to include)

Advanced examples:

```bash
# Complete operation with all options
odoo-un-install run --server_path=./env_configs --module_path=./modules_yaml --uninstall_modules --install_modules --update_modules --check_dependencies --parallel --max_workers=10 --show_status --verbose

# Multiple servers with update
odoo-un-install run --server_path=$HOME/configs/odoo_servers --module_path=$HOME/configs/odoo_modules --uninstall_modules --install_modules --update_modules

# Parallel processing across multiple servers
odoo-un-install run --server_path=$HOME/configs/odoo_servers --module_path=$HOME/configs/odoo_modules --uninstall_modules --install_modules --update_modules --parallel
```

## Security

### Password Management Priority

The tool uses passwords in the following priority order:

1. **Environment variable** `ODOO_PASSWORD` (if set in .env file or shell environment)
2. **System keyring** (if `use_keyring: true` or `ODOO_USE_KEYRING=true`)
3. **Interactive prompt** (fallback if no password found)

### Recommendations

**For Production Servers:**
```bash
ODOO_URL=https://production.example.com
ODOO_USER=admin
ODOO_PASSWORD=              # Leave empty
ODOO_USE_KEYRING=true      # Use system keyring for secure storage
```

**For Development:**
```bash
ODOO_URL=http://localhost
ODOO_PORT=8069
ODOO_USER=admin
ODOO_PASSWORD=admin        # OK for local development
ODOO_USE_KEYRING=false
```

**For CI/CD Pipelines:**
```bash
ODOO_URL=https://staging.example.com
ODOO_USER=ci_user
ODOO_PASSWORD=${CI_ODOO_PASSWORD}  # From CI secrets
ODOO_USE_KEYRING=false
```

**⚠️ Important:** Never commit .env files with passwords to version control! Add `*.env` to your `.gitignore` (excluding templates like `template.env.example`)

## Local Testing

### Development Installation

```bash
# 1. Clone or navigate to the project directory
cd /path/to/odoo-module-un-install

# 2. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# or on Windows: .venv\Scripts\activate

# 3. Install dependencies with UV (recommended)
pip install uv
uv pip install -r requirements.txt

# 4. Install package in editable mode
uv pip install -e .

# 5. Verify installation
odoo-un-install --version
odoo-un-install --help
```

### Test Configuration Setup

```bash
# Create test directories
mkdir -p test_config/servers
mkdir -p test_config/modules

# Create test .env server configuration
cat > test_config/servers/localhost.env << 'EOF'
ODOO_URL=http://localhost
ODOO_PORT=8069
ODOO_USER=admin
ODOO_PASSWORD=admin
ODOO_DATABASE=test_db
ODOO_USE_KEYRING=false
EOF

# Create test module YAML configuration
cat > test_config/modules/test_modules.yaml << 'EOF'
Install:
  - base
  - sale_management

Uninstall:
  - website_blog
EOF
```

### Running Tests

```bash
# Test connection to server
odoo-un-install status --server_path=test_config/servers

# Test module installation with verbose output
odoo-un-install run \
  --server_path=test_config/servers \
  --module_path=test_config/modules \
  --install_modules \
  --verbose

# Test with example configurations
odoo-un-install run \
  --server_path=./env_examples \
  --module_path=./yaml_examples/modules_yaml \
  --install_modules \
  --verbose

# Run unit tests
pytest tests/ -v

# Run tests with coverage
pytest --cov=odoo_module_un_install tests/
```

### Testing Checklist

- ✅ Package installs without errors
- ✅ CLI commands work (`--version`, `--help`)
- ✅ .env files are parsed correctly
- ✅ Connection to Odoo server succeeds
- ✅ Module operations (install/uninstall/update) work
- ✅ All unit tests pass (21/21)
- ✅ Verbose logging shows detailed information

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a detailed history of changes.

For release notes of the current version, see [RELEASE_NOTES.md](RELEASE_NOTES.md).

## License

This project is licensed under the terms of the **AGPLv3** license.

## Support

For questions and support, please open an issue on the GitHub repository.

## Contributors

- **Equitania Software GmbH** - [Website](https://www.equitania.de)

## Acknowledgments

This tool is built with:
- [OdooRPC](https://github.com/OCA/odoorpc) - Odoo RPC client library
- [Click](https://click.palletsprojects.com/) - Command-line interface framework
- [Colorama](https://github.com/tartley/colorama) - Terminal color support
