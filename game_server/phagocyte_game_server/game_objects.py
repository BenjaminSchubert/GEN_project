#!/usr/bin/env python3

"""
This module contains class representing each type of in game objects
"""
import enum
import itertools

import random
import time

from math import sin, cos

from phagocyte_game_server.custom_types import json_object


__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


class BonusTypes(enum.IntEnum):
    """
    Represents each bonus types a user can obtain
    """
    SHIELD = 0
    POWERUP = 1
    GROWTH = 2
    SPEEDUP = 3


class GameObject:
    """
    Represents an object in the game
    """
    __slots__ = ["x", "y"]

    def __init__(self):
        self.x = None  # type: float
        self.y = None  # type: float


class RoundGameObject(GameObject):
    """
    Represents an object in the game

    :param radius: radius of the object
    """
    __slots__ = ["radius", "size"]

    def __init__(self, radius: float):
        super().__init__()
        self.radius = None  # type: float
        self.size = None  # type: float

        self.update_radius(radius)

    def to_json(self) -> json_object:
        """ transforms the object to a dictionary to be sent on the wire """
        return {
            "size": self.size,
            "x": int(self.x),
            "y": int(self.y)
        }

    def update_radius(self, new_radius: float):
        """
        Updates the radius of the object. This should be used instead of directly updating the radius
        as it also handles the update of the object's size

        :param new_radius: new value for the radius
        """
        self.radius = new_radius
        self.size = new_radius * 2


class RandomPositionedGameObject(RoundGameObject):
    """
    Represents an object in the game that gets placed randomly

    :param radius: radius of the object
    :param max_x: size of the x axis of the world
    :param max_y: size of the y axis of the world
    """
    def __init__(self, radius: float, max_x: int, max_y: int):
        super().__init__(radius)
        self.set_random_position(max_x, max_y)

    def set_random_position(self, max_x: int, max_y: int):
        """
        sets a random position between max_x and max_y, taking into account
        the radius of the object so that it doesn't get out of the screen
        """
        self.x = random.randint(self.radius, max_x - self.radius)
        self.y = random.randint(self.radius, max_y - self.radius)


class Player(RandomPositionedGameObject):
    """
    Represents a player in the game

    :param name: name of the player
    :param color: color used to represent the player
    :param radius: radius of the disc representing the player
    :param max_x: maximum width of the map
    :param max_y: maximum height of the map
    """
    __slots__ = [
        "name", "color", "timestamp", "initial_size", "max_speed", "hit_count", "bonus", "bonus_callback",
        "hook", "grabbed_x", "grabbed_y"
    ]

    def __init__(self, name: str, color: str, radius: float, max_x: int, max_y: int):
        super().__init__(radius, max_x, max_y)
        self.initial_size = self.size  # type: int
        self.name = name  # type: str
        self.color = color  # type: str
        self.timestamp = time.time()  # type: int
        self.max_speed = 50 * self.initial_size / self.size ** 0.5  # type: float
        self.hit_count = 0  # type: int
        self.bonus = None  # type: Bonus
        self.bonus_callback = None  # type: callable
        self.hook = None  # type: GrabHook
        self.grabbed_x = 0  # type: float
        self.grabbed_y = 0  # type: float

    def to_json(self) -> json_object:
        """ transforms the object to a dictionary to be sent on the wire """
        return {
            "name": self.name,
            "color": self.color,
            "x": int(self.x),
            "y": int(self.y),
            "size": self.size,
            "bonus": self.bonus,
            "hook": self.hook.to_json() if self.hook is not None else self.hook
        }

    def update_size(self, obj: RoundGameObject):
        """
        updates the size of the object with the size of the object in parameter

        :param obj: object for which to take the size
        """
        gain = obj.radius ** 2
        if self.bonus == BonusTypes.GROWTH:
            gain *= 1.5

        self.update_radius((self.radius ** 2 + gain) ** 0.5)
        self.max_speed = 50 * self.initial_size / self.size ** 0.5

    def collides_with(self, obj: GameObject) -> bool:
        """
        determines whether an object has the center of the object given in parameter in its radius

        :param obj: the object for which to check the center
        :return: True if the object in parameter is in us, else False
        """
        return self.radius ** 2 > (obj.x - self.x) ** 2 + (obj.y - self.y) ** 2


class Bullet(RoundGameObject):
    """
    Represents a bullet in game
    """
    __slots__ = ["uid", "color", "speed_x", "speed_y", "player"]
    id_counter = itertools.count()  # type: itertools.count

    def __init__(self, angle: float, player: Player):
        size = player.size / 100
        player.size -= size

        if player.bonus == BonusTypes.POWERUP:
            size *= 2

        super().__init__(size * 10)

        self.x = player.x  # type: int
        self.y = player.y  # type: int
        self.color = player.color  # type: str
        self.speed_x = 2 * sin(angle) * player.max_speed  # type: float
        self.speed_y = 2 * cos(angle) * player.max_speed  # type: float
        self.uid = next(self.id_counter)  # type: int
        self.player = player

    def to_json(self):
        """ transforms the object to a dictionary to be sent on the wire """
        return {
            "uid": self.uid,
            "color": self.color,
            "x": int(self.x),
            "y": int(self.y),
            "speed_x": self.speed_x,
            "speed_y": self.speed_y,
            "size": self.size
        }


class Bonus(RandomPositionedGameObject):
    """
    Bonus object a user can take
    """
    __slots__ = ["bonus"]

    bonus_number = len(list(BonusTypes))  # type: int

    def __init__(self, max_x: int, max_y: int):
        super().__init__(15, max_x, max_y)
        self.bonus = random.randrange(self.bonus_number)  # type: int


class GrabHook(GameObject):
    """
    Object representing the hook a player can throw to grab another player to him
    """
    __slots__ = ["ratio_x", "ratio_y", "hooked_player", "moves"]

    def __init__(self, player: Player, angle: float):
        super().__init__()
        self.x = player.x  # type: float
        self.y = player.y  # type: float
        self.ratio_x = sin(angle)  # type: float
        self.ratio_y = cos(angle)  # type: float
        self.hooked_player = None  # type: Player
        self.moves = 0  # type: int

    def to_json(self):
        """ transforms the object to a dictionary to be sent on the wire """
        return {
            "x": int(self.x),
            "y": int(self.y),
        }
