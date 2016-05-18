from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.vector import Vector
from random import randint


class MainPlayer(Widget):
    MAX_SPEED = 10

    def move(self):
        def get_speed(pos, center, max_speed=self.MAX_SPEED):
            if pos < center:
                return max(-max_speed, (pos - center) / 10)
            else:
                return min((pos - center) / 10, max_speed)

        m_x, m_y = Window.mouse_pos
        center_x, center_y = Window.width / 2, Window.height / 2

        x = get_speed(m_x, center_x)
        y = get_speed(m_y, center_y)

        self.pos = Vector(x, y) + self.pos

        return x, y

    def set_random_pos(self):
        self.center_x = randint(2000, 5000)
        self.center_y = randint(2000, 5000)


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
    def add_food(self, nb):
        for i in range(nb):
            self.add_widget(Food(randint(self.x, self.width + self.x), randint(self.y, self.height + self.y)))


class GameInstance(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.server = None
        self.game.add_food(100)
        Clock.schedule_interval(self.follow_main_player, 1.0 / 60.0)
        self.game.main_player.set_random_pos()

        x, y = self.camera.convert_distance_to_scroll(
            -400 + 9800 / 9000 * self.game.main_player.x,
            -300 + 9600 / 9000 * self.game.main_player.y
        )
        print(x, y)
        print(self.game.main_player.pos)
        print(self.game.main_player.center)
        print(self.game.main_player.center_x / 9000)
        self.camera.scroll_x = x
        self.camera.scroll_y = y

    def follow_main_player(self, dt):
        x, y = self.camera.convert_distance_to_scroll(*self.game.main_player.move())
        self.camera.scroll_x += x
        self.camera.scroll_y += y

    def register_game_server(self, server):
        self.server = server
