#!/usr/bin/env python
# coding: utf-8

from __future__ import division # should be in the doctest, but it doesn't work.
# This is the reason why we are not using the file-based doctest methods.

filename = "doctests.txt"
__doc__ = open(filename).read()

#
# Test Runner
# ------------------------------------------------------------------------------
#

# Python 2.7 Standard Library
import doctest
import unittest

__main__ = (__name__ == "__main__") 


test_suite = doctest.DocTestSuite() # support for `python setup.py test`

if __main__:
    doctest.testmod()

