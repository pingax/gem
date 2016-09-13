#!/usr/bin/python3 -B
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
# ------------------------------------------------------------------

# ------------------------------------------------------------------
#   Modules - System
# ------------------------------------------------------------------

# GI
from gi import require_version

require_version("Gtk", "3.0")

# Logging
import logging
from logging.config import fileConfig

# System
from sys import argv

from os import mkdir
from os import makedirs
from os.path import join as path_join
from os.path import exists
from os.path import expanduser

from shutil import copy2 as copy

from argparse import ArgumentParser

# Translation
from gettext import gettext as _
from gettext import textdomain
from gettext import bindtextdomain

# ------------------------------------------------------------------
#   Modules - GEM
# ------------------------------------------------------------------

from utils import *
from configuration import Configuration

# ------------------------------------------------------------------
#   Translation
# ------------------------------------------------------------------

bindtextdomain("gem", get_data("i18n"))
textdomain("gem")

# ------------------------------------------------------------------
#   Functions
# ------------------------------------------------------------------

def main():

    # ------------------------------------
    #   Arguments
    # ------------------------------------

    if len(argv) >= 1:

        parser = ArgumentParser(
            description="Graphical Emulators Manager",
            epilog="Copyleft 2016 - Kawa Team",
            conflict_handler="resolve")

        parser.add_argument("-v", "--version", action="version",
            version="GEM %s (%s) - Licence GPLv3" % (Gem.Version, Gem.CodeName),
            help="show the current version")
        parser.add_argument("-p", "--preferences", action="store_true",
            help="configure gem")
        parser.add_argument("-r", "--reconstruct", action="store_true",
            help="reconstruct gem db")
        parser.add_argument("-d", "--debug", action="store_true",
            help="start gem with debug mode")

        args = parser.parse_args()

    # ------------------------------------
    #   Create default folders
    # ------------------------------------

    # ~/.config/gem
    if not exists(expanduser(Path.User)):
        mkdir(expanduser(Path.User))

    # ~/.local/share/gem
    # ~/.local/share/gem/logs
    if not exists(expanduser(Path.Data)):
        makedirs(path_join(expanduser(Path.Data), "logs"))

    # ------------------------------------
    #   Create default configuration files
    # ------------------------------------

    if not exists(expanduser(path_join(Path.User, "gem.conf"))):
        copy(get_data(Conf.Default),
            expanduser(path_join(Path.User, "gem.conf")))

    if not exists(expanduser(path_join(Path.User, "consoles.conf"))):
        copy(get_data(Conf.Consoles),
            expanduser(path_join(Path.User, "consoles.conf")))

    if not exists(expanduser(path_join(Path.User, "emulators.conf"))):
        copy(get_data(Conf.Emulators),
            expanduser(path_join(Path.User, "emulators.conf")))

    # ------------------------------------
    #   Launch logger
    # ------------------------------------

    # Define log path with a global variable
    logging.log_path = expanduser(path_join(Path.Data, "gem.log"))

    # Generate logger from log.conf
    fileConfig(get_data(Conf.Log))

    logger = logging.getLogger("gem")

    if args.debug:
        logger.set_level(logging.DEBUG)

    # ------------------------------------
    #   Start main window
    # ------------------------------------

    try:
        if args.preferences:
            from preferences import Preferences
            Preferences(logger=logger)

        else:
            from interface import launch_gem
            launch_gem(logger, args.reconstruct)

    except ImportError as error:
        logger.critical(_("Cannot import interface: %s" % str(error)))

    except Exception as error:
        logger.critical(
            _("An error occur during program exec: %s" % str(error)))

    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
