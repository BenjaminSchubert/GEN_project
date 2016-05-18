#!/usr/bin/env python3

from phagocyte_frontend.screens import AutoLoadableScreen
from phagocyte_frontend.screens.login import LoginScreen
from phagocyte_frontend.screens.parameters import ParametersScreen
from phagocyte_frontend.screens.register import RegisterScreen


__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


class LobbyScreen(AutoLoadableScreen):
    screen_name = "lobby"

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
