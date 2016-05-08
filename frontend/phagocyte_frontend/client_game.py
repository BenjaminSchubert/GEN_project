#!/usr/bin/env python3

from twisted.internet import defer, protocol, reactor

__author__ = "Basile Vu <basile.vu@gmail.com>"


class ClientGameProtocol(protocol.Protocol):

    def connectionMade(self):
        print("Connection established!")
        self.transport.write(self.factory.token)

    def dataReceived(self, data):
        print("Received data.")

    def connectionLost(self, _):
        print("Connection lost.")


class ClientGameFactory(protocol.ClientFactory):

    def __init__(self, token):
        self.token = token
        self.d = defer.Deferred()
        print(token)

    def startedConnecting(self, connector):
        print("Started to connect.")

    def buildProtocol(self, _):
        p = ClientGameProtocol()
        p.factory = self
        return p

    def clientConnectionFailed(self, _, reason):
        print("Connection failed")


class ClientGame:

    def __init__(self, token, host, port):
        reactor.connectTCP(host, port, ClientGameFactory(token))
        reactor.run()
