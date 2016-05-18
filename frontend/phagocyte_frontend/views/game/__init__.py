from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.widget import Widget
from random import randint


class BoundedMixin:
    position_x = 0
    position_y = 0

    def set_position(self, x, y):
        self.position_x = max(min(x, self.parent.size[0] - self.size[0]), 0)
        self.position_y = max(min(y, self.parent.size[1] - self.size[1]), 0)

        self.x = self.position_x + self.get_parent_window().size[0] / 2
        self.y = self.position_y + self.get_parent_window().size[1] / 2

    def add_position(self, x, y):
        self.set_position(x + self.position_x, y + self.position_y)


class MainPlayer(Widget, BoundedMixin):
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

        self.add_position(x, y)


class Food(Widget):
    def __init__(self, x, y, **kwargs):
        super().__init__(**kwargs)
        self.x = x
        self.y = y
        Clock.schedule_interval(self.shake, 1.0 / 60.0)

    def shake(self, dt):
        self.x += randint(-5, 5)
        self.y += randint(-5, 5)


class World(Widget):
    def add_food(self, nb):
        for i in range(nb):
            self.add_widget(Food(randint(self.x, self.width + self.x), randint(self.y, self.height + self.y)))


class GameInstance(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.server = None
        self.world.add_food(100)

    def follow_main_player(self, dt):
        self.world.main_player.move()
        x, y = self.camera.convert_distance_to_scroll(
            self.world.main_player.center_x - 400,
            self.world.main_player.center_y - 300
        )

        self.camera.scroll_x = x
        self.camera.scroll_y = y

    def register_game_server(self, server):
        self.server = server
        Clock.schedule_interval(self.follow_main_player, 1 / 60)
