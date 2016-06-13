"""
Main configuration for the Phagocyte Application
"""

from kivy.config import Config

from phagocyte_frontend.views.screens.statistics import StatisticsScreen


Config.set('input', 'mouse', 'mouse, multitouch_on_demand')


from kivy.app import App

from phagocyte_frontend.views.screens import PhagocyteScreenManager
from phagocyte_frontend.views.screens.creation import CreateGameScreen
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
    def __init__(self, config_parser, **kwargs):
        super().__init__(**kwargs)
        self.config_parser = config_parser

    def build(self) -> PhagocyteScreenManager:
        """
        Load all needed screens into the screen manager

        :return: the screen manager
        """
        screen_manager = PhagocyteScreenManager(self.config_parser)
        screen_manager.add_widget(LobbyScreen())
        screen_manager.add_widget(LoginScreen())
        screen_manager.add_widget(RegisterScreen())
        screen_manager.add_widget(ParametersScreen())
        screen_manager.add_widget(GameScreen())
        screen_manager.add_widget(CreateGameScreen())
        screen_manager.add_widget(StatisticsScreen())

        return screen_manager
