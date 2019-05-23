from collections import namedtuple
from unittest import mock

from sensors import PythonVersion

import pytest


@pytest.fixture
def version():
    return namedtuple(
        "sys_versioninfo", ("major", "minor", "micro", "releaselevel", "serial")
    )


class TestPythonVersionFormatter:
    @pytest.fixture
    def subject(self):
        return PythonVersion().format

    def test_format_py38(self, subject, version):
        py38 = version(3, 8, 0, "final", 0)
        assert subject(py38) == "3.8"

    def test_format_large_version(self, subject, version):
        large = version(255, 128, 0, "final", 0)
        assert subject(large) == "255.128"

    def test_alpha_of_minor_is_marked(self, subject, version):
        py39 = version(3, 9, 0, "alpha", 1)
        assert subject(py39) == "3.9.0a1"

    def test_alpha_of_micro_is_unmarked(self, subject, version):
        py39 = version(3, 9, 1, "alpha", 1)
        assert subject(py39) == "3.9"


class TestPythonVersionValue:
    @pytest.fixture
    def subject(self):
        return PythonVersion().value

    @pytest.fixture
    def python_version(self):
        import sys

        return sys.version_info

    def test_data_value_is_sys_versioninfo(self, python_version, subject):
        assert subject() == python_version


class TestPythonVersionSensor:
    @pytest.fixture
    def subject(self):
        return PythonVersion()

    def test_str_representation_is_formatted_value(self, subject, version):
        with mock.patch("sys.version_info", new=version(3, 4, 1, "final", 1)):
            assert str(subject) == "3.4"
