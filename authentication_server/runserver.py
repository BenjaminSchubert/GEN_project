#!/usr/bin/python3

"""
Main runner for the Phagocyte authentication server.

You can run `python3 runserver.py` to get information about its various commands
"""

from phagocyte_authentication_server import manager


__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


if __name__ == '__main__':
    manager.run()
