"""
Authentication for Phagocyte. Here are defined various authentication
related functions, mostly linked to JWT
"""

from typing import Dict

import sqlalchemy.orm

from phagocyte_authentication_server.models import User, db


__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


def authenticate(username: str, password: str):
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

    if user is not None and user.check_password(password):
        return user


def identity(payload: Dict):
    """
    get the user identified by the given payload

    :param payload: JWT payload
    :return: user associated to the payload
    """
    return db.session.query(User).filter_by(id=payload['identity']).one()
