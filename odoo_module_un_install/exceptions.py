# -*- coding: utf-8 -*-
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""Custom exceptions for Odoo module management operations."""


class OdooConnectionError(Exception):
    """Raised when connection to Odoo server fails."""
    pass


class PathDoesNotExistError(Exception):
    """Raised when a specified path does not exist."""
    pass


class ModuleDependencyError(Exception):
    """Raised when module dependencies prevent operation."""
    pass


class OdooModuleNotFoundError(Exception):
    """Raised when a module could not be found in Odoo.

    Named with an ``Odoo`` prefix to avoid shadowing the Python builtin
    ``ModuleNotFoundError`` (a subclass of ``ImportError`` used by the import
    system), which would silently break any unqualified ``except`` clause.
    """
    pass
