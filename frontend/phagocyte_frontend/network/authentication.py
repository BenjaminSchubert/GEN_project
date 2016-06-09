#!/usr/bin/env python3

"""
Contains client-related classes used to interact with the authentication server.
"""

import hashlib
import requests
from kivy.logger import Logger

from phagocyte_frontend.exceptions import CredentialsException
from phagocyte_frontend.network.api import REGISTER_PATH, AUTH_PATH, PARAMETERS_PATH, GAMES_PATH


__author__ = "Basile Vu <basile.vu@gmail.com>"


class CreationFailedException(Exception):
    """
    Exception thrown when the creation of a game fails
    """


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
        self.username = None
        self.password = None

    def get_base_url(self):
        """
        Creates the base url for the server.
        """
        return "http://{host}:{port}".format(host=self.host, port=self.port)

    @staticmethod
    def create_credentials_data(username, password):
        """
        Creates the data to send, containing the username and the hashed password.

        :param username: the username to send.
        :param password: the password to hash and send.
        """
        return {
            "username": username,
            "password": hashlib.sha512(
                (hashlib.sha512(password.encode("utf-8")).hexdigest() + username).encode("utf-8")
            ).hexdigest()
        }

    def post_json(self, endpoint, **kwargs):
        """
        Sends the json using a POST request at the given relative path.

        :param endpoint: the relative path (relative to the base url).
        :param kwargs: the data to send as json.
        """
        headers = {}

        if self.is_logged_in():
            headers["authorization"] = "JWT " + self.token

        return requests.post(url=self.get_base_url() + endpoint, headers=headers, json=kwargs)

    def get_json_as_dict(self, endpoint):
        """
        Gets the data as dict from the server at the endpoint (the server should return a json for this endpoint).

        :param: endpoint: the relative path where to GET ("/auth", for example)
        """
        def try_get():
            headers = {}

            if self.is_logged_in():
                headers["authorization"] = "JWT " + self.token

            r = requests.get(url=self.get_base_url() + endpoint, headers=headers)

            if r.status_code == requests.codes.unauthorized:
                self.token = None
                raise CredentialsException("Token expired")

            return r

        try:
            return try_get().json()
        except CredentialsException:
            if self.username is not None and self.password is not None:
                self.login(self.username, self.password)
                return try_get().json()

            raise

    def register(self, username, password):
        """
        Registers the user using his username and password.

        :param username: the username to use.
        :param password: the password to use.
        """
        r = self.post_json(REGISTER_PATH, **self.create_credentials_data(username, password))
        self.username = username
        self.password = password

        if r.status_code == requests.codes.conflict:
            raise CredentialsException("The user already exists")

    def login(self, username, password):
        """
        Logs in the user using his username and password.

        :param username: the username to use.
        :param password: the password to use.
        """
        r = self.post_json(AUTH_PATH, **self.create_credentials_data(username, password))

        if r.status_code < 400:
            try:
                self.token = r.json()["access_token"]
            except ValueError:
                Logger.error("Malformed json")
        elif r.status_code == requests.codes.unauthorized:
            raise CredentialsException("Bad credentials")

        self.username = username
        self.password = password

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
        self.password = None
        self.username = None

    def post_account_info(self, **kwargs):
        """
        Modifies account info.

        :param kwargs: the data as dict to send as json
        """
        self.post_json(endpoint=PARAMETERS_PATH, **kwargs)

    def get_account_info(self):
        """
        Fetches the accounts info and returns them as a dict.
        """
        return self.get_json_as_dict(PARAMETERS_PATH)

    def get_games(self):
        """
        Gets the list of available games.
        """
        r = requests.get(self.get_base_url() + GAMES_PATH)
        return r.json()

    def create_game(self, **kwargs):
        """
        Creates a game.

        :param kwargs: the game info as dict to send as json.
        """
        r = self.post_json(endpoint=GAMES_PATH, **kwargs)

        if r.status_code != requests.codes.ok:
            raise CreationFailedException(r.json()["error"])
