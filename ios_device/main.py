import os
import sys

import click
sys.path.append(os.getcwd())

from ios_device.cli.instruments import cli as instruments_cli


def cli():
    cli_commands = click.CommandCollection(sources=[
        instruments_cli
    ])
    cli_commands()


if __name__ == '__main__':
    cli()
