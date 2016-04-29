#!/usr/bin/python3

from phagocyte_frontend.client import Client

__author__ = "Basile Vu <basile.vu@gmail.com>"


if __name__ == '__main__':
    client = Client("127.0.0.1", 8000)
    #client.register("Test", "lol")

    print("client logging in")
    client.login("Test", "lol")

    print("client connected ? " + str(client.is_connected()))
    print("client logging out")
    client.logout()
    print("client connected ? " + str(client.is_connected()))

