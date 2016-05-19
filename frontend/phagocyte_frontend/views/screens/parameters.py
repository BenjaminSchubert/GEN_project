#!/usr/bin/env python3


from phagocyte_frontend.views.screens import AutoLoadableScreen

__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


class ParametersScreen(AutoLoadableScreen):
    """
    The player parameters screen
    """
    screen_name = "parameters"

    def validate_parameters(self):
        """
        modification parameters user account for the specified user
        """
        print(self.newUserName.text)

        self.buttonChangeParameters.disabled = True

        if self.newUserName.text == "":
            self.manager.warn("New user name can't be emtpy", title="Error")
        else:
            parameters = {
                "userName": self.newUserName.text,
                "ballColor": self.newBallColor.color
            }

            self.manager.client.post_account_info(parameters)

        self.buttonChangeParameters.disabled = False

    def validate_password(self):
        """
        modification password user account for the specified user
        """
        print(self.newUserName.text)

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
                "oldPassword": self.oldPassword.text,
                "newPassword": self.newPassword.text
            }

            self.manager.client.post_account_info(password)

        self.buttonSend.disabled = False
