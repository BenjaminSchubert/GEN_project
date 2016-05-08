#!/usr/bin/env python3

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
        if self.token is None:
            self.transport.write("None".encode("utf-8")) # TODO
        else:
            self.transport.write(self.token.encode("utf-8"))


class ClientGame:

    def __init__(self, token, host, port):
        self.host = host
        self.port = port
        self.token = token

    def run(self):
        reactor.listenUDP(0, ClientGameProtocol(self.host, self.port, self.token))
