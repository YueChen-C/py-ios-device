import json
from pprint import pprint

import click


class Enconding(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, bytes):
            try:
                return o.decode()
            except:
                return str(o)


def print_json(buf, format=True):
    if format == 'json':
        formatted_json = json.dumps(buf, indent=4, cls=Enconding)
        print(formatted_json)
    elif format == 'flush':
        print(f'\r{buf}', end='', flush=True)
    else:
        print(buf)


class Command(click.Command):

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.params[:0] = [
            click.Option(('udid', '--udid'), help='specify unique device identifier'),
            click.Option(('network', '--network'), is_flag=True, help='ios devices on wireless network'),
            click.Option(('format', '--format'),type=click.Choice(['text','json','flush']), help='print format type'),
        ]
