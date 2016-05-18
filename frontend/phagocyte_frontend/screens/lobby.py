#!/usr/bin/env python3

from kivy.adapters.dictadapter import DictAdapter
from kivy.properties import Clock
from kivy.uix.listview import ListItemButton

from phagocyte_frontend.screens import AutoLoadableScreen
from phagocyte_frontend.screens.login import LoginScreen
from phagocyte_frontend.screens.parameters import ParametersScreen
from phagocyte_frontend.screens.register import RegisterScreen


__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


data = [{'text': str(i), 'is_selected': False} for i in range(100)]


def game_list_display_converter(row_index, entry):
    return {
        "text": entry["name"],
        "size_hint_y": None,
        "height": 30
    }


class LobbyScreen(AutoLoadableScreen):
    screen_name = "lobby"

    game_list = DictAdapter(
        data={}, cls=ListItemButton, args_converter=game_list_display_converter,
        allow_empty_selection=False
    )

    def __init__(self, **kw):
        super().__init__(**kw)
        Clock.schedule_once(self.update_game_list)
        Clock.schedule_interval(self.update_game_list, 5)

    def update_game_list(self, _):
        self.game_list.data = self.manager.client.get_games()
        if not self.game_list.selection:
            print(self.game_list.check_for_empty_selection())
            print(dir(self.game_list))

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

        """
        if not self.manager.client.is_logged_in():
            self.manager.warn("You need to be connected", title="Error")
        else:
            # TODO implement
            print("IL FAUT CREER UNE NOUVELLE PARTIE => 'CHANGER' D'ABORD DE FENETRE")

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

    def play(self):
        self.manager.current = "game"
        # TODO join the correct game
        # self.client.join_game(games["Main"]["ip"], games["Main"]["port"], self)
