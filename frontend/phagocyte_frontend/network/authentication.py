#!/usr/bin/env python3

"""
Contains client-related classes used to interact with the authentication server.
"""

import json

import hashlib
import requests

from phagocyte_frontend.exceptions import CredentialsException
from phagocyte_frontend.network.api import REGISTER_PATH, AUTH_PATH, PARAMETERS_PATH, GAMES_PATH


__author__ = "Basile Vu <basile.vu@gmail.com>"


class Client:
    """
    Provides various utility methods relative to interact with authentication and game servers.

    :param host: The hostname of the server.
    :param port: The port number of the server.
    """

    token = None

    def __init__(self, host, port):
        self.host = host
        self.port = port

    def get_base_url(self):
        """
        Creates the base url for the server.
        """
        return "http://" + self.host + ":" + str(self.port)

    @staticmethod
    def create_credentials_data(username, password):
        """
        Creates the data to send, containing the username and the hashed password.

        :param username: the username to send.
        :param password: the password to hash and send.
        """
        return {
            "username": username,
            "password": hashlib.sha512((hashlib.sha512(password.encode("utf-8")).hexdigest() + username).encode("utf-8")).hexdigest()
        }

    def post_json(self, _json, endpoint):
        """
        Sends the json using a POST request at the given relative path.

        :param _json: the json to send.
        :param endpoint: the relative path (relative to the base url).
        """
        headers = {
            "content-type": "application/json"
        }

        if self.is_logged_in():
            headers["authorization"] = "JWT " + self.token

        return requests.post(url=self.get_base_url() + endpoint, headers=headers, json=_json)

    def register(self, username, password):
        """
        Registers the user using his username and password.

        :param username: the username to use.
        :param password: the password to use.
        """
        r = self.post_json(self.create_credentials_data(username, password), REGISTER_PATH)

        if r.status_code == requests.codes.conflict:
            raise CredentialsException(r.json().get("error", "register error: got " + str(r.json())))

    def login(self, username, password):
        """
        Logs in the user using his username and password.

        :param username: the username to use.
        :param password: the password to use.
        """
        r = self.post_json(self.create_credentials_data(username, password), AUTH_PATH)

        if r.status_code < 400:
            self.token = r.json()["access_token"]
        elif r.status_code == requests.codes.unauthorized:
            raise CredentialsException("bad credentials")

    def is_logged_in(self):
        """
        Determines whether the user is logged in.
        """
        return self.token is not None

    def logout(self):
        """
        Logs out the user.
        """
        self.token = None

    def post_dict_as_json(self, *, endpoint, **kwargs):
        """
        Sends a POST request to the server, with data as json.

        :param endpoint: the relative path where to POST ("/auth", for example)
        :param kwargs: the data as dict to send as json
        """
        self.post_json(json.dumps(kwargs), endpoint)

    def post_account_info(self, **kwargs):
        """
        Modifies account info.

        :param kwargs: the data as dict to send as json
        """
        self.post_dict_as_json(endpoint=PARAMETERS_PATH, **kwargs)

    def get_games(self):
        """
        Gets the list of available games.
        """
        r = requests.get(self.get_base_url() + GAMES_PATH)
        return r.json()