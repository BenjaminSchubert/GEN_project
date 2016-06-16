"""
Various commands for the runserver utility

These can be called through the manager and are useful for handling
the state of the application
"""

from typing import Tuple

from flask import Flask
from flask_script import Command, Option


__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


class Server(Command):
    """
    Command to launch the server

    :param host: host on which to listen
    :param port: port on which to listen
    :param debug: whether to use debug mode or not
    """

    help = description = "Run Phagocyte Authentication Server"

    def __init__(self, host: str, port: int, debug: bool):
        super().__init__()
        self.port = port
        self.host = host
        self.debug = debug

    def get_options(self) -> Tuple[Option]:
        """
        Lists all options available to the given command

        :return: tuple of all options available
        """
        return (
            Option('-h', '--host', dest='host', default=self.host),
            Option('-p', '--port', dest='port', type=int, default=self.port),
            Option('-d', '--debug', action='store_true', dest='debug', default=self.debug)
        )

    # noinspection PyMethodOverriding
    def run(self, app: Flask, host: str, port: int, debug: bool):
        """
        Launches the application with the given parameters

        :param app: the flask application
        :param host: host on which to listen
        :param port: port on which to listen
        :param debug: whether to launch in debug mode or not
        """
        app.run(host=host, port=port, debug=debug, threaded=True)

    # noinspection PyMethodOverriding
    def __call__(self, app, host, port, debug):
        self.run(app=app, host=host, port=port, debug=debug)
