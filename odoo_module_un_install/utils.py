# -*- coding: utf-8 -*-
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

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
from dotenv import dotenv_values
from . import exceptions
from .odoo_connection import OdooConnection

# Initialize colorama
init()

# Get logger for this module (configuration happens in CLI)
logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> str:
    """Configure logging for the application.

    Args:
        verbose: If True, show INFO+ on console. If False, only WARNING+ (default: False).

    Returns:
        Path to the log file.

    Example:
        >>> log_file = setup_logging(verbose=True)
        >>> logger.info("This will be shown on console and in file")
    """
    # Configure log file location
    log_dir = os.environ.get('ODOO_MODULE_LOG_DIR', tempfile.gettempdir())
    log_file = os.path.join(log_dir, 'odoo_module_un_install.log')

    # Remove existing handlers to avoid duplicates
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # File handler - logs everything INFO and above
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    # Console handler - only WARNING+ unless verbose
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO if verbose else logging.WARNING)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)

    # Configure root logger
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    logger.debug(f"Logging to: {log_file}")
    return log_file


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


def parse_env_file(env_file: Union[str, Path]) -> Union[Dict[str, Any], bool]:
    """Parse .env file and return its contents as a dictionary.

    Args:
        env_file: Path to the .env file to parse.

    Returns:
        Parsed .env content as dictionary with server configuration, or False on error.

    Example:
        >>> config = parse_env_file('.env')
        >>> print(config['url'])
        https://odoo.com
    """
    try:
        if not os.path.exists(env_file):
            raise FileNotFoundError(f".env file not found: {env_file}")

        # Load .env file
        env_values = dotenv_values(env_file)

        # Convert to server config format (compatible with YAML structure)
        server_config = {
            'url': env_values.get('ODOO_URL'),
            'port': int(env_values.get('ODOO_PORT', 0)) if env_values.get('ODOO_PORT') else 0,
            'user': env_values.get('ODOO_USER'),
            'password': env_values.get('ODOO_PASSWORD'),
            'database': env_values.get('ODOO_DATABASE'),
            'use_keyring': env_values.get('ODOO_USE_KEYRING', 'true').lower() in ('true', '1', 'yes')
        }

        return server_config

    except FileNotFoundError as e:
        logger.error(f".env file not found: {env_file}")
        print(f"{Fore.RED}File not found: {env_file}{Style.RESET_ALL}")
        return False
    except Exception as e:
        logger.error(f"Error parsing .env file {env_file}: {e}")
        print(f"{Fore.RED}Error parsing {env_file}: {e}{Style.RESET_ALL}")
        return False


def parse_env_folder(path: Union[str, Path]) -> List[Dict[str, Any]]:
    """Parse all .env files in a directory and return their contents.

    Args:
        path: Path to directory containing .env files.

    Returns:
        List of parsed .env configurations.

    Raises:
        PathDoesNotExistError: If the specified path does not exist.

    Example:
        >>> configs = parse_env_folder('./env_configs')
        >>> for config in configs:
        ...     print(config['url'])
    """
    env_configs = []
    try:
        if not os.path.exists(path):
            raise exceptions.PathDoesNotExistError(f"Path does not exist: {path}")

        for file in os.listdir(path):
            if file.endswith(".env"):
                env_config = parse_env_file(os.path.join(path, file))
                if env_config:
                    env_configs.append(env_config)
                    logger.info(f"Parsed .env file: {file}")

        if not env_configs:
            logger.warning(f"No valid .env files found in {path}")
            print(f"{Fore.YELLOW}Warning: No valid .env files found in {path}{Style.RESET_ALL}")

        return env_configs
    except exceptions.PathDoesNotExistError as e:
        logger.error(str(e))
        print(f"{Fore.RED}{str(e)}{Style.RESET_ALL}")
        raise


def create_odoo_connection_from_env(env_config: Dict[str, Any]) -> Optional[OdooConnection]:
    """Create an OdooConnection instance from a .env configuration.

    Args:
        env_config: Dictionary containing server configuration with keys:
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

    Example:
        >>> env_config = {'url': 'example.com', 'user': 'admin', 'port': 443}
        >>> conn = create_odoo_connection_from_env(env_config)
    """
    try:
        url = env_config.get('url')
        port = env_config.get('port', 0)
        user = env_config.get('user')
        password = env_config.get('password')
        database = env_config.get('database')
        use_keyring = env_config.get('use_keyring', True)

        if not all([url, user]):
            missing = []
            if not url: missing.append('ODOO_URL')
            if not user: missing.append('ODOO_USER')
            raise ValueError(f"Missing required .env variables: {', '.join(missing)}")

        odoo_connection_object = OdooConnection(
            url, port, user, password, database, use_keyring
        )
        return odoo_connection_object
    except ValueError as e:
        logger.error(f"Invalid .env configuration: {e}")
        print(f"{Fore.RED}Invalid configuration: {e}{Style.RESET_ALL}")
        return None
    except Exception as e:
        logger.error(f"Error creating connection from .env: {e}")
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
    """Parse .env configuration files and create OdooConnection objects.

    Args:
        path: Path to directory containing .env server configuration files.

    Returns:
        List of OdooConnection objects.

    Raises:
        PathDoesNotExistError: If the specified path does not exist.

    Example:
        >>> connections = collect_all_connections('./env_configs')
        >>> for conn in connections:
        ...     conn.login()
    """
    try:
        # Parse .env files
        env_configs = parse_env_folder(path)
        connections = convert_all_yaml_objects(
            env_configs,
            create_odoo_connection_from_env
        )

        if connections:
            logger.info(f"Loaded {len(connections)} connection(s) from .env files")
        else:
            logger.warning("No valid connections created from .env files")
            print(f"{Fore.YELLOW}Warning: No valid .env configuration files found in {path}{Style.RESET_ALL}")

        return connections
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


def _translate_category_to_english(category: str) -> str:
    """Translate Odoo category names to English.

    Args:
        category: Category name (may be in German or other language).

    Returns:
        English category name.
    """
    # German to English mapping
    category_mapping = {
        # German translations
        'Rechnungswesen': 'Accounting',
        'Buchhaltung': 'Accounting',
        'Verkauf': 'Sales',
        'Vertrieb': 'Sales',
        'Einkauf': 'Purchase',
        'Beschaffung': 'Purchase',
        'Lager': 'Inventory',
        'Bestand': 'Inventory',
        'Website': 'Website',
        'Webseite': 'Website',
        'Personalwesen': 'Human Resources',
        'Personal': 'Human Resources',
        'Projekt': 'Project',
        'Fertigung': 'Manufacturing',
        'Produktion': 'Manufacturing',
        'Marketing': 'Marketing',
        'Verwaltung': 'Administration',
        'Einstellungen': 'Settings',
        'Technik': 'Technical',
        'Versteckt': 'Hidden',
        'Nicht kategorisiert': 'Uncategorized',
        # Keep English categories as-is
        'Accounting': 'Accounting',
        'Sales': 'Sales',
        'Purchase': 'Purchase',
        'Inventory': 'Inventory',
        'Human Resources': 'Human Resources',
        'Project': 'Project',
        'Manufacturing': 'Manufacturing',
        'CRM': 'CRM',
        'Settings': 'Settings',
        'Technical': 'Technical',
        'Administration': 'Administration',
        'Hidden': 'Hidden',
        'Uncategorized': 'Uncategorized',
        'Extra Tools': 'Extra Tools',
        'Point of Sale': 'Point of Sale',
        'Productivity': 'Productivity',
        'Services': 'Services',
    }

    return category_mapping.get(category, category)


def export_modules_to_yaml(
    connection: OdooConnection,
    output_file: Union[str, Path],
    include_states: Optional[List[str]] = None,
    exclude_base: bool = True
) -> bool:
    """Export installed modules from Odoo server to YAML file.

    Args:
        connection: OdooConnection object for the target server.
        output_file: Path to output YAML file.
        include_states: List of module states to include (default: ['installed']).
                       Options: 'installed', 'to upgrade', 'to install', 'to remove'
        exclude_base: If True, exclude base Odoo modules (default: True).

    Returns:
        True if export successful, False otherwise.

    Example:
        >>> conn = OdooConnection('http://localhost', 8069, 'admin', 'admin')
        >>> conn.login()
        >>> export_modules_to_yaml(conn, 'my_modules.yaml')
        Exported 42 modules to my_modules.yaml
        True
    """
    try:
        if include_states is None:
            include_states = ['installed']

        # Get all modules status
        modules_status = connection.get_all_modules_status()

        # Base Odoo modules to exclude (common core modules)
        base_modules = {
            'base', 'web', 'mail', 'base_setup', 'web_tour', 'web_kanban_gauge',
            'auth_signup', 'bus', 'calendar', 'contacts', 'digest', 'fetchmail',
            'google_account', 'google_calendar', 'iap', 'link_tracker', 'phone_validation',
            'portal', 'resource', 'sms', 'snailmail', 'social_media', 'utm',
            'web_editor', 'web_unsplash', 'barcodes', 'mass_mailing'
        }

        # Collect modules from requested states
        all_modules = []
        for state in include_states:
            if state in modules_status:
                all_modules.extend(modules_status[state])

        # Filter and categorize modules
        categorized_modules = {}
        total_count = 0

        for module in all_modules:
            module_name = module['name']
            # Exclude base modules if requested
            if exclude_base and module_name in base_modules:
                continue
            # Exclude modules starting with 'l10n_' (localizations) if exclude_base
            if exclude_base and module_name.startswith('l10n_'):
                continue

            # Get category
            category = module.get('category', 'Uncategorized')

            # Translate category to English
            category = _translate_category_to_english(category)

            if not category or category == 'Uncategorized':
                # Try to infer category from module name prefix
                if module_name.startswith('account_'):
                    category = 'Accounting'
                elif module_name.startswith('sale_') or module_name.startswith('sales_'):
                    category = 'Sales'
                elif module_name.startswith('purchase_'):
                    category = 'Purchase'
                elif module_name.startswith('stock_'):
                    category = 'Inventory'
                elif module_name.startswith('website_'):
                    category = 'Website'
                elif module_name.startswith('crm_'):
                    category = 'CRM'
                elif module_name.startswith('hr_'):
                    category = 'Human Resources'
                elif module_name.startswith('project_'):
                    category = 'Project'
                else:
                    category = 'Other'

            if category not in categorized_modules:
                categorized_modules[category] = []
            categorized_modules[category].append(module_name)
            total_count += 1

        # Sort categories alphabetically
        sorted_categories = sorted(categorized_modules.keys())

        # Sort modules within each category
        for category in sorted_categories:
            categorized_modules[category].sort()

        # Add comment header
        header_comment = (
            f"# Exported modules from {connection.cleaned_url}\n"
            f"# Server: Odoo {connection.version}\n"
            f"# Database: {connection.database}\n"
            f"# Total modules: {total_count}\n"
            f"# States included: {', '.join(include_states)}\n"
            f"# Base modules excluded: {exclude_base}\n"
            f"#\n"
            f"# Generated by odoo-module-un-install\n\n"
        )

        # Write to file with structured format
        with open(output_file, 'w') as f:
            f.write(header_comment)
            f.write("Install:\n")

            # Write modules by category
            for category in sorted_categories:
                modules = categorized_modules[category]
                f.write(f"  # {category} ({len(modules)} modules)\n")
                for module in modules:
                    f.write(f"  - {module}\n")
                f.write("\n")

            f.write("Uninstall: []\n")

        print(f"{Fore.GREEN}✓ Exported {total_count} modules to {output_file}{Style.RESET_ALL}")
        logger.info(f"Exported {total_count} modules to {output_file}")
        return True

    except Exception as e:
        logger.error(f"Error exporting modules to YAML: {e}")
        print(f"{Fore.RED}Error exporting modules: {e}{Style.RESET_ALL}")
        return False
