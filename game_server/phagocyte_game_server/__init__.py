#!/usr/bin/env python3

import json
import random

import requests
from twisted.internet import reactor
from twisted.internet.protocol import DatagramProtocol

from phagocyte_game_server.events import Event


__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


class AuthenticationError(Exception):
    def __init__(self, msg):
        self.msg = msg


def random_color():
    """
    get a new random color in hexadecimal

    :return: new hexadecimal color
    """
    return "#%06x" % random.randint(0, 0xFFFFFF)


class GameProtocol(DatagramProtocol):
    clients = dict()
    max_x = 2000
    max_y = 2000

    def __init__(self, auth_ip, auth_port):
        self.auth_ip = auth_ip
        self.auth_port = auth_port
        self.url = "http://{}:{}".format(self.auth_ip, self.auth_port)

    def random_position(self):
        return (random.randint(0, self.max_x), random.randint(0, self.max_y))

    def authenticate(self, token):
        r = requests.post(self.url + "/validate", json=dict(token=token))
        if r.status_code == requests.codes.ok:
            return r.json().values()

        raise AuthenticationError(r.json())

    def register(self, data, addr):
        if data.get("event") != Event.TOKEN:
            return dict(event=Event.ERROR, error="Client not registered")

        elif data.get("token") is None:
            color = random_color()
            name = data.get("name")
        else:
            try:
                name, color = self.authenticate(data.get("token"))
            except AuthenticationError as e:
                e.msg["event"] = Event.ERROR
                return e.msg

        position = dict(position=self.random_position(), name=name, color=color, max_x=self.max_x, max_y=self.max_y)
        self.clients[addr] = position
        return position

    def datagramReceived(self, datagram, addr):
        data = json.loads(datagram.decode("utf8"))
        if self.clients.get(addr) is None:
            ret = self.register(data, addr)
        else:
            ret = None

        self.transport.write(json.dumps(ret).encode("utf8"), addr)


def runserver(port, auth_ip, auth_port):
    reactor.listenUDP(port, GameProtocol(auth_ip, auth_port))
    reactor.run()
