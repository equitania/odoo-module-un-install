# -*- coding: utf-8 -*-
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from .utils import collect_all_connections, parse_yaml_folder
import click


def welcome():
    click.echo("Welcome to the odoo-module-un-install!")


@click.command()
@click.option('--server_path', help='Server configuration folder',
              prompt='Please enter the path to your configuration folder')
@click.option('--module_path', help='Modules folder',
              prompt='Please enter the path to your module folder')
@click.option('--uninstall_modules', help='Uninstall modules',
              prompt='Enter \"y\" to uninstall the modules defined under "uninstall" in your yaml file')
@click.option('--install_modules', help='Install modules',
              prompt='Enter \"y\" to install the modules defined under "install" in your yaml file')
def start_odoo_module_un_install(server_path, module_path, uninstall_modules, install_modules):
    # Collect yaml files and build objects
    connections = collect_all_connections(server_path)
    module_objects = parse_yaml_folder(module_path)[0]
    # Uninstall modules
    if uninstall_modules == 'y':
        modules_to_be_uninstalled = module_objects["Uninstall"]
        for connection in connections:
            connection.login()
            print("Uninstall modules for " + connection.url)
            for module in modules_to_be_uninstalled:
                connection.uninstall_module(module)
    # Install modules
    if install_modules == 'y':
        modules_to_be_installed = module_objects['Install']
        for connection in connections:
            connection.login()
            print("Install modules for " + connection.url)
            for module in modules_to_be_installed:
                connection.install_module(module)
    click.echo("##### DONE #####")


if __name__ == "__main__":
    welcome()
    start_odoo_module_un_install()
