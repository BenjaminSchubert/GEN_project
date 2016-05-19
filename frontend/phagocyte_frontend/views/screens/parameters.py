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
        print("VALIDER LES PARAMETRES DE L'UTILISATEUR")
