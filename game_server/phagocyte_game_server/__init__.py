#!/usr/bin/env python3

"""
Phagocyte's game handler

This module defines the controller for the Phagocyte's game.
"""

import json
import json.decoder
import logging
import socket
import sys
import time
import uuid
from typing import Dict, List, Set, Tuple

import collections
import random
import requests
from rainbow_logging_handler import RainbowLoggingHandler
from twisted.internet import reactor, task
from twisted.internet.error import CannotListenError
from twisted.internet.protocol import DatagramProtocol

from phagocyte_game_server.events import Event
from phagocyte_game_server.game_objects import RandomPositionedGameObject, Bullet, Player, GameObject
from phagocyte_game_server.types import address, json_object


__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


def create_logger(name: str, port: int, debug: bool) -> logging.Logger:
    """
    Setup a logger to use for the game server

    :param name: name of the server
    :param port: port on which the server listens
    :param debug: whether to enable debugging or not
    :return: a new logger instance configured for the game
    """
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

    def __init__(self, msg: str):
        self.msg = msg


def random_color() -> str:
    """
    get a new random color in hexadecimal

    :return: new hexadecimal color
    """
    return "#%06x" % random.randint(0, 0xFFFFFF)


def register(port: int, auth_host: str, auth_port: int, name: int, capacity: int):
    """
    registers the game server against the authentication server

    :param port: port of the game server
    :param auth_host: address of the authentication server
    :param auth_port: port of the authentication server
    :param name: name of the game server
    :param capacity: max capacity of the game server
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("www.google.com", 80))
    ip_addr = s.getsockname()
    s.close()

    r = requests.post(
        "http://{}:{}/games/server".format(auth_host, auth_port),
        json={"port": port, "name": name, "capacity": capacity, "ip": ip_addr[0]}
    )

    if r.status_code != requests.codes.ok:
        logging.fatal("Couldn't contact authentication server. exiting")
        exit(2)


class GameProtocol(DatagramProtocol):
    """
    Implementation of the Game protocol for Phagocytes

    This class contains the whole logic of the game and decides what is
    or not valid in the context of the game

    :param auth_host: host address of the authentication server
    :param auth_port: port of the authentication server
    :param capacity: max capacity of the server
    :param logger: logger instance to use to report errors and other messages
    """
    death_message = json.dumps({"event": Event.DEATH}).encode("utf-8")

    def __init__(self, auth_host: str, auth_port: int, capacity: int, logger: logging.Logger):
        self.players = dict()  # type: Dict[address, Player]
        self.moves = dict()  # type: Dict[address, Tuple[int, int]]
        self.deaths = set()  # type: Set[address]
        self.food = [set() for _ in range(5)]  # type: List[Set[RandomPositionedGameObject]]
        self.bullets = collections.deque()  # type: collections.deque[Bullet]
        self.new_bullets = dict()  # type: Dict[address, float]

        self.food_notify_index = 0  # type: int
        self.bullet_notify_index = 0  # type: int
        self.new_bullet_id = 0  # type: int
        self.last_bullet_update = time.time()  # type: int

        self.auth_host = auth_host  # type: str
        self.auth_port = auth_port  # type: int
        self.url = "http://{}:{}".format(self.auth_host, self.auth_port)  # type: str
        self.max_capacity = capacity  # type: int

        self.max_x = 5000  # type: int
        self.max_y = 5000  # type: int
        self.default_radius = 50  # type: int
        self.max_speed = 400  # type: int
        self.eat_ratio = 1.2  # type: float
        self.new_food_ratio = 5  # type: int
        self.max_hit_count = 10  # type: int

        self.last_time = time.time()  # type: int

        self.logger = logger  # type: logging.Logger

        task.LoopingCall(self.handle_players).start(1 / 30)
        task.LoopingCall(self.handle_food).start(1 / 30)
        task.LoopingCall(self.handle_food_reminder).start(1 / 2)
        task.LoopingCall(self.handle_new_bullets).start(1 / 3)
        task.LoopingCall(self.handle_bullets).start(1 / 30)

    def authenticate(self, token: str) -> Tuple[str, str]:
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

    def register(self, data: json_object, addr: address):
        """
        register a new player on the game server

        :param data: data got from the client
        :param addr: client address
        """
        if data.get("event") != Event.TOKEN:
            self.logger.warning("User from {addr} not registered tried to gain access".format(addr=addr))
            self.send_to(addr, dict(event=Event.ERROR, error="Client not registered"))
            return

        elif data.get("token") is None:
            color = random_color()
            name = data.get("name", str(uuid.uuid4()))
        else:
            try:
                name, color = self.authenticate(data.get("token"))
            except AuthenticationError as e:
                self.logger.warning("User from {addr} tried to register with invalid token".format(addr=addr))
                self.send_to(addr, dict(event=Event, error=e.msg))
                return

        self.logger.debug("Registered new user {name}".format(name=name))

        client = Player(name, color, self.default_radius, self.max_x, self.max_y)
        self.players[addr] = client

        self.send_to(addr, dict(
            event=Event.GAME_INFO, name=name, max_x=self.max_x, max_y=self.max_y,
            x=client.x, y=client.y, color=color, size=client.size
        ))

    def datagramReceived(self, datagram: bytes, addr: address):
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
                        self.transport.write(self.death_message, addr)
                else:
                    self.register(data, addr)
            elif data["event"] == Event.STATE:
                self.moves[addr] = data["position"]
            elif data["event"] == Event.BULLETS:
                self.new_bullets[addr] = data["angle"]
            else:
                logging.error("Received invalid action: {json}".format(json=data))

    def send_to(self, addr: address, data: json_object):
        """
        Sends the given data to the user identified by the given address

        :param addr: address to which to send the data
        :param data: data to send
        """
        self.transport.write(json.dumps(data).encode("utf8"), addr)

    def send_all_players(self, data: json_object):
        """
        Sends the given data to all users connected

        :param data: data to send
        """
        json_data = json.dumps(data).encode("utf-8")
        for client in self.players.keys():
            self.transport.write(json_data, addr=client)

    def handle_new_bullets(self):
        """
        handles the addition of new bullets
        """
        for addr, angle in self.new_bullets.items():
            player = self.players[addr]
            if player.size > player.initial_size:
                self.bullets.append(Bullet(angle, player))

        self.new_bullets = dict()  # type: Dict[address, float]

    def handle_bullets(self):
        """
        handles new bullets, checks for collisions and updates results
        """
        step = 50
        new_time = time.time()
        dt = new_time - self.last_bullet_update

        for i in range(0, len(self.bullets), step):
            data_to_send = []
            deleted_bullets = []
            max_boundary = min(step, len(self.bullets) - step * i)

            for j in range(max_boundary):
                has_hit = False

                bullet = self.bullets.popleft()
                bullet.x = min(self.max_x - bullet.radius, max(bullet.radius, bullet.x + bullet.speed_x * dt))
                bullet.y = min(self.max_y - bullet.radius, max(bullet.radius, bullet.y + bullet.speed_y * dt))

                for player in self.players.values():
                    if player != bullet.player and player.collides_with(bullet):
                        has_hit = True
                        player.hit_count += 1
                        if player.hit_count >= self.max_hit_count:
                            player.hit_count = 0

                            if player.size >= player.initial_size:
                                lost_size = player.size / 3
                                player.size = max(player.initial_size, player.size - lost_size)
                                self.throw_food(int(lost_size), player.x, player.y, player.radius)

                        deleted_bullets.append(bullet.uid)
                        break

                if not has_hit and not (bullet.x == self.max_x - bullet.radius or bullet.x == bullet.radius or
                                        bullet.y == self.max_y - bullet.radius or bullet.y == bullet.radius):
                    self.bullets.append(bullet)

                data_to_send.append(bullet.to_json())

            self.send_all_players({"event": Event.BULLETS, "bullets": data_to_send, "deleted": deleted_bullets})

        self.last_bullet_update = new_time

    def throw_food(self, size_to_disptach, player_x, player_y, player_radius):
        new_food = []

        while size_to_disptach > 10:
            size = random.randint(10, size_to_disptach)
            size_to_disptach -= size
            radius = size / 2
            f = GameObject(radius)
            f.x = max(radius, (min(self.max_x - radius, random.randint(
                int(player_x - 3 * player_radius), int(3 * player_radius + player_x)
            ))))
            f.y = max(radius, (min(self.max_y - radius, random.randint(
                int(player_y - 3 * player_radius), int(3 * player_radius + player_y)
            ))))
            new_food.append(f)

        self.send_all_players({"event": Event.FOOD_REMINDER, "food": [f.to_json() for f in new_food]})
        self.food[0] |= set(new_food)

    def handle_players(self):
        """
        checks moves from all the players and handle collisions between them
        """
        data = {}  # type: Dict[address, json_object]

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

            if speed_x > client.max_speed:
                factor_x = delta_x * client.max_speed / speed_x
                client.x = min(self.max_x - client.radius, max(
                    client.radius, client.x + factor_x
                ))
            else:
                client.x = min(self.max_x - client.radius, max(client.radius, update[0]))

            if speed_y > client.max_speed:
                factor_y = delta_y * client.max_speed / speed_y
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
            self.send_all_players({"event": Event.STATE, "updates": list(data.values())})

        deaths = set()  # type: Set[address]

        for eater_addr, eater in self.players.items():
            for eaten_addr, eaten in self.players.items():
                if eaten_addr in deaths or eater_addr in deaths:
                    continue

                if eaten.size > eater.size * self.eat_ratio:
                    # the eaten is bigger than the eater, let's inverse roles
                    eater, eaten = eaten, eater
                    eater_addr, eaten_addr = eaten_addr, eater_addr
                elif eater.size < eaten.size * self.eat_ratio:
                    # eater is not big enough to eat the eaten, we go on
                    continue

                if eater.collides_with(eaten):
                    eater.update_size(eaten)
                    deaths.add(eaten_addr)

                    # FIXME : notify auth server for scores and so on

        for death in deaths:
            self.players.pop(death)
            self.transport.write(self.death_message, addr=death)

        self.deaths |= deaths  # add the users dead this turn to the list of dead

    def handle_food_reminder(self):
        """
        Reminds user periodically of the food that is in the world
        """
        if len(self.food[self.food_notify_index]) != 0:
            self.send_all_players({
                "event": Event.FOOD_REMINDER,
                "food": [food.to_json() for food in self.food[self.food_notify_index]]
            })

        self.food_notify_index = (self.food_notify_index + 1) % len(self.food)

    def handle_food(self):
        """
        randomly adds new food and checks for collisions against all players
        """
        event = {"event": Event.FOOD}  # type: json_object
        deletions = []

        if random.randrange(100) < self.new_food_ratio:
            for entry in self.food:
                if len(entry) < 100:
                    food = RandomPositionedGameObject(random.randint(5, 25), self.max_x, self.max_y)
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
            self.send_all_players(event)


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
