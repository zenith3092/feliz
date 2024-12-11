from .file_tools import read_yaml

import os
import copy

GLOBALS = {"INIT": {},
           "CONFIGS": {},
           "DB": {},
           "API": {},
           "MONGO": "mongo",
           "POSTGRES": "postgres"}

def get_dict(d: dict, key: str, default=None):
    """
    Get the value of the key from the dictionary.
    
    Args:
        d (dict): The dictionary.
        key (str): The key.
        default (any): The default value.
        
    Returns:
        res (any): The value of the key.
    """
    if type(d) != dict:
        raise TypeError("The input d should be a dictionary.")
    if type(key) != str:
        raise TypeError("The input key should be a string.")
    
    if key == "":
        return d
    
    key_list = key.split(".")

    if len(key_list) == 1:
        if key not in d:
            return default
        return d[key]
    
    res = copy.deepcopy(d)
    for k in key_list:
        if k == "":
            raise ValueError("The input key with dot should not contain any empty value.")
        
        if k not in res:
            return default
        res = res[k]
    return res

## Directly get/set/delete/load the GLOBALS

def get_globals(key= "", default={}):
    return get_dict(GLOBALS, key, default)

def set_globals(key: str, value):
    GLOBALS[key] = value

def delete_globals(key: str):
    del GLOBALS[key]

def load_globals_from_yaml(key: str, config_fn="", fn="", raise_exception=False):
    """
    Load the GLOBALS from the yaml file.
    
    Args:
        key (str): The key of the GLOBALS.
        config_fn (str): The config file name.
        fn (str): The file name.
        raise_exception (bool): Whether to raise an exception when the indicator is False.
        
    Returns:
        res (dict): The result.
    """
    if config_fn:
        res = read_yaml(os.path.join(os.getcwd(), "configs", config_fn))
    else:
        res = read_yaml(fn)
        
    if res["indicator"]:
        set_globals(key, res["content"])
    elif raise_exception:
        raise Exception(res["message"])

    return res

## =========================================================

## Directly get/set/delete the CONFIGS

def get_configs(key= "", default={}):
    return get_dict(GLOBALS["CONFIGS"], key, default)

def set_configs(key: str, value):
    GLOBALS["CONFIGS"][key] = value

def delete_configs(key: str):
    del GLOBALS["CONFIGS"][key]

## =========================================================

## Directly get/set/delete the DB

def get_db(db_type="", key= ""):
    if db_type and key:
        return GLOBALS["DB"][db_type].get(key, None)
    elif db_type:
        return GLOBALS["DB"].get(db_type, {})
    else:
        return GLOBALS["DB"]

def set_db(db_type, key: str, value):
    if db_type not in GLOBALS["DB"]:
        GLOBALS["DB"][db_type] = {}
    GLOBALS["DB"][db_type][key] = value

def delete_db(db_type, key: str):
    del GLOBALS["DB"][db_type][key]