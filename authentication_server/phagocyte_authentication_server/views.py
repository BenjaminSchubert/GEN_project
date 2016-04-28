#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Various views for the Phagocyte authentication server
"""

from flask import request

from phagocyte_authentication_server import app
from phagocyte_authentication_server.models import User, db


__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


@app.route("/register", methods=["POST"])
def create_user():
    """
    Creates a new user with the data given in parameter
    """
    # TODO : a better error handling would be good here
    data = request.get_json()
    user = User(username=data["username"], password=data["password"])
    db.session.add(user)
    db.session.commit()
