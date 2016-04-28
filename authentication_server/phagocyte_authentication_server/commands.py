#!/usr/bin/python3
# -*- coding: utf-8 -*-

from flask_script import Command, Option


__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


class Server(Command):
    help = description = "Run Phagocyte Authentication Server"

    def __init__(self, host, port, debug):
        super().__init__()
        self.port = port
        self.host = host
        self.debug = debug

    def get_options(self):
        return (
            Option('-h', '--host', dest='host', default=self.host),
            Option('-p', '--port', dest='port', type=int, default=self.port),
            Option('-d', '--debug', action='store_true', dest='debug', default=self.debug)
        )

    # noinspection PyMethodOverriding
    def run(self, app, host, port, debug):
        app.run(host=host, port=port, debug=debug, threaded=True)

    # noinspection PyMethodOverriding
    def __call__(self, app, host, port, debug):
        self.run(app=app, host=host, port=port, debug=debug)
