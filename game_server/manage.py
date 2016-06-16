#!/usr/bin/python3

"""
Manage commands to run game servers
"""

import argparse
import sys

from phagocyte_game_server import runserver as run_node
from phagocyte_game_manager import runserver


__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


def parse_args(_args):
    """
    parse the argument given in parameter

    :param _args: args to parse
    :return: dictionary of arguments
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-?", "--help", action="help")

    subparsers = parser.add_subparsers(help="commands")

    server = subparsers.add_parser("runserver", help="Launch server manager", add_help=False)
    server.set_defaults(func=runserver)
    server.add_argument("-?", "--help", action="help")
    server.add_argument("-h", "--host", default="127.0.0.1")
    server.add_argument("-p", "--port", default=5000)
    server.add_argument("-d", "--debug", action="store_true", help="enable the Werkzeug Debugger")

    node = subparsers.add_parser("node", help="Launch a new game node", add_help=False)
    node.set_defaults(func=run_node)
    node.add_argument("-?", "--help", action="help")
    node.add_argument("-p", "--port", dest="port", required=True, type=int, help="port on which to run the server")
    node.add_argument("-a", "--auth", "--authserver", dest="auth_host", required=True,
                      help="authentication server ip address")
    node.add_argument("--auth-port", default=8080, dest="auth_port", type=int, help="authentication server port")
    node.add_argument("--name", help="name of the node to create")
    node.add_argument("-d", "--debug", action="store_true", help="turn on debugging")
    node.add_argument("--token", help="Token used by the manager", required=True)

    for entry in ["capacity", "map_width", "min_radius", "food_production_rate",
                  "map_height", "max_speed", "max_hit_count", "win_size"]:
        node.add_argument("--" + entry, type=int)

    for entry in ["eat_ratio"]:
        node.add_argument("--" + entry, type=float)

    parsed_args = vars(parser.parse_args(_args))

    if not parsed_args.get("func", None):
        parser.print_help()
        exit(1)

    return parsed_args


if __name__ == '__main__':
    args = parse_args(sys.argv[1:])
    func = args["func"]
    del args["func"]
    func(**args)
