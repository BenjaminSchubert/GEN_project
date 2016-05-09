#!/usr/bin/env python3

import json

import phagocyte_frontend.twisted_reactor
import twisted.internet

twisted.internet._threadedselect = phagocyte_frontend.twisted_reactor

from kivy.support import install_twisted_reactor
install_twisted_reactor()

from twisted.internet import reactor
from twisted.internet.protocol import DatagramProtocol

__author__ = "Basile Vu <basile.vu@gmail.com>"


class ClientGameProtocol(DatagramProtocol):

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

    def send_token(self):
        _json = {
            "token": self.token
        }

        self.send_dict(_json)

    def send_dict(self, d):
        self.transport.write(json.dumps(d).encode("utf-8"))


class ClientGame:

    def __init__(self, token, host, port):
        self.host = host
        self.port = port
        self.token = token

    def run(self):
        reactor.listenUDP(0, ClientGameProtocol(self.host, self.port, self.token))
