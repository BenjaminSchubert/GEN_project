#!/usr/bin/env python3

"""
Authentication for Phagocyte. Here are defined various authentication
related functions, mostly linked to JWT
"""

import sqlalchemy.orm

from phagocyte_authentication_server.models import User, db
from flask import abort


__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


def authenticate(username, password):
    """
    authenticates a user

    :param username: username of the user
    :param password: password of the user
    :return: the user instance if it exists
    :raise: HttpException if no user with the given username exists or the password is wrong
    """
    try:
        user = db.session.query(User).filter_by(username=username).one()
    except sqlalchemy.orm.exc.NoResultFound:
        user = None

    if user is None or not user.check_password(password):
        abort(401)

    return user


def identity(payload):
    raise NotImplementedError("Identity is not implemented yet")
