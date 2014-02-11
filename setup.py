#!/usr/bin/env python
# coding: utf-8

# Python 2.7 Standard Library
import setuptools
import os.path
import sys

# Third-Party Libraries
import about


metadata = about.get_metadata("breakpoint", path=os.getcwd())
contents = dict(py_modules=["about"], zip_safe=False)
requirements = {}

info = {}
info.update(contents)
info.update(metadata)
info.update(requirements)

def setup():
    setuptools.setup(**info)

if __name__ == "__main__":
    setup()

