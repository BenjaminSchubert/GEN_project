#!/usr/bin/env python3

"""
Application that just represents a GUI for connection and creating a user.
"""

from concurrent.futures import ThreadPoolExecutor

import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput

import requests.exceptions

from phagocyte_frontend.client import Client
from phagocyte_frontend.exceptions import CredentialsException


kivy.require('1.0.7')


__author__ = "Boson Sébastien <sebastboson@gmail.com>"


class LoginScreen(GridLayout):
    """
    login screen

    :param kwargs: additional key word send to the parent
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        client = Client("127.0.0.1", 8000)

        self.executor = ThreadPoolExecutor(max_workers=1)

        self.cols = 2

        self.add_widget(Label(text='User name:'))

        username = TextInput(multiline=False)
        self.add_widget(username)

        self.add_widget(Label(text='Password:'))

        password = TextInput(password=True, multiline=False)
        self.add_widget(password)

        box_left = BoxLayout(padding=30, orientation='horizontal')
        self.add_widget(box_left)
        register = Button(text='Register', size_hint=(1, 0.4))
        box_left.add_widget(register)
        register.bind(on_press=lambda _: self.executor.submit(register))

        box_right = BoxLayout(padding=30, orientation="horizontal")
        self.add_widget(box_right)
        login = Button(text="Login", size_hint=(1, 0.4))
        box_right.add_widget(login)
        login.bind(on_press=lambda _: self.executor.submit(connection))

        info_label = Label()
        self.add_widget(info_label)

        # test
        join = Button(text="join game", size_hint=(1, 0.4))
        box_right.add_widget(join)
        join.bind(on_press=lambda _: client.join_game("127.0.0.1", 8090))

        def connection():
            """
            Connects the specified user with his name and password
            """
            handle_credentials_sending("Logging in...", "Logged in!", client.login)

        def register():
            """
            Registers the specified user with his name and password
            """
            handle_credentials_sending("Registering...", "Registered!", client.register)

        def handle_credentials_sending(wait_msg, ok_msg, func):
            """
            Executes a function related to sending credentials to the server and displays info related to server
            responses.

            :param wait_msg: the default message to display when waiting for server response.
            :param ok_msg: the message to display when everything is ok (no error).
            :param func: the function to use. Must take username and password as first and second parameter.
            """
            info_label.text = wait_msg

            try:
                func(username.text, password.text)
            except CredentialsException as e:
                info_label.text = "Error: " + str(e)
            except requests.exceptions.ConnectionError:
                info_label.text = ("Error: could not connect to server. Please check your internet connection and "
                                   "whether the server is running.")
            except Exception as e:
                print(e)  # FIXME handle proper logging
            else:
                info_label.text = ok_msg

    def __del__(self):
        self.executor.shutdown(True)


class MyApp(App):
    """
    main kivy application
    """
    def build(self):
        """
        builds and returns GUI

        :return: loginScreen
        """
        return LoginScreen()


if __name__ == '__main__':
    MyApp().run()
