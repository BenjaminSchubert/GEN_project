#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sqlalchemy.orm

from phagocyte_authentication_server.models import User, db
from flask import abort


__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


def authenticate(username, password):
    try:
        user = db.session.query(User).filter_by(username=username).one()
    except sqlalchemy.orm.exc.NoResultFound:
        user = None

    if user is None or not user.check_password(password):
        abort(401)

    return user


def identity(payload):
    print(payload)
