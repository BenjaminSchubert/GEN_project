#!/usr/bin/env python3

"""
Application that just represents a GUI for connection and creating a user.
"""

import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput

from phagocyte_frontend.client import Client
from phagocyte_frontend.exceptions import CreateUserException, LoginFailedException

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
        register.bind(on_press=lambda _: register())

        box_right = BoxLayout(padding=30, orientation="horizontal")
        self.add_widget(box_right)
        login = Button(text="Login", size_hint=(1, 0.4))
        box_right.add_widget(login)
        login.bind(on_press=lambda _: connection())

        answer_server = Label()
        self.add_widget(answer_server)

        def connection():
            """
            connects the specified user with his name and password
            """
            try:
                client.login(username.text, password.text)
            except LoginFailedException as e:
                answer_server.text = str(e)
            else:
                answer_server.text = "logged in"

        def register():
            """
            registers the specified user with his name and password
            """
            try:
                client.register(username.text, password.text)
            except CreateUserException as e:
                answer_server.text = str(e)
            else:
                answer_server.text = "registered"


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
