# -*- coding: utf-8 -*-

from os.path import abspath, dirname

import sys

sys.dont_write_bytecode = True
sys.path.insert(0, abspath(dirname(__file__)))

from server import application
