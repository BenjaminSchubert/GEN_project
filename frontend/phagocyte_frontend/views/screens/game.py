#!/usr/bin/python3
# -*- coding: utf-8 -*-

from phagocyte_frontend.network.game import NetworkGameClient, REACTOR
from phagocyte_frontend.views.game import GameInstance
from phagocyte_frontend.views.screens import AutoLoadableScreen
from phagocyte_frontend.views.screens.lobby import LobbyScreen


__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


class GameScreen(AutoLoadableScreen):
    """
    Screen where the game will be played
    """
    screen_name = "game"

    def __init__(self, **kw):
        super().__init__(**kw)
        self.game_instance = None

    def on_pre_enter(self):
        """
        Define the state of the game screen before you enter it
        """
        # gets the server selected by the user
        game = self.manager.get_screen(LobbyScreen.screen_name).game_list.selection[0]

        self.game_instance = GameInstance()
        network_server = NetworkGameClient(game.ip, game.port, self.manager.client.token, self.game_instance)
        REACTOR.listenUDP(0, network_server)
        self.game_instance.register_game_server(network_server)
        self.add_widget(self.game_instance)

    def on_leave(self, *args):
        """
        Define the state of the game screen on leave
        """
        # remove the game instance
        self.clear_widgets()
        self.game_instance = None
        # stop the server connection
        REACTOR.stop()

