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
from math import ceil
from typing import Dict, Set, Tuple
from typing import List

import atexit
import collections
import random
import requests
from rainbow_logging_handler import RainbowLoggingHandler
from twisted.internet import reactor, task
from twisted.internet.error import CannotListenError
from twisted.internet.protocol import DatagramProtocol

from phagocyte_game_server.events import Event, Error
from phagocyte_game_server.game_objects import Bonus, BonusTypes, RandomPositionedGameObject, Bullet, Player,\
    RoundGameObject, GrabHook
from phagocyte_game_server.custom_types import address, json_object


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

    def __init__(self, msg: Dict):
        self.msg = msg


def random_color() -> str:
    """
    get a new random color in hexadecimal

    :return: new hexadecimal color
    """
    return "#%06x" % random.randint(0, 0xFFFFFF)


def bonus_timeout(player: Player) -> None:
    """ sets the given bonus to None """
    player.bonus = None
    player.bonus_callback = None


def register(auth_host: str, auth_port: int, **kwargs: Dict):
    """
    registers the game server against the authentication server

    :param auth_host: address of the authentication server
    :param auth_port: port of the authentication server
    :param kwargs: arguments neeted to register the server
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("www.google.com", 80))
    kwargs["ip"] = s.getsockname()[0]
    s.close()

    r = requests.post("http://{}:{}/games/server".format(auth_host, auth_port), json=kwargs)

    if r.status_code != requests.codes.ok:
        logging.fatal("Couldn't contact authentication server. exiting")
        exit(2)

    return kwargs["ip"]


class GameProtocol(DatagramProtocol):
    """
    Implementation of the Game protocol for Phagocytes

    This class contains the whole logic of the game and decides what is
    or not valid in the context of the game

    :param auth_host: host address of the authentication server
    :param auth_port: port of the authentication server
    :param capacity: max capacity of the server
    :param logger: logger instance to use to report errors and other messages
    :param token: the token used to authenticate the server
    """
    death_message = json.dumps({"event": Event.DEATH}).encode("utf-8")

    def __init__(self, auth_host: str, auth_port: int, capacity: int, logger: logging.Logger, token: str, port: int,
                 map_height: int, map_width: int, max_speed: int, max_hit_count: int, eat_ratio: float, min_radius: int,
                 food_production_rate: int, win_size: int):
        self.players = dict()  # type: Dict[address, Player]
        self.moves = dict()  # type: Dict[address, Tuple[int, int]]
        self.deaths = set()  # type: Set[address]
        self.food = collections.deque()  # type: collections.deque[RandomPositionedGameObject]
        self.bullets = collections.deque()  # type: collections.deque[Bullet]
        self.bonuses = collections.deque()  # type: collections.deque[Bonus]

        self.new_bullets = dict()  # type: Dict[address, float]

        self.food_notify_index = 0  # type: int
        self.bullet_notify_index = 0  # type: int
        self.new_bullet_id = 0  # type: int
        self.last_bullet_update = time.time()  # type: int

        self.auth_host = auth_host  # type: str
        self.auth_port = auth_port  # type: int
        self.url = "http://{}:{}".format(self.auth_host, self.auth_port)  # type: str
        self.max_capacity = capacity  # type: int

        self.max_x = map_width  # type: int
        self.max_y = map_height  # type: int
        self.default_radius = min_radius  # type: int
        self.max_speed = max_speed  # type: int
        self.eat_ratio = eat_ratio  # type: float

        self.food_production_rate = food_production_rate  # type: int
        self.new_bonuses_ratio = 3  # type: int

        self.max_hit_count = max_hit_count  # type: int
        self.bonus_time = 10  # type: int
        self.win_size = win_size  # type: int

        self.last_time = time.time()  # type: int

        self.winning_player = None
        self.finished = None

        self.logger = logger  # type: logging.Logger
        self.closing_call = None
        self.token = token

        self.port = port
        self.ip = None

        task.LoopingCall(self.handle_players).start(1 / 30)
        task.LoopingCall(self.handle_food).start(1 / 30)
        task.LoopingCall(self.handle_new_bullets).start(1 / 3)
        task.LoopingCall(self.handle_bullets).start(1 / 30)
        task.LoopingCall(self.handle_bonuses).start(1 / 30)
        task.LoopingCall(self.handle_hooks).start(1 / 30)
        task.LoopingCall(self.handle_disconnects).start(5)

        task.LoopingCall(self.check_usage).start(60)

    def authenticate(self, token: str) -> Tuple[str, str, str]:
        """
        tries to authenticate the user against the authentication server

        :param token: token given by the user
        :raise AuthenticationError: if authentication failed
        :return: name and color of the user as returned by the authentication server
        """
        r = requests.post(self.url + "/account/validate", json=dict(token=token))
        if r.status_code == requests.codes.ok:
            return r.json()["uid"], r.json()["username"], r.json()["color"]

        raise AuthenticationError(r.json())

    def register(self, data: json_object, addr: address):
        """
        register a new player on the game server

        :param data: data got from the client
        :param addr: client address
        """
        if data.get("event") != Event.TOKEN:
            self.logger.warning("User from {addr} not registered tried to gain access".format(addr=addr))
            self.send_to(addr, dict(event=Event.ERROR, code=Error.NO_TOKEN))
            return

        elif len(self.players) >= self.max_capacity:
            self.logger.info("Refusing user due to too much people")
            self.send_to(addr, dict(event=Event.ERROR, code=Error.MAX_CAPACITY))
            return

        elif data.get("token") is None:
            color = random_color()
            name = data.get("name", str(uuid.uuid4()))
            uid = None
        else:
            try:
                uid, name, color = self.authenticate(data.get("token"))
            except AuthenticationError as e:
                self.logger.warning("User from {addr} tried to register with invalid token".format(addr=addr))
                self.send_to(addr, dict(event=Event.ERROR, error=e.msg["error"], code=Error.TOKEN_INVALID))
                return

        for player in self.players.values():
            if player.name == name:
                if time.time() - player.timestamp < 15:
                    self.logger.warning("User from {addr} tried to connect as a user already playing".format(addr=addr))
                    self.send_to(addr, dict(event=Event.ERROR, code=Error.DUPLICATE_USERNAME))
                    return

                else:
                    client = player
                    self.logger.warning("User {name} was reconnected".format(name=name))
                    break
        else:
            self.logger.debug("Registered new user {name}".format(name=name))
            client = Player(uid, name, color, self.default_radius, self.max_x, self.max_y)

        self.send_to(addr, dict(
            event=Event.GAME_INFO, name=name, max_x=self.max_x, max_y=self.max_y, win_size=self.win_size,
            x=client.x, y=client.y, color=color, size=client.size, others=[p.to_json() for p in self.players.values()]
        ))

        self.players[addr] = client

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
            if self.finished:
                if data["event"] == Event.FINISHED:
                    self.players.pop(addr, None)
                    if len(self.players) == 0:
                        self.close()
                else:
                    self.send_to(addr, dict(event=Event.FINISHED, win=self.winning_player))
            elif self.players.get(addr) is None:
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
            elif data["event"] == Event.HOOK:
                player = self.players[addr]
                if player.hook is None:
                    player.hook = GrabHook(player, data["angle"])
            elif data["event"] == "ALIVE":
                self.players[addr].timestamp = time.time()
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
            player = self.players.get(addr)
            if player is not None and player.size > player.initial_size:
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

                        if player.bonus == BonusTypes.SHIELD:
                            deleted_bullets.append(bullet.uid)
                            break

                        player.hit_count += ceil((bullet.size / 10)**.5)
                        if player.hit_count >= self.max_hit_count:
                            player.hit_count = 0

                            if player.size >= player.initial_size:
                                lost_size = player.size / 3
                                player.matter_lost += lost_size
                                player.size = max(player.initial_size, player.size - lost_size)
                                player.radius = player.size / 2
                                self.throw_food(int(lost_size), player.x, player.y, player.radius)

                        deleted_bullets.append(bullet.uid)
                        break

                if not has_hit and not (bullet.x == self.max_x - bullet.radius or bullet.x == bullet.radius or
                                        bullet.y == self.max_y - bullet.radius or bullet.y == bullet.radius):
                    self.bullets.append(bullet)

                data_to_send.append(bullet.to_json())

            self.send_all_players(dict(event=Event.BULLETS, bullets=data_to_send, deleted=deleted_bullets))

        self.last_bullet_update = new_time

    def throw_food(self, size_to_disptach, player_x, player_y, player_radius):
        while size_to_disptach > 10:
            size = random.randint(10, size_to_disptach)
            size_to_disptach -= size
            radius = size / 2
            f = RoundGameObject(radius)
            f.x = max(radius, (min(self.max_x - radius, random.randint(
                int(player_x - 5 * player_radius), int(5 * player_radius + player_x)
            ))))
            f.y = max(radius, (min(self.max_y - radius, random.randint(
                int(player_y - 5 * player_radius), int(5 * player_radius + player_y)
            ))))
            self.food.appendleft(f)

    def handle_players(self):
        """
        checks moves from all the players and handle collisions between them
        """
        data = []  # type: List[json_object]

        for addr, update in self.moves.items():
            if update is None:
                continue

            timestamp = time.time()
            player = self.players[addr]

            factor_x = factor_y = 0

            delta_x = update[0] - player.x
            delta_y = update[1] - player.y
            speed_x = abs(delta_x / (timestamp - player.timestamp))
            speed_y = abs(delta_y / (timestamp - player.timestamp))

            max_speed = player.max_speed * 1.5 if player.bonus == BonusTypes.SPEEDUP else player.max_speed

            if speed_x > max_speed:
                factor_x = delta_x * max_speed / speed_x
                player.x = min(self.max_x - player.radius, max(
                    player.radius, player.x + factor_x
                ))
            else:
                player.x = min(self.max_x - player.radius, max(player.radius, update[0]))

            if speed_y > max_speed:
                factor_y = delta_y * max_speed / speed_y
                player.y = min(self.max_y - player.radius, max(
                    player.radius, player.y + factor_y
                ))
            else:
                player.y = min(self.max_y - player.radius, max(player.radius, update[1]))

            _json = player.to_json()
            if factor_x or factor_y or player.grabbed_x or player.grabbed_y:
                _json["dirty"] = (factor_x + player.grabbed_x - delta_x, factor_y + player.grabbed_y - delta_y)
                player.grabbed_x = player.grabbed_y = 0

            data.append(_json)
            self.moves[addr] = None
            player.timestamp = timestamp

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

                    if eaten.uid is not None:
                        try:
                            stats = eaten.get_stats(died=True)
                            stats["token"] = self.token
                            requests.post(
                                "{}/account/{}".format(self.url, eaten.uid),
                                json=stats
                            )
                        except Exception as e:
                            self.logger.error("Couldn't post stats for player, got" + str(e))

                    if eater.size > self.win_size:
                        self.win(eater)

        corpses = []
        for death in deaths:
            corpses.append(self.players.pop(death).name)
            self.transport.write(self.death_message, addr=death)

        self.deaths |= deaths  # add the users dead this turn to the list of dead

        if len(data) or len(corpses):
            self.send_all_players(dict(event=Event.STATE, updates=data, deaths=corpses))

    def handle_food(self):
        """
        randomly adds new food and checks for collisions against all players
        """
        deletions = []  # type: json_object
        food_to_send = []  # type: json_object

        if random.randrange(100) < self.food_production_rate and len(self.food) < 50 + 50 * len(self.players)**1.1:
            self.food.appendleft(RandomPositionedGameObject(random.randint(5, 25), self.max_x, self.max_y))

        for i in range(min(len(self.food), 70)):
            food = self.food.popleft()
            for player in self.players.values():
                if player.collides_with(food):
                    player.update_size(food)
                    deletions.append(food.to_json())
                    if player.size > self.win_size:
                        self.win(player)
                    break
            else:
                self.food.append(food)
                food_to_send.append(food.to_json())

        self.send_all_players(dict(event=Event.FOOD, food=food_to_send, deleted=deletions))

    def handle_bonuses(self):
        """
        randomly adds new bonuses in the game and checks for collisions against all players
        """
        deletions = []  # type: json_object
        bonuses_to_send = []  # type: json_object

        if random.randrange(1000) < self.new_bonuses_ratio and len(self.bonuses) < 5 * len(self.players) ** 1.1:
            self.bonuses.append(Bonus(self.max_x, self.max_y))

        for i in range(min(len(self.bonuses), 70)):
            bonus = self.bonuses.popleft()
            for player in self.players.values():
                if player.collides_with(bonus):
                    if player.bonus_callback is not None:
                        player.bonus_callback.cancel()

                    player.bonus = bonus.bonus
                    player.bonus_callback = reactor.callLater(10, bonus_timeout, player)
                    deletions.append(bonus.to_json())
                    player.bonuses_taken += 1
                    break
            else:
                self.bonuses.append(bonus)
                bonuses_to_send.append(bonus.to_json())

        self.send_all_players(dict(event=Event.BONUS, bonus=bonuses_to_send, deleted=deletions))

    def handle_hooks(self):
        """
        handles the movements and throwing of grab hooks
        """
        for player1 in self.players.values():
            hook = player1.hook
            if hook is None:
                continue
            elif hook.hooked_player is None:
                # we need to find if a player is hit by the hook
                for player2 in self.players.values():
                    if player2 == player1:
                        continue

                    if player2.collides_with(hook):
                        hook.hooked_player = player2
                        player1.successful_hooks += 1
                        break

                else:
                    hook.x = max(0, min(self.max_x, hook.x + 2 * player1.initial_max_speed * hook.ratio_x * (1 / 30)))
                    hook.y = max(0, min(self.max_y, hook.y + 2 * player1.initial_max_speed * hook.ratio_y * (1 / 30)))

                    if (hook.x - player1.x) ** 2 + (hook.y - player1.y) ** 2 >= (2 * player1.size) ** 2:
                        player1.hook = None

            else:
                # we need to move the players closer from each other
                player2 = hook.hooked_player

                move_ratio1 = player1.size / (player1.size + player2.size)
                move_ratio2 = 1 - move_ratio1

                total_movement = (player1.max_speed + player2.max_speed) / 30

                x_delta = player1.x - player2.x
                y_delta = player1.y - player2.y

                x_ratio = abs(x_delta) / (abs(x_delta) + abs(y_delta))
                y_ratio = 1 - x_ratio

                if x_delta > 0:
                    movement_x = min(total_movement * x_ratio, x_delta)
                else:
                    movement_x = max(-total_movement * x_ratio, x_delta)

                if y_delta > 0:
                    movement_y = min(total_movement * y_ratio, y_delta)
                else:
                    movement_y = max(-total_movement * y_ratio, y_delta)

                player1.grabbed_x -= movement_x * move_ratio1
                player1.grabbed_y -= movement_y * move_ratio1

                player2.grabbed_x += movement_x * move_ratio2
                player2.grabbed_y += movement_y * move_ratio2

                hook.moves += 1
                if hook.moves >= 15:
                    player1.hook = None
                else:
                    hook.x = player2.x
                    hook.y = player2.y

    def handle_disconnects(self):
        """
        handles all users that were not connected for too long
        """
        alives = []
        deads = []

        now = time.time()

        for addr, player in self.players.items():
            if now - player.timestamp > 60:
                deads.append(addr)
            else:
                alives.append(player.to_json())

        for dead in deads:
            self.players.pop(dead)

        self.send_all_players(dict(event=Event.ALIVE, alives=alives))

        if len(self.players) == 0 and self.finished:
            self.close()

    def win(self, winner: Player):
        """
        notify all players that a player has won

        :param winner: player that won
        """
        self.finished = True
        self.winning_player = winner.name

        self.send_all_players(dict(event=Event.FINISHED, win=winner.name))

        for player in self.players.values():
            if player.uid is None:
                continue
            try:
                stats = player.get_stats(won=(player == winner))
                stats["token"] = self.token
                requests.post(
                    "{}/account/{}".format(self.url, player.uid),
                    json=stats
                )
            except Exception as e:
                self.logger.error("Couldn't log information for player, got " + str(e))

    def check_usage(self):
        """
        Checks that some players are still in the game
        """
        if len(self.players) != 0 and self.closing_call is not None:
            self.closing_call.cancel()
            self.closing_call = None
        elif len(self.players) == 0 and self.closing_call is None:
            self.closing_call = reactor.callLater(360, self.close)

    def close(self):
        """
        Shuts down the system and unregisters it
        """
        if len(self.players) != 0 and self.closing_call is not None:
            self.closing_call.cancel()
            self.closing_call = None
            return

        r = requests.delete(
            "http://{}:{}/games/server".format(self.auth_host, self.auth_port),
            json=dict(token=self.token, port=self.port, ip=self.ip)
        )

        if r.status_code != requests.codes.ok:
            self.logger.error("Couldn't unregister successfully")

        if reactor.running:
            reactor.stop()

        atexit.unregister(self.close)


def runserver(port, auth_host, auth_port, name, capacity, debug, **kwargs):
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
        game_protocol = GameProtocol(auth_host, auth_port, capacity, logger, port=port, **kwargs)
        reactor.listenUDP(port, game_protocol)
    except CannotListenError as e:
        if isinstance(e.socketError, PermissionError):
            logger.error("Permission denied. Do you have the right to open port {} ?".format(port))
        elif isinstance(e.socketError, OSError):
            logger.error("Couldn't listen on port {}. Port is already used.".format(port))
        else:
            raise e.socketError
    else:
        logger.info("server launched")
        ip = register(auth_host, auth_port, name=name, capacity=capacity, port=port, **kwargs)
        game_protocol.ip = ip
        reactor.run()

        atexit.register(game_protocol.close)
