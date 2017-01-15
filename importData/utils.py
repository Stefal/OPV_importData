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
    """ A class which contain all the configuration """
    def __init__(self, configFile: str = 'config/main.json'):
        super().__init__()
        self.configFile = configFile
        self._fetchConfig()

    def _fetchConfig(self):
        with open(self.configFile, "r") as f:
            self.data = json.load(f)

    def reloadConfigFile(self):
        self._fetchConfig()


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
        return select_arg(args['--' + name], args['--no-' + name])
    else:
        return args['--' + name]
