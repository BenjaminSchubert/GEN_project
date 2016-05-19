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

        self.buttonSend.disabled = True

        if self.newPassword.text != self.newPasswordConfirmation.text:
            self.manager.warn("New password doesn't match the confirmation", title="Error")
        else:
            parameters = {}

            if self.newUserName != "":
                parameters["userName"] = self.newUserName.text
            else:
                self.manager.warn("New user name can't be emtpy", title="Error")

            #if self.newBallColor.text

        self.buttonSend.disabled = False

        #todo declarer dico
        #todo tester si les champs ne sont pas vides les uns après les autres

    def test_send_param(self):
        print("test")
        self.manager.client.post_account_info(message="salut")