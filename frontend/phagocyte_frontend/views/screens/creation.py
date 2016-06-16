#!/usr/bin/env python3

from kivy.properties import StringProperty

from phagocyte_frontend.network.authentication import CreationFailedException
from phagocyte_frontend.views.screens import AutoLoadableScreen


__author__ = "Sébastien Boson <sebastboson@gmail.com>"


class CreateGameScreen(AutoLoadableScreen):
    screen_name = "creation"

    DEFAULT_NAME = StringProperty("Game")
    DEFAULT_CAPACITY = "50"
    DEFAULT_MAP_WIDTH = "5000"
    DEFAULT_MAP_HEIGHT = "5000"
    DEFAULT_MIN_RADIUS = "50"
    DEFAULT_WIN_SIZE = "500"
    DEFAULT_MAX_SPEED = "400"
    DEFAULT_EAT_RATIO = "1.2"
    DEFAULT_FOOD_PRODUCTION_RATE = "5"
    DEFAULT_MAX_HIT_COUNT = "10"

    def on_enter(self, *args):
        self.DEFAULT_NAME = self.manager.client.username + "'s game"

    def game_creation(self):
        """
        Creates a new game.
        """
        try:
            self.manager.client.create_game(
                name=self.game_name.text or self.DEFAULT_NAME,
                capacity=self.capacity.text or self.DEFAULT_CAPACITY,
                map_width=self.map_width.text or self.DEFAULT_MAP_WIDTH,
                map_height=self.map_height.text or self.DEFAULT_MAP_HEIGHT,
                min_radius=self.min_radius.text or self.DEFAULT_MIN_RADIUS,
                win_size=self.win_size.text or self.DEFAULT_WIN_SIZE,
                max_speed=self.max_speed.text or self.DEFAULT_MAX_SPEED,
                eat_ratio=self.eat_ratio.text or self.DEFAULT_EAT_RATIO,
                food_production_rate=self.food_production_rate.text or self.DEFAULT_FOOD_PRODUCTION_RATE,
                max_hit_count=self.max_hit_count.text or self.DEFAULT_MAX_HIT_COUNT
            )
        except CreationFailedException as e:
            self.manager.warn(str(e), title="Error")
        else:
            self.manager.main_screen()
