#!/usr/bin/env python3

import responses
import requests
import unittest

from phagocyte_frontend.network.authentication import Client
from phagocyte_frontend.network.api import REGISTER_PATH, AUTH_PATH
from phagocyte_frontend.exceptions import CredentialsException


__author__ = "Basile Vu <basile.vu@gmail.com>"


class TestAuthentication(unittest.TestCase):

    client = Client("42", "42")

    @responses.activate
    def test_user_already_registered(self):
        responses.add(responses.POST, self.client.get_base_url() + REGISTER_PATH,
                      status=requests.codes.conflict, content_type="application/json")

        self.assertRaises(CredentialsException, self.client.register, "username", "password")

    @responses.activate
    def test_user_can_login(self):
        responses.add(responses.POST, self.client.get_base_url() + AUTH_PATH,
                      status=200, body='{"access_token": "test"}',
                      content_type="application/json")

        self.client.login("username", "password")
        assert self.client.token == "test"

    @responses.activate
    def test_login_bad_credentials(self):
        responses.add(responses.POST, self.client.get_base_url() + AUTH_PATH,
                      status=requests.codes.unauthorized, content_type="application/json")

        self.assertRaises(CredentialsException, self.client.login, "username", "password")

    def test_is_logged_in(self):
        self.client.token = "test"
        assert self.client.is_logged_in()
