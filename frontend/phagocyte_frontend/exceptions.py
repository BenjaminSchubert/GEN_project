#!/usr/bin/env python3

__author__ = "Basile Vu <basile.vu@gmail.com>"


class CreateUserException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class LoginFailedException(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg

