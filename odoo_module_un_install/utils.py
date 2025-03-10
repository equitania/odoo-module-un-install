# -*- coding: utf-8 -*-
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import yaml
import os
import logging
import concurrent.futures
from tqdm import tqdm
from colorama import Fore, Style, init
from . import exceptions
from .odoo_connection import OdooConnection

# Initialize colorama
init()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("odoo_module_un_install.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def fire_all_functions(function_list: list):
    """
    Execute each function in a list
    
    :param function_list: List of functions
    """
    for func in function_list:
        func()


def self_clean(input_dictionary: dict) -> dict:
    """
    Remove duplicates in dictionary
    
    :param input_dictionary: Dictionary to clean
    :return: Cleaned dictionary
    """
    return_dict = input_dictionary.copy()
    for key, value in input_dictionary.items():
        return_dict[key] = list(dict.fromkeys(value))
    return return_dict


def parse_yaml(yaml_file):
    """
    Parse yaml file to object and return it
    
    :param yaml_file: Path to yaml file
    :return: yaml_object or False on error
    """
    try:
        with open(yaml_file, 'r') as stream:
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


def parse_yaml_folder(path):
    """
    Parse multiple yaml files to list of objects and return them
    
    :param path: Path to yaml files directory
    :return: List of yaml objects
    """
    yaml_objects = []
    try:
        if not os.path.exists(path):
            raise exceptions.PathDoesNotExitError(f"Path does not exist: {path}")
            
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
    except exceptions.PathDoesNotExitError as e:
        logger.error(str(e))
        print(f"{Fore.RED}{str(e)}{Style.RESET_ALL}")
        raise


def create_odoo_connection_from_yaml_object(yaml_object):
    """
    Create OdooConnection object from yaml_object
    
    :param yaml_object: YAML configuration object
    :return: OdooConnection object
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


def convert_all_yaml_objects(yaml_objects: list, converting_function):
    """
    Convert list of yaml_objects through a converting function
    
    :param yaml_objects: List of yaml_objects
    :param converting_function: Function with which the yaml_objects should be converted
    :return: List of converted objects
    """
    local_object_list = []
    for yaml_object in yaml_objects:
        local_object = converting_function(yaml_object)
        if local_object:  # Only add if conversion was successful
            local_object_list.append(local_object)
    return local_object_list


def collect_all_connections(path):
    """
    Get all yaml objects from path and convert them into connection objects
    
    :param path: Path to yaml files
    :return: List of connection objects
    """
    try:
        yaml_connection_objects = parse_yaml_folder(path)
        eq_connection_objects = convert_all_yaml_objects(yaml_connection_objects, create_odoo_connection_from_yaml_object)
        
        if not eq_connection_objects:
            logger.warning("No valid connections created from configuration files")
            print(f"{Fore.YELLOW}Warning: No valid connections created from configuration files{Style.RESET_ALL}")
            
        return eq_connection_objects
    except exceptions.PathDoesNotExitError as ex:
        logger.error(f"Path error: {ex}")
        raise


def process_modules_in_parallel(connection, module_list, operation_func, max_workers=5):
    """
    Process modules in parallel using a thread pool
    
    :param connection: OdooConnection object
    :param module_list: List of module names to process
    :param operation_func: Function to call for each module (install, uninstall, update)
    :param max_workers: Maximum number of parallel workers
    :return: List of successfully processed modules
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


def analyze_dependencies(connection, modules, operation="uninstall"):
    """
    Analyze dependencies for a list of modules
    
    :param connection: OdooConnection object
    :param modules: List of module names
    :param operation: Operation to perform (uninstall, install, update)
    :return: Dict with modules grouped by status
    """
    result = {
        'ready': [],       # Can be processed immediately
        'dependent': {},   # Modules with their dependents
        'missing': [],     # Modules not found
        'not_installed': [] # Modules not installed (for uninstall/update)
    }
    
    if operation == "uninstall":
        # For uninstallation, we need to check if other modules depend on these
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
        # For installation, we need to check what dependencies these modules have
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


def display_module_status(connection):
    """
    Display status of all modules in a nice format
    
    :param connection: OdooConnection object
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

    print(f"\n{Fore.CYAN}Total: {len(installed) + len(to_install) + len(to_upgrade) + len(to_remove) + len(modules_status.get('uninstalled', []))}{Style.RESET_ALL}")
