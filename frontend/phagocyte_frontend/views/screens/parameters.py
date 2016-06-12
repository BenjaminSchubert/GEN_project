"""
Parameter's screen
"""

from kivy.properties import StringProperty

from phagocyte_frontend.network.authentication import CreationFailedException
from phagocyte_frontend.views.screens import AutoLoadableScreen

__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


class ParametersScreen(AutoLoadableScreen):
    """
    The player parameters screen
    """
    screen_name = "parameters"
    username = StringProperty("")
    color = StringProperty("#000000")

    def on_enter(self, *args):
        """
        fetches account information from the server on enter

        :param args: additional arguments
        """
        try:
            infos = self.manager.client.get_account_info()
        except ConnectionError:
            self.manager.warn("Could not connect to server", title="Error", callback=self.manager.main_screen)
        else:
            self.username = infos["username"]
            self.color = infos["color"]

    def validate_parameters(self):
        """
        modification parameters user account for the specified user
        """
        self.button_change_parameters.disabled = True

        parameters = {
            "color": self.new_ball_color.hex_color
        }

        if self.new_user_name.text != "":
            parameters["name"] = self.new_user_name.text

        try:
            self.manager.client.post_account_info(**parameters)
        except ConnectionError:
            self.manager.warn("Could not connect to server", title="Error")
        else:
            self.manager.warn("Parameters changed", callback=self.manager.main_screen)

        self.button_change_parameters.disabled = False

    def validate_password(self):
        """
        modification password user account for the specified user
        """
        self.button_change_password.disabled = True

        if self.old_password.text == "":
            self.manager.warn("Old password can't be emtpy", title="Error")
        elif self.new_password.text == "":
            self.manager.warn("New password can't be emtpy", title="Error")
        elif self.new_password_confirmation.text == "":
            self.manager.warn("New password confirmation can't be empty", title="Error")
        elif self.new_password.text != self.new_password_confirmation.text:
            self.manager.warn("New password doesn't match the confirmation", title="Error")
        else:
            password = {
                "old_password": self.old_password.text,
                "new_password": self.new_password.text
            }

            try:
                self.manager.client.post_account_info(**password)
            except CreationFailedException as e:
                self.manager.warn(str(e), title="Error")
            except ConnectionError:
                self.manager.warn("Could not connect to server", title="Error")
            else:
                self.manager.warn("Parameters changed", callback=self.manager.main_screen)

        self.button_change_password.disabled = False
