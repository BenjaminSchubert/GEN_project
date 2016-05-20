#!/usr/bin/python3

"""
Definition of events that can be sent on the game
"""

import enum

__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


class Event(enum.IntEnum):
    """
    Enumeration of all events valid in the game
    """
    ERROR = 0
    TOKEN = 1
    GAME_INFO = 2
    UPDATE = 3
    STATE = 4
    FOOD = 5
    FOOD_REMINDER = 6
    DEATH = 7
