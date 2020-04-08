from pint import _DEFAULT_REGISTRY as ureg
import pytest

from apd.sensors.sensors import Temperature, RelativeHumidity


@pytest.fixture
def temperature_sensor():
    return Temperature()


@pytest.fixture
def humidity_sensor():
    return RelativeHumidity()


class TestTemperatureFormatter:
    @pytest.fixture
    def subject(self, temperature_sensor):
        return temperature_sensor.format

    @pytest.fixture
    def celsius(self):
        return lambda temp: ureg.Quantity(temp, ureg.celsius)

    @pytest.fixture
    def fahrenheit(self):
        return lambda temp: ureg.Quantity(temp, ureg.fahrenheit)

    def test_format_21c(self, subject, celsius):
        assert subject(celsius(21.0)) == "21.0 °C (69.8 °F)"

    def test_format_negative(self, subject, celsius):
        assert subject(celsius(-32.0)) == "-32.0 °C (-25.6 °F)"

    def test_format_fahrenheit(self, subject, fahrenheit):
        assert subject(fahrenheit(-25.6)) == "-32.0 °C (-25.6 °F)"

    def test_format_unknown(self, subject):
        assert subject(None) == "Unknown"


class TestHumidityFormatter:
    @pytest.fixture
    def subject(self, humidity_sensor):
        return humidity_sensor.format

    def test_format_percentage(self, subject):
        assert subject(0.035) == "3.5%"

    def test_format_unknown(self, subject):
        assert subject(None) == "Unknown"
