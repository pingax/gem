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

# Logging
import logging
from logging.config import fileConfig

# System
from os import mkdir
from os import makedirs

from os.path import join as path_join
from os.path import isfile
from os.path import exists
from os.path import expanduser

from sys import exit as sys_exit

from glob import glob

from shutil import copy2 as copy

from argparse import ArgumentParser

# Translation
from gettext import gettext as _
from gettext import textdomain
from gettext import bindtextdomain

# ------------------------------------------------------------------
#   Modules - Interface
# ------------------------------------------------------------------

try:
    from gi import require_version

    require_version("Gtk", "3.0")

except ImportError as error:
    sys_exit("Cannot found python3-gobject module: %s" % str(error))

# ------------------------------------------------------------------
#   Modules - GEM
# ------------------------------------------------------------------

try:
    from gem.utils import *
    from gem.configuration import Configuration

except ImportError as error:
    sys_exit("Cannot found gem module: %s" % str(error))

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

    parser = ArgumentParser(
        description=Gem.Name, epilog=Gem.Copyleft, conflict_handler="resolve")

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

    for folder in [
        Path.User, Path.Data, Path.Logs, Path.Roms, Path.Notes, Path.Icons]:
        if not exists(expanduser(folder)):
            mkdir(expanduser(folder))

    # Create roms folder based on default consoles.conf
    default_consoles = Configuration(get_data(Conf.Consoles))

    for console in default_consoles.sections():
        path = default_consoles.item(console, "roms", None)

        if path is not None and not exists(expanduser(path)):
            makedirs(expanduser(path))

    # ------------------------------------
    #   Launch logger
    # ------------------------------------

    # Define log path with a global variable
    logging.log_path = expanduser(path_join(Path.Data, "gem.log"))

    # Save older log file to ~/.local/share/gem/gem.log.old
    if(exists(logging.log_path)):
        copy(logging.log_path, expanduser(
            path_join(Path.Data, "gem.log.old")))

    # Generate logger from log.conf
    fileConfig(get_data(Conf.Log))

    logger = logging.getLogger("gem")

    try:
        # ------------------------------------
        #   Icons folders
        # ------------------------------------

        # ~/.local/share/gem/icons/consoles
        if not exists(expanduser(Path.Consoles)):
            mkdir(expanduser(Path.Consoles))

            for filename in glob(path_join(
                get_data("icons"), "consoles", "*")):
                if isfile(filename):
                    copy(filename, Path.Consoles)

        # ~/.local/share/gem/icons/emulators
        if not exists(expanduser(Path.Emulators)):
            mkdir(expanduser(Path.Emulators))

            for filename in glob(path_join(
                get_data("icons"), "emulators", "*")):
                if isfile(filename):
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
        #   Start main window
        # ------------------------------------

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
