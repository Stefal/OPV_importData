from functools import wraps
from collections import UserDict
import os.path
import json


def ensure_dir(d):
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
    """A class which contain all the configuration"""
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
    if disable:
        return False
    elif active:
        return True
    return None

def convert_args(args, name, invert=False):
    if invert:
        return select_arg(args['--' + name], args['--no-' + name])
    else:
        return args['--' + name]
