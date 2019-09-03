from abc import ABC, abstractmethod
import typing as t
import json

import flask

from apd.sensors.sensors import Sensor
from apd.sensors.cli import get_sensors
from apd.sensors.wsgi import require_api_key, set_up_config

app = flask.Flask(__name__)


T_value = t.TypeVar("T_value")


class SerializableSensor(ABC, t.Generic[T_value]):

    title: str

    @abstractmethod
    def value(self) -> T_value:
        pass

    @classmethod
    @abstractmethod
    def serialize(self, value: T_value) -> str:
        pass

    @classmethod
    @abstractmethod
    def deserialize(self, serialized: str) -> T_value:
        pass

    @classmethod
    def __subclasshook__(cls, C: t.Type[t.Any]) -> t.Union[bool, "NotImplemented"]:
        if cls is SerializableSensor:
            has_abstract_methods = [
                hasattr(C, name) for name in {"value", "serialize", "deserialize"}
            ]
            return all(has_abstract_methods)
        return NotImplemented


class JSONSerializedSensor(SerializableSensor[t.Any]):
    @classmethod
    def serialize(self, value: t.Any) -> str:
        return json.dumps(value)

    @classmethod
    def deserialize(self, serialized: str) -> t.Any:
        return json.loads(serialized)


class JSONWrappedSensor(JSONSerializedSensor):
    def __init__(self, sensor: Sensor[t.Any]):
        self.wrapped = sensor
        self.title = sensor.title

    def value(self) -> t.Any:
        return self.wrapped.value()


def get_serializable_sensors() -> t.Iterable[SerializableSensor[t.Any]]:
    sensors = get_sensors()
    found = []
    for sensor in sensors:
        if isinstance(sensor, SerializableSensor):
            found.append(sensor)
        else:
            found.append(JSONWrappedSensor(sensor))
    return found


@app.route("/sensors/")
@require_api_key
def sensor_values() -> t.Tuple[t.Dict[str, t.Any], int, t.Dict[str, str]]:
    headers = {"Content-Security-Policy": "default-src 'none'"}
    data = {}
    for sensor in get_serializable_sensors():
        data[sensor.title] = sensor.serialize(sensor.value())
    return data, 200, headers


if __name__ == "__main__":
    import wsgiref.simple_server

    set_up_config(None, app)

    with wsgiref.simple_server.make_server("", 8000, app) as server:
        server.serve_forever()
