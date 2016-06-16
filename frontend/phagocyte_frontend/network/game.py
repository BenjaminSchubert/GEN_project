#!/usr/bin/env python3

"""
Client-side classes to communicate with the game server.
"""
import enum
import json
from typing import Dict, Union

import time
import twisted.internet

import phagocyte_frontend.network.twisted_reactor
from phagocyte_frontend.exceptions import CredentialsException


twisted.internet._threadedselect = phagocyte_frontend.network.twisted_reactor

from kivy.support import install_twisted_reactor
install_twisted_reactor()

from twisted.internet import reactor, task
from twisted.internet.protocol import DatagramProtocol

from kivy.logger import Logger

__author__ = "Basile Vu <basile.vu@gmail.com>"


REACTOR = reactor


@enum.unique
class Event(enum.IntEnum):
    ERROR = 0
    TOKEN = 1
    GAME_INFO = 2
    STATE = 3
    FOOD = 4
    DEATH = 5
    BULLETS = 6
    BONUS = 7
    HOOK = 8
    ALIVE = 9
    FINISHED = 10


@enum.unique
class Error(enum.IntEnum):
    TOKEN_INVALID = 0
    MAX_CAPACITY = 1
    NO_TOKEN = 2
    DUPLICATE_USERNAME = 3


class NetworkGameClient(DatagramProtocol):
    """
    Executes various actions related to messages related to client - game server communication.

    :param host: the ip of the server
    :param port: the port of the server
    :param auth_client: the client handling authentication
    """
    name = None

    def __init__(self, host, port, auth_client, game):
        self.host = host
        self.port = port
        self.auth_client = auth_client
        self.game = game
        self.died = False
        self.tried_connection = False
        self.last_timestamp = 0

    def startProtocol(self):
        """
        Establishes connection with game server and sends the token.
        """
        self.transport.connect(self.host, self.port)
        self.send_token()

    def datagramReceived(self, datagram, addr):
        """
        Executes various actions based on the type of the message.
        """
        try:
            data = json.loads(datagram.decode("utf-8"))
        except json.decoder.JSONDecodeError:
            Logger.warning("Invalid json received : '{json}".format(json=datagram.decode("utf-8")))
            return

        event_type = data.get("event", None)

        if event_type == Event.GAME_INFO:
            self.name = data["name"]
            self.game.start_game(self, data)
            self.last_timestamp = time.time()
            task.LoopingCall(self.check_server_alive).start(3)
        elif event_type == Event.STATE:
            self.game.update_state(data["updates"], data["deaths"])
        elif event_type == Event.FOOD:
            self.game.update_food(data.get("food", []), data.get("deleted", []))
        elif event_type == Event.BULLETS:
            self.game.check_bullets(data["bullets"], data["deleted"])
        elif event_type == Event.BONUS:
            self.game.update_bonus(data.get("bonus", []), data.get("deleted", []))
        elif event_type == Event.DEATH:
            self.died = True
            self.send_dict(event=Event.DEATH)
            self.game.death()
        elif event_type == Event.ALIVE:
            self.game.handle_alives(data.get("alives"))
            self.last_timestamp = time.time()
        elif event_type == Event.FINISHED:
            self.send_dict(event=Event.FINISHED)
            self.game.handle_win(data.get("win"))
        elif event_type == Event.ERROR:
            self.handle_error(data)
        elif event_type is None:
            Logger.error("The datagram doesn't have any event: ", datagram.decode("utf-8"))
        else:
            Logger.error("Unhandled event type : data is ", datagram.decode("utf-8"))

    def handle_error(self, data: Dict[str, Union[str, int]]) -> None:
        """
        Handles errors received from the client

        :param data: data containing information about the error
        """
        code = data.get("code", None)

        if code is None:
            Logger.error("Got error without code : {data}".format(data=data))

        elif code == Error.TOKEN_INVALID:
            if not self.tried_connection:
                self.auth_client.login()
                self.send_token()
                self.tried_connection = True
            else:
                raise CredentialsException(data.get("error"))

        elif code == Error.NO_TOKEN:
            if not self.died:
                Logger.warning("Token needed to access game")

        elif code == Error.MAX_CAPACITY:
            self.game.handle_error("The game is complete, please choose another one")

        elif code == Error.DUPLICATE_USERNAME:
            self.game.handle_error("Another user with the same name is already playing here")

        else:
            Logger.error("Got unknown error code {code}".format(code=code))

    def check_server_alive(self):
        if self.last_timestamp < time.time() - 10:
            self.game.handle_error("Cannot reach game server anymore, sorry !")
            self.last_timestamp = time.time()

    def send_token(self):
        """
        Sends the token to the server.
        """
        self.send_dict(event=Event.TOKEN, token=self.auth_client.token)

    def send_state(self, position):
        """
        Sends the state of the phagocyte to the server.
        """
        self.send_dict(event=Event.STATE, position=position)

    def send_bullet(self, angle):
        """
        send that the user wants to fire a bullet with the given angle

        :param angle: angle at which the bullet was fired
        """
        self.send_dict(event=Event.BULLETS, angle=angle)

    def send_hook(self, angle):
        """
        send that the user wants to launch its hook with the given angle

        :param angle: angle at which the hook is thrown
        """
        self.send_dict(event=Event.HOOK, angle=angle)

    def send_dict(self, **kwargs):
        """
        Sends a dictionary as json to the server.
        """
        self.transport.write(json.dumps(kwargs).encode("utf-8"))
