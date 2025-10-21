# -*- coding: utf-8 -*-
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# Date: 24.06.2025

"""Test custom exceptions."""

import pytest
from odoo_module_un_install import exceptions


@pytest.mark.unit
def test_odoo_connection_error():
    """Test OdooConnectionError exception."""
    with pytest.raises(exceptions.OdooConnectionError):
        raise exceptions.OdooConnectionError("Test error")


@pytest.mark.unit
def test_path_does_not_exist_error():
    """Test PathDoesNotExistError exception."""
    with pytest.raises(exceptions.PathDoesNotExistError):
        raise exceptions.PathDoesNotExistError("Path does not exist")


@pytest.mark.unit
def test_module_dependency_error():
    """Test ModuleDependencyError exception."""
    with pytest.raises(exceptions.ModuleDependencyError):
        raise exceptions.ModuleDependencyError("Dependency error")


@pytest.mark.unit
def test_module_not_found_error():
    """Test ModuleNotFoundError exception."""
    with pytest.raises(exceptions.ModuleNotFoundError):
        raise exceptions.ModuleNotFoundError("Module not found")


@pytest.mark.unit
def test_exception_messages():
    """Test exception messages are preserved."""
    msg = "Custom error message"

    try:
        raise exceptions.OdooConnectionError(msg)
    except exceptions.OdooConnectionError as e:
        assert str(e) == msg

    try:
        raise exceptions.PathDoesNotExistError(msg)
    except exceptions.PathDoesNotExistError as e:
        assert str(e) == msg
