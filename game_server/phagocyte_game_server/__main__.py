#!/usr/bin/python3

from twisted.internet import protocol, reactor
from twisted.protocols import basic

__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


class TestProtocol(basic.LineReceiver):

    def connectionMade(self):
        print("new connection")

    def lineReceived(self, line):
        print("Received:" + line)


class TestFactory(protocol.ServerFactory):
    protocol = TestProtocol

if __name__ == '__main__':
    reactor.listenTCP(8090, TestFactory())
    reactor.run()
