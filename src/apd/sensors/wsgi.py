from hmac import compare_digest
import functools
import os
import typing as t

import flask

from apd.sensors.cli import get_sensors


app = flask.Flask(__name__)

ViewFuncReturn = t.TypeVar("ViewFuncReturn")
ErrorReturn = t.Tuple[t.Dict[str, str], int]
REQUIRED_CONFIG_KEYS = {"APD_SENSORS_API_KEY"}


def require_api_key(func):
    @functools.wraps(func)
    def wrapped():
        api_key = flask.current_app.config["APD_SENSORS_API_KEY"]
        headers = flask.request.headers
        supplied_key = headers.get("X-API-Key", "")
        if not compare_digest(api_key, supplied_key):
            return {"error": "Supply API key in X-API-Key header"}, 403
        return func()

    return wrapped


@app.route("/sensors/")
@require_api_key
def sensor_values():
    headers = {"Content-Security-Policy": "default-src 'none'"}
    data = {}
    for sensor in get_sensors():
        data[sensor.title] = sensor.value()
    return data, 200, headers


def set_up_config(environ=None):
    if environ is None:
        environ = dict(os.environ)
    missing_keys = REQUIRED_CONFIG_KEYS - environ.keys()
    if missing_keys:
        raise ValueError("Missing config variables: {}".format(", ".join(missing_keys)))
    app.config.from_mapping(environ)
    return app


if __name__ == "__main__":
    import wsgiref.simple_server

    set_up_config()

    with wsgiref.simple_server.make_server("", 8000, app) as server:
        server.serve_forever()
