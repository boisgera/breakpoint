# coding: utf-8
"""
About - Metadata for Setuptools
"""

# Python 2.7 Standard Library
import importlib
import inspect
import os
import re
import sys

# Metadata
__project__ = "about"
__author__  = u"Sébastien Boisgérault <Sebastien.Boisgerault@gmail.com>"
__version__ = "0.1.5"
__license__ = "MIT License"


def get_metadata(name, path=None):
    """
    Return metadata for setuptools `setup`.
    """

    if path is None:
        path = os.getcwd()
    sys.path.insert(0, path)
    about_data = importlib.import_module(name).__dict__
    if path is not None:
        del sys.path[0]
    metadata = {}

    # read the relevant __*__ module attributes
    for name in "project name author version license doc url classifiers".split():
        value = about_data.get("__" + name + "__")
        if value is not None:
            metadata[name] = value

    # when 'project' is here, it overrides the (generated) 'name' attribute
    project = metadata.get("project")
    if project is not None:
        metadata["name"] = project
        del metadata["project"]

    # search for author email with <...@...> syntax in the author field
    author = metadata.get("author")
    if author is not None:
        email_pattern = r"<([^>]+@[^>]+)>"
        match = re.search(email_pattern, author)
        if match is not None:
            metadata["author_email"] = email = match.groups()[0]
            metadata["author"] = author.replace("<" + email + ">", "").strip()

    # get the module short description from the docstring
    doc = metadata.get("doc")
    if doc is not None:
        lines = [line for line in doc.splitlines() if line.strip()]
        metadata["description"] = lines[0].strip()
        del metadata["doc"]

    # process trove classifiers
    classifiers = metadata.get("classifiers")
    if classifiers and isinstance(classifiers, str):
        classifiers = [l.strip() for l in classifiers.splitlines() if l.strip()]
        metadata["classifiers"] = classifiers

    return metadata

if __name__ == "__main__":
    import about
    local = open("about.py", "w")
    local.write(open(inspect.getsourcefile(about)).read())
    local.close()
    
