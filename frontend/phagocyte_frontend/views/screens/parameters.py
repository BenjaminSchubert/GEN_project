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
        self.buttonChangeParameters.disabled = True

        parameters = {
            "color": self.newBallColor.hex_color
        }

        if self.newUserName.text != "":
            parameters["name"] = self.newUserName.text

        try:
            self.manager.client.post_account_info(**parameters)
        except ConnectionError:
            self.manager.warn("Could not connect to server", title="Error")

        self.buttonChangeParameters.disabled = False

    def validate_password(self):
        """
        modification password user account for the specified user
        """
        self.buttonChangePassword.disabled = True

        if self.oldPassword.text == "":
            self.manager.warn("Old password can't be emtpy", title="Error")
        elif self.newPassword.text == "":
            self.manager.warn("New password can't be emtpy", title="Error")
        elif self.newPasswordConfirmation.text == "":
            self.manager.warn("New password confirmation can't be empty", title="Error")
        elif self.newPassword.text != self.newPasswordConfirmation.text:
            self.manager.warn("New password doesn't match the confirmation", title="Error")
        else:
            password = {
                "old_password": self.oldPassword.text,
                "new_password": self.newPassword.text
            }

            try:
                self.manager.client.post_account_info(**password)
            except CreationFailedException as e:
                self.manager.warn(str(e), title="Error")
            except ConnectionError:
                self.manager.warn("Could not connect to server", title="Error")

        self.buttonChangePassword.disabled = False
