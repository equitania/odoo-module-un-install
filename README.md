# Odoo Module (Un)Install Tool

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://pypi.org/project/odoo-module-un-install-equitania/)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-AGPL--3.0-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-production-brightgreen.svg)](RELEASE_NOTES.md)

A powerful command-line tool for managing Odoo modules across multiple server instances.

**Version 1.0.0 - Production Ready** 🚀

## Features

- Install, uninstall, and update Odoo modules
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

The tool provides two main commands:

1. `run` - Execute module operations (install, uninstall, update)
2. `status` - Display module status information

```bash
# Run operations
odoo-un-install run [OPTIONS]

# Show version
odoo-un-install --version

# Show module status
odoo-un-install status [OPTIONS]
```

### Available Options:

#### Global Options:

```bash
$ odoo-un-install --help
usage: odoo-un-install [--help] [--server_path] [--module_path] [--uninstall_modules] [--install_modules]
```
```bash
Optional arguments:
  --server_path       Server configuration folder
  --module_path       Modules folder
  --uninstall_modules Uninstall modules (y/n)
  --install_modules   Install modules (y/n)
  --help              Show this message and exit.
```
---

## Example
```bash
odoo-un-install --server_path=./connection_yaml --module_path=./module_yaml --uninstall_modules=y --install_modules=y
# v12 basis dbs
odoo-un-install --server_path=$HOME/gitbase/dev-helpers/yaml/v12-yaml-con --module_path=$HOME/gitbase/helper_script/v12/yaml --uninstall_modules=y --install_modules=y
# v13 basis dbs
odoo-un-install --server_path=$HOME/gitbase/dev-helpers/yaml/v13-yaml-con --module_path=$HOME/gitbase/helper_script/v13/yaml --uninstall_modules=y --install_modules=y
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

#### Server Configuration (YAML)

Create YAML files in your server configuration folder:

```yaml
Server:
  url: "https://your-odoo-server.com"
  port: 443
  user: "admin"
  password: "your-password"  # Optional, can be entered interactively
  database: "your-database"  # Optional, can be selected interactively
  use_keyring: true          # Whether to store password in system keyring
```

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
odoo-un-install run --server_path=./connection_yaml --module_path=./module_yaml --install_modules

# Uninstall modules
odoo-un-install run --server_path=./connection_yaml --module_path=./module_yaml --uninstall_modules

# Update modules
odoo-un-install run --server_path=./connection_yaml --module_path=./module_yaml --update_modules

# Install and update modules with dependency checking
odoo-un-install run --server_path=./connection_yaml --module_path=./module_yaml --install_modules --update_modules --check_dependencies

# Check module status
odoo-un-install status --server_path=./connection_yaml
```

Advanced examples:

```bash
# Complete operation with all options
odoo-un-install run --server_path=./connection_yaml --module_path=./module_yaml --uninstall_modules --install_modules --update_modules --check_dependencies --parallel --max_workers=10 --show_status --verbose

# v12 basis dbs with update
odoo-un-install run --server_path=$HOME/gitbase/dev-helpers/yaml/v12-yaml-con --module_path=$HOME/gitbase/helper_script/v12/yaml --uninstall_modules --install_modules --update_modules

# v13 basis dbs with parallel processing
odoo-un-install run --server_path=$HOME/gitbase/dev-helpers/yaml/v13-yaml-con --module_path=$HOME/gitbase/helper_script/v13/yaml --uninstall_modules --install_modules --update_modules --parallel
```

## Security

Passwords can be:
1. Stored in the YAML configuration file (not recommended for production)
2. Stored in the system keyring (secure)
3. Provided via environment variable `ODOO_PASSWORD`
4. Entered interactively when prompted

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
