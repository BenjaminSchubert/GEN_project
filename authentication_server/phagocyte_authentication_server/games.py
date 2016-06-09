#!/usr/bin/python3

"""
Game Manager handling
"""
import requests


__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


class GameExistsException(Exception):
    """
    Exception to be raised if a game with the same name already exists
    """


class GameManager:
    """
    Manager for all game server and managers

    :param app: Flask application on which to run
    """
    class Manager:
        """
        Representation of a game server

        :param host: hostname of the server
        :param port: port of the server
        :param token: token to send to authenticate on the server
        :param capacity: maximum capacity of the server
        """
        def __init__(self, host, port, token, capacity):
            self.host = host
            self.port = port
            self.token = token
            self.capacity = capacity
            self.slots = 0

    games = {}
    managers = []

    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """
        Registers the GameManager on Flask

        :param app: Flask application
        """
        app.games = self

    def add_game(self, ip, port, name, capacity):
        """
        add a new game to the list of available games

        :param ip: ip of the server hosting the game
        :param port: port of the game server
        :param name: name of the game server
        :param capacity: maximum capacity of the game server
        :raise GameExistsException: if a game with the same name already exists
        """
        if self.games.get(name) is not None:
            raise GameExistsException()

        self.games[name] = dict(ip=ip, port=port, name=name, max_capacity=capacity)

    def add_manager(self, **kwargs):
        """
        Adds a new game manager

        :param kwargs: arguments to define the game manager
        """
        to_remove = None
        for manager in self.managers:
            if manager.host == kwargs["host"] and manager.port == kwargs["port"]:
                to_remove = manager
                break

        if to_remove is not None:
            self.managers.remove(to_remove)

        self.managers.append(self.Manager(**kwargs))

    def remove_manager(self, token):
        """
        removes the given manager from the list of active managers

        :param token: token identifying the manager
        """
        to_remove = None
        for manager in self.managers:
            if manager.token == token:
                to_remove = manager
                break

        if to_remove is not None:
            self.managers.remove(to_remove)

    def create_game(self, data):
        """
        creates a new game on the first available game server
        """
        for manager in self.managers:
            if manager.slots < manager.capacity:
                break
        else:
            raise KeyError("Not enough servers to handle a new game")

        data["token"] = manager.token

        name = data.get("name", None)
        if name is None:
            raise KeyError("Need a name")

        for game in self.games.values():
            if game["name"] == name:
                raise KeyError("A server with the given name already exists")

        r = requests.post("http://{}:{}/games".format(manager.host, manager.port), json=data)

        if r.status_code != requests.codes.ok:
            raise KeyError(r.json())

        manager.slots += 1
