#!/usr/bin/env python3


from configparser import ConfigParser
import os

from abc import ABCMeta
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen

from phagocyte_frontend.network.authentication import Client
from phagocyte_frontend.views import KV_DIRECTORY
from phagocyte_frontend.views.popups import InfoPopup


__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


def noop(*_):
    """ simple function that does nothing """


class AutoLoadableScreen(Screen):
    """
    Auto load screen from it's name
    """
    __metaclass__ = ABCMeta

    def __init__(self, **kw):
        Builder.load_file(os.path.join(KV_DIRECTORY, "screens/{name}.kv").format(name=self.screen_name))
        super(Screen, self).__init__(**kw)
        self.name = self.screen_name


class PhagocyteScreenManager(ScreenManager):

    info_popup = InfoPopup()

    def __init__(self, **kw):
        super().__init__(**kw)
        self.config_parser = ConfigParser()
        self.config_parser.read("config.cfg")
        self.client = Client(self.config_parser.get("Server", "host"), self.config_parser.get("Server", "port"))

    def main_screen(self, *args, **kwargs):
        """
        set the current screen to the lobby main screen
        """
        self.current = self.screen_names[0]

    def warn(self, msg, title="Info", callback=None):
        """
        Open a warn popup

        :param msg: content of the popup
        :param title: title of the popup
        :param callback:
        :return:
        """
        if callback is None:
            callback = noop

        self.info_popup.msg = msg
        self.info_popup.title = title
        self.info_popup.bind(on_dismiss=callback)
        self.info_popup.open()
