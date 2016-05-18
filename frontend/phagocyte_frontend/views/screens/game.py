#!/usr/bin/python3
# -*- coding: utf-8 -*-
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen

from phagocyte_frontend.network.game import NetworkGameClient, REACTOR
from phagocyte_frontend.views.game import GameInstance
from phagocyte_frontend.views.screens.lobby import LobbyScreen


__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


class GameScreen(Screen):
    def __init__(self, **kw):
        Builder.load_file('kv/game.kv')
        super().__init__(**kw)
        self.name = "game"
        self.game_instance = None

    def on_pre_enter(self):
        game = self.manager.get_screen(LobbyScreen.screen_name).game_list.selection[0]

        self.game_instance = GameInstance()
        network_server = NetworkGameClient(game.ip, game.port, self.manager.client.token, self.game_instance)
        REACTOR.listenUDP(0, network_server)

        self.game_instance.register_game_server(network_server)
        self.add_widget(self.game_instance)

    def on_leave(self, *args):
        self.clear_widgets()
        REACTOR.stop()
        self.game_instance = None

