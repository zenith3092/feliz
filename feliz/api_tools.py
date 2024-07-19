import traceback
import logging
from functools import wraps
from flask import request, g, Blueprint
from .inspector_tools import api_use_inspector

def handler(endpoint: str, blueprint: Blueprint, **options):
    """
    This decorator is used to handle the request from the client.
    Parameters:
        endpoint: The endpoint of the request.
        blueprint: The blueprint of the request.
        **options: The options of the request.
    
    Returns:
        func: The function to handle the request with the following parameters:
        - input_request: The input request from the client.
        - DB: The database objects (Postgres Handler).
        - CONFIGS: The configurations of the server.
        - API_CONFIGS: The configurations of the API.
        - USER_DATA: The information of the user.
    """
    def decorator(func):
        @blueprint.route(endpoint, **options)
        @wraps(func)
        def wrapper(**kwargs):
            if api_use_inspector(request):
                user_list = g.get("user_list", [])
                if len(user_list) == 1:
                    user_data = user_list[0]
                else:
                    user_data = {}
                params = {"input_request": g.get("input_request", {}),
                          "API_CONFIGS":   g.get("API_CONFIGS", {}),
                          "CONFIGS":       g.get("CONFIGS", {}),
                          "DB":            g.get("DB", {}),
                          "USER_DATA":     user_data}
                params.update(kwargs)
                return func(**params)
            else:
                raise DevelopmentError("The server_api.yaml is not used, so 'handler' decorator is invalid.")
        return wrapper
    return decorator

def TrueResponse(message: str, content=None) -> dict:
    """
    This function is used to return the message to the client with {"indicator": True, "message": message, "content": content}
    
    Args:
        message (str): The message to return to the client.
        content (any): The content to return to the client.
    
    Returns:
        dict: The message to return to the client.
    """
    return {"indicator": True, "message": message, "content": content}

def FalseResponse(message: str, content=None) -> dict:
    """
    This function is used to return the message to the client with {"indicator": False, "message": message}
    
    Args:
        message (str): The message to return to the client.
    
    Returns:
        dict: The message to return to the client.
    """
    raise IndicatorFalseException(message, content=content)

class IndicatorFalseException(Exception):
    """
    This class is used to raise errors in the server.
    If developers want to return indicator False, they should raise this error.
    Then, server will return the message to the client with {"indicator": False, "message": message}
    """
    def __init__(self, message, content=None):
        super().__init__()
        self.message = message
        self.content = content
        self.filename, self.lineno, self.function, self.text = traceback.extract_stack()[-2]
    
    def __str__(self):
        return self.message
    
    def get_json_response(self):
        return {"indicator": False, "message": self.message, "content": self.content}

class DevelopmentError(Exception):
    def __init__(self, message):
        super().__init__()
        self.message = message
        self.filename, self.lineno, self.function, self.text = traceback.extract_stack()[-2]
    
    def __str__(self):
        return self.message

class EmptyInputRequest:
    """
    This class is used to handle the empty input request.
    """
    def __init__(self, key: str) -> None:
        self.key = key
    
    def __str__(self) -> str:
        return f"(EmptyInputRequest) {self.key}"
    
    def __repr__(self) -> str:
        return self.__str__()

def error_handler(e, loggerIndicatorFalse=False):
    """
    This function is used to handle the error in the server.

    Args:
        e (Exception): The exception to handle.
        loggerIndicatorFalse (bool): If True, the server will log the error message when the class is IndicatorFalseException.
    """
    if isinstance(e, IndicatorFalseException):
        if loggerIndicatorFalse:
            logging.warning(f"\n============ Server API Indicator False ============")
            logging.warning(traceback.format_exc())
            logging.warning("=====================================================\n")
        return e.get_json_response()
    else:
        logging.warning(f"\n====================================================")
        logging.warning(traceback.format_exc())
        logging.warning("=====================================================\n")
        return {"indicator": False, "message": str(e), "content": None}

def api_route_register(app, blueprint: Blueprint):
    """
    This function is used to register the blueprint to the app.
    The url_prefix is f"/api/{blueprint.name}".
    """
    app.register_blueprint(blueprint, url_prefix=f"/api/{blueprint.name}")
