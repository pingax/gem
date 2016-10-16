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

from glob import glob

from shutil import copy2 as copy

from argparse import ArgumentParser

# Translation
from gettext import gettext as _
from gettext import textdomain
from gettext import bindtextdomain

# ------------------------------------------------------------------
#   Modules - GEM
# ------------------------------------------------------------------

from gem.utils import *
from gem.configuration import Configuration

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

        args = parser.parse_args()

    # ------------------------------------
    #   Create default folders
    # ------------------------------------

    # ~/.config/gem
    if not exists(expanduser(Path.User)):
        mkdir(expanduser(Path.User))

    # ~/.local/share/gem
    if not exists(expanduser(Path.Data)):
        mkdir(expanduser(Path.Data))

    # ~/.local/share/gem/logs
    if not exists(path_join(expanduser(Path.Data), "logs")):
        mkdir(path_join(expanduser(Path.Data), "logs"))

    # ~/.local/share/gem/icons
    # ~/.local/share/gem/icons/consoles
    # ~/.local/share/gem/icons/emulators
    if not exists(expanduser(Path.Icons)):
        makedirs(expanduser(Path.Consoles))
        mkdir(expanduser(Path.Emulators))

        # Consoles icons
        for filename in glob(path_join(get_data("icons"), "consoles", "*")):
            copy(filename, Path.Consoles)

        # Emulators icons
        for filename in glob(path_join(get_data("icons"), "emulators", "*")):
            copy(filename, Path.Emulators)

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

    # Save older log file to ~/.local/share/gem/gem.log.old
    if(exists(logging.log_path)):
        copy(logging.log_path, expanduser(path_join(Path.Data, "gem.log.old")))

    # Generate logger from log.conf
    fileConfig(get_data(Conf.Log))

    logger = logging.getLogger("gem")

    # ------------------------------------
    #   Start main window
    # ------------------------------------

    try:
        if args.preferences:
            from gem.preferences import Preferences
            Preferences(logger=logger)

        else:
            from gem.interface import launch_gem
            launch_gem(logger, args.reconstruct)

    except ImportError as error:
        logger.critical(_("Cannot import interface: %s" % str(error)))

    except KeyboardInterrupt as error:
        logger.warning(_("Terminate by keyboard interrupt"))

    except Exception as error:
        logger.critical(
            _("An error occur during program exec: %s" % str(error)))


if __name__ == "__main__":
    main()
