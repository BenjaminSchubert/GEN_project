#!/usr/bin/env python3


from phagocyte_frontend.exceptions import CredentialsException
from phagocyte_frontend.views.screens import AutoLoadableScreen


__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


class RegisterScreen(AutoLoadableScreen):
    """
    Create account (register) screen
    """
    screen_name = "register"

    def user_creation(self):
        """
        registers the specified user with his name and password
        """
        self.creationButton.disabled = True

        try:
            self.manager.client.register(self.username.text, self.password.text)
        except CredentialsException as e:
            self.manager.warn(str(e), title="Error")
        except ConnectionError:
            self.manager.warn("Could not connect to the server", title="Error")
        else:  # we already connect the user if his registration is correct
            self.manager.client.login(self.username.text, self.password.text)
            self.manager.warn("Welcome here !", callback=self.manager.main_screen)

        self.creationButton.disabled = False
