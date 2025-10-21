# -*- coding: utf-8 -*-
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# Date: 24.06.2025

"""Test utility functions."""

import pytest
import tempfile
import os
import yaml
from odoo_module_un_install import utils, exceptions


@pytest.mark.unit
def test_self_clean():
    """Test self_clean function removes duplicates."""
    input_dict = {
        'modules': ['base', 'sale', 'base', 'crm'],
        'servers': ['server1', 'server2', 'server1']
    }
    result = utils.self_clean(input_dict)

    assert result['modules'] == ['base', 'sale', 'crm']
    assert result['servers'] == ['server1', 'server2']


@pytest.mark.unit
def test_self_clean_empty():
    """Test self_clean with empty dictionary."""
    result = utils.self_clean({})
    assert result == {}


@pytest.mark.unit
def test_parse_yaml_valid_file():
    """Test parsing valid YAML file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml_content = {'Server': {'url': 'example.com', 'user': 'admin'}}
        yaml.dump(yaml_content, f)
        temp_file = f.name

    try:
        result = utils.parse_yaml(temp_file)
        assert result is not False
        assert result['Server']['url'] == 'example.com'
        assert result['Server']['user'] == 'admin'
    finally:
        os.unlink(temp_file)


@pytest.mark.unit
def test_parse_yaml_nonexistent_file():
    """Test parsing non-existent YAML file."""
    result = utils.parse_yaml('/nonexistent/file.yaml')
    assert result is False


@pytest.mark.unit
def test_parse_yaml_folder():
    """Test parsing folder with YAML files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create valid YAML files
        yaml1 = os.path.join(tmpdir, 'server1.yaml')
        yaml2 = os.path.join(tmpdir, 'server2.yml')

        with open(yaml1, 'w') as f:
            yaml.dump({'Server': {'url': 'server1.com'}}, f)

        with open(yaml2, 'w') as f:
            yaml.dump({'Server': {'url': 'server2.com'}}, f)

        result = utils.parse_yaml_folder(tmpdir)
        assert len(result) == 2
        assert any(obj['Server']['url'] == 'server1.com' for obj in result)
        assert any(obj['Server']['url'] == 'server2.com' for obj in result)


@pytest.mark.unit
def test_parse_yaml_folder_nonexistent():
    """Test parsing non-existent folder."""
    with pytest.raises(exceptions.PathDoesNotExistError):
        utils.parse_yaml_folder('/nonexistent/folder')


@pytest.mark.unit
def test_convert_all_yaml_objects():
    """Test converting YAML objects."""
    yaml_objects = [
        {'value': 1},
        {'value': 2},
        {'value': 3}
    ]

    def multiply_by_two(obj):
        return obj['value'] * 2

    result = utils.convert_all_yaml_objects(yaml_objects, multiply_by_two)
    assert result == [2, 4, 6]


@pytest.mark.unit
def test_convert_all_yaml_objects_with_none():
    """Test converting YAML objects that may return None."""
    yaml_objects = [
        {'value': 1},
        {'value': None},
        {'value': 3}
    ]

    def process_value(obj):
        return obj['value'] if obj['value'] is not None else None

    result = utils.convert_all_yaml_objects(yaml_objects, process_value)
    # None values should be filtered out
    assert result == [1, 3]


@pytest.mark.unit
def test_parse_env_file_valid():
    """Test parsing valid .env file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("ODOO_URL=https://example.com\n")
        f.write("ODOO_PORT=443\n")
        f.write("ODOO_USER=admin\n")
        f.write("ODOO_PASSWORD=secret\n")
        f.write("ODOO_DATABASE=testdb\n")
        f.write("ODOO_USE_KEYRING=true\n")
        temp_file = f.name

    try:
        result = utils.parse_env_file(temp_file)
        assert result is not False
        assert result['url'] == 'https://example.com'
        assert result['port'] == 443
        assert result['user'] == 'admin'
        assert result['password'] == 'secret'
        assert result['database'] == 'testdb'
        assert result['use_keyring'] is True
    finally:
        os.unlink(temp_file)


@pytest.mark.unit
def test_parse_env_file_minimal():
    """Test parsing .env file with only required fields."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
        f.write("ODOO_URL=http://localhost\n")
        f.write("ODOO_USER=admin\n")
        temp_file = f.name

    try:
        result = utils.parse_env_file(temp_file)
        assert result is not False
        assert result['url'] == 'http://localhost'
        assert result['user'] == 'admin'
        assert result['port'] == 0  # Default value
        assert result['password'] is None
        assert result['database'] is None
        assert result['use_keyring'] is True  # Default value
    finally:
        os.unlink(temp_file)


@pytest.mark.unit
def test_parse_env_file_nonexistent():
    """Test parsing non-existent .env file."""
    result = utils.parse_env_file('/nonexistent/file.env')
    assert result is False


@pytest.mark.unit
def test_parse_env_folder():
    """Test parsing folder with .env files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create valid .env files
        env1 = os.path.join(tmpdir, 'production.env')
        env2 = os.path.join(tmpdir, 'staging.env')

        with open(env1, 'w') as f:
            f.write("ODOO_URL=https://production.com\n")
            f.write("ODOO_USER=admin\n")

        with open(env2, 'w') as f:
            f.write("ODOO_URL=https://staging.com\n")
            f.write("ODOO_USER=admin\n")

        result = utils.parse_env_folder(tmpdir)
        assert len(result) == 2
        assert any(obj['url'] == 'https://production.com' for obj in result)
        assert any(obj['url'] == 'https://staging.com' for obj in result)


@pytest.mark.unit
def test_parse_env_folder_mixed():
    """Test parsing folder with both YAML and .env files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create .env file
        env_file = os.path.join(tmpdir, 'server.env')
        with open(env_file, 'w') as f:
            f.write("ODOO_URL=https://env-server.com\n")
            f.write("ODOO_USER=admin\n")

        # Create YAML file
        yaml_file = os.path.join(tmpdir, 'server.yaml')
        with open(yaml_file, 'w') as f:
            yaml.dump({'Server': {'url': 'https://yaml-server.com', 'user': 'admin'}}, f)

        # Test env parsing
        env_result = utils.parse_env_folder(tmpdir)
        assert len(env_result) >= 1
        assert any(obj['url'] == 'https://env-server.com' for obj in env_result)

        # Test yaml parsing
        yaml_result = utils.parse_yaml_folder(tmpdir)
        assert len(yaml_result) >= 1
        assert any(obj['Server']['url'] == 'https://yaml-server.com' for obj in yaml_result)
