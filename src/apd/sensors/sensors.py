#!/usr/bin/env python
# coding: utf-8
import math
import os
import socket
import sys
import typing as t

import psutil
from pint import _DEFAULT_REGISTRY as ureg

from .base import Sensor, JSONSensor, version_info_type
from .exceptions import (
    PersistentSensorFailureError,
    IntermittentSensorFailureError,
    DataCollectionError,
)


dht_sensor = None


class PythonVersion(JSONSensor[version_info_type]):
    name = "PythonVersion"
    title = "Python Version"

    def value(self) -> version_info_type:
        return version_info_type(*sys.version_info)

    @classmethod
    def from_json_compatible(cls, json_version: t.Any) -> version_info_type:
        return version_info_type(*json_version)

    @classmethod
    def format(cls, value: version_info_type) -> str:
        if value.micro == 0 and value.releaselevel == "alpha":
            return "{0.major}.{0.minor}.{0.micro}a{0.serial}".format(value)
        return "{0.major}.{0.minor}".format(value)


class IPAddresses(JSONSensor[t.Iterable[t.Tuple[str, str]]]):
    name = "IPAddresses"
    title = "IP Addresses"
    FAMILIES = {"AF_INET": "IPv4", "AF_INET6": "IPv6"}

    def value(self) -> t.List[t.Tuple[str, str]]:
        hostname = socket.gethostname()
        addresses = socket.getaddrinfo(hostname, None)
        address_info: t.List[t.Tuple[str, str]] = []
        for address in addresses:
            family, ip = (address[0].name, address[4][0])
            if family not in self.FAMILIES:
                continue
            value = (family, ip)
            if value not in address_info:
                address_info.append(value)
        return address_info

    @classmethod
    def format(cls, value: t.Iterable[t.Tuple[str, str]]) -> str:
        return "\n".join(
            "{0} ({1})".format(address[1], cls.FAMILIES.get(address[0], "Unknown"))
            for address in value
        )


class CPULoad(JSONSensor[float]):
    name = "CPULoad"
    title = "CPU Usage"

    def value(self) -> float:
        return float(psutil.cpu_percent(interval=3)) / 100.0

    @classmethod
    def format(cls, value: float) -> str:
        return "{:.1%}".format(value)


class RAMAvailable(JSONSensor[int]):
    name = "RAMAvailable"
    title = "RAM Available"
    UNITS = ("B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB")
    UNIT_SIZE = 2 ** 10

    def value(self) -> int:
        return int(psutil.virtual_memory().available)

    @classmethod
    def format(cls, value: int) -> str:
        magnitude = math.floor(math.log(value, cls.UNIT_SIZE))
        max_magnitude = len(cls.UNITS) - 1
        magnitude = min(magnitude, max_magnitude)
        scaled_value = value / (cls.UNIT_SIZE ** magnitude)
        return "{:.1f} {}".format(scaled_value, cls.UNITS[magnitude])


class ACStatus(JSONSensor[bool]):
    name = "ACStatus"
    title = "AC Connected"

    def value(self) -> bool:
        battery = psutil.sensors_battery()
        if battery is not None:
            value = battery.power_plugged
            if value is None:
                raise IntermittentSensorFailureError("Can't find AC status")
            else:
                return bool(value)
        else:
            raise PersistentSensorFailureError("No charging circuit installed")

    @classmethod
    def format(cls, value: bool) -> str:
        if value:
            return "Connected"
        else:
            return "Not connected"


class DHTSensor:
    def __init__(self) -> None:
        self.board = os.environ.get("APD_SENSORS_TEMPERATURE_BOARD", "DHT22")
        self.pin = os.environ.get("APD_SENSORS_TEMPERATURE_PIN", "D20")

    @property
    def sensor(self) -> t.Any:
        global dht_sensor
        if dht_sensor is None:
            try:
                import adafruit_dht
                import board

                sensor_type = getattr(adafruit_dht, self.board)
                pin = getattr(board, self.pin)
                dht_sensor = sensor_type(pin)
            except (ImportError, NotImplementedError, AttributeError) as err:
                # No DHT library results in an ImportError.
                # Running on an unknown platform results in a
                # NotImplementedError when getting the pin
                raise PersistentSensorFailureError(
                    "Unable to initialise sensor interface"
                ) from err
        return dht_sensor


class Temperature(Sensor[t.Any], DHTSensor):
    name = "Temperature"
    title = "Ambient Temperature"

    def value(self) -> t.Any:
        try:
            return ureg.Quantity(self.sensor.temperature, ureg.celsius)
        except DataCollectionError:
            # This is one of our own exceptions, we don't need to re-wrap it
            raise
        except (RuntimeError, AttributeError) as err:
            raise IntermittentSensorFailureError(
                "Couldn't determine temperature"
            ) from err

    @classmethod
    def format(cls, value: t.Any) -> str:
        return "{:.3~P} ({:.3~P})".format(value, value.to(ureg.fahrenheit))

    @classmethod
    def to_json_compatible(cls, value: t.Any) -> t.Any:
        return {"magnitude": value.magnitude, "unit": str(value.units)}

    @classmethod
    def from_json_compatible(cls, json_version: t.Any) -> t.Any:
        return ureg.Quantity(json_version["magnitude"], ureg[json_version["unit"]])

    def __str__(self) -> str:
        return self.format(self.value())


class RelativeHumidity(JSONSensor[float], DHTSensor):
    name = "RelativeHumidity"
    title = "Relative Humidity"

    def value(self) -> float:
        try:
            return float(self.sensor.humidity)
        except DataCollectionError:
            # This is one of our own exceptions, we don't need to re-wrap it
            raise
        except (TypeError, AttributeError) as err:
            raise IntermittentSensorFailureError("Couldn't determine humidity") from err

    @classmethod
    def format(cls, value: float) -> str:
        return "{:.1%}".format(value / 100.0)
