import enum
from math import atan2

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics.context_instructions import Color
from kivy.properties import NumericProperty
from kivy.uix.progressbar import ProgressBar
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex


@enum.unique
class BonusTypes(enum.IntEnum):
    """
    Represents each bonus types a user can obtain
    """
    SHIELD = 0
    POWERUP = 1
    GROWTH = 2
    SPEEDUP = 3


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


class Player(Widget, BoundedMixin):
    """

    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.shield = Shield()
        self.hook_graphic = Hook()
        self.bonus = None
        self.hook = None

    def set_bonus(self, bonus: int):
        if self.bonus == bonus:
            return
        elif self.bonus == BonusTypes.SHIELD:
            self.remove_widget(self.shield)

        if bonus == BonusTypes.SHIELD:
            self.add_widget(self.shield)

        self.bonus = bonus

    def set_hook(self, hook):
        if hook is None and self.hook is None:
            return

        elif hook is None:
            self.remove_widget(self.hook)
            self.hook = None

        elif self.hook is None:
            self.hook = Hook()
            self.hook.points = [
                self.center_x, self.center_y,
                Window.size[0] / 2 + hook["x"], Window.size[1] / 2 + hook["y"]
            ]
            self.add_widget(self.hook)

        else:
            self.hook.points[2] = hook["x"] + Window.size[0] / 2
            self.hook.points[3] = hook["y"] + Window.size[1] / 2

    def set_position(self, x, y):
        super().set_position(x, y)
        self.shield.center = self.center
        if self.hook:
            self.hook.points[0] = self.center_x
            self.hook.points[1] = self.center_y

    def set_size(self, size):
        super().set_size(size)
        self.shield.width = self.width * 1.3
        self.shield.height = self.height * 1.3

    def set_color(self, color):
        super().set_color(color)
        r, g, b, a = get_color_from_hex(color)
        for i in self.shield.canvas.get_group(None):
            if type(i) is Color:
                i.r = r
                i.g = g
                i.b = b
                i.a = a * 0.6
                break


class MainPlayer(Player):
    initial_size = NumericProperty(0)
    max_speed = None
    shooting = False
    bonus_speedup = 1
    speed_x = speed_y = 0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down, on_key_up=self._on_keyboard_up)

    def _keyboard_closed(self):
        """
        Unbind the keyboard from the system
        """
        self._keyboard.unbind(on_key_down=self._on_keyboard_down, on_key_up=self._on_keyboard_up)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, *args):
        """
        Event called when a key is pressed

        :param keyboard: the keyboard interface
        :param keycode: the keycode of the pressed key
        :param args: eventual additional args
        :return: True to accept the key
        """
        if keycode[1] == "up" or keycode[1] == "w":
            self.speed_x = 1
        elif keycode[1] == "down" or keycode[1] == "s":
            self.speed_x = -1
        elif keycode[1] == "left" or keycode[1] == "a":
            self.speed_y = -1
        elif keycode[1] == "right" or keycode[1] == "d":
            self.speed_y = 1

        return True

    def _on_keyboard_up(self, keyboard, keycode, *args):
        """
        Event called when a key is released

        :param keyboard: the keyboard interface
        :param keycode: the keycode of the released key
        :param args: eventual additional args
        :return: True to accept the key
        """
        if keycode[1] == "up" or keycode[1] == "w":
            self.speed_x = 0
        elif keycode[1] == "down" or keycode[1] == "s":
            self.speed_x = 0
        elif keycode[1] == "left" or keycode[1] == "a":
            self.speed_y = 0
        elif keycode[1] == "right" or keycode[1] == "d":
            self.speed_y = 0

        return True

    def release_keyboard(self):
        """
        We the player died, we must release the keyboard
        """
        self._keyboard.release()

    def set_size(self, size):
        super().set_size(size)
        self.set_max_speed()

    def set_max_speed(self):
        self.max_speed = self.bonus_speedup * 50 * self.initial_size / self.size[0] ** 0.5

    def move(self, dt):
        self.add_position(
            self.max_speed * self.speed_y * dt,
            self.max_speed * self.speed_x * dt
        )

    def set_bonus(self, bonus: int):
        super().set_bonus(bonus)

        if bonus == BonusTypes.SPEEDUP:
            self.bonus_speedup = 1.5
        else:
            self.bonus_speedup = 1

        self.set_max_speed()


class Food(Widget, BoundedMixin):
    """
    The food let the player grow
    """


class Bonus(Widget, BoundedMixin):
    """
    A bonus a user can pick
    """


class Shield(Widget):
    """
    The bonus shield
    """


class Hook(Widget):
    """
    the hook a user can use to grab another user
    """


class Bullet(Widget, BoundedMixin):
    """
    A bullet thrown by a player
    """

    def __init__(self, uid, speed_x, speed_y, **kwargs):
        super().__init__(**kwargs)
        self._id = uid
        self.speed_x = speed_x
        self.speed_y = speed_y


class HealthBar(ProgressBar):
    """
    A bar that represents the health of the player
    """


class World(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.players = {}
        self.food = {}
        self.bullets = {}
        self.bonuses = {}

    def add_food(self, x, y, size):
        food = Food(size=(size, size))
        self.food[(x, y)] = food
        self.add_widget(food)
        food.set_position(x, y)

    def add_bullet(self, uid, x, y, speed_x, speed_y, color, size):
        if self.bullets.get(uid) is None:
            self.bullets[uid] = Bullet(uid, speed_x, speed_y)
            self.bullets[uid].set_color(color)
            self.bullets[uid].set_size(size)
            self.add_widget(self.bullets[uid])
        self.bullets[uid].set_position(x, y)

    def add_bonus(self, x, y, size):
        bonus = Bonus(size=(size, size))
        self.add_widget(bonus)
        self.bonuses[(x, y)] = bonus
        bonus.set_position(x, y)

    def remove_bonus(self, x, y):
        b = self.bonuses.pop((x, y), None)
        if b:
            self.remove_widget(b)

    def remove_food(self, x, y):
        f = self.food.pop((x, y), None)
        if f:
            self.remove_widget(f)

    def remove_bullet(self, id):
        b = self.bullets.pop(id, None)
        if b:
            self.remove_widget(b)


class GameInstance(Widget):
    """
    The instance of the game displayed by the game manager
    """
    REFRESH_RATE = 1 / 60
    SCALE_RATIO = 8  # >= 1
    MAX_SIZE = 1000
    scale_ratio_util = None
    server = None

    def move_main_player(self, dt):
        self.world.main_player.move(dt)
        self.follow_main_player()

    def follow_main_player(self):
        """
        Makes the camera follow the player
        """
        self.map.scale = self.SCALE_RATIO / (self.world.main_player.width + self.scale_ratio_util) ** .5

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

    def send_bullets(self, dt):
        if self.world.main_player.shooting:
            m_x, m_y = Window.mouse_pos
            self.server.send_bullet(atan2(m_x - Window.width / 2, m_y - Window.height / 2))

    def start_game(self, server, data):
        self.server = server

        self.world.size = (data["max_x"], data["max_y"])

        self.world.main_player.set_position(data["x"], data["y"])
        self.world.main_player.set_color(data["color"])

        self.world.main_player.initial_size = data["size"]
        self.world.main_player.set_size(data["size"])
        self.scale_ratio_util = self.SCALE_RATIO ** 2 - data["size"]

        Window.bind(on_resize=self.redraw, on_mouse_down=self._on_mouse_down, on_mouse_up=self._on_mouse_up)

        self.start_timers()

    def start_timers(self):
        Clock.schedule_interval(self.move_main_player, self.REFRESH_RATE)
        Clock.schedule_interval(self.send_moves, self.REFRESH_RATE)
        Clock.schedule_interval(self.send_bullets, self.REFRESH_RATE)
        Clock.schedule_interval(self.move_bullets, self.REFRESH_RATE)

    def update_state(self, states):
        for state in states:
            if state["name"] == self.server.name:
                if state.get("dirty", None):
                    self.world.main_player.correction_x += state["dirty"][0]
                    self.world.main_player.correction_y += state["dirty"][1]
                self.world.main_player.set_size(state["size"])
                self.world.main_player.set_bonus(state["bonus"])
                self.world.main_player.set_hook(state["hook"])

            elif state["name"] in self.world.players.keys():
                p = self.world.players[state["name"]]
                p.set_position(
                    state["x"] - p.size[0] / 2,
                    state["y"] - p.size[1] / 2
                )
                p.set_size(state["size"])
                p.set_bonus(state.get("bonus", None))
                p.set_hook(state["hook"])

            else:
                p = Player()
                self.world.add_widget(p)
                p.set_size(state["size"])
                p.set_position(state["x"], state["y"])
                p.set_color(state["color"])
                self.world.players[state["name"]] = p

        names = set(state["name"] for state in states)
        keys = set(self.world.players.keys())
        keys -= names

        for key in keys:
            to_remove = self.world.players.pop(key)
            self.world.remove_widget(to_remove)

    def update_food(self, new, deleted):
        for entry in new:
            if (entry["x"], entry["y"]) not in self.world.food.keys():
                self.world.add_food(entry["x"], entry["y"], entry["size"])

        for entry in deleted:
            self.world.remove_food(entry["x"], entry["y"])

    def update_bonus(self, new, deleted):
        for entry in new:
            if (entry["x"], entry["y"]) not in self.world.bonuses.keys():
                self.world.add_bonus(entry["x"], entry["y"], entry["size"])

        for entry in deleted:
            self.world.remove_bonus(entry["x"], entry["y"])

    def move_bullets(self, dt):
        to_remove = []

        world_size_x = self.world.size[0]
        world_size_y = self.world.size[1]

        for bullet in self.world.bullets.values():
            bullet.add_position(bullet.speed_x * dt, bullet.speed_y * dt)
            if (
                    bullet.position_x == 0 or bullet.position_y == 0 or
                    bullet.position_x + bullet.size[0] == world_size_x or
                    bullet.position_y + bullet.size[1] == world_size_y
            ):
                to_remove.append(bullet._id)

        for bid in to_remove:
            self.world.remove_bullet(bid)

    def death(self):
        Clock.unschedule(self.follow_main_player)
        Clock.unschedule(self.send_moves)
        self.world.main_player.release_keyboard()
        self.parent.player_died()

    def redraw(self, *args):
        self.follow_main_player()

        for i in self.world.food.values():
            i.set_position(i.position_x, i.position_y)

    def check_bullets(self, bullets, deleted):
        for bullet in bullets:
            self.world.add_bullet(**bullet)

        for bullet in deleted:
            self.world.remove_bullet(bullet)

    def _on_mouse_down(self, window, x, y, button, modifiers):
        print(dir(self.health_bar))
        if button == "left":
            self.world.main_player.shooting = True
        elif button == "right":
            self.server.send_hook(atan2(x - Window.size[0] / 2, Window.size[1] / 2 - y))

    def _on_mouse_up(self, window, x, y, button, modifiers):
        if button == "left":
            self.world.main_player.shooting = False
