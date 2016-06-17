"""
Module containing the screen for the game
"""

from kivy.uix.popup import Popup

from phagocyte_frontend.network.game import NetworkGameClient, REACTOR
from phagocyte_frontend.views.game import GameInstance
from phagocyte_frontend.views.screens import AutoLoadableScreen
from phagocyte_frontend.views.screens.lobby import LobbyScreen


__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


class DeathPopup(Popup):
    """
    Popup fired on the death of the player

    :param main_menu_call: callback to move to the main menu
    :param restart_call: callback to restart the game
    :param kwargs: additional arguments
    """
    def __init__(self, main_menu_call: callable, restart_call: callable, **kwargs):
        super().__init__(**kwargs)
        self.main_menu_button.on_release = main_menu_call
        self.restart_button.on_release = restart_call


class WinPopup(Popup):
    """
    Popup fired when a player has won

    :param main_menu_call: callback to move to the main menu
    :param kwargs: additional arguments
    """
    def __init__(self, main_menu_call: callable, **kwargs):
        super().__init__(**kwargs)
        self.main_menu_button.on_release = self.dismiss
        self.on_dismiss = main_menu_call


class GameScreen(AutoLoadableScreen):
    """
    Screen where the game will be played

    :param kwargs: additional arguments
    """
    screen_name = "game"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game_instance = None
        self.death_popup = DeathPopup(self.main_menu, self.restart)
        self.win_popup = WinPopup(self.main_menu)

    def setup_game(self):
        """
        Prepares and launch the game
        """
        game = self.manager.get_screen(LobbyScreen.screen_name).game_list.selection[0]

        self.game_instance = GameInstance()
        REACTOR.listenUDP(0, NetworkGameClient(game.ip, game.port, self.manager.client, self.game_instance))

        self.add_widget(self.game_instance)

    def reset_game(self):
        """
        Resets the state of the game
        """
        self.clear_widgets()
        self.game_instance = None
        # noinspection PyUnresolvedReferences
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
        """
        Event to be called when the player died
        """
        self.death_popup.open()

    def player_won(self, name: str, main: bool=True):
        """
        Event to be called when a player won

        :param name: name of the player that won
        :param main: True if the player that won is the one player on this program
        """
        if main:
            self.win_popup.text = "You won, congrats !"
        else:
            self.win_popup.text = "You lost, {name} won, sorry !".format(name=name)

        self.win_popup.open()

    def main_menu(self):
        """
        Returns to the main menu
        """
        self.death_popup.dismiss()
        self.manager.current = LobbyScreen.screen_name

    def restart(self):
        """
        Restarts the game
        """
        self.death_popup.dismiss()
        self.reset_game()
        self.setup_game()

    def handle_error(self, error: str):
        """
        Event called when an error that cannot be handled happens

        :param error: error message
        """
        self.manager.warn(error, title="Error", callback=self.manager.main_screen)
