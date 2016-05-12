#!/usr/bin/python3

"""
Game Manager handling
"""

__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


class GameExistsException(Exception):
    """
    Exception to be raised if a game with the same name already exists
    """
    pass


class GameManager:
    """
    Manager for all game server and managers

    :param app: Flask application on which to run
    """
    class Manager:
        """
        Representation of a game server

        :param ip: ip of the server
        :param port: port of the server
        :param token: token to send to authenticate on the server
        :param capacity: maximum capacity of the server
        """
        def __init__(self, ip, port, token, capacity):
            self.ip = ip
            self.port = port
            self.token = token
            self.capacity = capacity
            self.slots = 0

    games = {}
    managers = []

    def __init__(self, app):
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
        # FIXME : check that max_capacity is positive
        if self.games.get(name) is not None:
            raise GameExistsException()

        self.games[name] = dict(ip=ip, port=port, name=name, max_capacity=capacity)

    def add_manager(self, **kwargs):
        """
        Adds a new game manager
        :param kwargs: arguments to define the game manager
        """
        self.managers.append(self.Manager(**kwargs))
