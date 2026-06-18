# -*- coding: utf-8 -*-
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""Odoo RPC connection management and module operations."""

import logging
import sys
import urllib.error
from typing import Any, Dict, List, Optional

import odoorpc_toolbox as odoorpc
from colorama import Fore, Style, init

from . import exceptions, secure_login

# Initialize colorama
init()

logger = logging.getLogger(__name__)


class OdooConnection:
    """Manages connection to Odoo server and provides module operation methods.

    This class handles connection establishment, authentication, and provides
    methods for module management (install, uninstall, update) with dependency
    tracking and status reporting.

    Attributes:
        url: Server URL.
        username: Username for authentication.
        password: User password (optional, can be retrieved from keyring).
        database: Database name (optional, can be selected interactively).
        version: Odoo version string.
        use_keyring: Whether to use system keyring for password storage.
        connection: OdooRPC connection object.
        is_connected: Connection status flag.
        is_logged_in: Authentication status flag.
        cleaned_url: Normalized URL without protocol prefix.

    Example:
        >>> conn = OdooConnection('https://example.com', 443, 'admin', use_keyring=True)
        >>> conn.login()
        >>> conn.install_module('sale')
        >>> conn.logout()
    """

    def __init__(
        self,
        url: str,
        port: int,
        username: str,
        password: Optional[str] = None,
        database: Optional[str] = None,
        use_keyring: bool = True
    ):
        """Initialize Odoo connection.

        Args:
            url: Server URL (with or without protocol prefix).
            port: Port number (0 for default: 443 for HTTPS, 80 for HTTP).
            username: Username for authentication.
            password: Password (optional, can be retrieved from keyring).
            database: Database name (optional, can be selected interactively).
            use_keyring: Whether to use system keyring for password storage (default: True).

        Raises:
            OdooConnectionError: If connection cannot be established.
        """
        self.url = url
        self.username = username
        self.password = password
        self.database = database
        self.version = ""
        self.use_keyring = use_keyring
        self.connection: Optional[odoorpc.ODOO] = None
        self.is_connected = False
        self.is_logged_in = False
        self.cleaned_url = ""

        try:
            # Build connection
            port = int(port)
            _protocol = 'jsonrpc+ssl'

            if url.startswith('https'):
                url = url.replace('https:', '')
                if port <= 0:
                    port = 443
            elif url.startswith('http:'):
                url = url.replace('http:', '')
                _protocol = 'jsonrpc'
                if port <= 0:
                    port = 80

            # Clean URL formatting
            while url and url.startswith('/'):
                url = url[1:]
            while url and url.endswith('/'):
                url = url[:-1]
            while url and url.endswith('\\'):
                url = url[:-1]

            self.cleaned_url = url
            self.connection = odoorpc.ODOO(url, port=port, protocol=_protocol)
            self.is_connected = True
            logger.info(f"Connection established to {url}:{port}")
        except urllib.error.URLError as ex:
            logger.error(f"Connection error: {ex}")
            raise exceptions.OdooConnectionError(
                f"ERROR: Please check your parameters and your connection: {ex}")

    def login(self) -> None:
        """Authenticate to Odoo server and configure connection settings.

        This method handles password retrieval (from keyring, environment, or prompt),
        database selection (automatic or interactive), and optimizes connection settings
        for faster operations.

        Raises:
            OdooConnectionError: If login fails.

        Example:
            >>> conn = OdooConnection('example.com', 443, 'admin')
            >>> conn.login()  # Will prompt for password and database if not provided
        """
        try:
            # Get password if not provided
            if not self.password:
                self.password = secure_login.get_password(
                    self.username, self.url, self.use_keyring, env_var="ODOO_PASSWORD"
                )

            # Get database if not provided
            if not self.database:
                databases = self.connection.db.list()
                if len(databases) == 1:
                    self.database = databases[0]
                    logger.info(f"Using single available database: {self.database}")
                elif not sys.stdin.isatty():
                    # Non-interactive context (pipe, CI, parallel run): we cannot
                    # safely prompt for a choice without blocking or deadlocking.
                    raise exceptions.OdooConnectionError(
                        f"Multiple databases available on {self.cleaned_url} "
                        f"({', '.join(databases)}) but no interactive terminal is "
                        f"attached. Set ODOO_DATABASE in the .env file to select one."
                    )
                else:
                    print(f"{Fore.CYAN}Available databases:{Style.RESET_ALL}")
                    for i, db in enumerate(databases, 1):
                        print(f"{Fore.GREEN}{i}.{Style.RESET_ALL} {db}")
                    self.database = self._prompt_database_choice(databases)

            # Perform login
            self.connection.login(self.database, self.username, self.password)
            self.is_logged_in = True

            # Optimize connection settings
            self.connection.config['auto_commit'] = True  # No need for manual commits
            self.connection.env.context['active_test'] = False  # Show inactive records
            self.connection.env.context['tracking_disable'] = True
            self.version = self.connection.version.split(".")[0]

            logger.info(f"Login successful for {self.username} to {self.url} (Odoo v{self.version})")
            print(
                f"{Fore.GREEN}✓ Connected to {self.cleaned_url}"
                f" (Odoo v{self.version}) as {self.username}{Style.RESET_ALL}"
            )
        except odoorpc.error.RPCError as ex:
            logger.error(f"Login failed: {ex}")
            print(f"{Fore.RED}✗ Login failed for {self.cleaned_url}: {ex}{Style.RESET_ALL}")
            raise exceptions.OdooConnectionError(
                f"ERROR: Please check your parameters and your connection: {ex}")

    @staticmethod
    def _prompt_database_choice(databases: List[str]) -> str:
        """Interactively prompt for a database selection with input validation.

        Args:
            databases: List of available database names.

        Returns:
            The selected database name.

        Raises:
            OdooConnectionError: If end-of-input is reached before a valid choice.
        """
        while True:
            try:
                raw = input(f"{Fore.YELLOW}Select database number (1-{len(databases)}): {Style.RESET_ALL}")
            except EOFError:
                raise exceptions.OdooConnectionError(
                    "No database selected (end of input). Set ODOO_DATABASE in the .env file."
                )
            try:
                choice = int(raw)
            except ValueError:
                print(f"{Fore.RED}Invalid input. Please enter a number.{Style.RESET_ALL}")
                continue
            if 1 <= choice <= len(databases):
                return databases[choice - 1]
            print(f"{Fore.RED}Please enter a number between 1 and {len(databases)}.{Style.RESET_ALL}")

    def _get_module_object(self, module_name: str) -> Any:
        """Retrieve module object from Odoo by name.

        Args:
            module_name: Name of the module to find.

        Returns:
            Module object from Odoo.

        Raises:
            OdooModuleNotFoundError: If module does not exist.
        """
        MODULES = self.connection.env['ir.module.module']
        module_id = MODULES.search([['name', '=', module_name]])

        if not module_id:
            raise exceptions.OdooModuleNotFoundError(f"Module '{module_name}' not found")

        module_object = MODULES.browse(module_id)
        return module_object

    def install_module(self, module_name: str) -> bool:
        """Install an Odoo module.

        Args:
            module_name: Name of the module to install.

        Returns:
            True if module is installed (newly or already), False if error occurred.

        Example:
            >>> conn.install_module('sale')
            Installing sale... ✓ Installed
            True
        """
        try:
            module_object = self._get_module_object(module_name)
            if module_object.state == "uninstalled":
                print(f"{Fore.YELLOW}Installing {module_name}...{Style.RESET_ALL}", end='', flush=True)
                module_object.button_immediate_install()
                print(f"{Fore.GREEN} ✓ Installed{Style.RESET_ALL}")
                logger.info(f"Module {module_name} installed")
                return True
            else:
                print(f"{Fore.CYAN}Module {module_name} already installed{Style.RESET_ALL}")
                logger.info(f"Module {module_name} already installed")
                return True  # Already in desired state = success
        except exceptions.OdooModuleNotFoundError as e:
            print(f"{Fore.RED}✗ {e}{Style.RESET_ALL}")
            logger.error(str(e))
            return False
        except Exception as e:
            print(f"{Fore.RED}✗ Error installing {module_name}: {e}{Style.RESET_ALL}")
            logger.exception(f"Error installing {module_name}")
            return False

    def uninstall_module(self, module_name: str, check_dependencies: bool = True) -> bool:
        """Uninstall an Odoo module.

        Args:
            module_name: Name of the module to uninstall.
            check_dependencies: Whether to check for dependent modules (default: True).

        Returns:
            True if module is uninstalled (newly or already), False if has dependents or error occurred.

        Example:
            >>> conn.uninstall_module('sale', check_dependencies=True)
            Cannot uninstall sale: Used by sale_management, sale_stock
            False
        """
        try:
            module_object = self._get_module_object(module_name)
            if module_object.state == "installed":
                if check_dependencies:
                    dependents = self.get_module_dependents(module_name)
                    if dependents:
                        deps_str = ", ".join(dependents)
                        print(f"{Fore.RED}Cannot uninstall {module_name}: Used by {deps_str}{Style.RESET_ALL}")
                        logger.warning(f"Cannot uninstall {module_name}: Used by {deps_str}")
                        return False

                print(f"{Fore.YELLOW}Uninstalling {module_name}...{Style.RESET_ALL}", end='', flush=True)
                module_object.button_immediate_uninstall()
                print(f"{Fore.GREEN} ✓ Uninstalled{Style.RESET_ALL}")
                logger.info(f"Module {module_name} uninstalled")
                return True
            else:
                print(f"{Fore.CYAN}Module {module_name} already uninstalled{Style.RESET_ALL}")
                logger.info(f"Module {module_name} already uninstalled")
                return True  # Already in desired state = success
        except exceptions.OdooModuleNotFoundError as e:
            print(f"{Fore.RED}✗ {e}{Style.RESET_ALL}")
            logger.error(str(e))
            return False
        except Exception as e:
            print(f"{Fore.RED}✗ Error uninstalling {module_name}: {e}{Style.RESET_ALL}")
            logger.exception(f"Error uninstalling {module_name}")
            return False

    def update_module(self, module_name: str) -> bool:
        """Update an installed Odoo module.

        Args:
            module_name: Name of the module to update.

        Returns:
            True if module was updated, False if not installed or error occurred.

        Example:
            >>> conn.update_module('sale')
            Updating sale... ✓ Updated
            True
        """
        try:
            module_object = self._get_module_object(module_name)
            if module_object.state == "installed":
                print(f"{Fore.YELLOW}Updating {module_name}...{Style.RESET_ALL}", end='', flush=True)
                module_object.button_immediate_upgrade()
                print(f"{Fore.GREEN} ✓ Updated{Style.RESET_ALL}")
                logger.info(f"Module {module_name} updated")
                return True
            else:
                print(f"{Fore.RED}Module {module_name} is not installed, cannot update{Style.RESET_ALL}")
                logger.warning(f"Module {module_name} is not installed, cannot update")
                return False
        except exceptions.OdooModuleNotFoundError as e:
            print(f"{Fore.RED}✗ {e}{Style.RESET_ALL}")
            logger.error(str(e))
            return False
        except Exception as e:
            print(f"{Fore.RED}✗ Error updating {module_name}: {e}{Style.RESET_ALL}")
            logger.exception(f"Error updating {module_name}")
            return False

    def get_module_dependents(self, module_name: str) -> List[str]:
        """Get list of installed modules that depend on the specified module.

        Args:
            module_name: Name of the module to check.

        Returns:
            List of module names that depend on this module.

        Example:
            >>> dependents = conn.get_module_dependents('sale')
            >>> print(dependents)
            ['sale_management', 'sale_stock', 'sale_crm']
        """
        try:
            MODULES = self.connection.env['ir.module.module']
            self._get_module_object(module_name)  # Validate module exists
            dependent_ids = MODULES.search([
                ('state', '=', 'installed'),
                ('dependencies_id.name', '=', module_name)
            ])

            if not dependent_ids:
                return []

            dependents = MODULES.browse(dependent_ids)
            return [dep.name for dep in dependents]
        except Exception:
            logger.exception(f"Error getting dependents for {module_name}")
            return []

    def get_module_dependencies(self, module_name: str) -> List[str]:
        """Get list of modules that the specified module depends on.

        Args:
            module_name: Name of the module to check.

        Returns:
            List of module names this module depends on.

        Example:
            >>> dependencies = conn.get_module_dependencies('sale_management')
            >>> print(dependencies)
            ['base', 'sale', 'product']
        """
        try:
            module = self._get_module_object(module_name)
            dependencies = []
            for dep in module.dependencies_id:
                dep_name = dep.name
                dependencies.append(dep_name)
            return dependencies
        except Exception:
            logger.exception(f"Error getting dependencies for {module_name}")
            return []

    def get_all_modules_status(self) -> Dict[str, List[Dict[str, str]]]:
        """Retrieve status information for all modules.

        Returns:
            Dictionary with module states as keys and lists of module info dicts as values.
            Each module info dict contains 'name' and 'version' keys.

        Example:
            >>> status = conn.get_all_modules_status()
            >>> print(f"Installed: {len(status['installed'])}")
            >>> print(f"To upgrade: {len(status['to upgrade'])}")
        """
        try:
            MODULES = self.connection.env['ir.module.module']
            modules = MODULES.search_read([], ['name', 'state', 'installed_version', 'category_id'])

            result = {
                'installed': [],
                'uninstalled': [],
                'to install': [],
                'to upgrade': [],
                'to remove': []
            }

            for module in modules:
                state = module['state']
                if state in result:
                    category_name = module.get('category_id', [False, 'Uncategorized'])
                    if isinstance(category_name, list) and len(category_name) > 1:
                        category_name = category_name[1]
                    elif not category_name:
                        category_name = 'Uncategorized'

                    result[state].append({
                        'name': module['name'],
                        'version': module.get('installed_version', 'N/A'),
                        'category': category_name
                    })

            return result
        except Exception:
            logger.exception("Error getting module status")
            return {}
