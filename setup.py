#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup
from setuptools import find_packages

from os.path import join
from os.path import dirname

setup(
    name = "gem",
    version = "0.5.2",
    author = "PacMiam",
    author_email = "pacmiam@tuxfamily.org",
    description = "Graphical Emulators Manager",
    url = "https://pacmiam.tuxfamily.org",
    license = "GPLv3",

    packages = find_packages(),
    include_package_data=True,

    entry_points = {
        "console_scripts": [
            "gem-ui = gem.main:main",
        ],
    },

    classifiers = [
        "Programming Language :: Python :: 3.4",
        "Development Status :: Stable",
        "License :: GPL3",
        "Operating System :: GNU/Linux",
        "Topic :: Games",
        "Topic :: Utilities",
    ],
)

