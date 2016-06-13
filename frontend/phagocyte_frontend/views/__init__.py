"""
Package containing the different views of the application
"""

import os
import sys


__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


def resource_path() -> str:
    """
    Returns path where kv files are stored - either locally or in pyinstaller tmp file
    """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, "kv")

    return os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), "kv")
