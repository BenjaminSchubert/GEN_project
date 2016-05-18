#!/usr/bin/env python3


from abc import ABCMeta
from kivy.lang import Builder

from kivy.uix.screenmanager import ScreenManager, Screen

from phagocyte_frontend.client import Client
from phagocyte_frontend.popups import InfoPopup


__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


def noop(*_):
    pass


class AutoLoadableScreen(Screen):
    __metaclass__ = ABCMeta

    def __init__(self, **kw):
        Builder.load_file("kv/screens/{name}.kv".format(name=self.screen_name))
        super(Screen, self).__init__(**kw)
        self.name = self.screen_name


class PhagocyteScreenManager(ScreenManager):
    client = Client("127.0.0.1", 8000)  # FIXME : add this to some configuration file
    info_popup = InfoPopup()

    def main_screen(self, *args, **kwargs):
        self.current = self.screen_names[0]

    def warn(self, msg, title="Info", callback=None):
        if callback is None:
            callback = noop

        self.info_popup.msg = msg
        self.info_popup.title = title
        self.info_popup.bind(on_dismiss=callback)
        self.info_popup.open()

    def __del__(self):
        self.executor.shutdown(True)
