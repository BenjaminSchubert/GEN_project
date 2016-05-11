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

    def __init__(self, name, x, y, v_x, v_y):
        self.id = name
        self.x = x
        self.y = y
        self.v_x = v_x
        self.v_y = v_y


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
        print("Received data.")
        data = json.loads(datagram.decode("utf-8"))

        # TODO enum cases

        # TODO when connection OK
        self.phagocyte = Phagocyte(0, 0, 0, 0, 0)

    def send_token(self):
        self.send_dict(token=self.token, event=Event.TOKEN)

    def send_state(self):
        self.send_dict(v_x=self.phagocyte.v_x, v_y=self.phagocyte.v_y)

    def send_dict(self, **kwargs):
        self.transport.write(json.dumps(kwargs).encode("utf-8"))


class ClientGame:

    def __init__(self, token, host, port):
        self.host = host
        self.port = port
        self.token = token

    def run(self):
        reactor.listenUDP(0, ClientGameProtocol(self.host, self.port, self.token))
