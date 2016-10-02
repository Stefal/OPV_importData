from functools import wraps
from contextlib import contextmanager
from collections import UserDict

import json

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

    @contextmanager
    def get(self, *keys):
        try:
            yield [self[k] for k in keys]
        finally:
            pass

    def _fetchConfig(self):
        with open(self.configFile, "r") as f:
            self.data = json.load(f)

    def reloadConfigFile(self):
        self._fetchConfig()
