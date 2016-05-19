from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics.context_instructions import Color
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex


class BoundedMixin:
    """
    Limit the player to the edge of the map
    """
    position_x = 0
    position_y = 0

    correction_x = 0
    correction_y = 0

    def set_position(self, x, y):
        self.correction_x /= 2
        self.correction_y /= 2

        self.position_x = max(min(x + self.correction_x, self.parent.size[0] - self.size[0]), 0)
        self.position_y = max(min(y + self.correction_y, self.parent.size[1] - self.size[1]), 0)

        self.x = self.position_x + Window.size[0] / 2
        self.y = self.position_y + Window.size[1] / 2

    def add_position(self, x, y):
        self.set_position(x + self.position_x, y + self.position_y)


class Player(Widget, BoundedMixin):
    def set_size(self, size):
        self.size = size, size

    def set_color(self, color):
        r, g, b, a = get_color_from_hex(color)
        for i in self.canvas.get_group(None):
            if type(i) is Color:
                i.r = r
                i.g = g
                i.b = b
                i.a = a
                break


class MainPlayer(Player):
    MAX_SPEED = 10

    def move(self, dt):
        def get_speed(pos, center, max_speed=self.MAX_SPEED):
            ds = 200 * dt
            if pos < center:
                return max(-max_speed, (pos - center) / ds)
            else:
                return min((pos - center) / ds, max_speed)

        m_x, m_y = Window.mouse_pos

        x = get_speed(m_x, Window.width / 2)
        y = get_speed(m_y, Window.height / 2)

        self.add_position(x, y)


class Food(Widget, BoundedMixin):
    """
    The food let the player grow
    """


class World(Widget):
    players = {}
    food = {}

    def add_food(self, x, y, size):
        food = Food(size=(size, size))
        self.food[(x, y)] = food
        self.add_widget(food)
        food.set_position(x, y)


class GameInstance(Widget):
    """
    The instance of the game displayed by the game manager
    """
    REFRESH_RATE = 1 / 60
    SCALE_RATIO = 1 / 2
    server = None

    def follow_main_player(self, dt):
        """
        Makes the camera follow the player

        :param dt: date time of the schedule_interval
        """
        self.world.main_player.move(dt)

        # FIXME : this could be done better
        self.map.scale = self.SCALE_RATIO

        x, y = self.camera.convert_distance_to_scroll(
            self.world.main_player.center_x * self.map.scale - Window.width / 2,
            self.world.main_player.center_y * self.map.scale - Window.height / 2
        )
        self.camera.scroll_x = x
        self.camera.scroll_y = y

    def send_moves(self, dt):
        self.server.send_state((
            self.world.main_player.center_x - Window.width / 2,
            self.world.main_player.center_y - Window.height / 2
        ))

    def start_game(self, server, data):
        self.server = server
        self.world.size = (data["max_x"], data["max_y"])
        self.world.main_player.set_position(*data["position"])
        self.world.main_player.set_color(data["color"])
        self.start_timers()

    def start_timers(self):
        Clock.schedule_interval(self.follow_main_player, self.REFRESH_RATE)
        Clock.schedule_interval(self.send_moves, self.REFRESH_RATE)

    def update_state(self, states):
        # FIXME update size
        for state in states:
            if state["name"] == self.server.name:
                if state.get("dirty", None):
                    self.world.main_player.correction_x += state["dirty"][0]
                    self.world.main_player.correction_y += state["dirty"][1]

            elif state["name"] in self.world.players.keys():
                p = self.world.players[state["name"]]
                p.set_position(
                    state["position"][0] - p.size[0] / 2,
                    state["position"][1] - p.size[1] / 2
                )

            else:
                p = Player()
                self.world.add_widget(p)
                p.set_position(*state["position"])
                self.world.players[state["name"]] = p

    def update_food(self, new, old):
        if new is not None:
            self.world.add_food(new["x"], new["y"], new["size"])

    def check_food(self, food):
        for entry in food:
            if (entry["x"], entry["y"]) not in self.world.food.keys():
                self.world.add_food(entry["x"], entry["y"], entry["size"])
