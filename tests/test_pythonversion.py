from collections import namedtuple

from sensors import PythonVersion

import pytest


class TestPythonVersionFormatter:
    @pytest.fixture(scope="class")
    def subject(self):
        return PythonVersion().format

    @pytest.fixture(scope="class")
    def versioninfo(self):
        return namedtuple(
            "sys_versioninfo", ("major", "minor", "micro", "releaselevel", "serial")
        )

    def test_format_py38(self, subject, versioninfo):
        py38 = versioninfo(3, 8, 0, "final", 0)
        assert subject(py38) == "3.8"

    def test_format_large_version(self, subject, versioninfo):
        large = versioninfo(255, 128, 1024, "final", 512)
        assert subject(large) == "255.128"
