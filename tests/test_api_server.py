import json
import os

import pytest
from webtest import TestApp

from apd.sensors.wsgi import app, set_up_config
from apd.sensors.sensors import PythonVersion


@pytest.fixture
def api_key():
    return "API key"


@pytest.fixture
def subject(api_key):
    set_up_config({"APD_SENSORS_API_KEY": api_key})
    return app


@pytest.fixture
def api_server(subject):
    return TestApp(subject)


def test_api_key_is_required_config_option():
    with pytest.raises(
        ValueError, match="Missing config variables: APD_SENSORS_API_KEY"
    ):
        set_up_config({})


def test_os_environ_is_default_for_config_values(api_key):
    os.environ["APD_SENSORS_API_KEY"] = api_key
    set_up_config(None)
    assert app.config["APD_SENSORS_API_KEY"] == api_key
    del os.environ["APD_SENSORS_API_KEY"]


@pytest.mark.functional
def test_sensor_values_fails_on_missing_api_key(api_server):
    response = api_server.get("/sensors/", expect_errors=True)
    assert response.status_code == 403
    assert response.json["error"] == "Supply API key in X-API-Key header"


@pytest.mark.functional
def test_sensor_values_require_correct_api_key(api_server):
    response = api_server.get(
        "/sensors/", headers={"X-API-Key": "wrong_key"}, expect_errors=True
    )
    assert response.status_code == 403
    assert response.json["error"] == "Supply API key in X-API-Key header"


@pytest.mark.functional
def test_sensor_values_returned_as_json(api_server, api_key):
    value = api_server.get("/sensors/", headers={"X-API-Key": api_key}).json
    python_version = PythonVersion().value()

    sensor_names = value.keys()
    assert "Python Version" in sensor_names
    assert json.loads(value["Python Version"]) == list(python_version)
