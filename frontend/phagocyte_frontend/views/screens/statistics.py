__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"

from kivy.properties import StringProperty

from phagocyte_frontend.network.authentication import CreationFailedException
from phagocyte_frontend.views.screens import AutoLoadableScreen


class StatisticsScreen(AutoLoadableScreen):
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
        try:
            stats = self.manager.client.get_account_statistics()
        except CreationFailedException as e:
            self.manager.warn(str(e), title="Error")
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
