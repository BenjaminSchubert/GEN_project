# !/usr/bin/env python3

"""
Application that just represents a GUI for connection and creating a user.
Container Example
This example shows how to add a container to our screen.
A container is simply an empty place on the screen which
could be filled with any other content from a .kv file.
"""

import kivy
from kivy.app import App
from kivy.config import Config
from kivy.lang import Builder
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.widget import Widget


Config.set("graphics", "resizable", False)
Config.set("graphics", "width", "1200")
Config.set("graphics", "height", "700")

kivy.require('1.0.7')


class LobbyApp(BoxLayout, GridLayout, Widget):
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
    screen_manager = None

    def __init__(self, screen_manager, **kwargs):
        super().__init__(**kwargs)
        self.screen_manager = screen_manager

    def follow_main_player(self, dt):
        self.game.main_player.move()
        self.camera.scroll_x = ((self.game.main_player.center_x) / self.background.width)
        self.camera.scroll_y = ((self.game.main_player.center_y) / self.background.height)

    def screen_lobby(self):
        self.infoPopup.dismiss()
        self.next_screen("lobby")


    def get_games(self):
        try:
            games = self.client.get_games()
        except Exception as e:
            print(e)
        print(games)
        try:
            self.getGame.text = games["Main"]["name"]
        except Exception as e:
            print(e)
        self.client.join_game(games["Main"]["ip"], games["Main"]["port"], self)
