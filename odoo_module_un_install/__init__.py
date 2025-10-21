# -*- coding: utf-8 -*-
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# Date: 24.06.2025

"""Odoo Module (Un)Install Tool - Command-line tool for managing Odoo modules.

This package provides utilities for installing, uninstalling, and updating
Odoo modules across multiple server instances with features like parallel
processing, dependency analysis, and secure password management.

Modules:
    odoo_connection: Odoo RPC connection management and module operations.
    utils: Utility functions for YAML parsing and parallel processing.
    secure_login: Secure password management using system keyring.
    exceptions: Custom exception classes.
    version: Version information.

Example:
    >>> from odoo_module_un_install import OdooConnection
    >>> conn = OdooConnection('example.com', 443, 'admin')
    >>> conn.login()
    >>> conn.install_module('sale')
"""

# Only import version at module level to avoid circular import issues
from .version import __version__

__all__ = [
    '__version__',
    'OdooConnection',
    'exceptions',
    'utils',
    'secure_login',
]


# Lazy imports using __getattr__ to avoid dependency issues during setup
def __getattr__(name):
    """Lazy import for package modules to avoid circular dependencies."""
    import importlib

    if name == 'OdooConnection':
        mod = importlib.import_module('.odoo_connection', package=__name__)
        return mod.OdooConnection
    elif name in ('exceptions', 'utils', 'secure_login'):
        return importlib.import_module(f'.{name}', package=__name__)

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
