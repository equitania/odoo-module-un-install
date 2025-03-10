# -*- coding: utf-8 -*-
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import keyring
import getpass
import logging
import os

logger = logging.getLogger(__name__)

SERVICE_NAME = "odoo_module_un_install"

def get_stored_password(username, server_url):
    """
    Get stored password from keyring
    
    :param username: Username for authentication
    :param server_url: Server URL as identifier
    :return: Password or None if not found
    """
    key = f"{username}@{server_url}"
    try:
        return keyring.get_password(SERVICE_NAME, key)
    except Exception as e:
        logger.warning(f"Could not retrieve password from keyring: {e}")
        return None

def store_password(username, server_url, password):
    """
    Store password in keyring
    
    :param username: Username for authentication
    :param server_url: Server URL as identifier
    :param password: Password to store
    """
    key = f"{username}@{server_url}"
    try:
        keyring.set_password(SERVICE_NAME, key, password)
        logger.info(f"Password stored for {username} at {server_url}")
    except Exception as e:
        logger.warning(f"Could not store password in keyring: {e}")

def get_password(username, server_url, use_keyring=True, env_var=None):
    """
    Get password, either from keyring, environment variable, or by prompting the user
    
    :param username: Username for authentication
    :param server_url: Server URL as identifier
    :param use_keyring: Whether to use keyring for password storage
    :param env_var: Environment variable name that might contain the password
    :return: Password
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