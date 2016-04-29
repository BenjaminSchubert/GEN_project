import requests
import hashlib

__author__ = "Basile Vu <basile.vu@gmail.com>"


class Client:

    host = "localhost"
    port = 8000
    token = None

    def __init__(self, host, port):
        self.host = host
        self.port = port

    def get_base_url(self):
        return "http://" + self.host + ":" + str(self.port)

    def create_credentials_data(self, username, password):
        return {
            "username": username,
            "password": hashlib.sha512((hashlib.sha512(password.encode("utf-8")).hexdigest() + username).encode("utf-8")).hexdigest()
        }

    def send_json(self, json, relative_path):
        headers = {
            "content-type": "application/json"
        }

        return requests.post(url=self.get_base_url() + relative_path, headers=headers, json=json)

    def register(self, username, password):
        r = self.send_json(self.create_credentials_data(username, password), "/register")
        print('register response: ' + r.text)

    def login(self, username, password):
        r = self.send_json(self.create_credentials_data(username, password), "/auth")
        print('auth response: ' + r.text)