#!/usr/bin/env python3

"""
Regroups client-related exceptions.
"""

__author__ = "Basile Vu <basile.vu@gmail.com>"


class CredentialsException(Exception):
    """
    Represents an exception occurring when there is a problem with the credentials.
    
    :param msg: What the exception is about.
    """
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg
