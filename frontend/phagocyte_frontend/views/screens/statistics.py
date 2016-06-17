"""
Statistics screen
"""

from kivy.properties import StringProperty

from phagocyte_frontend.network.authentication import CreationFailedException
from phagocyte_frontend.views.screens import AutoLoadableScreen


__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


class StatisticsScreen(AutoLoadableScreen):
    """
    Screen to show game statistics to the player
    """
    screen_name = "statistics"

    games_played = StringProperty()
    games_won = StringProperty()
    players_eaten = StringProperty()
    deaths = StringProperty()
    matter_lost = StringProperty()
    matter_absorbed = StringProperty()
    bonuses_taken = StringProperty()
    bullets_shot = StringProperty()
    successful_hooks = StringProperty()
    time_played = StringProperty()

    def on_enter(self, *args):
        """
        On enter will fetch statistics for the logged in player

        :param args: additional arguments
        """
        try:
            stats = self.manager.client.get_account_statistics()
        except CreationFailedException as e:
            self.manager.warn(str(e), title="Error")
        except ConnectionError:
            self.manager.warn("Couldn't connect to server", title="Error", callback=self.manager.main_screen)
        else:
            self.games_played = str(stats["games_played"])
            self.games_won = str(stats["games_won"])
            self.players_eaten = str(stats["players_eaten"])
            self.deaths = str(stats["deaths"])
            self.matter_lost = str(int(stats["matter_lost"]))
            self.matter_absorbed = str(int(stats["matter_absorbed"]))
            self.bonuses_taken = str(stats["bonuses_taken"])
            self.bullets_shot = str(stats["bullets_shot"])
            self.successful_hooks = str(stats["successful_hooks"])
            self.time_played = str(int(stats["time_played"]))
