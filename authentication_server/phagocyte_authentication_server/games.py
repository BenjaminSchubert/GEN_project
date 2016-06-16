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

    class Game:
        """
        Representation of a game
        """
        def __init__(self, name, token, capacity, ip, port, manager, **kwargs):
            self.name = name
            self.token = token
            self.max_capacity = capacity
            self.active_users = 0
            self.ip = ip
            self.port = port
            self.manager = manager

        def to_json(self):
            return {
                "name": self.name,
                "ip": self.ip,
                "port": self.port
            }

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

    def add_game(self, **kwargs):
        """

        :param kwargs:
        :return:
        """
        manager = None

        for manager in self.managers:
            if manager.token == kwargs["token"]:
                break

        if not manager:
            raise ValueError("Could not map this server to a manager")

        self.games[(kwargs["ip"], kwargs["port"])] = self.Game(manager=manager, **kwargs)

        manager.slots += 1

    def remove_game(self, ip, port, token):
        game = self.games.get((ip, port), None)

        if game is None:
            raise KeyError("No game registered for ip {} and port {}".format(ip, port))

        if game.token != token:
            raise KeyError("Invalid token")

        self.games.pop((ip, port))

        manager = game.manager
        manager.slots -= 1

        try:
            r = requests.delete("http://{}:{}/games".format(manager.host, manager.port),
                                json=dict(port=port, token=manager.token))
        except requests.exceptions.ConnectionError:
            pass
        else:
            if r.status_code != requests.codes.ok:
                raise KeyError(r.json())

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
            raise ValueError("Not enough servers to handle a new game")

        data["token"] = manager.token

        if data["name"] == "":
            raise ValueError("Need a name")

        if not (2 < int(data["capacity"]) < 200):
            raise ValueError("Cannot handle that much users in a game")

        if int(data["map_width"]) < 500:
            raise ValueError("Cannot create a map with width smaller than 500")

        if int(data["map_height"]) < 500:
            raise ValueError("Cannot create map with height smaller than 500")

        if int(data["min_radius"]) < 1:
            raise ValueError("The minimum radius must be at least 1")

        if int(data["win_size"]) < int(data["min_radius"]):
            raise ValueError("The size for winning must be greater than the default player's size")

        if int(data["win_size"]) > int(data["map_width"]):
            raise ValueError("The size for winning must be smaller than the map's width")

        if int(data["win_size"]) > int(data["map_height"]):
            raise ValueError("The size for winning must be smaller than the map's height")

        if int(data["max_speed"]) < 1:
            raise ValueError("The maximum speed must be positive")

        if float(data["eat_ratio"]) <= 1:
            raise ValueError("The eat ratio cannot be smaller than 1")

        if float(data["food_production_rate"]) <= 0:
            raise ValueError("The food production rate cannot be smaller than 0")

        if int(data["max_hit_count"]) == 0:
            raise ValueError("The maximum hit count cannot be 0")

        r = requests.post("http://{}:{}/games".format(manager.host, manager.port), json=data)

        if r.status_code != requests.codes.ok:
            raise ValueError(r.json())
