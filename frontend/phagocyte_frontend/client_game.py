#!/usr/bin/env python3

"""
Client-side classes to communicate with the game server.
"""

import json

import phagocyte_frontend.twisted_reactor
import twisted.internet

from phagocyte_frontend.events import Event


twisted.internet._threadedselect = phagocyte_frontend.twisted_reactor

from kivy.support import install_twisted_reactor
install_twisted_reactor()

from twisted.internet import reactor
from twisted.internet.protocol import DatagramProtocol

__author__ = "Basile Vu <basile.vu@gmail.com>"


class Phagocyte:
    """
    Represents the phagocyte of the player.

    :param info: a dict containing name and position.
    """
    def __init__(self, info):
        self.id = info["name"]
        self.position = info["position"]
        self.speed = [0, 0]

    def update(self, info):
        """
        Updates the info of the phagocyte.

        :param info: a dict containing the position and speed.
        """
        self.position = info["position"]
        self.speed = info["speed"]


class ClientGameProtocol(DatagramProtocol):
    """
    Executes various actions related to messages related to client - game server communication.

    :param host: the ip of the server
    :param port: the port of the server
    :param token: the token of the client
    """
    phagocyte = None

    def __init__(self, host, port, token):
        self.host = host
        self.port = port
        self.token = token

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

        print("Received data: ", datagram)
        data = json.loads(datagram.decode("utf-8"))
        event_type = data.get("event", None)

        if event_type == Event.GAME_INFO:
            self.init_gui(data)
        elif event_type == Event.UPDATE:
            self.update_gui(data)
        elif event_type == Event.ERROR:
            print("Error: ", data)  # FIXME
        elif event_type is None:
            print("The datagram doesn't have any event: ", data)
        else:
            print("Unhandled event type : data is ", data)

    def init_gui(self, data):
        """
        Changes the view of the gui to the in-game view.

        :param data: the data received from server.
        """
        print("Changing gui to game view")
        self.phagocyte = Phagocyte(data)

        # TODO

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

    def send_state(self):
        """
        Sends the state of the phagocyte to the server.
        """
        self.send_dict(event=Event.STATE, position=self.phagocyte.position)

    def send_dict(self, **kwargs):
        """
        Sends a dictionary as json to the server.
        """
        self.transport.write(json.dumps(kwargs).encode("utf-8"))


class ClientGame:
    """
    Represents the in-game client.

    :param host: the ip of the server
    :param port: the port of the server
    :param token: the token of the client
    """
    def __init__(self, token, host, port):
        self.host = host
        self.port = port
        self.token = token

    def run(self):
        """
        Runs the client.
        """
        reactor.listenUDP(0, ClientGameProtocol(self.host, self.port, self.token))
