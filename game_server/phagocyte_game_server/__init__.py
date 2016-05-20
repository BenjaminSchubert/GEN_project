#!/usr/bin/env python3

"""
Game server implementation
"""

import json
import json.decoder
import logging
import sys
import time
import uuid

import random
import requests
from rainbow_logging_handler import RainbowLoggingHandler
from twisted.internet import reactor, task
from twisted.internet.error import CannotListenError
from twisted.internet.protocol import DatagramProtocol

from phagocyte_game_server.events import Event


__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


def create_logger(name, port, debug):
    logger = logging.getLogger(name + ":" + str(port))
    handler = RainbowLoggingHandler(sys.stderr, color_process=("yellow", None, True))

    formatter = logging.Formatter("[%(asctime)s] %(name)s:%(process)d %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logger.setLevel(logging.INFO if not debug else logging.DEBUG)

    return logger


class AuthenticationError(Exception):
    """
    Exception raised when authentication failed

    :param msg: information about the error
    """
    def __init__(self, msg):
        self.msg = msg


def random_color():
    """
    get a new random color in hexadecimal

    :return: new hexadecimal color
    """
    return "#%06x" % random.randint(0, 0xFFFFFF)


def register(port, auth_host, auth_port, name, capacity):
    """
    registers the game server against the authentication server

    :param port: port of the game server
    :param auth_host: address of the authentication server
    :param auth_port: port of the authentication server
    :param name: name of the game server
    :param capacity: max capacity of the game server
    """
    r = requests.post(
        "http://{}:{}/games/server".format(auth_host, auth_port),
        json={"port": port, "name": name, "capacity": capacity}
    )

    if r.status_code != requests.codes.ok:
        logging.fatal("Couldn't contact authentication server. exiting")
        exit(2)


class GameObject:
    x = None
    y = None
    radius = None
    size = None

    def __init__(self, radius, max_x, max_y):
        self.update_radius(radius)
        self.set_random_position(max_x, max_y)

    def to_json(self):
        return {
            "size": self.size,
            "x": self.x,
            "y": self.y
        }

    def update_radius(self, new_radius):
        self.radius = new_radius
        self.size = new_radius * 2

    def set_random_position(self, max_x, max_y):
        """
        Returns a random position

        :return: tuple of X,Y position
        """
        self.x = random.randint(self.radius, max_x - self.radius)
        self.y = random.randint(self.radius, max_y - self.radius)

    def collides_with(self, obj: 'GameObject'):
        return self.radius ** 2 > (obj.x - self.x) ** 2 + (obj.y - self.y) ** 2


class Player(GameObject):
    def __init__(self, name, color, radius, max_x, max_y):
        super().__init__(radius, max_x, max_y)
        self.name = name
        self.color = color
        self.timestamp = time.time()

    def to_json(self):
        return {
            "name": self.name,
            "color": self.color,
            "position": (self.x, self.y),
            "size": self.size
        }

    def update_size(self, obj: 'GameObject'):
        self.update_radius((self.radius ** 2 + obj.radius ** 2) ** 0.5)


class GameProtocol(DatagramProtocol):
    """
    Implementation of the Game protocol for Phagocytes

    :param auth_host: host address of the authentication server
    :param auth_port: port of the authentication server
    :param capacity: max capacity of the server
    """
    players = dict()
    moves = dict()
    deaths = set()
    food = list()
    food_notify_index = 0

    max_x = 5000
    max_y = 5000
    default_radius = 50
    max_speed = 400
    eat_ratio = 1.5

    last_time = time.time()

    death_message = json.dumps({"event": Event.DEATH}).encode("utf-8")

    def __init__(self, auth_host, auth_port, capacity, logger):
        self.auth_host = auth_host
        self.auth_port = auth_port
        self.max_capacity = capacity
        self.logger = logger
        self.url = "http://{}:{}".format(self.auth_host, self.auth_port)

        task.LoopingCall(self.handle_players).start(1 / 30)
        task.LoopingCall(self.handle_food).start(1 / 30)
        task.LoopingCall(self.handle_food_reminder).start(1 / 2)

    def authenticate(self, token):
        """
        tries to authenticate the user against the authentication server

        :param token: token given by the user
        :raise AuthenticationError: if authentication failed
        :return: name and color of the user as returned by the authentication server
        """
        r = requests.post(self.url + "/validate", json=dict(token=token))
        if r.status_code == requests.codes.ok:
            return r.json()["username"], r.json()["color"]

        raise AuthenticationError(r.json())

    def register(self, data, addr):
        """
        register a new player on the game server

        :param data: data got from the client
        :param addr: client address
        :return:  message to send to the user
        """
        if data.get("event") != Event.TOKEN:
            self.logger.warning("User from {addr} not registered tried to gain access".format(addr=addr))
            return dict(event=Event.ERROR, error="Client not registered")

        elif data.get("token") is None:
            color = random_color()
            name = data.get("name", str(uuid.uuid4()))
            log_name = "with name {name}".format(name=name) if name is not None else "with no name"
            self.logger.debug("Registering new user {name}".format(name=log_name))
        else:
            try:
                name, color = self.authenticate(data.get("token"))
            except AuthenticationError as e:
                self.logger.warning("User from {addr} tried to register with invalid token".format(addr=addr))
                e.msg["event"] = Event.ERROR
                return e.msg
            else:
                self.logger.debug("Registered new user {name}".format(name=name))

        client = Player(name, color, self.default_radius, self.max_x, self.max_y)
        self.players[addr] = client
        
        data = dict(
            event=Event.GAME_INFO, name=name, max_x=self.max_x, max_y=self.max_y,
            position=(client.x, client.y), color=color, size=client.size
        )

        return data

    def datagramReceived(self, datagram, addr):
        """
        function called every time a new datagram is received.
        This will dispatch it to the correct handler

        :param datagram: datagram received from the client
        :param addr: client address
        """
        try:
            data = json.loads(datagram.decode("utf8"))
        except json.decoder.JSONDecodeError:
            self.logger.warning("Invalid json received : '{json}'".format(json=datagram.decode("utf-8")))
        else:
            if self.players.get(addr) is None:
                if addr in self.deaths:
                    if data["event"] == Event.DEATH:
                        self.deaths.remove(addr)
                    else:
                        self.transport.write(self.death_message, addr=addr)
                else:
                    self.transport.write(json.dumps(self.register(data, addr)).encode("utf8"), addr)
            elif data["event"] == Event.STATE:
                self.moves[addr] = data["position"]
            else:
                logging.error("Received invalid action: {json}".format(json=data))

    def send_all_players(self, data):
        for client in self.players.keys():
            self.transport.write(data, addr=client)

    def handle_players(self):
        data = {}

        for addr, update in self.moves.items():
            if update is None:
                continue

            timestamp = time.time()
            client = self.players[addr]

            factor_x = factor_y = 0

            delta_x = update[0] - client.x
            delta_y = update[1] - client.y
            speed_x = abs(delta_x / (timestamp - client.timestamp))
            speed_y = abs(delta_y / (timestamp - client.timestamp))

            if speed_x > self.max_speed:
                factor_x = delta_x * self.max_speed / speed_x
                client.x = min(self.max_x - client.radius, max(
                    client.radius, client.x + factor_x
                ))
            else:
                client.x = min(self.max_x - client.radius, max(client.radius, update[0]))

            if speed_y > self.max_speed:
                factor_y = delta_y * self.max_speed / speed_y
                client.y = min(self.max_y - client.radius, max(
                    client.radius, client.y + factor_y
                ))
            else:
                client.y = min(self.max_y - client.radius, max(client.radius, update[1]))

            data[addr] = self.players[addr].to_json()

            if factor_x or factor_y:
                data[addr]["dirty"] = (factor_x - delta_x, factor_y - delta_y)

            self.moves[addr] = None
            client.timestamp = timestamp

        if len(data):
            self.send_all_players(json.dumps({"event": Event.STATE, "updates": list(data.values())}).encode("utf-8"))

        deaths = set()

        for eater_addr, eater in self.players.items():
            for eaten_addr, eaten in self.players.items():
                if eaten_addr in deaths or eater_addr in deaths:
                    continue

                if eaten.size > eater.size * self.eat_ratio:
                    eater, eaten = eaten, eater
                    eater_addr, eaten_addr = eaten_addr, eater_addr
                elif eater.size < eaten.size * self.eat_ratio:
                    continue

                if eater.collides_with(eaten):
                    eater.update_size(eaten)
                    deaths.add(eaten_addr)

                    # FIXME : notify auth server for scores and so on

        for death in deaths:
            self.players.pop(death)
            self.transport.write(self.death_message, addr=death)

        self.deaths |= deaths

    def handle_food_reminder(self):
        if len(self.food) == 0:
            return

        self.send_all_players(json.dumps({
            "event": Event.FOOD_REMINDER,
            "food": [food.to_json() for food in self.food[self.food_notify_index]]
        }).encode("utf8"))

        self.food_notify_index = (self.food_notify_index + 1) % len(self.food)

    def handle_food(self):
        event = {"event": Event.FOOD}
        deletions = []
        entry = None

        if random.randrange(10) < 1:
            for entry in self.food:
                if len(entry) < 100:
                    break
            else:
                if len(self.food) < 5:
                    self.food.append(set())
                    entry = self.food[-1]

            if entry is not None:
                food = GameObject(random.randint(5, 25), self.max_x, self.max_y)
                entry.add(food)
                event["new"] = food.to_json()

        for player in self.players.values():
            for _list in self.food:
                to_remove = []

                for food in _list:
                    if player.collides_with(food):
                        player.update_size(food)
                        deletions.append(food.to_json())
                        to_remove.append(food)

                for remove in to_remove:
                    _list.remove(remove)

        if len(deletions):
            event["old"] = deletions

        if len(event) > 1:
            self.send_all_players(json.dumps(event).encode("utf-8"))


def runserver(port, auth_host, auth_port, name, capacity, debug):
    """
    launches the game server

    :param port: port on which to listen
    :param auth_host: hostname of the authentication server to which to refer
    :param auth_port: port of the authentication server to which to refer
    :param name: name of the game server
    :param capacity: capacity of the game server
    :param debug: whether to turn on debugging or not
    """
    logger = create_logger(name, port, debug)

    try:
        reactor.listenUDP(port, GameProtocol(auth_host, auth_port, capacity, logger))
    except CannotListenError as e:
        if isinstance(e.socketError, PermissionError):
            logger.error("Permission denied. Do you have the right to open port {} ?".format(port))
        elif isinstance(e.socketError, OSError):
            logger.error("Couldn't listen on port {}. Port is already used.".format(port))
        else:
            raise e.socketError
    else:
        logger.info("server launched")
        register(port, auth_host, auth_port, name, capacity)
        reactor.run()
