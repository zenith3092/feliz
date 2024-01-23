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
        - API: The configurations of the API.
    """
    def decorator(func):
        @blueprint.route(endpoint, **options)
        @wraps(func)
        def wrapper():
            if api_use_inspector(request):
                user_list = g.get("user_list", [])
                if len(user_list) == 1:
                    user_data = user_list[0]
                else:
                    user_data = {}
                params = {"input_request": g.get("input_request", {}),
                        "DB": g.get("DB", {}),
                        "USER_DATA": user_data,
                        "CONFIGS": g.get("CONFIGS", {}),
                        "API_CONFIGS": g.get("API_CONFIGS", {})}
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

def FalseResponse(message: str) -> dict:
    """
    This function is used to return the message to the client with {"indicator": False, "message": message}
    
    Args:
        message (str): The message to return to the client.
    
    Returns:
        dict: The message to return to the client.
    """
    raise IndicatorFalseException(message)

class IndicatorFalseException(Exception):
    """
    This class is used to raise errors in the server.
    If developers want to return indicator False, they should raise this error.
    Then, server will return the message to the client with {"indicator": False, "message": message}
    """
    def __init__(self, message):
        super().__init__()
        self.message = message
        self.filename, self.lineno, self.function, self.text = traceback.extract_stack()[-2]
    
    def __str__(self):
        # logging.warning("\nServer API Indicator False:")
        # logging.warning(f"{self.filename}  Line:{self.lineno}  {self.function}")
        # logging.warning(self.message, "\n")
        return self.message

class DevelopmentError(Exception):
    def __init__(self, message):
        super().__init__()
        self.message = message
        self.filename, self.lineno, self.function, self.text = traceback.extract_stack()[-2]
    
    def __str__(self):
        print("\nServer Development Error:")
        print(f"{self.filename}   Line:{self.lineno} {self.function}")
        print(self.message, "\n")
        return self.message

def error_handler(e):
    if not isinstance(e, IndicatorFalseException):
        logging.warning(f"\n====================================================")
        logging.warning(traceback.format_exc())
        logging.warning("=====================================================\n")

def api_route_register(app, blueprint: Blueprint):
    app.register_blueprint(blueprint, url_prefix=f"/api/{blueprint.name}")