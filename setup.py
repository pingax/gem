#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup
from setuptools import find_packages

from os.path import join
from os.path import dirname

setup(
    name = "gem",
    version = "0.10-rc3",
    author = "PacMiam",
    author_email = "pacmiam@tuxfamily.org",
    description = "Graphical Emulators Manager",
    url = "https://gem.tuxfamily.org",
    download_url = "https://download.tuxfamily.org/gem/releases/",
    license = "GPLv3",

    packages = find_packages(),
    include_package_data=True,

    entry_points = {
        "console_scripts": [
            "gem-ui = gem.__main__:main",
        ],
    },

    classifiers = [
        "Development Status :: Stable",
        "Environment :: Desktop Environment",
        "Intended Audience :: End Users/Desktop",
        "License :: GPL3",
        "Operating System :: GNU/Linux",
        "Programming Language :: Python :: 3.6",
        "Topic :: Games",
        "Topic :: Utilities",
    ],
)

