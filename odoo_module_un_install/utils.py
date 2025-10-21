# -*- coding: utf-8 -*-
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# Date: 24.06.2025

"""Utility functions for Odoo module management operations."""

import yaml
import os
import logging
import tempfile
from typing import List, Dict, Callable, Optional, Union, Any
from pathlib import Path
import concurrent.futures
from tqdm import tqdm
from colorama import Fore, Style, init
from . import exceptions
from .odoo_connection import OdooConnection

# Initialize colorama
init()

# Configure logging with configurable log file location
_log_dir = os.environ.get('ODOO_MODULE_LOG_DIR', tempfile.gettempdir())
_log_file = os.path.join(_log_dir, 'odoo_module_un_install.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(_log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
logger.info(f"Logging to: {_log_file}")


def self_clean(input_dictionary: Dict[str, List]) -> Dict[str, List]:
    """Remove duplicate entries from dictionary values.

    Args:
        input_dictionary: Dictionary with list values to clean.

    Returns:
        Dictionary with deduplicated list values.

    Example:
        >>> self_clean({'modules': ['base', 'sale', 'base']})
        {'modules': ['base', 'sale']}
    """
    return_dict = input_dictionary.copy()
    for key, value in input_dictionary.items():
        return_dict[key] = list(dict.fromkeys(value))
    return return_dict


def parse_yaml(yaml_file: Union[str, Path]) -> Union[Dict[str, Any], bool]:
    """Parse YAML file and return its contents as a dictionary.

    Args:
        yaml_file: Path to the YAML file to parse.

    Returns:
        Parsed YAML content as dictionary, or False on error.

    Raises:
        FileNotFoundError: If the YAML file does not exist.
        yaml.YAMLError: If the YAML content is malformed.
    """
    try:
        with open(yaml_file, 'r', encoding='utf-8') as stream:
            try:
                return yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                logger.error(f"Error parsing YAML file {yaml_file}: {exc}")
                print(f"{Fore.RED}Error parsing {yaml_file}: {exc}{Style.RESET_ALL}")
                return False
    except FileNotFoundError:
        logger.error(f"YAML file not found: {yaml_file}")
        print(f"{Fore.RED}File not found: {yaml_file}{Style.RESET_ALL}")
        return False


def parse_yaml_folder(path: Union[str, Path]) -> List[Dict[str, Any]]:
    """Parse all YAML files in a directory and return their contents.

    Args:
        path: Path to directory containing YAML files.

    Returns:
        List of parsed YAML objects.

    Raises:
        PathDoesNotExistError: If the specified path does not exist.
    """
    yaml_objects = []
    try:
        if not os.path.exists(path):
            raise exceptions.PathDoesNotExistError(f"Path does not exist: {path}")

        for file in os.listdir(path):
            if file.endswith(".yaml") or file.endswith(".yml"):
                yaml_object = parse_yaml(os.path.join(path, file))
                if yaml_object:
                    yaml_objects.append(yaml_object)
                    logger.info(f"Parsed YAML file: {file}")

        if not yaml_objects:
            logger.warning(f"No valid YAML files found in {path}")
            print(f"{Fore.YELLOW}Warning: No valid YAML files found in {path}{Style.RESET_ALL}")

        return yaml_objects
    except exceptions.PathDoesNotExistError as e:
        logger.error(str(e))
        print(f"{Fore.RED}{str(e)}{Style.RESET_ALL}")
        raise


def create_odoo_connection_from_yaml_object(yaml_object: Dict[str, Any]) -> Optional[OdooConnection]:
    """Create an OdooConnection instance from a YAML configuration object.

    Args:
        yaml_object: Dictionary containing server configuration with keys:
            - url: Server URL (required)
            - port: Port number (optional, default: 0)
            - user: Username (required)
            - password: Password (optional)
            - database: Database name (optional)
            - use_keyring: Whether to use system keyring (optional, default: True)

    Returns:
        OdooConnection object if successful, None otherwise.

    Raises:
        ValueError: If required configuration keys are missing.
    """
    try:
        server_config = yaml_object.get('Server', {})
        url = server_config.get('url')
        port = server_config.get('port', 0)
        user = server_config.get('user')
        password = server_config.get('password')
        database = server_config.get('database')
        use_keyring = server_config.get('use_keyring', True)

        if not all([url, user]):
            missing = []
            if not url: missing.append('url')
            if not user: missing.append('user')
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")

        odoo_connection_object = OdooConnection(
            url, port, user, password, database, use_keyring
        )
        return odoo_connection_object
    except ValueError as e:
        logger.error(f"Invalid YAML configuration: {e}")
        print(f"{Fore.RED}Invalid configuration: {e}{Style.RESET_ALL}")
        return None
    except Exception as e:
        logger.error(f"Error creating connection: {e}")
        print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
        return None


def convert_all_yaml_objects(
    yaml_objects: List[Dict[str, Any]],
    converting_function: Callable[[Dict[str, Any]], Any]
) -> List[Any]:
    """Convert a list of YAML objects using a specified conversion function.

    Args:
        yaml_objects: List of YAML configuration dictionaries.
        converting_function: Function to convert each YAML object.

    Returns:
        List of successfully converted objects.

    Example:
        >>> yaml_objs = [{'Server': {'url': 'example.com', 'user': 'admin'}}]
        >>> connections = convert_all_yaml_objects(yaml_objs, create_odoo_connection_from_yaml_object)
    """
    local_object_list = []
    for yaml_object in yaml_objects:
        local_object = converting_function(yaml_object)
        if local_object:  # Only add if conversion was successful
            local_object_list.append(local_object)
    return local_object_list


def collect_all_connections(path: Union[str, Path]) -> List[OdooConnection]:
    """Parse YAML configuration files and create OdooConnection objects.

    Args:
        path: Path to directory containing server configuration YAML files.

    Returns:
        List of OdooConnection objects.

    Raises:
        PathDoesNotExistError: If the specified path does not exist.

    Example:
        >>> connections = collect_all_connections('./config/servers')
        >>> for conn in connections:
        ...     conn.login()
    """
    try:
        yaml_connection_objects = parse_yaml_folder(path)
        eq_connection_objects = convert_all_yaml_objects(
            yaml_connection_objects,
            create_odoo_connection_from_yaml_object
        )

        if not eq_connection_objects:
            logger.warning("No valid connections created from configuration files")
            print(f"{Fore.YELLOW}Warning: No valid connections created from configuration files{Style.RESET_ALL}")

        return eq_connection_objects
    except exceptions.PathDoesNotExistError as ex:
        logger.error(f"Path error: {ex}")
        raise


def process_modules_in_parallel(
    connection: OdooConnection,
    module_list: List[str],
    operation_func: Callable[[str], bool],
    max_workers: int = 5
) -> List[str]:
    """Process modules in parallel using a thread pool.

    Args:
        connection: OdooConnection object for the target server.
        module_list: List of module names to process.
        operation_func: Function to call for each module (e.g., install, uninstall, update).
        max_workers: Maximum number of concurrent workers (default: 5).

    Returns:
        List of successfully processed module names.

    Example:
        >>> def install(module): return connection.install_module(module)
        >>> successful = process_modules_in_parallel(conn, ['sale', 'crm'], install, max_workers=3)
    """
    successful_modules = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_module = {executor.submit(operation_func, module): module for module in module_list}

        with tqdm(total=len(module_list), desc=f"Processing modules on {connection.cleaned_url}") as pbar:
            for future in concurrent.futures.as_completed(future_to_module):
                module = future_to_module[future]
                try:
                    success = future.result()
                    if success:
                        successful_modules.append(module)
                except Exception as e:
                    logger.error(f"Error processing {module}: {e}")
                    print(f"{Fore.RED}Error processing {module}: {e}{Style.RESET_ALL}")
                pbar.update(1)

    return successful_modules


def analyze_dependencies(
    connection: OdooConnection,
    modules: List[str],
    operation: str = "uninstall"
) -> Dict[str, Union[List[str], Dict[str, List[str]]]]:
    """Analyze module dependencies for a given operation.

    Args:
        connection: OdooConnection object for the target server.
        modules: List of module names to analyze.
        operation: Operation type - "uninstall", "install", or "update" (default: "uninstall").

    Returns:
        Dictionary with the following keys:
            - ready: List of modules that can be processed immediately
            - dependent: Dict mapping modules to their dependencies or dependents
            - missing: List of modules not found in the system
            - not_installed: List of modules not installed (for uninstall/update)

    Example:
        >>> result = analyze_dependencies(conn, ['sale', 'crm'], operation="install")
        >>> print(f"Ready to install: {result['ready']}")
        >>> print(f"Missing dependencies: {result['dependent']}")
    """
    result = {
        'ready': [],       # Can be processed immediately
        'dependent': {},   # Modules with their dependents
        'missing': [],     # Modules not found
        'not_installed': [] # Modules not installed (for uninstall/update)
    }

    if operation == "uninstall":
        # For uninstallation, check if other modules depend on these
        for module in modules:
            try:
                dependents = connection.get_module_dependents(module)
                if dependents:
                    result['dependent'][module] = dependents
                else:
                    result['ready'].append(module)
            except exceptions.ModuleNotFoundError:
                result['missing'].append(module)
            except Exception as e:
                logger.error(f"Error analyzing dependencies for {module}: {e}")

    elif operation == "install":
        # For installation, check what dependencies these modules have
        for module in modules:
            try:
                deps = connection.get_module_dependencies(module)
                if deps:
                    # Check if all dependencies are installed
                    missing_deps = []
                    for dep in deps:
                        try:
                            dep_obj = connection._get_module_object(dep)
                            if dep_obj.state != 'installed':
                                missing_deps.append(dep)
                        except exceptions.ModuleNotFoundError:
                            missing_deps.append(dep)

                    if missing_deps:
                        result['dependent'][module] = missing_deps
                    else:
                        result['ready'].append(module)
                else:
                    result['ready'].append(module)
            except exceptions.ModuleNotFoundError:
                result['missing'].append(module)
            except Exception as e:
                logger.error(f"Error analyzing dependencies for {module}: {e}")

    elif operation == "update":
        # For update, the module must be installed
        for module in modules:
            try:
                module_obj = connection._get_module_object(module)
                if module_obj.state == 'installed':
                    result['ready'].append(module)
                else:
                    result['not_installed'].append(module)
            except exceptions.ModuleNotFoundError:
                result['missing'].append(module)
            except Exception as e:
                logger.error(f"Error analyzing status for {module}: {e}")

    return result


def display_module_status(connection: OdooConnection) -> None:
    """Display comprehensive module status information for an Odoo server.

    Args:
        connection: OdooConnection object for the target server.

    Returns:
        None. Prints formatted status information to console.

    Example:
        >>> conn = OdooConnection('example.com', 443, 'admin')
        >>> conn.login()
        >>> display_module_status(conn)
    """
    modules_status = connection.get_all_modules_status()

    print(f"\n{Fore.CYAN}=== Module Status for {connection.cleaned_url} ==={Style.RESET_ALL}")

    # Installed modules (green)
    installed = modules_status.get('installed', [])
    if installed:
        print(f"\n{Fore.GREEN}Installed Modules ({len(installed)}):{Style.RESET_ALL}")
        for i, module in enumerate(sorted(installed, key=lambda m: m['name']), 1):
            print(f"{i:4}. {module['name']} (v{module['version']})")

    # To upgrade modules (yellow)
    to_upgrade = modules_status.get('to upgrade', [])
    if to_upgrade:
        print(f"\n{Fore.YELLOW}Modules To Upgrade ({len(to_upgrade)}):{Style.RESET_ALL}")
        for module in sorted(to_upgrade, key=lambda m: m['name']):
            print(f"  • {module['name']} (v{module['version']})")

    # To install modules (blue)
    to_install = modules_status.get('to install', [])
    if to_install:
        print(f"\n{Fore.BLUE}Modules To Install ({len(to_install)}):{Style.RESET_ALL}")
        for module in sorted(to_install, key=lambda m: m['name']):
            print(f"  • {module['name']}")

    # To remove modules (red)
    to_remove = modules_status.get('to remove', [])
    if to_remove:
        print(f"\n{Fore.RED}Modules To Remove ({len(to_remove)}):{Style.RESET_ALL}")
        for module in sorted(to_remove, key=lambda m: m['name']):
            print(f"  • {module['name']} (v{module['version']})")

    total_modules = (
        len(installed) +
        len(to_install) +
        len(to_upgrade) +
        len(to_remove) +
        len(modules_status.get('uninstalled', []))
    )
    print(f"\n{Fore.CYAN}Total: {total_modules}{Style.RESET_ALL}")
