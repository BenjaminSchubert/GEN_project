#!/usr/bin/python3

"""
Application that just
==========================================

An application can be built if you return a widget on build(), or if you set
self.root.
"""

from locale import _strip_padding

import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput

kivy.require('1.0.7')

__author__ = "Basile Vu <basile.vu@gmail.com>"


class LoginScreen(GridLayout):
    def __init__(self, **kwargs):
        super(LoginScreen, self).__init__(**kwargs)

        self.cols = 2

        self.add_widget(Label(text='User name:'))

        self.username = TextInput(multiline=False)
        self.add_widget(self.username)

        self.add_widget(Label(text='Password:'))

        self.password = TextInput(password=True, multiline=False)
        self.add_widget(self.password)

        self.box = BoxLayout(padding=30, orientation='horizontal')
        self.add_widget(self.box)
        self.send = Button(text='Send', size_hint=(1, 0.4))
        self.box.add_widget(self.send)

        # b = GridLayout(
        #     cols=1,
        #     pos_hint={
        #         'center_x': .5,
        #         'center_y': .5},
        #     size_hint=(None, None),
        #     spacing=20,
        #     width=200)
        # b.bind(minimum_height=b.setter('height'))
        # self.add_widget(b)


class MyApp(App):
    def build(self):
        return LoginScreen()


if __name__ == '__main__':
    MyApp().run()
