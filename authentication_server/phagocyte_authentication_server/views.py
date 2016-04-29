#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Various views for the Phagocyte authentication server
"""

import sqlalchemy.exc
from flask import request, jsonify, make_response

from phagocyte_authentication_server import app
from phagocyte_authentication_server.models import User, db


__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


@app.route("/register", methods=["POST"])
def create_user():
    """
    Creates a new user with the data given in parameter
    """
    data = request.get_json()
    user = User(username=data["username"], password=data["password"])
    try:
        db.session.add(user)
        db.session.commit()
    except sqlalchemy.exc.IntegrityError:
        return make_response(jsonify(error="user with the same name already exists"), 409)
