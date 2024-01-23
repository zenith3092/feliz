import logging
from .global_tools import get_configs, get_globals

def global_use_inspector():
    """
    This function is used to check whether the GLOBALS is used.
    """
    return len(get_globals().keys()) != 0

def config_use_inspector():
    """
    This function is used to check whether the CONFIGS is used.
    """
    if len(get_configs().keys()) == 0:
        logging.debug("CONFIGS is not used.")

def api_use_inspector(request):
    """
    This function is used to check whether the server_api.yml is used and the request is from the API.
    """
    config_use_inspector()
    SERVER_CONFIGS_API = get_configs("API")
    return SERVER_CONFIGS_API.get("API_ENABLE", False) and request.path.startswith("/api") 

def cors_use_inspector():
    """
    This function is used to check whether the CORS is used.
    """
    config_use_inspector()
    CORS_CONFIGS = get_configs("CORS")
    return CORS_CONFIGS.get("CORS_ENABLE", False)

def db_use_inspector():
    """
    This function is used to check whether the DB is used.
    """
    config_use_inspector()
    DB_CONFIGS = get_configs("DB")
    return DB_CONFIGS.get("DB_ENABLE", False)

def jwt_use_inspector():
    config_use_inspector()
    JWT_CONFIGS = get_configs("JWT")
    if type(JWT_CONFIGS) == dict:
        return JWT_CONFIGS.get("JWT_ENABLE", False)
    else:
        return False