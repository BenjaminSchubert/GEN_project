#!/usr/bin/python3

from kivy.app import App

from phagocyte_frontend.views.screens import PhagocyteScreenManager
from phagocyte_frontend.views.screens.game import GameScreen
from phagocyte_frontend.views.screens.lobby import LobbyScreen
from phagocyte_frontend.views.screens.login import LoginScreen
from phagocyte_frontend.views.screens.parameters import ParametersScreen
from phagocyte_frontend.views.screens.register import RegisterScreen


__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


class Phagocyte(App):
    """
    main kivy application
    """
    def build(self):
        screen_manager = PhagocyteScreenManager()
        screen_manager.add_widget(LobbyScreen())
        screen_manager.add_widget(LoginScreen())
        screen_manager.add_widget(RegisterScreen())
        screen_manager.add_widget(ParametersScreen())
        screen_manager.add_widget(GameScreen())

        return screen_manager
