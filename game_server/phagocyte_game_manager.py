#!/usr/bin/python3

"""
Game server manager for Phagocytes

This is used to handle the creation on the fly of new server instance
to allow multiple games to be run at the same time
"""

import multiprocessing
import subprocess

import atexit
import os

import requests
import sys
from flask import Flask, request, jsonify


__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


class FullCapacityException(Exception):
    """
    Error raised when a server is operating at full capacity
    """
    pass


class NotifierFlask(Flask):
    """
    This is a Flask server that is able of sending a token to another server before launch
    """
    token = None
    capacity = multiprocessing.cpu_count()
    ports_used = None

    def setup_ports(self):
        self.ports_used = [False] * self.capacity

    def next_available_port(self):
        for index in range(len(self.ports_used)):
            if not self.ports_used[index]:
                self.ports_used[index] = True
                return index

        raise FullCapacityException()

    def get_token(self, host, port):
        """
        Get the server authentication token against the authentication server

        :param host: flask server host
        :param port: port of the flask server
        """
        r = requests.post(
            "http://{}:{}/games/manager".format(app.config["AUTH_SERVER"], app.config["AUTH_SERVER_PORT"]),
            json={"port": port, "host": host, "capacity": multiprocessing.cpu_count()}
        )

        if r.status_code == requests.codes.ok:
            self.token = r.json()["token"]
            if r.json().get("create"):
                self.create_game_server(r.json()["name"], r.json()["capacity"])
        else:
            print("Couldn't contact authentication server")
            exit(2)

    def run(self, host=None, port=None, debug=None, **options):
        """
        Gets the token from the authentication server before launching Flask

        :param host: host on which to listen
        :param port: port on which to listen
        :param debug: whether to enable debugging options or not
        :param options: additional options sent to the server
        """
        self.get_token(host, port)
        self.debug = debug
        super().run(host, port, debug, **options)

    def create_game_server(self, name, capacity):
        """
        Creates a new game server
        :param name: name of the new server
        :param capacity: maximum capacity of the new server
        """
        cmd = [
            sys.executable, "manage.py", "node", "-p", str(self.config["PORT_GAMESERVER"] + self.next_available_port()),
            "-a", str(app.config["AUTH_SERVER"]), "--auth-port", str(app.config["AUTH_SERVER_PORT"]),
            "--name", name, "--capacity", str(capacity)
        ]

        if self.debug:
            cmd.append("-d")

        subprocess.Popen(cmd, cwd=os.path.dirname(os.path.abspath(__file__)), stderr=sys.stderr, stdout=sys.stdout)


app = NotifierFlask("phagocytes_game_manager")

# Flask configuration
config_path = os.environ.get("PHAGOCYTE_GAMEMANAGER_SERVER", os.path.join(app.root_path, "config.cfg"))
app.config.from_pyfile(config_path)
app.setup_ports()


@atexit.register
def unregister_app():
    """
    unregisters the manager from the server
    """
    requests.delete(
        "http://{}:{}/games/manager".format(app.config["AUTH_SERVER"], app.config["AUTH_SERVER_PORT"]),
        json={"token": app.token}
    )


@app.route("/games", methods=["POST"])
def create():
    """
    Creates a new game server

    :return: 200 on ok, 401 if token is not valid, 412 if capacity is exceeded
    """
    if request.json["token"] != app.token:
        return (jsonify({"error": "unauthorized"}), 401)

    try:
        app.create_game_server(request.json["name"], request.json["capacity"])
    except FullCapacityException:
        return (jsonify({"error": "maximum capacity exceeded"}), 412)
    return ("", 200)


def runserver(host, port, debug=False):
    """
    runs the server

    :param debug: whether to enable debugging or not
    :param host: host on which to listen
    :param port: port on which to listen
    """
    app.run(host=host, port=port, debug=debug)
