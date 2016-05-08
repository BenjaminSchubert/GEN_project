#!/usr/bin/python3

from twisted.internet import reactor
from twisted.internet.protocol import DatagramProtocol

__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


class TestProtocol(DatagramProtocol):

    def startProtocol(self):
        print("Started")

    def datagramReceived(self, datagram, addr):
        print("Received datagram!")
        print(addr)
        print(datagram)

if __name__ == '__main__':
    reactor.listenUDP(8090, TestProtocol())
    reactor.run()
