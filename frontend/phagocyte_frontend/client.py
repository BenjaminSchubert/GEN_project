#!/usr/bin/env python3

"""
Contains client-related classes used to interact with the authentication server.
"""

import requests
import hashlib

from phagocyte_frontend.exceptions import CredentialsException

__author__ = "Basile Vu <basile.vu@gmail.com>"


class Client:

    host = "localhost"
    port = 8000
    token = None

    def __init__(self, host, port):
        """
        Initializes the client using a host and a port number.
        :param host: The hostname of the server.
        :param port: The port number of the server.
        """
        self.host = host
        self.port = port

    def get_base_url(self):
        """
        Creates the base url for the server.
        """
        return "http://" + self.host + ":" + str(self.port)

    def create_credentials_data(self, username, password):
        """
        Creates the data to send, containing the username and the hashed password.
        :param username: the username to send.
        :param password: the password to hash and send.
        """
        return {
            "username": username,
            "password": hashlib.sha512((hashlib.sha512(password.encode("utf-8")).hexdigest() + username).encode("utf-8")).hexdigest()
        }

    def send_json(self, json, relative_path):
        """
        Sends the json using a POST request at the given relative path.
        :param json: the json to send.
        :param relative_path: the relative path (relative to the base url).
        """
        headers = {
            "content-type": "application/json"
        }

        return requests.post(url=self.get_base_url() + relative_path, headers=headers, json=json)

    def register(self, username, password):
        """
        Registers the user using his username and password.
        :param username: the username to use.
        :param password: the password to use.
        """
        r = self.send_json(self.create_credentials_data(username, password), "/register")

        if r.status_code == requests.codes.conflict:
            raise CredentialsException(r.json().get("error"))

    def login(self, username, password):
        """
        Logs in the user using his username and password.
        :param username: the username to use.
        :param password: the password to use.
        """
        r = self.send_json(self.create_credentials_data(username, password), "/auth")

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
