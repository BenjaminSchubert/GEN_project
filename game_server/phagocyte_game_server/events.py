"""
Definition of events that can be sent on the game
"""

import enum

__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


@enum.unique
class Event(enum.IntEnum):
    """
    Enumeration of all events valid in the game
    """
    ERROR = 0
    TOKEN = 1
    GAME_INFO = 2
    STATE = 3
    FOOD = 4
    DEATH = 5
    BULLETS = 6
    BONUS = 7
    HOOK = 8
    ALIVE = 9
    FINISHED = 10


@enum.unique
class Error(enum.IntEnum):
    """
    Enumeration of all errors that the server can throw to a player
    """
    TOKEN_INVALID = 0
    MAX_CAPACITY = 1
    NO_TOKEN = 2
    DUPLICATE_USERNAME = 3
