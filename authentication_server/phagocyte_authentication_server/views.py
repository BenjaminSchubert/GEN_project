#!/usr/bin/python3
# -*- coding: utf-8 -*-
from flask import request

from phagocyte_authentication_server.models import User, db


__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


from phagocyte_authentication_server import app


@app.route("/register", methods=["POST"])
def create_user():
    data = request.get_json()
    user = User(username=data["username"], password=data["password"])
    db.session.add(user)
    db.session.commit()
