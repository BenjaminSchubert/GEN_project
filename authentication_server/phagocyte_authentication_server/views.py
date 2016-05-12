#!/usr/bin/python3

"""
Various views for the Phagocyte authentication server
"""

import uuid

import jwt
import requests
import sqlalchemy.exc
from flask import request, jsonify, make_response

from phagocyte_authentication_server import app
from phagocyte_authentication_server.auth import identity
from phagocyte_authentication_server.models import User, db


__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


def create_game_server(manager):
    """
    Creates a new game server on the manager given in parameter

    :param manager: manager on which to create a new game server
    """
    requests.post(
        "http://{}:{}/create".format(manager.ip, manager.port),
        json={"token": manager.token}
    )
    # TODO : handle errors


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


@app.route("/validate", methods=["POST"])
def validate_token():
    """
    Validates the token and send back the user's name and color
    """
    token = request.get_json()["token"]
    try:
        user = identity(app.extensions["jwt"].jwt_decode_callback(token))
    except jwt.exceptions.ExpiredSignatureError:
        return (jsonify(error="signature expired"), 403)
    return jsonify(user.to_json())


@app.route("/games")
def games():
    """
    Get the list of all games available
    """
    return jsonify(app.games.games)


@app.route("/games/server", methods=["POST"])
def register_server():
    """
    Registers a new game server

    :return: 200 OK
    """
    # FIXME : check that there are no name clashes
    app.games.add_game(request.remote_addr, request.json["port"], request.json["name"], request.json["capacity"])
    return "", 200


@app.route("/games/manager", methods=["POST"])
def register_manager():
    """
    Registers a new game manager

    :return: token for authentication and information on which server to create if needed
    """
    token = str(uuid.uuid4())
    data = {"token": token}
    app.games.add_manager(**request.json, token=token)
    if len(app.games.games) <= 1:
        data["create"] = True
        data["name"] = "Main"
        data["capacity"] = 200
    return jsonify(data)
