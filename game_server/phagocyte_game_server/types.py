#!/usr/bin/env python3
from typing import Tuple, Union, List, Dict


__author__ = "Benjamin Schubert <ben.c.schubert@gmail.com>"


address = Tuple[str, int]
json_values = Union['json_object', str, bool, int, None]
json_object = Union[List[json_values], Dict[str, json_values]]
