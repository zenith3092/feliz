# Update History

## v0.1.0

### Modify `FalseResponse` in api_tools

Adding a new parameter `raise_error` to the `FalseResponse` to determine whether to raise an error when the response is `FalseResponse`. The default value is `True`.

In addition, another parameter `print_log` is added to the `FalseResponse` to determine whether to print the log when the response is `FalseResponse`. This parameter can be `True`, `False` or `None`. The default value is `None`.

The effect of the `print_log` is as follows:

-   `True`: Print the log.
-   `False`: Do not print the log.
-   `None`: Print the log when the parameter `loggerIndicatorFalse` of the function `error_handler` is `True` . Otherwise, do not print the log. This case is posterior to the above two cases.

### Modify `api_route_register` in api_tools

Adding a new parameter `api_prefix` to the `api_route_register` to determine the prefix of the api route. The default value is `"/api"`.

### Modify `hash_password` in auth_tools

Adding a new parameter `salt_rounds` to the `hash_password` to determine the rounds of the salt. The default value is `12`.

### Modify all functions in file_tools

All the functions in the `file_tools` return the same dictionary format. The dictionary contains the key `indicator`, `message` and `content`.

Besides, in function `read_yaml`, if the content of a file is empty, the function will return an empty dictionary as the content.

### Modify `get_globals` and `get_configs` in global_tools

Now, programmers can get the global variables and configurations via dot notation. For example, `get_globals("a.b.c")` is equivalent to `get_globals("a")["b"]["c"]`.

### Modify `JwtInitialware` in initialware_tools

Now, new config parameters below are added to the `JwtInitialware`(in `JWT` zone of config file):

-   `ETERNAL_JWT_TOKEN`: [bool] Whether the jwt token is eternal. The default value is `False`.
-   `EXPIRE_TIME_DELTA`: [dict] The expire time delta of the jwt token. e.g. `{"days": 1}`. -`PRINT_LOG`: [bool] Whether to print the log when the jwt token is invalid. The default value is `False`.

### Modify `CorsInitialware` in initialware_tools

Now, new config parameters below are added to the `CorsInitialware`(
in `CORS` zone of config file):

-   `SETTINGS` : [dict] The settings of the cors. The default value is `None`.

### Modify `UserStatusCheck` in middleware_tools

Adding new parameter `excluding_status_message` to customize the message when the user status is excluded.

### Modify `SafeInputType` in middleware_tools

Now the type notation can use `|` to represent the union type. For example, `int|str` means the input can be `int` or `str`.

### Add a new tool `type_tools`

Adding a new typed dictionary `FelizResponse` to represent the response of the api. The `FelizResponse` contains the key `indicator`, `message` and `content`.

## v0.0.8

### New initialware `ImportI18NInitialware`

In light of the internationalization, the `ImportI18NInitialware` is used to load the i18n file so that server can response the message in different languages.

### New initialware `RegisterApisInitialware`

The `RegisterApisInitialware` is used to register the apis in the server base on the settings in the `server_api.yaml`.

## v0.0.7

### New input type - `EmptyInputRequest`

The `EmptyInputRequest` is a new input type, which is used to handle the input which is not given.

New Feature in setting `server_api.yaml`:

### OptionalDefaults

The `OptionalDefaults` should be a list before, but now it can be a dictionary.

If it is a dictionary, no length restriction for the `OptionalDefaults`. That is, you don't need to set all keys of the `Optionals` in the `OptionalDefaults`, and the lack of the keys will be automatically filled with the object `EmptyInputRequest`.

You can use `isinstance` to check whether users give the input.

#### Example:

```yaml
Optionals: ["name", "age"]
OptionalDefaults: {"name": "default_name"}
```

```python
@handler("/home", xxxApi, methods=["GET"])
def index(input_request, **params):
    print(isinstance(input_request["name"], EmptyInputRequest)) # False
    print(isinstance(input_request["age"], EmptyInputRequest))  # True
```

### Nullable datatype is supported in InputType

It is a decorator option in the `InputType` to determine whether the input can be `None` (`null`). Namely, if using the decorator option `::nullable`, middleware will accept the input as `None` although the `InputType` is set.

#### Example:

```yaml
Optionals: ["name", "age"]
OptionalDefaults: {"name": null}
InputInspect: True
InputType: {"name": str::nullable, "age": int}
```

## v0.0.6

### Update `PostgresInitialware`

If the `init_type` in meta is `schema` and the `authorization` is `None`, the `PostgresInitialware` will try to use the `username` of the database configuration as the authorization.

That is, if you want to use configuration's username as the authorization, do not need to set the `authorization` in the meta, except that you want to use another authorization.

## v0.0.5

### Add Dynamic Routing

In previous versions, the routing is static, which means that you can't set the parameter of the routing dynamically. In this version, you can set the parameter of the routing dynamically.

#### Example:

```python
# xxx_api.py

from flask import Blueprint
from feliz.api_tools import handler

xxxApi = Blueprint('xxx', __name__)
74
@handler("/home/<uid>", xxxApi, methods=["GET"])
def home(uid, input_request, **params):
    return {"uid": uid}
```

## v0.0.4

### Fix the bug of `PostgresInitialware`

The `PostgresInitialware` now can detect the parameter `initialize` in meta of the `PostgresModelHandler`.

If `initialize` is `True`, the `PostgresInitialware` will initialize the database.

## v0.0.3

### Added new initialware `JsonifyInitialware`

This initialware is used to customized the rule of the json serialization of the response data.

#### Example:

```python
import datetime
from flask import Flask
from feliz.initialware_tools import InitialwareSystem, JsonifyInitialware
from feliz.middleware_tools import MiddlewareSystem, JsonifyResponse

def customized_jsonify(obj, default_jsonify):
    if isinstance(obj, datetime.datetime):
        return obj.strftime("%Y-%m-%d %H:%M:%S")
    else:
        return default_jsonify(obj)

app = Flask(__name__)

iws = InitialwareSystem()
iws.use(JsonifyInitialware(customized_jsonify))
iws.execute(app)

@app.after_request
def after_request(response):
    mws = MiddlewareSystem()
    mws.use(JsonifyResponse())
    mws.process_response(response)
    return response
```

### Revised the `FalseResponse`

Now you can pass the `content` key to the `FalseResponse` to customize the response content.

### Revised the `error_handler`

Add the parameter `loggerIndicatorFalse` to determine whether to log the traceback when the response arises from the `FalseResponse`.

Besides, this function now can returns the response json data.

#### Example:

```python
from feliz.api_tools import error_handler

@app.errorhandler(Exception)
def handle_exception(e):
    return error_handler(e, True)
```
