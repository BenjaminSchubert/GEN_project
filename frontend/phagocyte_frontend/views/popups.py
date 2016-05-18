#!/usr/bin/python3
# -*- coding: utf-8 -*-

from kivy.lang import Builder
from kivy.uix.popup import Popup


__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


class InfoPopup(Popup):
    def __init__(self, **kwargs):
        Builder.load_file("kv/popup.kv")
        super().__init__(**kwargs)
