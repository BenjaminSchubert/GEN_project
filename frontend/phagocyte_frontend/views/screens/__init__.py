"""
Package containing all the screens used in the application
"""

from abc import ABCMeta
from configparser import ConfigParser, Error
from functools import partial
import os

from kivy.lang import Builder
from kivy.logger import Logger
from kivy.uix.screenmanager import ScreenManager, Screen

from phagocyte_frontend.network.authentication import Client
from phagocyte_frontend.views import KV_DIRECTORY
from phagocyte_frontend.views.popups import InfoPopup


__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


class AutoLoadableScreen(Screen):
    """
    Auto load screen from it's name

    :param kwargs: additional keyword arguments
    """
    __metaclass__ = ABCMeta

    def __init__(self, **kwargs):
        Builder.load_file(os.path.join(KV_DIRECTORY, "screens/{name}.kv").format(name=self.screen_name))
        super(Screen, self).__init__(**kwargs)
        self.name = self.screen_name


class PhagocyteScreenManager(ScreenManager):
    """
    Screen manager for the application

    :param kwargs: additional keyword arguments
    """
    info_popup = InfoPopup()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config_parser = ConfigParser()
        self.callback = None

        try:
            files_read = self.config_parser.read("config.cfg")
        except Error as e:
            Logger.error(str(e))
            raise SystemExit(1)  # FIXME : popup and then quit

        if len(files_read) == 0:
            Logger.error("Cannot read config file")
            raise SystemExit(1)  # FIXME : popup and then quit

        self.client = Client(self.config_parser.get("Server", "host"), self.config_parser.get("Server", "port"))

    # noinspection PyUnusedLocal
    def main_screen(self, *args, **kwargs):
        """
        set the current screen to the lobby main screen
        """
        self.current = self.screen_names[0]

    def warn(self, msg: str, title: str="Info", callback: callable=None):
        """
        Open a warn popup

        :param msg: content of the popup
        :param title: title of the popup
        :param callback: callback to call when the popup is dismissed
        """
        self.info_popup.msg = msg
        self.info_popup.title = title
        self.callback = partial(self.callback_handler, callback)
        self.info_popup.bind(on_dismiss=self.callback)
        self.info_popup.open()

    def callback_handler(self, callback: callable, *args):
        """
        call the callback given in parameter if not None, and removes it from the event on which it was bound

        :param callback: callback to call when the event is fired
        :param args: arguments to pass to the callback
        """
        if callback is not None:
            callback(*args)
        self.info_popup.unbind(on_dismiss=self.callback)
