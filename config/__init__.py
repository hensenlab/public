"""
Created 2022

@author: B.J.Hensen

This work is licensed under the GNU Affero General Public License v3.0

Copyright (c) 2022, Hensen Lab

All rights reserved.

"""


import os
from copy import deepcopy

from . import default_config
from ..lib.io import tools

CONFIG_FILENAME = 'config.json'

def get_config_folder():
    return tools.get_config_folder()

    
class Config:
    def __init__(self):
        self.current_config = deepcopy(default_config.config)
        self.load()
        self.save()

    def load(self):
        fp = os.path.join(get_config_folder(),CONFIG_FILENAME)
        if os.path.exists(fp):
            loaded_config = tools.load_dict_from_json(fp)
            self.current_config.update(loaded_config)

    def save(self):
        cfg_folder = get_config_folder()
        if not(os.path.exists(cfg_folder)):
            os.makedirs(cfg_folder)
        fp = os.path.join(cfg_folder,CONFIG_FILENAME)
        tools.save_dict_to_json(fp,self.current_config)

    def __setitem__(self, key, value):
        self.current_config[key] = value

    def __getitem__(self, key):
        return self.current_config[key]

    def __str__(self):
        return str(self.current_config)

    def __len__(self):
        return len(self.current_config)

    def keys(self):
        return self.current_config.keys()

    def items(self):
        return self.current_config.items()    

config = Config()

def get_default_config():
    return default_config.config

def get(key):
    return config[key]

def set(key, value, check_exists = True):
    if check_exists and key not in config.current_config:
        raise KeyError(f'Key {key} does not exist in current config. To set a new key, use check_exists = False')
    else:
        config[key] = value
        config.save()
        

def keys():
    return config.keys()

def items():
    return config.items()

def print_all():
    print(config.current_config)

def save():
    config.save()

def load():
    config.load()

