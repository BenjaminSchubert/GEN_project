#!/usr/bin/env python3
from kivy.uix.popup import Popup

from phagocyte_frontend.network.game import NetworkGameClient, REACTOR
from phagocyte_frontend.views.game import GameInstance
from phagocyte_frontend.views.screens import AutoLoadableScreen
from phagocyte_frontend.views.screens.lobby import LobbyScreen


__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


class DeathPopup(Popup):
    def __init__(self, main_menu_call, restart_call, **kwargs):
        super().__init__(**kwargs)
        self.main_menu_button.on_release = main_menu_call
        self.restart_button.on_release = restart_call


class GameScreen(AutoLoadableScreen):
    """
    Screen where the game will be played
    """
    screen_name = "game"

    def __init__(self, **kw):
        super().__init__(**kw)
        self.game_instance = None
        self.popup = DeathPopup(self.main_menu, self.restart)

    def setup_game(self):
        game = self.manager.get_screen(LobbyScreen.screen_name).game_list.selection[0]

        self.game_instance = GameInstance()
        network_server = NetworkGameClient(game.ip, game.port, self.manager.client.token, self.game_instance)
        REACTOR.listenUDP(0, network_server)

        self.add_widget(self.game_instance)

    def reset_game(self):
        self.clear_widgets()
        self.game_instance = None
        REACTOR.removeAll()

    def on_pre_enter(self):
        """
        Sets up the game state before entering the screen
        """
        self.setup_game()

    def on_leave(self, *args):
        """
        Resets the game state before leaving the screen
        """
        self.reset_game()

    def player_died(self):
        self.popup.open()

    def main_menu(self):
        self.popup.dismiss()
        self.manager.current = LobbyScreen.screen_name

    def restart(self):
        self.popup.dismiss()
        self.reset_game()
        self.setup_game()
