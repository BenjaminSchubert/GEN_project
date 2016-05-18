from kivy.app import App
from kivy.uix.screenmanager import Screen

from phagocyte_frontend.screens import PhagocyteScreenManager
from phagocyte_frontend.screens.lobby import LobbyScreen
from phagocyte_frontend.screens.login import LoginScreen
from phagocyte_frontend.screens.parameters import ParametersScreen
from phagocyte_frontend.screens.register import RegisterScreen


class GameScreen(Screen):
    pass


#screen_manager = ScreenManager()
#game_screen = GameScreen(name="Game")
#lobby_screen.add_widget(Lobby().get_instance("lobby", screen_manager))
#game_screen.add_widget(GameApp().get_instance(screen_manager))
#screen_manager.add_widget(lobby_screen)
#screen_manager.add_widget(game_screen)


class Phagocyte(App):
    """
    main kivy application
    """
    def build(self):
        screen_manager = PhagocyteScreenManager()
        screen_manager.add_widget(LobbyScreen())
        screen_manager.add_widget(LoginScreen())
        screen_manager.add_widget(RegisterScreen())
        screen_manager.add_widget(ParametersScreen())
        return screen_manager


if __name__ == '__main__':
    Phagocyte().run()
