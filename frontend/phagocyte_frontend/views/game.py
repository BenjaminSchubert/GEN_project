import enum
from math import atan2

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import NumericProperty, ListProperty
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


class BoundedWidget(Widget):
    """
    Limit the player to the edge of the map
    """
    position_x = 0
    position_y = 0

    # noinspection PyArgumentList
    color = ListProperty([0, 0, 0, 0])

    def set_position(self, x, y):
        self.position_x = max(min(x, self.parent.size[0] - self.size[0]), 0)
        self.position_y = max(min(y, self.parent.size[1] - self.size[1]), 0)

        self.x = self.position_x + Window.size[0] / 2
        self.y = self.position_y + Window.size[1] / 2

    def redraw(self):
        self.x = self.position_x + Window.size[0] / 2
        self.y = self.position_y + Window.size[1] / 2

    def add_position(self, x, y):
        self.set_position(x + self.position_x, y + self.position_y)


class Player(BoundedWidget):
    """

    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.shield = Shield(self)
        self.bonus = None
        self.hook = None

    def update(self, size, bonus, hook):
        self.size = size, size
        self.set_bonus(bonus)
        self.set_hook(hook)

    def set_bonus(self, bonus: int):
        if self.bonus == bonus:
            return
        elif self.bonus == BonusTypes.SHIELD:
            self.remove_widget(self.shield)

        if bonus == BonusTypes.SHIELD:
            self.add_widget(self.shield)
            self.shield.center = self.center

        self.bonus = bonus

    def set_hook(self, hook):
        if hook is None and self.hook is None:
            return

        elif hook is None:
            self.remove_widget(self.hook)
            self.hook = None

        elif self.hook is None:
            self.hook = Hook(self)
            self.add_widget(self.hook)

        else:
            self.hook.end_x = hook["x"] + Window.size[0] / 2
            self.hook.end_y = hook["y"] + Window.size[1] / 2


class MainPlayer(Player):
    bonus_speedup = NumericProperty(0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.initial_size = 0
        self.max_speed = 0
        self.correction_x = 0
        self.correction_y = 0
        self.speed_x = 0
        self.speed_y = 0

        self.shooting = False

        self.bind(size=self.set_max_speed, bonus_speedup=self.set_max_speed)
        self.keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self.keyboard.bind(on_key_down=self._on_keyboard_down, on_key_up=self._on_keyboard_up)

    def _keyboard_closed(self):
        """
        Unbind the keyboard from the system
        """
        self.keyboard.unbind(on_key_down=self._on_keyboard_down, on_key_up=self._on_keyboard_up)

    def _on_keyboard_down(self, keyboard, keycode, *args):
        """
        Event called when a key is pressed

        :param keyboard: the keyboard interface
        :param keycode: the keycode of the pressed key
        :param args: eventual additional args
        :return: True to accept the key
        """
        if keycode[1] in ["up", "w"]:
            self.speed_x = 1
        elif keycode[1] in ["down", "s"]:
            self.speed_x = -1
        elif keycode[1] in ["left", "a"]:
            self.speed_y = -1
        elif keycode[1] in ["right", "d"]:
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
        if keycode[1] in ["down", "up", "s", "w"]:
            self.speed_x = 0
        elif keycode[1] in ["left", "right", "a", "d"]:
            self.speed_y = 0

        return True

    def set_position(self, x, y):
        self.correction_x /= 2
        self.correction_y /= 2

        super().set_position(x + self.correction_x, y + self.correction_y)

    def set_max_speed(self, instance, attribute):
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


class Food(BoundedWidget):
    """
    The food let the player grow
    """
    color = [0, 1, 0, 1]


class Bonus(BoundedWidget):
    """
    A bonus a user can pick
    """
    color = [1, 1, 0, 1]


class Shield(Widget):
    """
    The bonus shield
    """
    def __init__(self, player, **kwargs):
        self.player = player
        super().__init__(**kwargs)


class Hook(Widget):
    """
    the hook a user can use to grab another user
    """
    def __init__(self, player, **kwargs):
        self.player = player
        self.end_x = self.player.center_x
        self.end_y = self.player.center_y

        super().__init__(**kwargs)


class Bullet(BoundedWidget):
    """
    A bullet thrown by a player
    """

    def __init__(self, uid, speed_x, speed_y, **kwargs):
        super().__init__(**kwargs)
        self.bid = uid
        self.speed_x = speed_x
        self.speed_y = speed_y


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
            self.bullets[uid] = Bullet(uid, speed_x, speed_y, size=(size, size), color=get_color_from_hex(color))
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
    scale_ratio_util = NumericProperty(0)
    server = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.world.main_player.bind(center=self.follow_main_player)

    def move_main_player(self, dt):
        self.world.main_player.move(dt)

    def follow_main_player(self, instance, attribute):
        """
        Makes the camera follow the player
        """
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
        self.world.main_player.color = get_color_from_hex(data["color"])

        self.world.main_player.initial_size = data["size"]
        self.world.main_player.size = data["size"], data["size"]
        self.scale_ratio_util = self.SCALE_RATIO ** 2 - data["size"]
        self.follow_main_player(self.world.main_player, None)

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

                player = self.world.main_player

            elif state["name"] in self.world.players.keys():
                player = self.world.players[state["name"]]
                player.set_position(state["x"] - player.size[0] / 2, state["y"] - player.size[1] / 2)

            else:
                player = Player()
                self.world.add_widget(player)
                self.world.players[state["name"]] = player

            player.update(state["size"], state["bonus"], state["hook"])

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
                to_remove.append(bullet.bid)

        for bid in to_remove:
            self.world.remove_bullet(bid)

    def death(self):
        Clock.unschedule(self.move_main_player)
        Clock.unschedule(self.send_moves)
        self.world.main_player.keyboard.release()
        self.parent.player_died()

    def redraw(self, *args):
        for static_objects in [self.world.food.values(), self.world.bonuses.values()]:
            for obj in static_objects:
                obj.redraw()

    def check_bullets(self, bullets, deleted):
        for bullet in bullets:
            self.world.add_bullet(**bullet)

        for bullet in deleted:
            self.world.remove_bullet(bullet)

    def _on_mouse_down(self, window, x, y, button, modifiers):
        if button == "left":
            self.world.main_player.shooting = True
        elif button == "right":
            self.server.send_hook(atan2(x - Window.size[0] / 2, Window.size[1] / 2 - y))

    def _on_mouse_up(self, window, x, y, button, modifiers):
        if button == "left":
            self.world.main_player.shooting = False
