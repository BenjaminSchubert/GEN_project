"""
Various views for the Phagocyte authentication server
"""

import jwt
import re
import requests
import sqlalchemy.exc
import sqlalchemy.orm
from flask import request, jsonify, make_response
from flask_jwt import jwt_required, current_identity

from phagocyte_authentication_server import app
from phagocyte_authentication_server.auth import identity
from phagocyte_authentication_server.models import User, db, Stats


__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


@app.route("/register", methods=["POST"])
def create_user():
    """
    Creates a new user with the data given in parameter
    """
    data = request.get_json()
    user = User(username=data["username"], password=data["password"])
    user.stats = Stats()
    try:
        db.session.add(user)
        db.session.add(user.stats)
        db.session.commit()
    except sqlalchemy.exc.IntegrityError:
        return make_response(jsonify(error="user with the same name already exists"), 409)

    return "", 200


@app.route("/account/validate", methods=["POST"])
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


@app.route("/games", methods=["GET"])
def games():
    """
    Get the list of all games available
    """
    return jsonify({game.name: game.to_json() for game in app.games.games.values()})


@app.route("/games", methods=["POST"])
def create_game():
    """
    Creates a new game
    """
    try:
        app.games.create_game(request.get_json())
    except ValueError as e:
        return make_response(jsonify(error=str(e)), 400)
    except requests.exceptions.ConnectionError:
        return make_response(jsonify(error="Couldn't connect game server, please try again later"), 500)

    return "", 200


@app.route("/games/server", methods=["POST"])
def register_server():
    """
    Registers a new game server
    """
    app.games.add_game(**request.json)
    return "", 200


@app.route("/games/server", methods=["DELETE"])
def delete_game():
    """
    removes the given game from the list of available games
    """
    try:
        app.games.remove_game(**request.json)
    except KeyError as e:
        return jsonify(error=str(e)), 400
    return "", 200


@app.route("/games/manager", methods=["POST"])
def register_manager():
    """
    Registers a new game manager

    :return: token for authentication and information on which server to create if needed
    """
    return jsonify(dict(token=app.games.add_manager(**request.json)))


@app.route("/games/manager", methods=["DELETE"])
def delete_manager():
    """
    Removes a game manager from the list
    """
    app.games.remove_manager(request.get_json()["token"])
    return "", 200


@app.route("/account/parameters", methods=["POST"])
@jwt_required()
def change_account_parameters():
    """
    Changes the account parameters.
    """
    received = request.get_json()

    if "color" in received:
        if re.match("^#[0-9A-Fa-f]{8}$", received["color"]):
            current_identity.color = received["color"]
        else:
            return jsonify(error="invalid color format"), 400

    if "name" in received:
        current_identity.username = received["name"]

    if "new_password" in received:
        if "old_password" not in received or not current_identity.check_password(received["old_password"]):
            return jsonify(error="Old password incorrect"), 403

        current_identity.password = received["new_password"]

    try:
        db.session.commit()
    except sqlalchemy.exc.IntegrityError:
        return jsonify(error="Username already taken"), 400

    return "", 200


@app.route("/account/parameters", methods=["GET"])
@jwt_required()
def get_account_parameters():
    """
    Gets the accounts parameters.
    """
    return jsonify(current_identity.to_json())


@app.route("/account/statistics")
@jwt_required()
def get_statistics():
    """
    gets statistics about this account
    """
    return jsonify(current_identity.stats.to_json())


@app.route("/account/<uid>", methods=["POST"])
def update_statistics(uid):
    """
    Updates the statistics for the given player
    """
    _json = request.get_json()

    for manager in app.games.managers:
        if manager.token == _json["token"]:
            break
    else:
        return jsonify(error="not authenticated"), 401

    try:
        stats = db.session.query(User).filter(User.id == uid).one().stats
    except sqlalchemy.orm.exc.NoResultFound:
        return jsonify(error="user does not exist"), 404

    stats.bullets_shot += _json["bullets_shot"]
    stats.matter_absorbed += _json["matter_gained"]
    stats.bonuses_taken += _json["bonuses_taken"]
    stats.time_played += _json["time_played"]
    stats.matter_lost += _json["matter_lost"]
    stats.successful_hooks += _json["successful_hooks"]
    stats.players_eaten += _json["eaten"]

    stats.games_played += 1

    if request.json["won"]:
        stats.games_won += 1

    if request.json["death"]:
        stats.deaths += 1

    db.session.commit()

    return "", 200
