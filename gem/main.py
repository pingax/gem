# ------------------------------------------------------------------
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
# ------------------------------------------------------------------

# ------------------------------------------------------------------
#   Modules - System
# ------------------------------------------------------------------

# Logging
import logging
from logging.config import fileConfig

# System
from os import mkdir
from os import getpid
from os import remove
from os import environ
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
#   Modules - GEM
# ------------------------------------------------------------------

try:
    from gem import Gem
    from gem import Conf
    from gem import Path
    from gem.utils import get_data
    from gem.configuration import Configuration

except ImportError as error:
    sys_exit("Cannot find gem module: %s" % str(error))

# ------------------------------------------------------------------
#   Translation
# ------------------------------------------------------------------

bindtextdomain("gem", get_data("i18n"))
textdomain("gem")

# ------------------------------------------------------------------
#   Launcher
# ------------------------------------------------------------------

def main():
    parser = ArgumentParser(description="%s - %s" % (Gem.Name, Gem.Description),
        epilog=Gem.Copyleft, conflict_handler="resolve")

    parser.add_argument("-v", "--version", action="version",
        version="GEM %s (%s) - Licence GPLv3" % (Gem.Version, Gem.CodeName),
        help="show the current version")
    parser.add_argument("-p", "--preferences", action="store_true",
        help="configure gem")
    parser.add_argument("-r", "--reconstruct", action="store_true",
        help="reconstruct gem db")
    parser.add_argument("-d", "--debug", action="store_true",
        help="launch gem with debug flag")

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

    if not args.debug:
        logger.setLevel(logging.INFO)

    # ------------------------------------
    #   Check lock
    # ------------------------------------

    if exists(expanduser(Path.Lock)):
        with open(expanduser(Path.Lock), 'r') as pipe:
            gem_pid = pipe.read()

        # Lock PID still exists
        if len(gem_pid) > 0 and exists(path_join("/proc", gem_pid)):

            # Check process command line
            if exists(path_join("/proc", gem_pid, "cmdline")):
                with open(path_join("/proc", gem_pid, "cmdline"), 'r') as pipe:
                    content = pipe.read()

                # Check if lock process is gem
                if "gem.main" in content or "gem-ui" in content:
                    logger.critical(
                        _("GEM is already running with PID %s") % gem_pid)

                    return True

    # ------------------------------------
    #   Check folders and launch interface
    # ------------------------------------

    try:
        # ------------------------------------
        #   Icons folders
        # ------------------------------------

        logger.debug(_("Check icons folders"))

        # ~/.local/share/gem/icons/consoles
        if not exists(expanduser(Path.Consoles)):
            logger.debug("Copy consoles icons to %s" % Path.Consoles)
            mkdir(expanduser(Path.Consoles))

            for filename in glob(path_join(
                get_data("icons"), "consoles", "*")):
                if isfile(filename):
                    copy(filename, Path.Consoles)

        # ~/.local/share/gem/icons/emulators
        if not exists(expanduser(Path.Emulators)):
            logger.debug("Copy emulators icons to %s" % Path.Emulators)
            mkdir(expanduser(Path.Emulators))

            for filename in glob(path_join(
                get_data("icons"), "emulators", "*")):
                if isfile(filename):
                    copy(filename, Path.Emulators)

        # ------------------------------------
        #   Create default configuration files
        # ------------------------------------

        logger.debug(_("Check configuration files"))

        if not exists(expanduser(path_join(Path.User, "gem.conf"))):
            logger.debug("Copy gem.conf to %s" % Path.User)
            copy(get_data(Conf.Default),
                expanduser(path_join(Path.User, "gem.conf")))

        if not exists(expanduser(path_join(Path.User, "consoles.conf"))):
            logger.debug("Copy consoles.conf to %s" % Path.User)
            copy(get_data(Conf.Consoles),
                expanduser(path_join(Path.User, "consoles.conf")))

        if not exists(expanduser(path_join(Path.User, "emulators.conf"))):
            logger.debug("Copy emulators.conf to %s" % Path.User)
            copy(get_data(Conf.Emulators),
                expanduser(path_join(Path.User, "emulators.conf")))

        # ------------------------------------
        #   Start main window
        # ------------------------------------

        # Check display settings
        if "DISPLAY" in environ and len(environ["DISPLAY"]) > 0:

            # ------------------------------------
            #   Manage lock
            # ------------------------------------

            with open(expanduser(Path.Lock), 'w') as pipe:
                pipe.write(str(getpid()))

            logger.debug("Start with PID %s" % getpid())

            # ------------------------------------
            #   Launch interface
            # ------------------------------------

            if args.preferences:
                from gem.preferences import Preferences
                Preferences(logger=logger).start()

            else:
                from gem.interface import launch_gem
                launch_gem(logger, args.reconstruct)

            # ------------------------------------
            #   Remove lock
            # ------------------------------------

            if exists(expanduser(Path.Lock)):
                remove(expanduser(Path.Lock))

        else:
            logger.critical(_("Cannot launch GEM without display"))

    except ImportError as error:
        logger.critical(_("Import error with interface: %s") % str(error))

    except KeyboardInterrupt as error:
        logger.warning(_("Terminate by keyboard interrupt"))

    except Exception as error:
        logger.critical(
            _("An error occur during program exec: %s") % str(error))


if __name__ == "__main__":
    sys_exit(main())
