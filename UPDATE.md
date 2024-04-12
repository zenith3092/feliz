# Update History

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
