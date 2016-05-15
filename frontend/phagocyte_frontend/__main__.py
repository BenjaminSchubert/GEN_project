from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from phagocyte_frontend.lobbyapp import Lobby
from phagocyte_frontend.gameapp import GameApp


class LobbyScreen(Screen):
    pass


class GameScreen(Screen):
    pass


screen_manager = ScreenManager()
lobby_screen = LobbyScreen(name="Lobby")
game_screen = GameScreen(name="Game")
lobby_screen.add_widget(Lobby().get_instance("lobby", screen_manager))
game_screen.add_widget(GameApp().get_instance(screen_manager))
screen_manager.add_widget(lobby_screen)
screen_manager.add_widget(game_screen)


class Phagocyte(App):
    """
    main kivy application
    """

    def build(self):
        return screen_manager


if __name__ == '__main__':
    Phagocyte().run()
