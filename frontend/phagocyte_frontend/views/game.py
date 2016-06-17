"""
This module contains everything related to the actual game
"""

import enum
from itertools import chain
from math import atan2

import time
from typing import Dict, Union, List
from typing import Tuple

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import NumericProperty, ListProperty, StringProperty
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex

from phagocyte_frontend.network.game import NetworkGameClient


__author__ = "Mathieu Urstein <mathieu.urstein@heig-vd.ch"


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
    position_x = 0  # type: float
    position_y = 0  # type: float

    # noinspection PyArgumentList
    color = ListProperty([0, 0, 0, 0])  # type: ListProperty

    def set_position(self, x: float, y: float):
        """
        Sets the new position of the widget to (x,y) bounded by the size of the world

        :param x: position on the x axis
        :param y: position on the y axis
        """
        self.position_x = max(min(x, self.parent.size[0] - self.size[0]), 0)
        self.position_y = max(min(y, self.parent.size[1] - self.size[1]), 0)

        self.x = self.position_x + Window.size[0] / 2
        self.y = self.position_y + Window.size[1] / 2

    def redraw(self):
        """
        Moves the widget to its correct place. Must be called after the window changes size
        """
        self.x = self.position_x + Window.size[0] / 2
        self.y = self.position_y + Window.size[1] / 2

    def add_position(self, x: float, y: float):
        """
        Moves the widget from a delta of (x, y)

        :param x: move on the x axis
        :param y: move on the y axis
        """
        self.set_position(x + self.position_x, y + self.position_y)


class Player(BoundedWidget):
    """
    Represents a player in the game

    :param name: name of the player
    """
    def __init__(self, name: str, **kwargs):
        super().__init__(**kwargs)
        self.shield = Shield(self)  # type: Shield
        self.timestamp = time.time()  # type: int
        self.name = name  # type: str
        self.bonus = None  # type: Bonus
        self.hook = None  # type: Hook

    def update(self, size: float, bonus: int, hook: Dict[str, float]):
        """
        Updates the information about the player

        :param size: new size of the player
        :param bonus: number of the bonus of the player
        :param hook: hook of the player
        """
        self.size = size, size
        self.set_bonus(bonus)
        self.set_hook(hook)

    def set_bonus(self, bonus: int):
        """
        Gives the given bonus to the player, or removes it if bonus is None

        :param bonus: identifier of the bonus of the player
        """
        if self.bonus == bonus:
            return
        elif self.bonus == BonusTypes.SHIELD:
            self.remove_widget(self.shield)

        if bonus == BonusTypes.SHIELD:
            self.add_widget(self.shield)
            self.shield.center = self.center

        self.bonus = bonus

    def set_hook(self, hook: Dict[str, float]):
        """
        Updates the hook the player can throw

        :param hook: hook the player has
        """
        if hook is None and self.hook is None:
            return

        elif hook is None:
            self.remove_widget(self.hook)
            self.hook = None

        elif self.hook is None:
            self.hook = Hook(self)
            self.add_widget(self.hook)
            # this is a hack to force the display of the hook if the player doesn't move. Couldn't find a better way
            self.x += 1

        else:
            # this is a hack to force the display of the hook if the player doesn't move. Couldn't find a better way
            self.x += 1
            self.hook.end_x = hook["x"] + Window.size[0] / 2
            self.hook.end_y = hook["y"] + Window.size[1] / 2


class MainPlayer(Player):
    """
    Represents the main player of the application
    """
    bonus_speedup = NumericProperty(0)  # type: NumericProperty
    current_bonus = StringProperty("")  # type: StringProperty

    def __init__(self, **kwargs):
        super().__init__(name="", **kwargs)

        self.initial_size = 0  # type: float
        self.max_speed = 0  # type: float
        self.correction_x = 0  # type: float
        self.correction_y = 0  # type: float
        self.speed_x = 0  # type: float
        self.speed_y = 0  # type: float

        # determines whether the player is currently shooting or not
        self.shooting = False  # type: bool

        self.bind(size=self.set_max_speed, bonus_speedup=self.set_max_speed)
        self.keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self.keyboard.bind(on_key_down=self._on_keyboard_down, on_key_up=self._on_keyboard_up)

    def _keyboard_closed(self):
        """
        Unbind the keyboard from the system
        """
        self.keyboard.unbind(on_key_down=self._on_keyboard_down, on_key_up=self._on_keyboard_up)

    # noinspection PyUnusedLocal
    def _on_keyboard_down(self, keyboard, keycode, *args):
        """
        Event called when a key is pressed

        This allows the player to move using either arrows or wasd

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

    # noinspection PyUnusedLocal
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

    def set_position(self, x: float, y: float):
        """
        Sets the new position for this player, adding a bit of correction if asked by the server

        :param x: new x position
        :param y: new y position
        """
        self.correction_x /= 2
        self.correction_y /= 2

        super().set_position(x + self.correction_x, y + self.correction_y)

    # noinspection PyUnusedLocal
    def set_max_speed(self, instance, attribute):
        """
        Sets the new maximum speed for the player

        :param instance: instance of the class passed
        :param attribute: value updated, max_speed
        """
        self.max_speed = self.bonus_speedup * 50 * self.initial_size / self.size[0] ** 0.5

    def move(self, dt: float):
        """
        Moves the player according to the time since last move

        :param dt: delta of time since last move
        """
        self.add_position(
            self.max_speed * self.speed_y * dt,
            self.max_speed * self.speed_x * dt
        )

    def set_bonus(self, bonus: int):
        """
        Sets the given bonus on the player

        :param bonus: identifier of the bonus to set
        """
        super().set_bonus(bonus)

        if bonus == BonusTypes.SPEEDUP:
            self.bonus_speedup = 1.5
        else:
            self.bonus_speedup = 1

        self.current_bonus = BonusTypes(bonus).name if bonus is not None else ""


class Food(BoundedWidget):
    """
    The food let the player grow
    """
    color = [0, 1, 0, 1]  # type: list


class Bonus(BoundedWidget):
    """
    A bonus a user can pick
    """
    color = [1, 1, 0, 1]  # type: list


class Shield(Widget):
    """
    The bonus shield

    :param player: the player on which the shield is
    :param kwargs: additional keyword arguments
    """
    def __init__(self, player: Player, **kwargs):
        self.player = player
        super().__init__(**kwargs)


class Hook(Widget):
    """
    the hook a user can use to grab another user

    :param player: the player to which the hook belongs
    :param kwargs: additional keyword arguments
    """
    def __init__(self, player: Player, **kwargs):
        self.player = player
        self.end_x = self.player.center_x
        self.end_y = self.player.center_y

        super().__init__(**kwargs)


class Bullet(BoundedWidget):
    """
    A bullet thrown by a player

    :param uid: unique id of the bullet
    :param speed_x: speed on the x axis of the bullet
    :param speed_y: speed on the y axis of the bullet
    """
    def __init__(self, uid: str, speed_x: float, speed_y: float, **kwargs):
        super().__init__(**kwargs)
        self.bid = uid
        self.speed_x = speed_x
        self.speed_y = speed_y


class World(Widget):
    """
    Represents the world in which the game is played

    :param kwargs: additional keyword arguments
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.players = {}  # type: Dict[str, Player]
        self.food = {}  # type: Dict[Tuple(float, float), Food]
        self.bullets = {}  # type: Dict[str, Bullet]
        self.bonuses = {}  # type: Dict[Tuple(float, float), Bonus]

    def add_food(self, x: float, y: float, size: float):
        """
        add a new food on the map

        :param x: position on the x axis of the food
        :param y: position on the y axis of the food
        :param size: size of the food
        """
        food = Food(size=(size, size))
        self.food[(x, y)] = food
        self.add_widget(food)
        food.set_position(x, y)

    def add_bullet(self, uid: str, x: float, y: float, speed_x: float, speed_y: float, color: str, size: float):
        """
        Adds a new bullet on the map

        :param uid: unique id of the bullet
        :param x: position on the x axis of the bullet
        :param y: position on the y axis of the bullet
        :param speed_x: speed on the x axis of the bullet
        :param speed_y: speed on the y axis of the bullet
        :param color: color of the bullet
        :param size: size of the bullet
        """
        if self.bullets.get(uid) is None:
            self.bullets[uid] = Bullet(uid, speed_x, speed_y, size=(size, size), color=get_color_from_hex(color))
            self.add_widget(self.bullets[uid])
        self.bullets[uid].set_position(x, y)

    def add_bonus(self, x: float, y: float, size: float):
        """
        Adds a new bonus on the map

        :param x: position on the x axis of the bonus
        :param y: position on the y axis of the bonus
        :param size: size of the bonus
        """
        bonus = Bonus(size=(size, size))
        self.add_widget(bonus)
        self.bonuses[(x, y)] = bonus
        bonus.set_position(x, y)

    def remove_bonus(self, x: float, y: float):
        """
        Removes the bonus at the position (x, y)

        :param x: position on the x axis of the bonus
        :param y: position on the y axis of the bonus
        """
        b = self.bonuses.pop((x, y), None)
        if b:
            self.remove_widget(b)

    def remove_food(self, x: float, y: float):
        """
        Removes the food at the position (x, y)

        :param x: position on the x axis of the bonus
        :param y: position on the y axis of the bonus
        """
        f = self.food.pop((x, y), None)
        if f:
            self.remove_widget(f)

    def remove_bullet(self, bid: str):
        """
        Removes the bullet identified by the given bid

        :param bid: unique id of the bullet to remove
        """
        b = self.bullets.pop(bid, None)
        if b:
            self.remove_widget(b)


class GameInstance(Widget):
    """
    The instance of the game displayed by the game manager

    :param kwargs: additional keyword arguments
    """
    REFRESH_RATE = 1 / 60  # type: float
    SCALE_RATIO = 8  # type: int
    win_size = NumericProperty(1000)  # type: NumericProperty
    scale_ratio_util = NumericProperty(0)  # type: NumericProperty
    server = None  # type: NetworkGameClient

    bonus_label = StringProperty("")  # type: StringProperty
    # noinspection PyArgumentList
    best_players = ListProperty(["", "", ""])  # type: ListProperty

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.world.main_player.bind(center=self.follow_main_player)

        self.events = [self.move_main_player, self.send_moves, self.send_bullets, self.move_bullets]

    def _stop_game(self):
        """
        stops the game
        """
        for event in self.events:
            Clock.unschedule(event)

        self.world.main_player.keyboard.release()

    def move_main_player(self, dt: int):
        """
        Moves the main player for the given time

        :param dt: time elapsed since last move
        """
        self.world.main_player.move(dt)

    # noinspection PyUnusedLocal
    def follow_main_player(self, instance, attribute):
        """
        Makes the camera follow the player

        :param instance: instance of the player that moved
        :param attribute: attribute that changed
        """
        x, y = self.camera.convert_distance_to_scroll(
            self.world.main_player.center_x * self.map.scale - Window.width / 2,
            self.world.main_player.center_y * self.map.scale - Window.height / 2
        )
        self.camera.scroll_x = x
        self.camera.scroll_y = y

    # noinspection PyUnusedLocal
    def send_moves(self, dt: int):
        """
        Send new position to the server

        :param dt: time since last move was sent
        """
        self.server.send_state((
            self.world.main_player.center_x - Window.width / 2,
            self.world.main_player.center_y - Window.height / 2
        ))

    # noinspection PyUnusedLocal
    def send_bullets(self, dt: int):
        """
        send to the server the fact that the player is shooting

        :param dt: time since that function was called
        """
        if self.world.main_player.shooting:
            m_x, m_y = Window.mouse_pos
            self.server.send_bullet(atan2(m_x - Window.width / 2, m_y - Window.height / 2))

    def start_game(self, server: NetworkGameClient, data: Dict[str, Union[str, float, int]]):
        """
        Setups the environment for the game to start

        :param server: server used for communication with the game
        :param data: data received from the server
        """
        self.server = server

        self.world.size = (data["max_x"], data["max_y"])

        self.win_size = data["win_size"]

        self.world.main_player.set_position(data["x"], data["y"])
        self.world.main_player.color = get_color_from_hex(data["color"])

        self.world.main_player.initial_size = data["size"]
        self.world.main_player.size = data["size"], data["size"]
        self.world.main_player.name = data["name"]

        self.scale_ratio_util = self.SCALE_RATIO ** 2 - data["size"]
        self.follow_main_player(self.world.main_player, None)

        Window.bind(on_resize=self.redraw, on_mouse_down=self._on_mouse_down, on_mouse_up=self._on_mouse_up)

        self.start_timers()

    def start_timers(self):
        """
        Schedules all operations that have to be called every given time
        """
        for event in self.events:
            Clock.schedule_interval(event, self.REFRESH_RATE)

    def update_state(self, states: List[Dict[str, Union[str, int, float, Dict[str, float]]]], deaths: List[str]):
        """
        updates the current state of the game

        :param states: players that moved
        :param deaths: players that died
        """
        for state in states:
            if state["name"] == self.server.name:
                player = self.world.main_player

                if state.get("dirty", None):
                    player.correction_x += state["dirty"][0]
                    player.correction_y += state["dirty"][1]
            else:
                if state["name"] in self.world.players.keys():
                    player = self.world.players[state["name"]]

                else:
                    player = Player(name=state["name"])
                    player.color = get_color_from_hex(state["color"])
                    self.world.add_widget(player)
                    self.world.players[state["name"]] = player

                player.set_position(state["x"] - player.size[0] / 2, state["y"] - player.size[1] / 2)

            player.update(state["size"], state["bonus"], state["hook"])

        for death in deaths:
            dead = self.world.players.pop(death)
            if dead:
                self.world.remove_widget(dead)

    def update_food(self, new: List[Dict[str, float]], deleted: List[Dict[str, float]]):
        """
        updates the state of the food in the world

        :param new: new food objects
        :param deleted: food objects to remove from the game
        """
        for entry in new:
            if (entry["x"], entry["y"]) not in self.world.food.keys():
                self.world.add_food(entry["x"], entry["y"], entry["size"])

        for entry in deleted:
            self.world.remove_food(entry["x"], entry["y"])

    def update_bonus(self, new: List[Dict[str, float]], deleted: List[Dict[str, float]]):
        """
        updates the state of the bonus in the world

        :param new: new bonus objects
        :param deleted: bonus objects to remove from the game
        """
        for entry in new:
            if (entry["x"], entry["y"]) not in self.world.bonuses.keys():
                self.world.add_bonus(entry["x"], entry["y"], entry["size"])

        for entry in deleted:
            self.world.remove_bonus(entry["x"], entry["y"])

    def move_bullets(self, dt: int):
        """
        Moves all bullets

        :param dt: time since last move
        """
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
        """
        Event fired when the player died. Will allow the player to restart the game or go to the main menu
        """
        self._stop_game()
        self.parent.player_died()

    def handle_win(self, winner: Player):
        """
        Event fired when someone won

        :param winner: winner of the game
        """
        self._stop_game()
        self.parent.player_won(winner, winner == self.server.name)

    def handle_error(self, error_message: str):
        """
        Event fired when an error that cannot be handled appeared

        :param error_message: error message
        """
        self._stop_game()
        self.parent.handle_error(error_message)

    # noinspection PyUnusedLocal
    def redraw(self, *args):
        """
        Redraws all objects on the map

        :param args: additional arguments
        """
        for static_objects in [self.world.food.values(), self.world.bonuses.values()]:
            for obj in static_objects:
                obj.redraw()

    def check_bullets(self, bullets: List[Dict[str, Union[float, str]]], deleted: List[str]):
        """
        Adds new bullets and remove the ones that hit something

        :param bullets: new bullets to add
        :param deleted: bullets to remove
        """
        for bullet in bullets:
            self.world.add_bullet(**bullet)

        for bullet in deleted:
            self.world.remove_bullet(bullet)

    # noinspection PyUnusedLocal
    def _on_mouse_down(self, window: Window, x: float, y: float, button: str, modifiers: Dict[str, any]):
        """
        Event fired when the mouse is pressed

        :param window: windows on which the mouse was pressed
        :param x: position on the x axis where the button was pressed
        :param y: position on the y axis where the button was pressed
        :param button: button of the mouse that was pressed
        :param modifiers: additional modifiers
        """
        if button == "left":
            self.world.main_player.shooting = True
        elif button == "right":
            self.server.send_hook(atan2(x - Window.size[0] / 2, Window.size[1] / 2 - y))

    # noinspection PyUnusedLocal
    def _on_mouse_up(self, window, x, y, button, modifiers):
        """
        Event fired when the mouse is released

        :param window: windows on which the mouse was released
        :param x: position on the x axis where the button was released
        :param y: position on the y axis where the button was released
        :param button: button of the mouse that was released
        :param modifiers: additional modifiers
        """
        if button == "left":
            self.world.main_player.shooting = False

    def handle_alives(self, alives: List[Dict[str, Union[str, float, int, Dict[str, float]]]]):
        """
        handle players that are alive

        :param alives: players to draw on the map
        """
        now = time.time()
        to_remove = []

        for alive in alives:
            if alive["name"] == self.server.name:
                continue

            player = self.world.players.get(alive["name"], None)

            if player is not None:
                # we already have this player, just update the timestamp
                player.timestamp = now
            else:
                # this is a new player
                p = Player(name=alive["name"])
                p.color = get_color_from_hex(alive["color"])
                self.world.add_widget(p)
                self.world.players[alive["name"]] = p
                p.set_position(alive["x"] - p.size[0] / 2, alive["y"] - p.size[1] / 2)
                p.update(alive["size"], alive["bonus"], alive["hook"])

        for name, player in self.world.players.items():
            if now - player.timestamp > 5:
                to_remove.append((name, player))

        for player in to_remove:
            self.world.players.pop(player[0])
            self.world.remove_widget(player[1])

        best_players = sorted(
            chain(self.world.players.values(), [self.world.main_player]),
            key=lambda x: x.size[0], reverse=True
        )

        for i in range(3):
            if len(best_players) <= i:
                # noinspection PyUnresolvedReferences
                self.best_players[i] = ""
            else:
                name = best_players[i].name
                # noinspection PyUnresolvedReferences
                self.best_players[i] = "{:<15.15}".format(name)
