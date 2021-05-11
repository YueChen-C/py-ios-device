import json
from pprint import pprint

import click


def print_json(buf, json_format=True, default=None):
    if json_format:
        formatted_json = json.dumps(buf, indent=4, default=default)
        print(formatted_json)
    else:
        # pprint(buf,width=120)
        print(buf)

    # print('*' * 100)


class Command(click.Command):

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.params[:0] = [
            click.Option(('udid','--udid'),help='specify unique device identifier'),
            click.Option(('network','--network'),is_flag=True,help='ios devices on wireless network'),
            click.Option(('json_format','--json'),is_flag=True,help='ios devices on wireless network'),
        ]
