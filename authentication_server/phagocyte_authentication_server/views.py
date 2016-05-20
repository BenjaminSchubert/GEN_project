#!/usr/bin/python3

"""
Various views for the Phagocyte authentication server
"""

import json

import uuid

import jwt
import requests
import sqlalchemy.exc
from flask import request, jsonify, make_response
from flask_jwt import jwt_required, current_identity

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
    print(request)
    data = request.get_json()
    print(data, " ", type(data))
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
    print("lol")
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
    app.games.add_manager(token=token, **request.json)
    if len(app.games.games) <= 1:
        data["create"] = True
        data["name"] = "Main"
        data["capacity"] = 200
    return jsonify(data)


@app.route("/account/parameters", methods=["POST"])
@jwt_required()
def change_account_parameters():
    received = json.loads(request.get_json())

    print(received)
    print(type(received))

    if "color" in received:
        current_identity.color = received["color"]

    if "name" in request.json:
        current_identity.name = received["name"]

    print(current_identity.color, " ", current_identity.username)

    return "", 200


@app.route("/account/parameters", methods=["GET"])
@jwt_required()
def get_account_parameters():
    return current_identity.to_json(), 200


@app.route("/account/password", methods=["POST"])
@jwt_required()
def change_password():
    print("received")
    print(request.json)

    return "", 200