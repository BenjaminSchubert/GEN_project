#!/usr/bin/env python3

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
    def __init__(self, info):
        self.id = info["name"]
        self.position = info["position"]
        self.speed = [0, 0]

    def update(self, info):
        self.position = info["position"]
        self.speed = info["speed"]


class ClientGameProtocol(DatagramProtocol):
    phagocyte = None

    def __init__(self, host, port, token):
        self.host = host
        self.port = port
        self.token = token

    def startProtocol(self):
        print("Connection established! Sending token.")

        # we will only talk with server
        self.transport.connect(self.host, self.port)
        self.send_token()

    def datagramReceived(self, datagram, addr):
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
        print("Changing gui to game view")
        self.phagocyte = Phagocyte(data)

        # test
        print(self.phagocyte.position)
        self.send_state()

    def update_gui(self, data):
        self.phagocyte.update(data["phagocyte"])
        print("updating gui")  # FIXME

    def send_token(self):
        self.send_dict(event=Event.TOKEN, token=self.token)

    def send_state(self):
        self.send_dict(event=Event.STATE, position=self.phagocyte.position)

    def send_dict(self, **kwargs):
        self.transport.write(json.dumps(kwargs).encode("utf-8"))


class ClientGame:
    def __init__(self, token, host, port):
        self.host = host
        self.port = port
        self.token = token

    def run(self):
        reactor.listenUDP(0, ClientGameProtocol(self.host, self.port, self.token))
