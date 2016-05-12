#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest

testSuite = unittest.TestSuite(unittest.TestLoader().discover("./test"))
text_runner = unittest.TextTestRunner(None, True, 3).run(testSuite)