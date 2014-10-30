#!/usr/bin/env python
# coding: utf-8

# Python 2.7 Standard Library
import ConfigParser
import os
import os.path
import shutil
import sys

# Pip Package Manager
try:
    import pip
    import setuptools
except ImportError:
    error = "pip is not installed, refer to <{url}> for instructions."
    raise ImportError(error.format(url="http://pip.readthedocs.org"))

# Third-Party Libraries (automated install)
setup_requires = ["about>=4.0"]

def trueish(value):
    if not isinstance(value, str):
        return bool(value)
    else:
        value = value.lower()
        if value in ("y", "yes", "t", "true", "on", "1"):
            return True
        elif value in ("", "n", "no", "f", "false", "off", "0"):
            return False
        else:
            raise TypeError("invalid bool value {0!r}, use 'true' or 'false'.")

setuptools.Distribution.global_options.append(
  ("lib", "l", "install setup dependencies")
)

def lib_required():
    LIB = False
    if "-l" in sys.argv:
        sys.argv.remove("-l")
        LIB = True
    elif "--lib" in sys.argv:
        sys.argv.remove("--lib")
        LIB = True
    elif os.path.isfile("setup.cfg"):
        parser = ConfigParser.RawConfigParser()
        parser.read("setup.cfg")
        try: 
            LIB = trueish(parser.get("global", "lib"))
        except (ConfigParser.NoOptionError, ConfigParser.NoSectionError):
            pass
    return LIB

def install_lib(setup_requires, libdir):
    if os.path.exists(libdir):
        shutil.rmtree(libdir)
    os.mkdir(libdir)
    pip_install = pip.commands["install"]().main
    for package in setup_requires:
        options = ["--quiet", "--target=" + libdir, "--ignore-installed"]
        error = pip_install(options + [package])
        if error:
            raise RuntimeError("failed to install {0}.".format(package))
    os.chmod(libdir, 0o777)
    for dir, subdirs, others in os.walk(libdir):
        files = [os.path.join(dir, file) for file in subdirs + others]
        for file in files:
            os.chmod(file , 0o777)
    assert sys.path[0] in ("", os.getcwd())
    sys.path.insert(1, libdir)

if lib_required():
    install_lib(setup_requires, "lib")

assert sys.path[0] in ("", os.getcwd())
sys.path.insert(1, "lib")

import about

# This package (no runtime dependencies)
import breakpoint

# ------------------------------------------------------------------------------

info = dict(
  metadata     = about.get_metadata(breakpoint),
  code         = dict(py_modules=["breakpoint"]),
  data         = {},
  requirements = {},
  scripts      = {},
  plugins      = {},
  tests        = dict(test_suite="test.test_suite"),
)

if __name__ == "__main__":
    kwargs = {k:v for dct in info.values() for (k,v) in dct.items()}
    setuptools.setup(**kwargs)

