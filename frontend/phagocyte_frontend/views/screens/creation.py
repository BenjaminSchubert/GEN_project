#!/usr/bin/env python3


from phagocyte_frontend.views.screens import AutoLoadableScreen


__author__ = "Sébastien Boson <sebastboson@gmail.com>"


class CreateGameScreen(AutoLoadableScreen):
    screen_name = "creation"

    DEFAULT_GAME_NAME = "Game"
    DEFAULT_MAP_WIDTH = "5000"
    DEFAULT_MAP_HEIGHT = "5000"
    DEFAULT_MIN_RADIUS = "50"
    DEFAULT_MAX_SPEED = "400"
    DEFAULT_EAT_RATIO = "1.2"
    DEFAULT_FOOD_PRODUCTION_RATE = "5"
    DEFAULT_MAX_HIT_COUNT = "10"

    def on_enter(self, *args):
        # FIXME "<username's game>"
        self.DEFAULT_GAME_NAME = "Game"

    def game_creation(self):
        """
        Creates a new game.
        """

        game_info = {
            "game_name": self.game_name.text if self.game_name.text != "" else self.DEFAULT_GAME_NAME,
            "map_width": self.map_width.text if self.map_width.text != "" else self.DEFAULT_MAP_WIDTH,
            "map_height": self.map_height.text if self.map_height.text != "" else self.DEFAULT_MAP_HEIGHT,
            "min_radius": self.min_radius.text if self.min_radius.text != "" else self.DEFAULT_MIN_RADIUS,
            "max_speed": self.max_speed.text if self.max_speed.text != "" else self.DEFAULT_MAX_SPEED,
            "eat_ratio": self.eat_ratio.text if self.eat_ratio.text != "" else self.DEFAULT_EAT_RATIO,
            "food_production_rate": self.food_production_rate.text if self.food_production_rate.text != "" else self.DEFAULT_FOOD_PRODUCTION_RATE,
            "max_hit_count": self.max_hit_count.text if self.max_hit_count.text != "" else self.DEFAULT_MAX_HIT_COUNT
        }

        self.manager.client.create_game(**game_info)
