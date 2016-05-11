#!/usr/bin/python3
# -*- coding: utf-8 -*-
import enum


__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


class Event(enum.IntEnum):
    ERROR = 0
    TOKEN = 1
    GAME_INFO = 2
