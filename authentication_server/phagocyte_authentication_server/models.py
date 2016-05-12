#!/usr/bin/python3

"""
Models for the Phagocyte Application authentication
"""

import hashlib
import os
import random

from sqlalchemy import Column, INTEGER, BINARY, VARCHAR
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import validates

from phagocyte_authentication_server.sqlalchemy_session import SQLAlchemy


__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


# database and ORM base class
db = SQLAlchemy()
Base = declarative_base()


def random_color():
    """
    get a new random color in hexadecimal

    :return: new hexadecimal color
    """
    return "#%06x" % random.randint(0, 0xFFFFFF)


class User(Base):
    """
    User model containing all information directly linked to a player
    """
    __tablename__ = "user"

    id = Column(INTEGER, primary_key=True, autoincrement=True)
    username = Column(VARCHAR(255), unique=True)
    password = Column(BINARY(64), nullable=False)
    salt = Column(BINARY(255), nullable=False)
    color = Column(VARCHAR(6), default=random_color)

    level = Column(INTEGER, default=1)
    xp = Column(INTEGER, default=0)

    def hash_password(self, password: str) -> bytes:
        """
        Hashes the string given in parameter with the user's salt

        :param password: string to hash
        :return: hashed string
        """
        return hashlib.pbkdf2_hmac('sha512', password.encode("utf-8"), self.salt, 1000000)

    def check_password(self, password: str) -> bool:
        """
        Checks that the user's password is valid

        :param password: password to check against
        :return: True if the password is valid
        """
        return self.password == self.hash_password(password)

    # noinspection PyUnusedLocal
    @validates('password')
    def validate_password(self, key, value):
        """
        Hash the user's password and set a new salt.

        :param key. unused
        :param value: new password
        """
        self.salt = os.urandom(255)
        return self.hash_password(value)

    def to_json(self):
        """
        Transforms the user to a json format

        :return: dictionary to send to the user
        """
        return {
            "username": self.username,
            "color": self.color,
        }
