"""
Package containing the lobby screen
"""

from kivy.adapters.dictadapter import DictAdapter
from kivy.logger import Logger
from kivy.properties import Clock
from kivy.uix.listview import ListItemButton
from requests import exceptions

from phagocyte_frontend import CreateGameScreen
from phagocyte_frontend.views.screens import AutoLoadableScreen
from phagocyte_frontend.views.screens.login import LoginScreen
from phagocyte_frontend.views.screens.parameters import ParametersScreen
from phagocyte_frontend.views.screens.register import RegisterScreen
from phagocyte_frontend.views.screens.statistics import StatisticsScreen


__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


class GameListItemButton(ListItemButton):
    """
    Get the list of game servers

    :param ip: ip of the server
    :param port: port of the server
    :param kwargs: additional arguments
    """
    def __init__(self, ip: str, port: int, **kwargs):
        super().__init__(**kwargs)
        self.ip = ip
        self.port = port

    # noinspection PyUnusedLocal
    @classmethod
    def display_converter(cls, row_index, entry):
        """
        display a game server information

        :param row_index: index of the server
        :param entry: values
        """
        return {
            "text": entry["name"],
            "size_hint_y": None,
            "height": 30,
            "ip": entry["ip"],
            "port": entry["port"]
        }


class LobbyScreen(AutoLoadableScreen):
    """
    The main lobby screen

    :param kwargs: additional keyword arguments
    """
    screen_name = "lobby"

    game_list = DictAdapter(
        data={}, cls=GameListItemButton, args_converter=GameListItemButton.display_converter,
        allow_empty_selection=False
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # update the game list instantly (next frame)
        Clock.schedule_once(self.update_game_list)
        # update the game list every 5 seconds
        Clock.schedule_interval(self.update_game_list, 5)

    def update_game_list(self, _):
        """
        Updates the game list.

        :param _: unused argument
        """
        try:
            self.game_list.data = self.manager.client.get_games()
        except exceptions.ConnectionError:
            self.manager.warn("Cannot connect to server", title="Error")
            Logger.error("Cannot connect to server")

    def user_login_process(self):
        """
        connects the specified user with his name and password
        """
        if self.manager.client.is_logged_in():
            self.manager.warn("You are already connected", title="Error")
        else:
            self.manager.current = LoginScreen.screen_name

    def game_creation_process(self):
        """
        create a new game
        """
        if not self.manager.client.is_logged_in():
            self.manager.warn("You need to be connected", title="Error")
        else:
            self.manager.current = CreateGameScreen.screen_name

    def user_creation_process(self):
        """
        registers the specified user with his name and password
        """
        if self.manager.client.is_logged_in():
            self.manager.warn("You are already connected", title="Error")
        else:
            self.manager.current = RegisterScreen.screen_name

    def user_parameters_process(self):
        """
        connects the specified user with his name and password
        """
        if not self.manager.client.is_logged_in():
            self.manager.warn("You need to be connected", title="Error")
        else:
            self.manager.current = ParametersScreen.screen_name

    def user_statistics_process(self):
        """
        shows the user's statistics
        """
        if not self.manager.client.is_logged_in():
            self.manager.warn("You need to be connected", title="Error")
        else:
            self.manager.current = StatisticsScreen.screen_name

    def play(self):
        """
        moves the player to the game
        """
        self.manager.current = "game"
