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


class Event(enum.IntEnum):
    ERROR = 0
    TOKEN = 1
    GAME_INFO = 2
    UPDATE = 3
    STATE = 4
    FOOD = 5
    FOOD_REMINDER = 6


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
        print("Started protocol")
        self.transport.connect(self.host, self.port)
        self.send_token()
        print("sent token")

    def datagramReceived(self, datagram, addr):
        """
        Executes various actions based on the type of the message.
        """
        data = json.loads(datagram.decode("utf-8"))
        event_type = data.get("event", None)

        if event_type == Event.GAME_INFO:
            self.name = data["name"]
            self.game.start_game(self, data)
        elif event_type == Event.UPDATE:
            self.update_gui(data)
        elif event_type == Event.STATE:
            self.game.update_state(data["updates"])
        elif event_type == Event.FOOD:
            self.game.update_food(data.get("new"), data.get("old", []))
        elif event_type == Event.FOOD_REMINDER:
            self.game.check_food(data["food"])
        elif event_type == Event.ERROR:
            print("Error: ", data)  # FIXME
        elif event_type is None:
            print("The datagram doesn't have any event: ", data)
        else:
            print("Unhandled event type : data is ", data)

    def update_gui(self, data):
        """
        Updates the gui (game view).

        :param data: the data received from server.
        """
        self.phagocyte.update(data["phagocyte"])
        print("updating gui")
        # TODO

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

    def send_dict(self, **kwargs):
        """
        Sends a dictionary as json to the server.
        """
        self.transport.write(json.dumps(kwargs).encode("utf-8"))
