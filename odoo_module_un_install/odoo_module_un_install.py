# -*- coding: utf-8 -*-
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import click
import time
import os
from colorama import Fore, Style, init
from .version import __version__
from .utils import (
    collect_all_connections, parse_yaml_folder, 
    process_modules_in_parallel, analyze_dependencies,
    display_module_status
)

# Initialize colorama
init()

# Configure logging
logger = logging.getLogger(__name__)

def welcome():
    """Display welcome message"""
    print(f"""
{Fore.CYAN}╔══════════════════════════════════════════════════╗
║ {Fore.GREEN}Welcome to the Odoo Module (Un)Install Tool!{Fore.CYAN}       ║
║ {Fore.YELLOW}Version {__version__}{Fore.CYAN}                                     ║
╚══════════════════════════════════════════════════╝{Style.RESET_ALL}
""")

def display_summary(results, operation):
    """Display operation summary"""
    if not results:
        print(f"{Fore.YELLOW}No results to display.{Style.RESET_ALL}")
        return
        
    print(f"\n{Fore.CYAN}=== Operation Summary: {operation.title()} ==={Style.RESET_ALL}")
    
    total_success = 0
    total_failure = 0
    
    for server, modules in results.items():
        success_count = len(modules.get('success', []))
        fail_count = len(modules.get('failure', []))
        total_success += success_count
        total_failure += fail_count
        
        print(f"\n{Fore.BLUE}Server: {server}{Style.RESET_ALL}")
        print(f"  {Fore.GREEN}Success: {success_count}{Style.RESET_ALL}")
        if modules.get('success'):
            for module in sorted(modules.get('success', [])):
                print(f"    ✓ {module}")
                
        print(f"  {Fore.RED}Failure: {fail_count}{Style.RESET_ALL}")
        if modules.get('failure'):
            for module in sorted(modules.get('failure', [])):
                print(f"    ✗ {module}")
    
    print(f"\n{Fore.CYAN}Total: {total_success + total_failure} modules processed{Style.RESET_ALL}")
    print(f"{Fore.GREEN}Success: {total_success}{Style.RESET_ALL} | {Fore.RED}Failure: {total_failure}{Style.RESET_ALL}")


@click.group(help="Odoo Module Management Tool - Install, uninstall and update modules across multiple Odoo instances")
@click.version_option(version=__version__, prog_name="Odoo Module (Un)Install Tool")
def cli():
    """Odoo Module Management Command Line Interface"""
    pass


@cli.command('run', help="Run module operations on Odoo servers")
@click.option('--server_path', 
              help='Path to folder containing server configuration YAML files',
              prompt='Please enter the path to your server configuration folder',
              type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True))
@click.option('--module_path', 
              help='Path to folder containing module configuration YAML files',
              prompt='Please enter the path to your module configuration folder',
              type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True))
@click.option('--uninstall_modules', 
              is_flag=True, 
              help='Uninstall modules defined in the "Uninstall" section of YAML files')
@click.option('--install_modules', 
              is_flag=True, 
              help='Install modules defined in the "Install" section of YAML files')
@click.option('--update_modules', 
              is_flag=True, 
              help='Update modules defined in the "Install" section of YAML files')
@click.option('--check_dependencies', 
              is_flag=True, 
              help='Check module dependencies before operations (recommended)')
@click.option('--parallel', 
              is_flag=True, 
              help='Process modules in parallel for faster execution')
@click.option('--max_workers', 
              default=5, 
              show_default=True,
              help='Maximum number of parallel workers when using --parallel')
@click.option('--show_status', 
              is_flag=True, 
              help='Show detailed module status report after operations')
@click.option('--verbose', '-v', 
              is_flag=True, 
              help='Enable verbose output for debugging')
def run(server_path, module_path, uninstall_modules, install_modules, update_modules, 
        check_dependencies, parallel, max_workers, show_status, verbose):
    """
    Execute module operations on Odoo servers.
    
    This command processes server and module configurations from YAML files and
    performs the requested operations (install, uninstall, update) on the specified
    Odoo servers. It can analyze dependencies, process modules in parallel, and
    provide detailed status reports.
    
    Examples:
    
    \b
    # Install and uninstall modules
    odoo-un-install run --server_path=./servers --module_path=./modules --install_modules --uninstall_modules
    
    \b
    # Update modules with dependency checking
    odoo-un-install run --server_path=./servers --module_path=./modules --update_modules --check_dependencies
    
    \b
    # Full operation with parallel processing
    odoo-un-install run --server_path=./servers --module_path=./modules --install_modules --uninstall_modules --update_modules --check_dependencies --parallel
    """
    # Set logging level based on verbose flag
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        
    welcome()
    start_time = time.time()
    
    print(f"{Fore.YELLOW}Loading configurations...{Style.RESET_ALL}")
    
    # Collect yaml files and build objects
    try:
        connections = collect_all_connections(server_path)
        if not connections:
            return
            
        module_objects = parse_yaml_folder(module_path)
        if not module_objects:
            return
            
        # Get the first module object for simplicity (assuming one file)
        module_object = module_objects[0]
        
        # Track results for summary
        results = {}
        
        # Process each server
        for connection in connections:
            connection_url = connection.cleaned_url
            results[connection_url] = {
                'success': [],
                'failure': []
            }
            
            # Login to the server
            connection.login()
            if not connection.is_logged_in:
                print(f"{Fore.RED}Failed to login to {connection_url}, skipping...{Style.RESET_ALL}")
                continue
            
            # Define operation functions
            def install_module(module):
                return connection.install_module(module)
                
            def uninstall_module(module):
                return connection.uninstall_module(module, check_dependencies=check_dependencies)
                
            def update_module(module):
                return connection.update_module(module)
            
            # Uninstall modules
            if uninstall_modules:
                modules_to_uninstall = module_object.get("Uninstall", [])
                if not modules_to_uninstall:
                    print(f"{Fore.YELLOW}No modules to uninstall defined{Style.RESET_ALL}")
                else:
                    print(f"\n{Fore.CYAN}=== Uninstalling modules on {connection_url} ==={Style.RESET_ALL}")
                    
                    if check_dependencies:
                        # Analyze dependencies
                        analysis = analyze_dependencies(connection, modules_to_uninstall, "uninstall")
                        if analysis['dependent']:
                            print(f"{Fore.YELLOW}Some modules have dependencies and will be skipped:{Style.RESET_ALL}")
                            for module, deps in analysis['dependent'].items():
                                print(f"  {Fore.RED}✗ {module} - Used by: {', '.join(deps)}{Style.RESET_ALL}")
                        
                        if analysis['missing']:
                            print(f"{Fore.YELLOW}Some modules were not found:{Style.RESET_ALL}")
                            for module in analysis['missing']:
                                print(f"  {Fore.RED}✗ {module} - Not found{Style.RESET_ALL}")
                                
                        # Only uninstall modules that are ready
                        modules_to_uninstall = analysis['ready']
                    
                    if parallel:
                        successful_modules = process_modules_in_parallel(
                            connection, modules_to_uninstall, uninstall_module, max_workers
                        )
                    else:
                        successful_modules = []
                        for module in modules_to_uninstall:
                            if uninstall_module(module):
                                successful_modules.append(module)
                    
                    results[connection_url]['success'].extend(successful_modules)
                    results[connection_url]['failure'].extend(
                        [m for m in modules_to_uninstall if m not in successful_modules]
                    )
            
            # Install modules
            if install_modules:
                modules_to_install = module_object.get("Install", [])
                if not modules_to_install:
                    print(f"{Fore.YELLOW}No modules to install defined{Style.RESET_ALL}")
                else:
                    print(f"\n{Fore.CYAN}=== Installing modules on {connection_url} ==={Style.RESET_ALL}")
                    
                    if check_dependencies:
                        # Analyze dependencies
                        analysis = analyze_dependencies(connection, modules_to_install, "install")
                        if analysis['dependent']:
                            print(f"{Fore.YELLOW}Some modules have missing dependencies:{Style.RESET_ALL}")
                            for module, deps in analysis['dependent'].items():
                                print(f"  {Fore.YELLOW}! {module} - Missing deps: {', '.join(deps)}{Style.RESET_ALL}")
                                # Add dependencies to the installation list
                                modules_to_install.extend(deps)
                        
                        if analysis['missing']:
                            print(f"{Fore.YELLOW}Some modules were not found:{Style.RESET_ALL}")
                            for module in analysis['missing']:
                                print(f"  {Fore.RED}✗ {module} - Not found{Style.RESET_ALL}")
                                
                        # Remove duplicates
                        modules_to_install = list(dict.fromkeys(modules_to_install))
                    
                    if parallel:
                        successful_modules = process_modules_in_parallel(
                            connection, modules_to_install, install_module, max_workers
                        )
                    else:
                        successful_modules = []
                        for module in modules_to_install:
                            if install_module(module):
                                successful_modules.append(module)
                    
                    results[connection_url]['success'].extend(successful_modules)
                    results[connection_url]['failure'].extend(
                        [m for m in modules_to_install if m not in successful_modules]
                    )
            
            # Update modules
            if update_modules:
                modules_to_update = module_object.get("Update", [])
                if not modules_to_update:
                    print(f"{Fore.YELLOW}No modules to update defined{Style.RESET_ALL}")
                else:
                    print(f"\n{Fore.CYAN}=== Updating modules on {connection_url} ==={Style.RESET_ALL}")
                    
                    if check_dependencies:
                        # Analyze dependencies
                        analysis = analyze_dependencies(connection, modules_to_update, "update")
                        if analysis['dependent']:
                            print(f"{Fore.YELLOW}Some modules have dependencies and will be skipped:{Style.RESET_ALL}")
                            for module, deps in analysis['dependent'].items():
                                print(f"  {Fore.RED}✗ {module} - Used by: {', '.join(deps)}{Style.RESET_ALL}")
                        
                        if analysis['missing']:
                            print(f"{Fore.YELLOW}Some modules were not found:{Style.RESET_ALL}")
                            for module in analysis['missing']:
                                print(f"  {Fore.RED}✗ {module} - Not found{Style.RESET_ALL}")
                                
                        # Only update modules that are ready
                        modules_to_update = analysis['ready']
                    
                    if parallel:
                        successful_modules = process_modules_in_parallel(
                            connection, modules_to_update, update_module, max_workers
                        )
                    else:
                        successful_modules = []
                        for module in modules_to_update:
                            if update_module(module):
                                successful_modules.append(module)
                    
                    results[connection_url]['success'].extend(successful_modules)
                    results[connection_url]['failure'].extend(
                        [m for m in modules_to_update if m not in successful_modules]
                    )
            
            # Display module status
            if show_status:
                display_module_status(connection)
        
        # Display summary
        display_summary(results, "operation")
    except Exception as e:
        logger.error(f"Error executing operation: {e}")
        print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")


# Add a status command to just show module status without modifications
@cli.command('status', help="Show module status information for Odoo servers")
@click.option('--server_path', 
              help='Path to folder containing server configuration YAML files',
              prompt='Please enter the path to your server configuration folder',
              type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True))
def status(server_path):
    """
    Display detailed status information about modules on Odoo servers.
    
    This command connects to the Odoo servers defined in the configuration files
    and displays a comprehensive report about installed modules, modules pending
    installation or update, and other relevant status information.
    
    Example:
    
    \b
    odoo-un-install status --server_path=./servers
    """
    welcome()
    
    # Collect yaml files and build objects
    try:
        connections = collect_all_connections(server_path)
        if not connections:
            print(f"{Fore.RED}No valid server connections found.{Style.RESET_ALL}")
            return
            
        # Process each server
        for connection in connections:
            connection_url = connection.cleaned_url
            
            # Login to the server
            connection.login()
            if not connection.is_logged_in:
                print(f"{Fore.RED}Failed to login to {connection_url}, skipping...{Style.RESET_ALL}")
                continue
                
            # Display module status
            display_module_status(connection)
            
    except Exception as e:
        print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
        logger.error(f"Error: {e}", exc_info=True)
        return 1
        
    print(f"\n{Fore.GREEN}Status check completed successfully.{Style.RESET_ALL}")
    return 0


if __name__ == "__main__":
    cli()
