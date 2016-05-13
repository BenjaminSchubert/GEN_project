from random import randint

from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.scrollview import ScrollView
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty
from kivy.vector import Vector
from kivy.clock import Clock
from kivy.logger import Logger


class MainPlayer(Widget):
    def move(self):
        if Window.mouse_pos[0] < (Window.width / 4) - 100:
            x = -10
        elif Window.mouse_pos[0] > (Window.width / 4) + 100:
            x = 10
        else:
            x = -(((Window.width / 4) - Window.mouse_pos[0]) / 10)

        if Window.mouse_pos[1] < (Window.height / 4) - 100:
            y = -10
        elif Window.mouse_pos[1] > (Window.height / 4) + 100:
            y = 10
        else:
            y = -(((Window.height / 4) - Window.mouse_pos[1]) / 10)

        self.pos = Vector(x, y) + self.pos

    def set_random_pos(self):
        self.x = randint(2000, 5000)
        self.y = randint(2000, 5000)


class Food(Widget):
    def __init__(self, x, y, **kwargs):
        super().__init__(**kwargs)
        self.x = x
        self.y = y
        Clock.schedule_interval(self.shake, 1.0 / 60.0)

    def shake(self, dt):
        self.x += randint(-5, 5)
        self.y += randint(-5, 5)


class Game(Widget):
    main_player = ObjectProperty(None)

    def add_food(self, nb):
        for i in range(nb):
            self.add_widget(Food(randint(self.x, self.width + self.x), randint(self.y, self.height + self.y)))


class Background(Widget):
    pass


class MainCam(Widget):
    game = ObjectProperty(None)
    camera = ObjectProperty(None)
    background = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.game.add_food(100)
        Clock.schedule_interval(self.follow_main_player, 1.0 / 60.0)
        self.game.main_player.set_random_pos()

    def follow_main_player(self, dt):
        self.game.main_player.move()
        self.camera.scroll_x = ((self.game.main_player.center_x) / self.background.width)
        self.camera.scroll_y = ((self.game.main_player.center_y) / self.background.height)


class GameApp(App):
    def build(self):
        Builder.load_file('kv/game.kv')
        return MainCam()


if __name__ == '__main__':
    GameApp().run()