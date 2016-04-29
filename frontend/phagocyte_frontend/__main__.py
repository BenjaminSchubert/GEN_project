#!/usr/bin/python3

"""
Application that just represent a GUI for connection and register a user

An application can be built if you return a widget on build(), or if you set
self.root.
"""

import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput

kivy.require('1.0.7')

__author__ = "Boson Sébastien <sebastboson@gmail.com>"


def callback(instance):
    print("test")


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

        self.boxLeft = BoxLayout(padding=30, orientation='horizontal')
        self.add_widget(self.boxLeft)
        self.register = Button(text='Regiser', size_hint=(1, 0.4))
        self.boxLeft.add_widget(self.register)
        self.register.bind(on_press=callback)

        self.boxRight = BoxLayout(padding=30, orientation="horizontal")
        self.add_widget(self.boxRight)
        self.send = Button(text="Send", size_hint=(1, 0.4))
        self.boxRight.add_widget(self.send)
        self.send.bind(on_press=callback)


class MyApp(App):
    def build(self):
        return LoginScreen()


if __name__ == '__main__':
    MyApp().run()
