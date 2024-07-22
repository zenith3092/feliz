from abc import ABC, abstractmethod
from flask import g, jsonify, Request, Response
from flask_jwt_extended import get_jwt, verify_jwt_in_request
import json, logging
from .api_tools import FalseResponse, DevelopmentError, EmptyInputRequest
from .global_tools import get_globals
from .inspector_tools import global_use_inspector, api_use_inspector, jwt_use_inspector, db_use_inspector

## =============== Original Middleware ===============

class Middleware(ABC):
    """
    Middleware is an abstract class that defines each process of middleware.
    
    The methods "process_request" and "process_response" must be implemented.
    """
    @abstractmethod
    def process_request(self, request: Request, stop):
        """
        Process a request.

        Args:
            request (Request): The request to process.
            stop (function): A function that stops the request from continuing through the middleware list.
        """
        pass

    @abstractmethod
    def process_response(self, response: Response, stop):
        """
        Process a response.

        Args:
            response (Response): The response to process.
            stop (function): A function that stops the response from continuing through the middleware list.
        """
        pass

class MiddlewareSystem:
    """
    MiddlewareSystem is a class that allows you to add middleware to your application.
    """
    def __init__(self):
        self.middleware_list = [_PassGlobal(), _InputRequest(), _JWTMiddleware()]
        self.continue_request = True
        self.continue_response = True

    def use(self, middleware: Middleware):
        """
        Add a middleware to the middleware list.
        
        Args:
            middleware (Middleware): The middleware to add to the list.
        """
        self.middleware_list.append(middleware)
        return self

    def process_request(self, request: Request):
        """
        Process a request through the middleware list.

        Args:
            request (Request): The request to process.
        """
        for middleware in self.middleware_list:
            if not self.continue_request:
                break
            middleware.process_request(request, lambda: self.stop_request())
        self.continue_request = True

    def process_response(self, response: Response):
        """
        Process a response through the middleware list.

        Args:
            response (Response): The response to process.
        """
        for middleware in self.middleware_list:
            if not self.continue_response:
                break
            middleware.process_response(response, lambda: self.stop_response())
        self.continue_response = True

    def stop_request(self):
        """
        Stop the request from continuing through the middleware list.
        """
        self.continue_request = False
    
    def stop_response(self):
        """
        Stop the response from continuing through the middleware list.
        """
        self.continue_response = False

## =============== Private Middleware ===============

class _PassGlobal(Middleware):
    def process_request(self, request, stop):
        if global_use_inspector():
            GLOBALS = get_globals()
            for key, value in GLOBALS.items():
                setattr(g, key, value)
        
            if api_use_inspector(request):
                if request.method in ["GET", "POST", "PATCH", "PUT", "DELETE"]:
                    g.API_CONFIGS = self.get_api_configs(request)
                else:
                    stop()
            else:
                stop()
        else:
            logging.warning("The GLOBALS is not loaded.")
            stop()

    def process_response(self, response, stop):
        pass

    def get_api_configs(self, request):
        api_configs = g.get("API", {})
        route_list = request.path.strip("/").split("/")
        service = route_list[1]
        operation = route_list[2]
        return api_configs[service][operation][request.method]

class _InputRequest(Middleware):
    def process_request(self, request, stop):
        try:
            if request.method in ["GET", "DELETE"]:
                input_request = request.args.to_dict()
            elif request.method in ["POST", "PATCH", "PUT"]:
                input_request = request.get_json()
            elif request.method in ["OPTIONS"]:
                input_request = {}
                stop()
            else:
                input_request = {}
                stop()
        except:
            input_request = {}
        g.input_request = input_request
        
    def process_response(self, response, stop):
        pass

class _JWTMiddleware(Middleware):
    def process_request(self, request, stop):
        if jwt_use_inspector():
            api_configs = g.get("API_CONFIGS", {})
            if api_configs.get("Authentication", False):
                verify_jwt_in_request()

    def process_response(self, response, stop):
        pass

## =============== Auth Middleware ===============

class _AuthMiddleware(Middleware):
    """
    AuthMiddleware is a middleware about authentication.
    """
    @classmethod
    def get_user_list(cls, DH_OBJ: object, target: str, unique_key: str) -> dict:
        """
        Get the user data from database.
        
        Args:
            DH_OBJ (object): The database handler ( Instantiated Object ).
            target (str): The table or collection name.
            unique_key (str): The unique key of the table or collection.
        
        Returns:
            dict: The user data or the exception.
        """
        user_list = g.get("user_list", None)
        if not user_list:
            user_list = cls._query_data(DH_OBJ, target, unique_key)
            g.user_list = user_list
        return user_list
    
    @staticmethod
    def _query_data(DH_OBJ: object, target: str, unique_key: str) -> dict:
        """
        Query the user data from database.
        
        Args:
            DH_OBJ (object): The database handler ( Instantiated Object ).
            target (str): The table or collection name.
            unique_key (str): The unique key of the table or collection.
        
        Returns:
            dict: The user data or the exception.
        """
        token_data: dict = get_jwt()
        uid = token_data.get(unique_key, "")
        if not uid:
            raise DevelopmentError(f"Token doesn't have the value from {unique_key}.")
        
        if DH_OBJ.db_type == get_globals("POSTGRES"):
            condition = [(f"{unique_key}=", token_data.get(unique_key, ""))]
            query_res = DH_OBJ.get_data(table=target, conditional_rule_list=condition)
        elif DH_OBJ.db_type == get_globals("MONGO"):
            condition = {unique_key: token_data.get(unique_key, "")}
            query_res = DH_OBJ.get_data(schema_name=target, conditions=condition)
        else :
            raise DevelopmentError("DB type is not supported.")
        
        if not query_res["indicator"]:
            return FalseResponse(query_res["message"])

        for item in query_res["formatted_data"]:
            del item["password"]
        return query_res["formatted_data"]

class UserExistence(_AuthMiddleware):
    """
    This middleware is used to check if the user exists in database.

    Args:
        DH_OBJ (object): The database handler ( Instantiated Object ).
        target (str): The table or collection name.
        unique_key (str): The unique key of the table or collection.
    """
    def __init__(self, DH_OBJ, target: str, unique_key: str):
        self.DH_OBJ = DH_OBJ
        self.target = target
        self.unique_key = unique_key
    
    def process_request(self, request, stop):
        if jwt_use_inspector() and api_use_inspector(request) and db_use_inspector():
            api_configs = g.get("API_CONFIGS", {})
            if api_configs.get("Authentication", False):
                user_list = UserExistence.get_user_list(self.DH_OBJ, self.target, self.unique_key)
            
                if len(user_list) == 0:
                    token_data:dict = get_jwt()
                    return FalseResponse(f"This account ({token_data[self.unique_key]}) is not in database.")
                elif len(user_list) > 1:
                    return FalseResponse("User ID Query Error: Length > 1")
    
    def process_response(self, response, stop):
        pass

class UserDatabasePermission(_AuthMiddleware):
    """
    This middleware is used to check if the user has the same permission as the permission in database.

    Args:
        DH_OBJ (object): The database handler ( Instantiated Object ).
        target (str): The table or collection name.
        unique_key (str): The unique key of the table or collection.
    """
    def __init__(self, DH_OBJ, target: str, unique_key: str):
        self.DH_OBJ = DH_OBJ
        self.target = target
        self.unique_key = unique_key
    
    def process_request(self, request, stop):
        if jwt_use_inspector() and api_use_inspector(request) and db_use_inspector():
            api_configs = g.get("API_CONFIGS", {})
            if api_configs.get("Authentication", False):
                user_list = UserDatabasePermission.get_user_list(self.DH_OBJ, self.target, self.unique_key)
                if len(user_list) != 1:
                    return FalseResponse("User ID Query Error: Length != 1")
                
                token_permission = get_jwt().get("permission", "")
                db_permission = user_list[0].get("permission", "")
                if token_permission != db_permission:
                    return FalseResponse("Your token permission is not consistent with permission in database.")

    def process_response(self, response, stop):
        pass

class UserApiPermission(_AuthMiddleware):
    """
    This middleware is used to check if the user has the permission to call this API.
    """
    def process_request(self, request, stop):
        if jwt_use_inspector() and api_use_inspector(request):
            api_configs = g.get("API_CONFIGS", {})
            if api_configs.get("Authentication", False):
                token_permission = get_jwt().get("permission", "")
                if token_permission not in api_configs["Permission"]:
                    return FalseResponse("Your don't have the permission to call this API.")

    def process_response(self, response, stop):
        pass

class UserStatusCheck(_AuthMiddleware):
    """
    This middleware is used to check the account status.
    
    Args:
        DH_OBJ (object): The database handler object.
        target (str): The table or collection name.
        unique_key (str): The unique key of the table or collection.
        status_key (str): The status key. Default: "status".
        excluding_status (list): The excluding status.
    """
    def __init__(self, DH_OBJ, target: str, unique_key: str, status_key="status", excluding_status=[]):
        self.DH_OBJ = DH_OBJ
        self.target = target
        self.unique_key = unique_key
        self.status_key = status_key
        self.excluding_status = excluding_status
    
    def process_request(self, request: Request, stop):
        if jwt_use_inspector() and api_use_inspector(request) and db_use_inspector():
            api_configs = g.get("API_CONFIGS", {})
            if api_configs.get("Authentication", False):
                user_list = UserStatusCheck.get_user_list(self.DH_OBJ, self.target, self.unique_key)
                if len(user_list) != 1:
                    return FalseResponse("User ID Query Error: Length != 1")
                
                status = user_list[0][self.status_key]
                if status in self.excluding_status:
                    return FalseResponse(f"This user is {status.capitalize()}")
    
    def process_response(self, response: Response, stop):
        pass

## =============== SafeKeys Middleware ===============

class _SafeKeysMiddleware(Middleware):
    @classmethod
    def get_input_request(cls, request):
        input_request = g.get("input_request", {})
        api_configs = g.get("API_CONFIGS", {})
        constructed_safe_keys = g.get("constructed_safe_keys", False)
        valid_methods = ["GET", "POST", "PATCH", "PUT", "DELETE"]

        if (request.method in valid_methods) and (not constructed_safe_keys) :
            input_request = cls._construct_input_request(input_request, api_configs)
            g.input_request = input_request
            g.constructed_safe_keys = True
        return input_request

    @classmethod
    def _construct_input_request(cls, input_request, api_configs):
        input_key_list = input_request.keys()
        opt_key_list = api_configs["Optionals"]
        opt_val_data = api_configs["OptionalDefaults"]
        if type(opt_val_data) == list:
            cls.check_api_configs_validity(api_configs)
            update_dict = {}
            for index in range(len(opt_key_list)):
                if opt_key_list[index] not in input_key_list:
                    update_dict[opt_key_list[index]] = opt_val_data[index]
            input_request.update(update_dict)
        elif type(opt_val_data) == dict:
            if not set(opt_val_data.keys()).issubset(set(opt_key_list)):
                raise DevelopmentError("The keys in OptionalDefaults should be included in Optionals.")
            for key in opt_key_list:
                if key not in input_key_list:
                    if key in opt_val_data:
                        input_request[key] = opt_val_data[key]
                    else:
                        input_request[key] = EmptyInputRequest(key)
        return input_request

    @staticmethod
    def check_api_configs_validity(api_configs):
        if not len(api_configs["Optionals"]) == len(api_configs["OptionalDefaults"]):
            raise DevelopmentError("The length of 'Optionals' and 'OptionalDefaults' in api config file should be the same.")

class SafeMandatoryKeys(_SafeKeysMiddleware):
    """
    This middleware is used to check if the input request has the mandatory keys.
    """
    def process_request(self, request, stop):
        if api_use_inspector(request):
            input_request = SafeMandatoryKeys.get_input_request(request)
            input_keys_list = input_request.keys()
            api_configs = g.get("API_CONFIGS", {})
            lack_list = []
            for item in api_configs["Mandatory"]:
                if item not in input_keys_list:
                    lack_list.append(item)
            if len(lack_list) > 0:
                return FalseResponse(f"No input: {','.join(lack_list)}")

    def process_response(self, response, stop):
        pass

class SafeInputType(_SafeKeysMiddleware):
    """
    This middleware is used to check if the input type is correct.
    """
    def process_request(self, request, stop):
        if api_use_inspector(request):
            input_request = SafeInputType.get_input_request(request)
            api_configs = g.get("API_CONFIGS", {})
            use_inspector = api_configs.get("InputInspect", False)
            input_type_configs = api_configs.get("InputType", None)
            if use_inspector:
                if input_type_configs == None:
                    raise DevelopmentError("You should set the InputType in server_api.yaml if you want to use InputInspect.")
                
                for inspect_key, inspect_type_info_str in input_type_configs.items():
                    inspect_type_info = inspect_type_info_str.split("::")
                    nullable = False
                    if len(inspect_type_info) > 1:
                        inspect_type = inspect_type_info[0]
                        nullable = "nullable" in inspect_type_info[1:]
                    else:
                        inspect_type = inspect_type_info[0]
                    
                    try:
                        inspect_value = input_request[inspect_key]
                    except KeyError as e:
                        raise DevelopmentError(f"The InputType of server_api.yaml not have the key '{inspect_key}'")
                    
                    if inspect_value == None:
                        if not nullable:
                            return FalseResponse(f"The input type of '{inspect_key}' should not be None but *{inspect_type}")
                    elif not isinstance(inspect_value, EmptyInputRequest):
                        if not self.input_type_inspector(inspect_type, inspect_value):
                            return FalseResponse(f"The input type of '{inspect_key}' should not be *{type(inspect_value).__name__} but *{inspect_type}")

    def input_type_inspector(self, inspect_type: str, inspect_value: str) -> bool:
        flag = True
        if inspect_type in ["json", "json-list", "json-dict"]:
                try:
                    loads = json.loads(inspect_value)
                    if inspect_type == "json-list":
                        flag = (type(loads) == list)
                    elif inspect_type == "json-dict":
                        flag = (type(loads) == dict)
                except:
                    flag = False
        else:
            flag = ( eval(inspect_type) == type(inspect_value) )
        return flag

    def process_response(self, response, stop):
        pass

# =============== Response Middleware ===============

class JsonifyResponse(Middleware):
    """
    This middleware is used to jsonify the response.
    """
    def process_request(self, request, stop):
        pass

    def process_response(self, response, stop):
        if isinstance(response.data, dict):
            response.data = jsonify(response.data)
        return response
