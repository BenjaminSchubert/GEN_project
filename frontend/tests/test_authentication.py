#!/usr/bin/env python3

import responses
import requests
import unittest

from phagocyte_frontend.network.authentication import Client
from phagocyte_frontend.network.api import REGISTER_PATH
from phagocyte_frontend.exceptions import CredentialsException


__author__ = "Basile Vu <basile.vu@gmail.com>"


class TestAuthentication(unittest.TestCase):

    client = Client("42", "42")

    @responses.activate
    def test_register_malformed_json(self):
        responses.add(responses.POST, self.client.get_base_url() + REGISTER_PATH,
                      status=requests.codes.conflict, content_type="application/json")

        self.assertRaises(ValueError, self.client.register, "username", "password")

        responses.add(responses.POST, self.client.get_base_url() + REGISTER_PATH,
                      body="{",
                      status=requests.codes.conflict, content_type="application/json")

        self.assertRaises(ValueError, self.client.register, "username", "password")

    @responses.activate
    def test_register_conflict(self):
        responses.add(responses.POST, self.client.get_base_url() + REGISTER_PATH,
                      status=requests.codes.conflict, body='{"error": "error"}',
                      content_type="application/json")

        self.assertRaises(CredentialsException, self.client.register, "username", "password")
