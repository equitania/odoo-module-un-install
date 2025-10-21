# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-06-24

### Added
- Multi-server management via YAML configuration files
- Install, uninstall, and update operations for Odoo modules
- Parallel processing support with configurable worker count
- Dependency analysis before module operations
- Secure password management via system keyring
- Interactive database selection when not configured
- Comprehensive CLI with `run` and `status` commands
- Colorful console output with detailed progress reporting
- Verbose logging mode for debugging
- Status reporting with success/failure summaries
- Support for environment variable authentication
- Interactive password prompts as fallback
- YAML-based configuration system for servers and modules
- Error handling and recovery mechanisms
- ThreadPoolExecutor-based parallel execution

### Changed
- Comprehensive refactoring of codebase for production readiness
- Enhanced error handling and logging throughout
- Improved user experience with better console output
- Optimized performance with parallel processing capabilities

### Fixed
- Install and uninstall functions when module is not found
- Dependency resolution and validation
- Connection handling across multiple servers
- PyYAML compatibility (5.4.1) and OdooRPC updates

### Security
- System keyring integration for secure password storage
- No requirement for plaintext passwords in configuration files
- Environment variable support for automated deployments

## [0.1.0] - Initial Development

### Added
- Initial project structure
- Basic module installation/uninstallation functionality
- OdooRPC integration
- YAML configuration support
- Command-line interface foundation

---

[1.0.0]: https://gitlab.ownerp.io/pypi-packages/odoo-module-un-install/-/releases/v1.0.0
