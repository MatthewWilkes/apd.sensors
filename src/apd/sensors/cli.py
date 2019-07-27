import typing as t

import click

from .sensors import (
    Sensor,
    ACStatus,
    CPULoad,
    IPAddresses,
    PythonVersion,
    RAMAvailable,
    RelativeHumidity,
    Temperature,
)


def get_sensors():
    return [
        PythonVersion(),
        IPAddresses(),
        CPULoad(),
        RAMAvailable(),
        ACStatus(),
        Temperature(),
        RelativeHumidity(),
    ]


@click.command(help="Displays the values of the sensors")
def show_sensors(develop):
    sensors: t.Iterable[Sensor[t.Any]]
    sensors = get_sensors()
    for sensor in sensors:
        click.secho(sensor.title, bold=True)
        click.echo(str(sensor))
        click.echo("")
    return
