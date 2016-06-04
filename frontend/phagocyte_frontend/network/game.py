#!/usr/bin/env python3

"""
Client-side classes to communicate with the game server.
"""
import enum
import json

import twisted.internet

import phagocyte_frontend.network.twisted_reactor


twisted.internet._threadedselect = phagocyte_frontend.network.twisted_reactor

from kivy.support import install_twisted_reactor
install_twisted_reactor()

from twisted.internet import reactor
from twisted.internet.protocol import DatagramProtocol

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


class NetworkGameClient(DatagramProtocol):
    """
    Executes various actions related to messages related to client - game server communication.

    :param host: the ip of the server
    :param port: the port of the server
    :param token: the token of the client
    """
    name = None

    def __init__(self, host, port, token, game):
        self.host = host
        self.port = port
        self.token = token
        self.game = game

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
        data = json.loads(datagram.decode("utf-8"))
        event_type = data.get("event", None)

        if event_type == Event.GAME_INFO:
            self.name = data["name"]
            self.game.start_game(self, data)
        elif event_type == Event.STATE:
            self.game.update_state(data["updates"], data["deaths"])
        elif event_type == Event.FOOD:
            self.game.update_food(data.get("food", []), data.get("deleted", []))
        elif event_type == Event.BULLETS:
            self.game.check_bullets(data["bullets"], data["deleted"])
        elif event_type == Event.BONUS:
            self.game.update_bonus(data.get("bonus", []), data.get("deleted", []))
        elif event_type == Event.DEATH:
            self.send_dict(event=Event.DEATH)
            self.game.death()
        elif event_type == Event.ALIVE:
            self.game.handle_alives(data.get("alives"))
        elif event_type == Event.ERROR:
            print("Error: ", data)  # FIXME
        elif event_type is None:
            print("The datagram doesn't have any event: ", data)
        else:
            print("Unhandled event type : data is ", data)

    def send_token(self):
        """
        Sends the token to the server.
        """
        self.send_dict(event=Event.TOKEN, token=self.token)

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
