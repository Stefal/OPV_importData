#!/usr/bin/python3
# coding: utf-8

import os.path
import json
from functools import wraps
from collections import UserDict


def ensure_dir(d):
    """ Ensure d exist and if not create it """
    if not os.path.exists(d):
        os.makedirs(d)


def singleton(cls):
    """make the class as singleton"""
    @wraps(cls)
    def fct():
        """
        create a new object if no one exit
        """
        if not fct.instance:
            fct.instance = cls()
        return fct.instance
    fct.instance = None

    return fct


class Config(UserDict):
    """ A class which contain all the configuration"""

    """
    Create a configuration object.
    :param configFile: The path of a JSON configuration file.
    :param configString: A JSON configuration string.
    """
    def __init__(self, configString: str = None):
        super().__init__()
        if configString:
            self.data = json.loads(configString)

    """
    Load configuration from JSON file (erase existing keys).
    :param filePath: Path of the JSON file.
    """
    def loadConfigFile(self, filePath):
        with open(filePath, "r") as f:
            self.data.update(json.load(f))


def select_arg(active, disable):
    """ "Return True if active and False if disable """
    if disable:
        return False
    elif active:
        return True
    return None


def convert_args(args, name, invert=False):
    """ Convert Args ? """
    if invert:
        active = '--' + name in args and args['--' + name]
        disable = '--no-' + name in args and args['--no-' + name]
        return select_arg(active, disable)
    else:
        return args['--' + name]
