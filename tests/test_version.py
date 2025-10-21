# -*- coding: utf-8 -*-
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# Date: 24.06.2025

"""Test version module."""

import pytest
from odoo_module_un_install.version import __version__


@pytest.mark.unit
def test_version_exists():
    """Test that version string exists."""
    assert __version__ is not None


@pytest.mark.unit
def test_version_format():
    """Test that version follows semantic versioning."""
    assert isinstance(__version__, str)
    parts = __version__.split('.')
    assert len(parts) == 3, "Version should be in format X.Y.Z"
    for part in parts:
        assert part.isdigit(), f"Version part '{part}' should be numeric"


@pytest.mark.unit
def test_version_value():
    """Test that version is 1.0.0."""
    assert __version__ == '1.0.0'
