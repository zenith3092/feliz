from .file_tools import read_ini
from .global_tools import load_globals_from_yaml, get_configs, set_db, get_db, get_globals, set_configs
from .inspector_tools import jwt_use_inspector, cors_use_inspector, db_use_inspector
from .api_tools import api_route_register

from flask import Flask
from flask.json.provider import DefaultJSONProvider, _default
from flask_jwt_extended import JWTManager
from flask_cors import CORS

from abc import ABC, abstractmethod
import logging
import datetime
import time
import os
import json
import importlib

## =============== Original Initialware =============== ##

class Initialware(ABC):
    """
    Initialware is an abstract class that defines each process of initialization.
    
    The method "process" must be implemented.
    """
    @abstractmethod
    def process(self, prev_data: dict):
        """
        Process the initialization.
        
        Args:
            prev_data (dict): The previous data.
        """
        pass
    
    def next(self, prev_data):
        """
        Call the process method.
        """
        return self.process(prev_data)

class InitialwareSystem:
    """
    The InitialwareSystem class allows you to execute a series of initialwares.
    """
    def __init__(self):
        self.initialwares = []

    def use(self, initialware: Initialware):
        """
        Add an initialware to the initialware list.
        
        Args:
            initialware (Initialware): The initialware to add to the list.
        
        Returns:
            InitialwareSystem: The InitialwareSystem instance.
        """
        self.initialwares.append(initialware)
        return self

    def execute(self, app: Flask, first_data: dict = {}):
        """
        Execute the initialware list.

        Args:
            first_data (dict): The first input data. (The key "app" is reserved.)
        """
        data = first_data
        if "app" in data:
            raise Exception("The key 'app' is reserved in InitialwareSystem.")
        data["app"] = app
        start = time.time()
        for initialware in self.initialwares:
            data = initialware.next(data)
        end = time.time()
        logging.info(f" InitialwareSystem Execution Time: {end - start} seconds")

        server_config = get_configs("SERVER")
        logging.info(f" ***** {server_config['NAME']} is running on {server_config['HOST']}:{server_config['PORT']} ***** ")

## =============== Initialware Tools =============== ##

class ImportGlobals(Initialware):
    """
    Import the GLOBALS.
    """
    def __init__(self, config_fn="private/server_config.yaml"):
        self.config_fn = config_fn

    def process(self, prev_data):
        """
        Import the GLOBALS.
        """
        load_config_res = load_globals_from_yaml(key="CONFIGS", config_fn=self.config_fn)
        if load_config_res["indicator"]:
            config_data = load_config_res["content"]
            if ("API" in config_data) and (config_data["API"].get("API_ENABLE", False)):
                load_api_res = load_globals_from_yaml(key="API", config_fn=config_data["API"].get("API_FILE", ""))
                if not load_api_res["indicator"]:
                    logging.warning(f'Load API Config File Error: {load_api_res["message"]}')
        else:
            logging.warning(f'Load Config File Error: {load_config_res["message"]}')
        return prev_data

class JwtInitialware(Initialware):
    """
    The JwtInitialware class is used to initialize the JWT.
    """
    def process(self, prev_data):
        """
        Initialize the JWT.
        """
        if jwt_use_inspector():
            JWT_CONFIGS = get_configs("JWT")
            ETERNAL_JWT_TOKEN = JWT_CONFIGS.get("ETERNAL_JWT_TOKEN", False)
            
            if ETERNAL_JWT_TOKEN:
                JWT_CONFIGS.update({"JWT_ACCESS_TOKEN_EXPIRES": False})
            else:
                expired_configs = JWT_CONFIGS.get("EXPIRE_TIME_DELTA", None)
                if expired_configs == None:
                    expired_configs = {"hours": JWT_CONFIGS["EXPIRE_HOURS"]}
                JWT_CONFIGS.update({"JWT_ACCESS_TOKEN_EXPIRES": datetime.timedelta(**expired_configs)})
            prev_data["app"].config.update(JWT_CONFIGS)
            jwt = JWTManager(prev_data["app"])
            
            RETURN_MESSAGE = JWT_CONFIGS.get("MESSAGE", {})

            @jwt.unauthorized_loader
            def unauthorized_callback(error):
                return {"indicator": False, "message": RETURN_MESSAGE.get("UNAUTHORIZED", "Missing JWT token")}

            @jwt.invalid_token_loader
            def invalid_token_callback(error):
                PRINT_LOG = JWT_CONFIGS.get("PRINT_LOG", False)
                if PRINT_LOG:
                    logging.warning(f"Invalid JWT token: {error}")
                return {"indicator": False, "message": RETURN_MESSAGE.get("INVALID_TOKEN", "Invalid JWT token")}

            @jwt.revoked_token_loader
            def revoked_token_callback(error):
                return {"indicator": False, "message": RETURN_MESSAGE.get("REVOKED_TOKEN", "Revoked JWT token")}

            @jwt.expired_token_loader
            def expired_token_callback(error, expired_token):
                return {"indicator": False, "message": RETURN_MESSAGE.get("EXPIRED_TOKEN", "Expired JWT token")}
        return prev_data

class CorsInitialware(Initialware):
    """
    The CorsInitialware class is used to initialize the CORS.
    Please refer to the Flask-CORS documentation for more information.
    https://flask-cors.readthedocs.io/en/latest/api.html
    
    Args:
        settings (dict)
    """
    def __init__(self, settings={}):
        self.kwargs = settings
    
    def process(self, prev_data):
        """
        Initialize the CORS.
        """
        if cors_use_inspector():
            cors_configs = {}
            if self.kwargs == {}:
                cors_configs = self.kwargs
            else:
                CORS_CONFIGS = get_configs("CORS")
                cors_configs = CORS_CONFIGS.get("SETTINGS", {})
            CORS(prev_data["app"], **cors_configs)
        return prev_data

class _DatabaseInitialware(Initialware):
    """
    The DatabaseInitialware class is used to initialize the database.
    """
    MONGO = get_globals("MONGO")
    POSTGRES = get_globals("POSTGRES")
    INI_CONFIG = {}
    
    @classmethod
    def get_ini_configs(cls):
        """
        Get the ini configs.
        """
        indicator = True
        message = "Success"

        if len(cls.INI_CONFIG.keys()) == 0:
            cls.INI_CONFIG = {cls.MONGO: {}, cls.POSTGRES: {}}

            DB_CONFIGS = get_configs("DB")
            ini_res = read_ini(f"{os.getcwd()}/configs/{DB_CONFIGS['INI_FILE']}")
            if ini_res["indicator"]:
                ini_data = ini_res["content"]
                for section in ini_res["content"].sections():
                    if ini_data[section]["db_type"] in cls.INI_CONFIG.keys():
                        cls.INI_CONFIG[ini_data[section]["db_type"]][section] = ini_data[section]
                    else:
                        indicator = False
                        message = f'({section}) {ini_data[section]["db_type"]} is not a valid db_type.'
            else:
                indicator = False
                message = f'{ini_res["message"]}'
        return {"indicator": indicator, "message": message, "content": cls.INI_CONFIG}

class MongoInitialware(_DatabaseInitialware):
    """
    The MongoInitialware class is used to initialize the mongo database.

    Args:
        mongo_handler_class (class): The mongo handler class.
        mongo_models (dict): {alias: models}
    """
    def __init__(self, mongo_handler_class, mongo_models):
        self.mongo_handler_class = mongo_handler_class
        self.mongo_models = mongo_models
    
    def process(self, prev_data):
        """
        Initialize the mongo database.
        """
        if db_use_inspector():
            get_ini_res = self.get_ini_configs()
            if not get_ini_res["indicator"]:
                logging.warning(f'Load INI File Error: {get_ini_res["message"]}')
                return prev_data
            ini_configs = get_ini_res["content"][MongoInitialware.MONGO]
            for section, configs in ini_configs.items():
                alias = section
                db_obj = self.mongo_handler_class(
                    alias=alias,
                    host=configs["host"],
                    port=int(configs["port"]),
                    username=configs["username"],
                    password=configs["password"],
                    database=configs["database"],
                    schemas=self.mongo_models[alias]
                )
                set_db(MongoInitialware.MONGO, section, db_obj)

            for section, configs in ini_configs.items():
                db_obj = get_db(MongoInitialware.MONGO, section)
                models = self.mongo_models[section]
                for schema_name, _ in models.items():
                    db_obj.get_data(schema_name, limit=1)

        return prev_data

class PostgresInitialware(_DatabaseInitialware):
    """
    The PostgresInitialware class is used to initialize the postgres database.

    Args:
        postgres_handler_class (class): The postgres handler class.
        postgres_models (dict): {section: models}
    """
    def __init__(self, postgres_handler_class, postgres_models={}):
        self.postgres_handler_class = postgres_handler_class
        self.postgres_models = postgres_models
    
    def process(self, prev_data):
        """
        Initialize the postgres database.
        """
        if db_use_inspector():
            get_ini_res = self.get_ini_configs()
            if not get_ini_res["indicator"]:
                logging.warning(f'Load INI File Error: {get_ini_res["message"]}')
                return prev_data
            ini_configs = get_ini_res["content"][PostgresInitialware.POSTGRES]

            for section, configs in ini_configs.items():
                db_obj = self.postgres_handler_class(
                    host=configs["host"],
                    port=configs["port"],
                    username=configs["username"],
                    password=configs["password"],
                    database=configs["database"],
                )
                set_db(PostgresInitialware.POSTGRES, section, db_obj)

            for section, configs in ini_configs.items():
                db_obj = get_db(PostgresInitialware.POSTGRES, section)
                if section in self.postgres_models:
                    init_models = self.postgres_models[section]
                    keys_list = list(init_models.keys())
                    modified_meta_authorization = False
                    for index in range(len(keys_list)):
                        key = keys_list[index]
                        model = init_models[key]
                        if model.meta["initialize"]:
                            if model.meta["init_type"] == model.INIT_TYPE["SCHEMA"] and model.meta["authorization"] == None:
                                model.meta["authorization"] = configs["username"]
                                modified_meta_authorization = True
                            model.create_sql()
                        if index == len(keys_list) - 1:
                            model.execute_sql(db_obj)
                            model.clear_sql()
                            if modified_meta_authorization:
                                model.meta["authorization"] = None
                                modified_meta_authorization = False
        return prev_data

class JsonifyInitialware(Initialware):
    """
    The JsonifyInitialware class is used to define the method of jsonify.
    Some classes may not be able to use jsonify directly, so this class is used to define jsonify.
    
    Args:
        customized_jsonify (function): The customized jsonify function. The function must have two arguments: obj and default_jsonify.
            \- obj: The object to jsonify.
            \- default_jsonify: If the obj is not the type that the customized jsonify function can handle, you should use this function to jsonify the obj.
    
    Example:
        def customized_jsonify(obj, default_jsonify):
            if isinstance(obj, YourClass):
                return obj.to_json()
            return default_jsonify(obj)
    """
    def __init__(self, customized_jsonify=None):
        self.customized_jsonify = customized_jsonify
    
    def process(self, prev_data: dict):
        class CustomJSONEncoder(DefaultJSONProvider):
            @staticmethod
            def default_action(obj):
                if self.customized_jsonify:
                    return self.customized_jsonify(obj, default_jsonify=_default)
                else:
                    return _default(obj)
            default = default_action
        prev_data["app"].json = CustomJSONEncoder(prev_data["app"])
        return prev_data

class ImportI18NInitialware(Initialware):
    """
    The ImportI18NInitialware class is used to import the i18n data. Thus, server can use the i18n config to translate the message.
    The structure of the i18n json file is as follows:
    \n {
        "key1": {
            "en": "value1",
            "zh": "value2"
        },
        "key2": {
            "en": "value3",
            "zh": "value4"
        }
    }

    Args:
        file_path (str): The file path of the i18n json file. The default value is f"{os.getcwd()}/configs/public/i18n.json".
    """
    def __init__(self, file_path=f"{os.getcwd()}/configs/public/i18n.json"):
        self.file_path = file_path

    def process(self, prev_data):
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                i18n_data = json.load(f)
        except:
            i18n_data = {}
        set_configs("I18N", i18n_data)
        
        return prev_data

class RegisterApisInitialware(Initialware):
    """
    The RegisterApisInitialware class is used to register the APIs. Based on the server_api.yaml, importing the necessary APIs to the server.
    Therefore, server does not need to import all the APIs in apis folder, which can reduce the memory usage and improve the efficiency.

    The process of registering the APIs is the same as the function api_route_register.
    Thus, the url_prefix is f"/api/{blueprint.name}".

    Args:
        api_folder (str): The folder name of the APIs. The default value is "apis".
        module_suffix (str): The suffix of the module. The default value is "_api".
        blueprint_suffix (str): The suffix of the blueprint. The default value is "Api".
        disabled_apis (list): The list of the disabled APIs. The default value is [].
    """
    def __init__(self, api_folder="apis", module_suffix="_api", blueprint_suffix="Api", disabled_apis=[]):
        self.api_folder = api_folder
        self.module_suffix = module_suffix
        self.blueprint_suffix = blueprint_suffix
        self.disabled_apis = disabled_apis
    
    def process(self, prev_data):
        SERVER_API = get_globals("API")
        API_CONFIGS = get_configs("API")
        API_ENABLE = API_CONFIGS.get("API_ENABLE", False)

        if API_ENABLE:
            api_list = SERVER_API.keys()
            for api_name in api_list:
                if api_name in self.disabled_apis:
                    continue
                api_module = importlib.import_module(f"{self.api_folder}.{api_name}{self.module_suffix}")
                api_blueprint = getattr(api_module, f"{api_name}{self.blueprint_suffix}")
                api_route_register(prev_data["app"], api_blueprint)
        return prev_data