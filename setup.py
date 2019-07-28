#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup
from setuptools import find_packages

setup(
    name='Geode-GEM',
    version='0.10.0',
    author='PacMiam',
    author_email='pacmiam@tuxfamily.org',
    description='Graphical Emulators Manager',
    long_description='GEM (Graphical Emulators Manager) is a GTK+ Graphical '
                     'User Interface (GUI) for GNU/Linux which allows you to '
                     'easily manage your emulators. This software aims to '
                     'stay the simplest.',
    keywords='gtk+ emulators games',
    url='https://gem.tuxfamily.org',
    project_urls={
        'Archives': 'https://download.tuxfamily.org/gem/releases',
        'Source': 'https://framagit.org/PacMiam/gem',
        'Tracker': 'https://framagit.org/PacMiam/gem/issues',
    },
    packages=find_packages(exclude=['tools', 'test']),
    include_package_data=True,
    python_requires='~= 3.6',
    install_requires=[
        'PyGobject ~= 3.32',
        'pyxdg ~= 0.26',
    ],
    entry_points={
        'console_scripts': [
            'gem-ui = gem.__main__:main',
        ],
    },
    license='GPLv3',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: X11 Applications :: GTK',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: French',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3.6',
        'Topic :: Games/Entertainment',
        'Topic :: Utilities',
    ],
)
