#!/usr/bin/python3


import argparse
import sys

from phagocyte_game_server import runserver


__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


def parse_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", dest="port", required=True, type=int, help="port on which to run the server")
    parser.add_argument("-a", "--auth", "--authserver", dest="auth_ip", required=True,
                        help="authentication server ip address")
    parser.add_argument("--auth-port", default=8080, dest="auth_port", type=int, help="authentication server port")

    return vars(parser.parse_args(args))


if __name__ == '__main__':
    args = parse_args(sys.argv[1:])
    runserver(**args)
