#!/usr/bin/env python3

"""
Runs the phagocyte client application
"""

from configparser import ConfigParser, Error

import os
import sys
from kivy import Logger

from phagocyte_frontend import Phagocyte


def get_config_parser():
    """
    Gets the config parser
    """
    config_parser = ConfigParser()

    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(__file__)

    config_file = os.path.join(os.path.abspath(application_path), "config.cfg")

    try:
        files_read = config_parser.read(config_file)
    except Error as e:
        Logger.error(str(e))
        raise SystemExit(1)

    if len(files_read) == 0:
        Logger.error("ScreenManager: Cannot read config file for hosts information : " + config_file)
        raise SystemExit(1)

    return config_parser


if __name__ == '__main__':
    Phagocyte(get_config_parser()).run()
