from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.widget import Widget
from random import randint


class BoundedMixin:
    """
    Limit the player to the edge of the map
    """
    position_x = 0
    position_y = 0

    delta_x = 0
    delta_y = 0

    def set_position(self, x, y):
        old_x = self.position_x
        old_y = self.position_y

        self.position_x = max(min(x, self.parent.size[0] - self.size[0]), 0)
        self.position_y = max(min(y, self.parent.size[1] - self.size[1]), 0)

        self.x = self.position_x + self.get_parent_window().size[0] / 2
        self.y = self.position_y + self.get_parent_window().size[1] / 2

        self.delta_x += self.position_x - old_x
        self.delta_y += self.position_y - old_y

    def add_position(self, x, y):
        self.set_position(x + self.position_x, y + self.position_y)


class Player(Widget, BoundedMixin):
    pass


class MainPlayer(Player):
    MAX_SPEED = 10

    def move(self):
        """
        Let the main player move
        """
        def get_speed(pos, center, max_speed=self.MAX_SPEED):
            """
            Get the direction of the mouse from the center point
            from that point calculate de distance like :
            distance from the center point to the pos if it's smaller than
            max_speed

            :param pos: x or y
            :param center: center point to calculate speed from
            :param max_speed: the maximum speed of the player
            :return: the speed
            """
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
    """
    The food let the player grow
    """
    def __init__(self, x, y, **kwargs):
        super().__init__(**kwargs)
        self.x = x
        self.y = y


class World(Widget):
    players = {}

    def add_food(self, nb):
        for i in range(nb):
            self.add_widget(Food(randint(self.x, self.width + self.x), randint(self.y, self.height + self.y)))


class GameInstance(Widget):
    """
    The instance of the game displayed by the game manager
    """

    REFRESH_RATE = 1 / 60

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.server = None

        # TODO remove
        self.world.add_food(100)

    def follow_main_player(self, dt):
        """
        Makes the camera follow the player

        :param dt: date time of the schedule_interval
        """

        self.world.main_player.move()

        x, y = self.camera.convert_distance_to_scroll(
            self.world.main_player.center_x - 400,
            self.world.main_player.center_y - 300
        )
        self.camera.scroll_x = x
        self.camera.scroll_y = y

    def send_moves(self, dt):
        self.server.send_state((self.world.main_player.delta_x, self.world.main_player.delta_y))
        self.world.main_player.delta_x = 0
        self.world.main_player.delta_y = 0

    def start_game(self, server, data):
        self.server = server
        self.world.size = (data["max_x"], data["max_y"])
        self.world.main_player.set_position(*data["position"])
        # FIXME : change color
        self.start_timers()

    def start_timers(self):
        Clock.schedule_interval(self.follow_main_player, 1 / 60)
        Clock.schedule_interval(self.send_moves, 1 / 20)

    def update_state(self, states):
        for state in states:
            if state["name"] == self.server.name:
                self.world.main_player.set_position(*state["position"])
            elif state["name"] in self.world.players.keys():
                p = self.world.players[state["name"]]
                p.set_position(*state["position"])
            else:
                p = Player()
                self.world.add_widget(p)
                p.set_position(*state["position"])
                self.world.players[state["name"]] = p
