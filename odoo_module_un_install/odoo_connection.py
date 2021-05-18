# -*- coding: utf-8 -*-
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import urllib
import odoorpc
import sys
from . import exceptions


class OdooConnection:
    def __init__(self, url, port, username, password, database):
        self.url = url
        self.username = username
        self.password = password
        self.database = database
        self.version = ""
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

            while url and url.startswith('/'):
                url = url[1:]

            while url and url.endswith('/'):
                url = url[:-1]

            while url and url.endswith('\\'):
                url = url[:-1]

            self.connection = odoorpc.ODOO(url, port=port, protocol=_protocol)
        except urllib.error.URLError as ex:
            raise exceptions.OdooConnectionError(
                "ERROR: Please check your parameters and your connection" + " " + str(ex))
            sys.exit(0)

    def login(self):
        """
            Try to login into the Odoo system and set parameters to optimize the connection
        """
        try:
            self.connection.login(self.database, self.username, self.password)
            # Change settings to make the connection faster
            self.connection.config['auto_commit'] = True  # No need for manual commits
            self.connection.env.context['active_test'] = False  # Show inactive articles
            self.connection.env.context['tracking_disable'] = True
            self.version = self.connection.version.split(".")[0]
        except odoorpc.error.RPCError as ex:
            raise exceptions.OdooConnectionError(
                "ERROR: Please check your parameters and your connection" + " " + str(ex))
            sys.exit(0)

    def _get_module_object(self, module_name):
        MODULES = self.connection.env['ir.module.module']
        module_id = MODULES.search([['name', '=', module_name]])
        module_object = MODULES.browse(module_id)
        return module_object

    def install_module(self, module_name):
        module_object = self._get_module_object(module_name)
        if module_object.state == "uninstalled":
            module_object.button_immediate_install()
            print(module_name + " installed")
        else:
            print(module_name + " already installed")

    def uninstall_module(self, module_name):
        module_object = self._get_module_object(module_name)
        if module_object.state == "installed":
            module_object.button_immediate_uninstall()
            print(module_name + " uninstalled")
        else:
            print(module_name + " already uninstalled")