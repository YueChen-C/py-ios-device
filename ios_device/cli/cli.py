import json
from pprint import pprint

import click


class Enconding(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, bytes):
            return o.decode()


def print_json(buf, json_format=True):
    if json_format:
        formatted_json = json.dumps(buf, indent=4, cls=Enconding)
        print(formatted_json)
    else:
        # pprint(buf,width=120)
        print(buf)

    # print('*' * 100)


class Command(click.Command):

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.params[:0] = [
            click.Option(('udid', '--udid'), help='specify unique device identifier'),
            click.Option(('network', '--network'), is_flag=True, help='ios devices on wireless network'),
            click.Option(('json_format', '--json'), is_flag=True, help='ios devices on wireless network'),
        ]
