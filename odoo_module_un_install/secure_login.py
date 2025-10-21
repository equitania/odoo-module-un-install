# -*- coding: utf-8 -*-
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# Date: 24.06.2025

"""Secure password management using system keyring."""

import keyring
import getpass
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

SERVICE_NAME = "odoo_module_un_install"


def get_stored_password(username: str, server_url: str) -> Optional[str]:
    """Retrieve stored password from system keyring.

    Args:
        username: Username for authentication.
        server_url: Server URL as unique identifier.

    Returns:
        Password string if found in keyring, None otherwise.

    Example:
        >>> password = get_stored_password('admin', 'example.com')
        >>> if password:
        ...     print("Password found in keyring")
    """
    key = f"{username}@{server_url}"
    try:
        return keyring.get_password(SERVICE_NAME, key)
    except Exception as e:
        logger.warning(f"Could not retrieve password from keyring: {e}")
        return None


def store_password(username: str, server_url: str, password: str) -> None:
    """Store password in system keyring.

    Args:
        username: Username for authentication.
        server_url: Server URL as unique identifier.
        password: Password to securely store.

    Returns:
        None.

    Example:
        >>> store_password('admin', 'example.com', 'secret123')
    """
    key = f"{username}@{server_url}"
    try:
        keyring.set_password(SERVICE_NAME, key, password)
        logger.info(f"Password stored for {username} at {server_url}")
    except Exception as e:
        logger.warning(f"Could not store password in keyring: {e}")


def get_password(
    username: str,
    server_url: str,
    use_keyring: bool = True,
    env_var: Optional[str] = None
) -> str:
    """Retrieve password from keyring, environment variable, or user prompt.

    Password retrieval priority:
    1. Environment variable (if specified)
    2. System keyring (if enabled)
    3. Interactive user prompt

    Args:
        username: Username for authentication.
        server_url: Server URL as unique identifier.
        use_keyring: Whether to use system keyring for password storage (default: True).
        env_var: Optional environment variable name containing the password.

    Returns:
        Password string.

    Example:
        >>> # Try environment variable, keyring, then prompt
        >>> password = get_password('admin', 'example.com', use_keyring=True, env_var='ODOO_PASSWORD')
        >>> # Only use prompt (no keyring or env var)
        >>> password = get_password('admin', 'example.com', use_keyring=False)
    """
    password = None

    # First try environment variable if specified
    if env_var and env_var in os.environ:
        password = os.environ[env_var]
        logger.info(f"Using password from environment variable {env_var}")

    # Then try keyring if enabled
    if not password and use_keyring:
        password = get_stored_password(username, server_url)
        if password:
            logger.info(f"Using password from keyring for {username} at {server_url}")

    # Finally prompt user if still no password
    if not password:
        password = getpass.getpass(f"Enter password for {username} at {server_url}: ")

        if use_keyring:
            save = input("Save password in keyring? (y/n): ").lower() == 'y'
            if save:
                store_password(username, server_url, password)

    return password
