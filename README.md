# Feliz (with Flask)

A framework designed to assist in using Flask.

## Template

If you want to use the template of Feliz, you can clone the following repository:

[feliz-template](https://github.com/zenith3092/feliz-template)

## Features

-   **Rapid API Development**: Offers decorators and utility functions to quickly establish RESTful APIs with minimal code.
-   **Configuration Management**: Built-in support for managing configurations across different development stages (development, testing, production).
-   **Error Handling**: Simplifies the process of handling errors and customizing responses for a better API user experience.
-   **Database Integration**: Facilitates easier integration with databases, providing abstraction layers for common operations. Supporting PostgresDB and MangoDB.
-   **Authentication & Authorization**: Includes ready-to-use modules for handling user authentication and authorization.

## Getting Started

### Environment

`Python 3.9` or later

### Installation

Install Feliz easily with pip, which will also install all required dependencies:

```bash
pip install feliz
```

### Dependencies

#### feliz

`flask`

`flask-cors`

`flask_jwt_extended`

`bcrypt`

`pyyaml`

## Configurations

### server_config.yaml

`$ cd {your_project}/configs/private/server_config.yaml`

This is the configuration file of the server. You can set the server name, host, port, debug mode, number of workers, etc.

If needed, you can add more configurations to this file.

```yaml
SERVER:
  NAME: # server name (string)
  HOST: # server host (string)
  PORT: # server port (int)
  DEBUG: # whether to open debug mode (boolean)
  WORKERS: # number of workers (int)
JWT:
  JWT_ENABLE: # whether to enable jwt (boolean)
  JWT_ALGORITHM: # jwt algorithm (string)
  JWT_SECRET_KEY: # jwt secret key (string)
  EXPIRE_HOURS: # jwt expire hours (int) or INFINITY
  MESSAGE: # jwt message (string) if not set, the default message will be used
    UNAUTHORIZED: # unauthorized message (string)
    INVALID: # invalid token message (string)
    EXPIRED: # expired token message (string)
    REVOKED: # revoked token message (string)
CORS:
  CORS_ENABLE: # whether to enable cors (boolean)
DB:
  DB_ENABLE: # whether to enable database function (boolean)
  INI_FILE: # database configuration file path (string)
API:
  API_ENABLE: # whether to enable api function (boolean)
  API_FILE: # api configuration file path (string)
```

### database.ini

`$ cd {your_project}/configs/private/database.ini` (recommended path)

This is the configuration file of the database. You can set the database type, host, port, database name, username, password, etc.

If needed, you can add more sections to this file.

```ini
[<your_section_name>]
db_type=; postgres or mongo
host=; database host
port=; database port
database=; database name
username=; database username
password=; database password
[<another_section_name>]
...
```

### server_api.yaml

`$ cd {your_project}/configs/public/server_api.yaml`

This is the configuration file of the API. If you use `@handler` decorator, you need to set the configuration of the API and not forget to turn the `API_ENABLE` to `True` in `server_config.yaml`.

```yaml
admin: # service
  accounts: # operation
    POST: # method
      Description: "add_accounts"
      Authentication: True # whether to enable authentication (jwt, user authentication)
      Permission: ["1", "2", "3", "4", "e"] # this API can be used by which permission
      Mandatory: ["add_list"] # mandatory parameters
      Optionals: ["return_added"] # optional parameters
      OptionalDefaults: [False] # default value of optional parameters
      InputInspect: True # whether to inspect the type of input parameters
      InputType: { "add_list": list, "return_added": bool } # type of input parameters
```

ç

1. The url of each API follows the format:
   `http://{host}:{port}/api/{service}/{opration}`
2. Each element in `Permission` is used to classify the user's group and no cascading relationship between them.
3. `Optionals` and `OptionalDefaults` must be the same length.
4. About `InputType`, no need to set all the parameters, only set the parameters that need to be inspected.
5. `InputType` supports all types which Python supports. Besides, Feliz supports `json` type, which inspect whether the input parameter can be json loads. Moreover, Feliz also supports `json-list` and `json-dict` types, which inspect whether the input parameter can be json loads and the type of the loaded data is list or dict.

## Usage

### Initialware & InitialwareSystem

Initialware is a class that handles a part of the initialization of the application. For example, you can use it load the configuration file, set up the jwt, create the tables in the database, etc.

InitialwareSystem is a class that manage the initialware. You can use it to add initialware to this class, and decide the order of the initialware.

Feliz provides some initialware for you to use, such as `ImportGlobals`, `JWTInitialware`, `CorsInitialware`, `_DatabaseInitialware` including `PostgresInitialware` and `MongoInitialware`.

The following is an example of how to use Initialware and InitialwareSystem:

```python
from flask import Flask
from feliz.initialware_tools import InitialwareSystem, ImportGlobals, JwtInitialware, CorsInitialware
from feliz_db.postgres_tools import PostgresHandler
from models import models

app = Flask(__name__)

iws = InitialwareSystem()
iws.use(ImportGlobals())
iws.use(JwtInitialware())
iws.use(CorsInitialware())
iws.use(PostgresInitialware(PostgresHandler, models["postgres"]))
iws.execute(app)
```

#### Note:

-   `models` is a dictionary that contains the models of the database. If you want to learn more about the models, please refer to the [feliz_db](https://github.com/zenith3092/feliz_db)

### Middleware & MiddlewareSystem

Middleware is a class that handles the part outside (i.e. before and after entering) a API handler. For example, you can use it to check the user's permission, inspect the input parameters, and close the database connection after the request is completed.

MiddlewareSystem is a class that manage the middleware. You can use it to add middleware to this class, and decide the order of the middleware.

Feliz provides some middleware for you to use, such as the fllowing:

1. Private Middleware: `_PassGlobal`, `_InputRequest`, `_JWTMiddleware`
2. Auth Middleware: `_AuthMiddleware`, `UserExistence`, `UserDatabasePermission`, `UserApiPermission`, `UserStatusCheck`
3. SafeKeys Middleware: `_SafeKeysMiddleware`, `SafeMandatoryKeys`, `SafeInputType`
4. Response Middleware: `JsonifyResponse`

MiddlewareSystem is used in before_request and after_request of Flask. The following is an example of how to use Middleware and MiddlewareSystem:

```python
from flask import request
from feliz.middleware_tools import MiddlewareSystem, UserExistence, UserDatabasePermission, UserApiPermission, SafeMandatoryKeys, SafeInputType, JsonifyResponse, UserStatusCheck


@app.before_request
def before_request():
    """
    This function is used to handle the request before the request is handled.
    """
    DH = get_db("postgres", "mlt")

    mws = MiddlewareSystem()
    mws.use(SafeMandatoryKeys())
    mws.use(SafeInputType())
    mws.use(UserExistence(DH, "admin.user_list", "user_id"))
    mws.use(UserStatusCheck(DH, "admin.user_list", "user_id"))
    mws.use(UserDatabasePermission(DH, "admin.user_list", "user_id"))
    mws.use(UserApiPermission())
    mws.process_request(request)

@app.after_request
def after_request(response):
    """
    This function is used to handle the response after the request is handled.
    """
    mws = MiddlewareSystem()
    mws.use(JsonifyResponse())
    mws.process_response(response)
    return response
```

### Handler Decorator

Feliz provides a decorator called `handler` to help you handle the API. It contains route decorator of Flask, and it can pass the parameters of the API to the handler function.

The parameters of the handler decorator are as follows:

1. input_request: the input parameters of the API.
2. DB: the database handler.
3. CONFIGS: the configuration of the server. (server_config.yaml)
4. API_CONFIGS: the configuration of the API. (server_api.yaml)
5. USER_DATA: the information of the user.

All the parameters are encapsulated in a parameter called `params`, and you can decide which parameters to use in the handler function. (Note that `params` is the required parameter of the handler function.)

#### Response

To communicate the outcome of operations to the client, we provide two response functions:

`TrueResponse(message= {message}, content= {content})` for successful operations, returning `{"indicator": True, "message": message, "content": content}`.

`FalseResponse(message= {message})` for unsuccessful operations, returning `{"indicator": False, "message": message}`.

These ensure a standardized way of conveying success or failure, along with any relevant message and content.

#### Example

The following is an example of how to use handler decorator:

In `apis/admin_api.py`:

```python
from flask import Blueprint
from feliz.api_tools import handler, TrueResponse, FalseResponse
from feliz_db.postgres_tools import PostgresHandler

adminApi = Blueprint("admin", __name__)

@handler("/accounts", adminApi, methods=["POST"])
def add_accounts(input_request, DB, **params):
    """
    This function is used to add accounts.
    """
    add_list, return_added = input_request["add_list"], input_request["return_added"]

    DH: PostgresHandler = DB["postgres"]["mlt"]
    add_res = DH.add_data("admin.accounts", add_list)
    if add_res["indicator"]:
        if return_added:
            get_res = DH.get_data("admin.accounts", conditional_rule_list= [("user_id=", add_list[0]["user_id"])])
            if get_res["indicator"]:
                return TrueResponse(get_res["message"], get_res["formatted_data"])
            else:
                return FalseResponse(get_res["message"])
        else:
            return TrueResponse(add_res["message"])
    else:
        return FalseResponse(add_res["message"])
```

Register in `app.py`:

```python
from feliz.api_tools import api_route_register
from apis.admin_api import adminApi

app = Flask(__name__)
api_route_register(app, adminApi)
```

## Author

-   **Vincent Wu** - [zenith3092@gmail.com](mailto:zenith3092@gmail.com)
-   **Linga Chen**
-   **Brian Yin** - [land7411bu@gmail.com](mailto:land7411bu@gmail.com)
