import sys

from click.testing import CliRunner

import sensors


def test_sensors():
    assert hasattr(sensors, "PythonVersion")


def test_python_version_is_first_two_lines_of_cli_output():
    runner = CliRunner()
    result = runner.invoke(sensors.show_sensors)
    python_version = "{}.{}".format(sys.version_info.major, sys.version_info.minor)
    assert ["Python Version", python_version] == result.stdout.split("\n")[:2]
