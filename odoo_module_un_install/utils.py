# -*- coding: utf-8 -*-
# Copyright 2014-now Equitania Software GmbH - Pforzheim - Germany
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import yaml
import os
from . import exceptions
from .odoo_connection import OdooConnection
import sys


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
        :param: input_dictionary
        :return: return_dict
    """
    return_dict = input_dictionary.copy()
    for key, value in input_dictionary.items():
        return_dict[key] = list(dict.fromkeys(value))
    return return_dict


def parse_yaml(yaml_file):
    """
        Parse yaml file to object and return it
        :param: yaml_file: path to yaml file
        :return: yaml_object
    """
    with open(yaml_file, 'r') as stream:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            return False


def parse_yaml_folder(path):
    """
        Parse multiple yaml files to list of objects and return them
        :param: yaml_file: path to yaml files
        :return: yaml_objects
    """
    yaml_objects = []
    for file in os.listdir(path):
        if file.endswith(".yaml"):
            yaml_object = parse_yaml(os.path.join(path, file))
            if yaml_object:
                yaml_objects.append(yaml_object)
    return yaml_objects


def create_odoo_connection_from_yaml_object(yaml_object):
    """
        Create EqOdooConnection object from yaml_object
        :param: yaml_object
        :return: EqOdooConnection object
    """
    eq_odoo_connection_object = OdooConnection(
        yaml_object['Server']['url'],
        yaml_object['Server']['port'],
        yaml_object['Server']['user'],
        yaml_object['Server']['password'],
        yaml_object['Server']['database'],
    )
    return eq_odoo_connection_object


def convert_all_yaml_objects(yaml_objects: list, converting_function):
    """
        Convert list of yaml_objects through a converting function
        :param: list of yaml_objects
        :param: Function with which the yaml_objects should be converted
        :return: list of objects
    """
    local_object_list = []
    for yaml_object in yaml_objects:
        local_object = converting_function(yaml_object)
        local_object_list.append(local_object)
    return local_object_list


def collect_all_connections(path):
    """
        Get all yaml objects from path and convert them into connection objects
        :param: path to yaml files
        :return: list of connection objects
    """
    try:
        yaml_connection_objects = parse_yaml_folder(path)
        eq_connection_objects = convert_all_yaml_objects(yaml_connection_objects, create_odoo_connection_from_yaml_object)
        return eq_connection_objects
    except FileNotFoundError as ex:
        raise exceptions.PathDoesNotExitError("ERROR: Please check your Path" + " " + str(ex))
        sys.exit(0)
