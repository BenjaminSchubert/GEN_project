#!/usr/bin/env python3

"""
Application that just represents a GUI for connection and creating a user.

Container Example

This example shows how to add a container to our screen.
A container is simply an empty place on the screen which
could be filled with any other content from a .kv file.
"""

from concurrent.futures import ThreadPoolExecutor

import kivy
from kivy.app import App
from kivy.config import Config
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput

import requests.exceptions

from phagocyte_frontend.client import Client
from phagocyte_frontend.exceptions import CredentialsException

Config.set("graphics", "resizable", False)
Config.set("graphics", "width", "1200")
Config.set("graphics", "height", "700")

kivy.require('1.0.7')

__author__ = "Sebastien Boson <sebastboson@gmail.com>"


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

        self.add_widget(Label(text="User name:"))

        username = TextInput(multiline=False)
        self.add_widget(username)

        self.add_widget(Label(text="Password:"))

        password = TextInput(password=True, multiline=False)
        self.add_widget(password)

        box_left = BoxLayout(padding=30, orientation="horizontal")
        self.add_widget(box_left)
        register = Button(text="Register", size_hint=(1, 0.4))
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


class RootWidget(BoxLayout, GridLayout):
    """
    create controllers that receive custom widgets from the kv lang file
    add actions to be called from a kv file
    """
    container = ObjectProperty(None)
    username = ObjectProperty(None)
    password = ObjectProperty(None)
    creationButton = ObjectProperty(None)
    loginButton = ObjectProperty(None)
    getGame = ObjectProperty(None)

    infoPopup = Popup(title="Info", size_hint=(None, None), size=(350, 200), auto_dismiss=False)
    infoPopup.add_widget(Button(text="Ok"))

    client = Client("127.0.0.1", 8000)

    def next_screen(self, screen):
        """
        clear container and load the given screen object from file in kv folder

        :param screen: name of the screen object made from the loaded .kv file
        """
        filename = screen + ".kv"

        Builder.unload_file("kv/" + filename)

        self.container.clear_widgets()

        screen = Builder.load_file("kv/" + filename)

        self.container.add_widget(screen)

    def game_creation_process(self):
        """

        """
        if not self.client.is_logged_in():
            box = BoxLayout(orientation="vertical")

            box.add_widget(Label(text="Error: you are not connected"))
            box.add_widget(
                Button(text="Ok", size_hint=(0.4, 0.4), pos_hint={"x": 0.6}, on_release=self.infoPopup.dismiss))

            self.infoPopup.content = box
            self.infoPopup.open()
        else:
            print("IL FAUT CREER UNE NOUVELLE PARTIE => 'CHANGER' D'ABORD DE FENETRE")

    def user_creation_process(self):
        """
        registers the specified user with his name and password
        """
        if self.client.is_logged_in():
            box = BoxLayout(orientation="vertical")

            box.add_widget(Label(text="Error: you are already connected"))
            box.add_widget(
                Button(text="Ok", size_hint=(0.4, 0.4), pos_hint={"x": 0.6}, on_release=self.infoPopup.dismiss))

            self.infoPopup.content = box
            self.infoPopup.open()
        else:
            self.next_screen("newUser")

    def user_login_process(self):
        """
        connects the specified user with his name and password
        """
        if self.client.is_logged_in():
            box = BoxLayout(orientation="vertical")

            box.add_widget(Label(text="Error: you are already connected"))
            box.add_widget(
                Button(text="Ok", size_hint=(0.4, 0.4), pos_hint={"x": 0.6}, on_release=self.infoPopup.dismiss))

            self.infoPopup.content = box
            self.infoPopup.open()
        else:
            self.next_screen("userLogin")

    def user_parameters_process(self):
        """
        connects the specified user with his name and password
        """
        if not self.client.is_logged_in():
            box = BoxLayout(orientation="vertical")

            box.add_widget(Label(text="Error: you are not connected"))
            box.add_widget(
                Button(text="Ok", size_hint=(0.4, 0.4), pos_hint={"x": 0.6}, on_release=self.infoPopup.dismiss))

            self.infoPopup.content = box
            self.infoPopup.open()
        else:
            self.next_screen("userAccountsParameters")

    def screen_root(self):
        self.infoPopup.dismiss()
        self.next_screen("root")

    def user_creation(self):
        """
        registers the specified user with his name and password
        """
        self.creationButton.disabled = True

        try:
            self.client.register(self.username.text, self.password.text)
        except CredentialsException as e:
            box = BoxLayout(orientation="vertical")

            box.add_widget(Label(text="Error: " + str(e)))
            box.add_widget(
                Button(text="Ok", size_hint=(0.4, 0.4), pos_hint={"x": 0.6}, on_release=self.infoPopup.dismiss))

            self.infoPopup.content = box
            self.infoPopup.open()
        else:
            box = BoxLayout(orientation="vertical")

            box.add_widget(Label(text="Correctly registered"))
            box.add_widget(
                Button(text="Ok", size_hint=(0.4, 0.4), pos_hint={"x": 0.6}, on_release=lambda _: self.screen_root()))

            self.infoPopup.content = box
            self.infoPopup.open()

        self.creationButton.disabled = False

    def user_login(self):
        """
        connects the specified user with his name and password
        """
        self.loginButton.disabled = True

        try:
            self.client.login(self.username.text, self.password.text)
        except CredentialsException as e:
            box = BoxLayout(orientation="vertical")

            box.add_widget(Label(text="Error: " + str(e)))
            box.add_widget(
                Button(text="Ok", size_hint=(0.4, 0.4), pos_hint={"x": 0.6}, on_release=self.infoPopup.dismiss))

            self.infoPopup.content = box
            self.infoPopup.open()
        else:
            box = BoxLayout(orientation="vertical")

            box.add_widget(Label(text="Correctly login"))
            box.add_widget(
                Button(text="Ok", size_hint=(0.4, 0.4), pos_hint={"x": 0.6}, on_release=lambda _: self.screen_root()))

            self.infoPopup.content = box
            self.infoPopup.open()

        self.loginButton.disabled = False

    def user_parameters(self):
        """
        modification parameters user account for the specified user
        """
        print("VALIDER LES PARAMETRES DE L'UTILISATEUR")

    def get_games(self):
        games = self.client.get_games()
        self.getGame.text = games.keys()[0]

class Phagocyte(App):
    """
    main kivy application
    """

    def build(self):
        """
        this method loads the root.kv file automatically
        """
        self.root = Builder.load_file("kv/root.kv")


if __name__ == '__main__':
    Phagocyte().run()
