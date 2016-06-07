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


class WinPopup(Popup):
    def __init__(self, main_menu_call, **kwargs):
        super().__init__(**kwargs)
        self.main_menu_button.on_release = self.dismiss
        self.on_dismiss = main_menu_call


class GameScreen(AutoLoadableScreen):
    """
    Screen where the game will be played
    """
    screen_name = "game"

    def __init__(self, **kw):
        super().__init__(**kw)
        self.game_instance = None
        self.death_popup = DeathPopup(self.main_menu, self.restart)
        self.win_popup = WinPopup(self.main_menu)

    def setup_game(self):
        game = self.manager.get_screen(LobbyScreen.screen_name).game_list.selection[0]

        self.game_instance = GameInstance()
        REACTOR.listenUDP(0, NetworkGameClient(game.ip, game.port, self.manager.client.token, self.game_instance))

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
        self.death_popup.open()

    def player_won(self, name, main=True):
        if main:
            self.win_popup.text = "You won, congrats !"
        else:
            self.win_popup.text = "You lost, {name} won, sorry !".format(name=name)

        self.win_popup.open()

    def main_menu(self):
        self.death_popup.dismiss()
        self.manager.current = LobbyScreen.screen_name

    def restart(self):
        self.death_popup.dismiss()
        self.reset_game()
        self.setup_game()
