# Release Notes

## Version 1.2.0 (11.03.2026)

### Changed
- Migrated from OdooRPC to odoorpc-toolbox (drop-in replacement with internalized OdooRPC)
- Migrated build system from setup.py to pyproject.toml with Hatchling backend
- Replaced black + isort + flake8 with ruff for linting and formatting
- Refactored `run()` command: extracted duplicated uninstall/install/update logic into `_process_operation()` helper (130 lines reduced)
- Removed `setup.py`, `requirements.txt`, and `requirements-dev.txt` (consolidated in pyproject.toml)
- Minimum Python version raised to 3.10

### Fixed
- Fixed test_version.py expecting outdated version string
- Fixed unused variable in `get_module_dependents()`
- Fixed trailing whitespace and import sorting across codebase

---

## Version 1.1.7 (19.11.2025)

### Bug Fixes

#### Module Status Reporting
- **Fixed**: Modules that were already installed are now correctly counted as success instead of failure
- **Fixed**: Modules that were already uninstalled are now correctly counted as success instead of failure

**Details**:
The tool previously treated "already in desired state" as a failure, which was incorrect. When a module was already installed and the user requested installation, this should be considered a success (the module is in the desired state). The same logic applies to uninstallation.

**Impact**:
- Summary reports now correctly reflect successful operations
- Success/Failure counts are accurate
- Users no longer see standard modules incorrectly reported as failures

### Technical Changes
- Modified `install_module()` to return `True` when module is already installed
- Modified `uninstall_module()` to return `True` when module is already uninstalled
- Updated docstrings to reflect the corrected behavior

---

## Version 1.0.0 (24.06.2025)

### Production Release

This is the first production-ready release of the Odoo Module (Un)Install Tool. The tool has been thoroughly tested and is ready for production use.

### New Features

#### Core Functionality
- **Multi-Server Management**: Process multiple Odoo server instances from YAML configuration files
- **Module Operations**: Install, uninstall, and update modules across servers
- **Parallel Processing**: Execute operations in parallel for faster execution (`--parallel` flag)
- **Dependency Analysis**: Intelligent dependency checking before operations (`--check_dependencies` flag)
- **Secure Authentication**: Password management via system keyring, environment variables, or interactive prompts

#### CLI Commands
- **run**: Execute module operations (install/uninstall/update) on Odoo servers
  - `--install_modules`: Install modules defined in YAML files
  - `--uninstall_modules`: Uninstall modules defined in YAML files
  - `--update_modules`: Update existing modules
  - `--check_dependencies`: Check module dependencies before operations
  - `--parallel`: Enable parallel processing
  - `--max_workers`: Configure number of parallel workers (default: 5)
  - `--show_status`: Display detailed module status after operations
  - `--verbose`: Enable verbose output for debugging

- **status**: Display detailed module status information without performing any modifications

#### Configuration System
- **Server Configuration**: YAML-based server connection settings
  - URL, port, user, password (optional with keyring)
  - Database selection (interactive or configured)
  - Keyring integration for secure password storage

- **Module Configuration**: YAML-based module operation definitions
  - Install: List of modules to install
  - Uninstall: List of modules to uninstall
  - Update: List of modules to update

#### User Experience
- **Colorful Output**: Enhanced console output with colors and formatting
- **Progress Reporting**: Detailed status and summary reports
- **Error Handling**: Comprehensive error handling and logging
- **Validation**: Pre-operation validation and warnings

### Technical Improvements

#### Architecture
- Click-based CLI framework for robust command handling
- OdooRPC integration for reliable Odoo server communication
- ThreadPoolExecutor for efficient parallel processing
- Modular code structure with separation of concerns

#### Security
- System keyring integration for secure password storage
- Environment variable support for automation scenarios
- No plaintext password requirements in configuration files

#### Performance
- Configurable parallel processing (1-N workers)
- Efficient batch operations across multiple servers
- Smart dependency resolution to minimize operations

### Code Quality
- Comprehensive refactoring for maintainability
- UTF-8 encoding support for international characters
- Proper exception handling throughout
- Detailed logging system for debugging

### Dependencies
- OdooRPC >= 0.10.1
- PyYAML >= 6.0.2
- click >= 8.1.8
- colorama >= 0.4.4
- tqdm >= 4.62.0
- keyring >= 23.0.0
- python-dateutil >= 2.8.2

### Python Support
- Python 3.8+
- Tested on Python 3.8, 3.9, 3.10, 3.11, 3.12

### Installation

```bash
pip install odoo-module-un-install-equitania
```

### Usage Examples

```bash
# Install modules with dependency checking
odoo-un-install run --server_path=./servers --module_path=./modules --install_modules --check_dependencies

# Update modules in parallel
odoo-un-install run --server_path=./servers --module_path=./modules --update_modules --parallel --max_workers=10

# Complete operation with all features
odoo-un-install run --server_path=./servers --module_path=./modules --install_modules --uninstall_modules --update_modules --check_dependencies --parallel --show_status

# Show module status
odoo-un-install status --server_path=./servers
```

### Breaking Changes
None (initial production release)

### Known Issues
None

### Migration Guide
This is the first production release. No migration required.

### Contributors
- Equitania Software GmbH

### License
AGPL-3.0 or later

---

For detailed usage instructions, see [README.md](README.md)
