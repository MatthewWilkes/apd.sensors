import datetime
import logging
import typing as t

import dateutil.parser
import flask

from apd.sensors import cli
from apd.sensors.base import HistoricalSensor
from apd.sensors.exceptions import DataCollectionError

from .base import require_api_key

version = flask.Blueprint(__name__, __name__)
logger = logging.getLogger(__name__)


@version.route("/sensors/")
@version.route("/sensors/<sensor_id>")
@require_api_key
def sensor_values(sensor_id=None) -> t.Tuple[t.Dict[str, t.Any], int, t.Dict[str, str]]:
    headers = {"Content-Security-Policy": "default-src 'none'"}
    sensors = []
    errors = []
    for sensor in cli.get_sensors():
        now = datetime.datetime.now()
        if sensor_id and sensor_id != sensor.name:
            continue
        try:
            try:
                value = sensor.value()
            except Exception as err:
                if isinstance(err, DataCollectionError):
                    # We allow data collection errors
                    message = str(err)
                else:
                    # Other errors shouldn't be published, but should be logged
                    # Don't refuse to service the request in this case
                    message = "Unhandled error"
                    logger.error(f"Unhandled error while handling {sensor.name}")
                error = {
                    "id": sensor.name,
                    "title": sensor.title,
                    "collected_at": now.isoformat(),
                    "error": message,
                }
                errors.append(error)
                continue
            sensor_data = {
                "id": sensor.name,
                "title": sensor.title,
                "value": sensor.to_json_compatible(value),
                "human_readable": sensor.format(value),
                "collected_at": now.isoformat(),
            }
            sensors.append(sensor_data)
        except NotImplementedError:
            pass
    data = {"sensors": sensors, "errors": errors}
    return data, 200, headers


@version.route("/info/sensors")
@require_api_key
def sensor_types(sensor_id=None) -> t.Tuple[t.Dict[str, t.Any], int, t.Dict[str, str]]:
    headers = {"Content-Security-Policy": "default-src 'none'"}
    known_sensors = {sensor.name: sensor.title for sensor in cli.get_sensors()}
    return known_sensors, 200, headers


@version.route("/sensors/<sensor_id>/historical")
@version.route("/sensors/<sensor_id>/historical/<start>")
@version.route("/sensors/<sensor_id>/historical/<start>/<end>")
@version.route("/historical")
@version.route("/historical/<start>")
@version.route("/historical/<start>/<end>")
@require_api_key
def historical_values(
    start: str = None, end: str = None, sensor_id: str=None,
) -> t.Tuple[t.Dict[str, t.Any], int, t.Dict[str, str]]:
    sensors = []
    known_sensors = {sensor.name: sensor for sensor in cli.get_sensors()}

    if sensor_id and sensor_id in known_sensors:
        known_sensors = {sensor_id: known_sensors[sensor_id]}


    headers = {"Content-Security-Policy": "default-src 'none'"}

    if start:
        start_dt = dateutil.parser.parse(start)
    else:
        start_dt = dateutil.parser.parse("1900-01-01")

    if end:
        end_dt = dateutil.parser.parse(end)
    else:
        end_dt = datetime.datetime.now()

    try:
        from apd.sensors.database import sensor_values as sensor_values_table
        from apd.sensors.wsgi import db
        session = db.session
    except (ImportError, AttributeError):
        session = None
    else:
        db_session = db.session

        query = db_session.query(sensor_values_table)
        query = query.filter(sensor_values_table.c.collected_at >= start_dt)
        query = query.filter(sensor_values_table.c.collected_at <= end_dt)
    
        for data in query:
            if data.sensor_name not in known_sensors:
                continue
            sensor = known_sensors[data.sensor_name]
            sensor_data = {
                "id": sensor.name,
                "title": sensor.title,
                "value": data.data,
                "human_readable": sensor.format(sensor.from_json_compatible(data.data)),
                "collected_at": data.collected_at.isoformat(),
            }
            sensors.append(sensor_data)
    
    for sensor in known_sensors.values():
        if isinstance(sensor, HistoricalSensor):
            for date, value in sensor.historical(start_dt, end_dt):
                sensor_data = {
                    "id": sensor.name,
                    "title": sensor.title,
                    "value": value,
                    "human_readable": sensor.format(sensor.from_json_compatible(value)),
                    "collected_at": date.isoformat(),
                }
                sensors.append(sensor_data)
    data = {"sensors": sensors}
    try:
        return data, 200, headers
    finally:
        if session is not None:
            session.close()


@version.route("/deployment_id")
def deployment_id() -> t.Tuple[t.Dict[str, t.Any], int, t.Dict[str, str]]:
    headers = {"Content-Security-Policy": "default-src 'none'"}
    data = {"deployment_id": flask.current_app.config["APD_SENSORS_DEPLOYMENT_ID"]}
    return data, 200, headers
