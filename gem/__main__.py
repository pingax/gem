# ------------------------------------------------------------------------------
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
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
#   Modules - System
# ------------------------------------------------------------------------------

# Filesystem
from os import mkdir
from os import getpid
from os import remove
from os import environ

from os.path import isfile
from os.path import exists
from os.path import basename
from os.path import join as path_join

from glob import glob
from shutil import copy2 as copy

# System
from sys import exit as sys_exit
from argparse import ArgumentParser

# ------------------------------------------------------------------------------
#   Modules - GEM
# ------------------------------------------------------------------------------

try:
    from gem.utils import get_data

    from gem.api import GEM

except ImportError as error:
    sys_exit("Import error with gem module: %s" % str(error))

# ------------------------------------------------------------------------------
#   Modules - Translation
# ------------------------------------------------------------------------------

from gettext import gettext as _
from gettext import textdomain
from gettext import bindtextdomain

bindtextdomain("gem", get_data("i18n"))
textdomain("gem")

# ------------------------------------------------------------------------------
#   Launcher
# ------------------------------------------------------------------------------

def main():
    """ Main launcher
    """

    # Generate default arguments
    parser = ArgumentParser(
        description=" - ".join([ GEM.Name, GEM.Description ]),
        epilog=GEM.Copyleft, conflict_handler="resolve")

    parser.add_argument("-v", "--version", action="version",
        version="GEM %s (%s) - Licence GPLv3" % (GEM.Version, GEM.CodeName),
        help="show the current version")
    parser.add_argument("-d", "--debug",
        action="store_true", help="launch gem with debug flag")

    parser_interface = parser.add_argument_group("interface arguments")
    parser_interface.add_argument("-i", "--gtk-ui", default=True,
        action="store_true", help="launch gem with GTK+ interface (default)")
    parser_interface.add_argument("-p", "--gtk-config",
        action="store_true", help="configure gem with GTK+ interface")

    args = parser.parse_args()

    # ------------------------------------
    #   Initialize lock
    # ------------------------------------

    if exists(path_join(GEM.Local, ".lock")):
        gem_pid = int()

        # Read lock content
        with open(path_join(GEM.Local, ".lock"), 'r') as pipe:
            gem_pid = pipe.read()

        # Lock PID still exists
        if len(gem_pid) > 0 and exists(path_join("/proc", gem_pid)):
            path = path_join("/proc", gem_pid, "cmdline")

            # Check process command line
            if exists(path):
                with open(path, 'r') as pipe:
                    content = pipe.read()

                # Check if lock process is gem
                if "gem.main" in content or "gem-ui" in content:
                    sys_exit(_("GEM is already running with PID %s") % gem_pid)

    # ------------------------------------
    #   Initialize GEM API
    # ------------------------------------

    gem = GEM(debug=args.debug)

    # ------------------------------------
    #   Launch interface
    # ------------------------------------

    try:
        # Default configuration files
        for path in [ "gem.conf", "consoles.conf", "emulators.conf" ]:

            if not exists(path_join(GEM.Config, path)):
                gem.logger.debug("Copy default %s" % path)

                # Copy default configuration
                copy(get_data(path_join("config", path)),
                    path_join(GEM.Config, path))

        # ------------------------------------
        #   GTK interface
        # ------------------------------------

        if args.gtk_ui or args.gtk_config:

            # Check display settings
            if "DISPLAY" in environ and len(environ["DISPLAY"]) > 0:

                # Default folders
                for folder in [ "icons", "logs", "notes" ]:
                    if not exists(path_join(GEM.Local, folder)):
                        gem.logger.debug("Generate %s folder" % folder)

                        mkdir(path_join(GEM.Local, folder))

                # Icons folders
                for path in [ "consoles", "emulators" ]:

                    if not exists(path_join(GEM.Local, "icons", path)):
                        gem.logger.debug("Copy default %s icons" % path)

                        mkdir(path_join(GEM.Local, "icons", path))

                        # Copy default icons
                        for filename in glob(
                            path_join(get_data("icons"), path, "*")):

                            if isfile(filename):
                                copy(filename, path_join(GEM.Local,
                                    "icons", path, basename(filename)))

                # ------------------------------------
                #   Manage lock
                # ------------------------------------

                # Save current PID into lock file
                with open(path_join(GEM.Local, ".lock"), 'w') as pipe:
                    pipe.write(str(getpid()))

                gem.logger.debug("Start GEM with PID %s" % getpid())

                # ------------------------------------
                #   Launch interface
                # ------------------------------------

                # Start splash
                from gem.gtk.interface import Splash
                Splash(gem)

                # Start preferences
                if args.gtk_config:
                    from gem.gtk.preferences import Preferences
                    Preferences(gem).start()

                # Start interface
                elif args.gtk_ui:
                    from gem.gtk.interface import Interface
                    Interface(gem)

                # ------------------------------------
                #   Remove lock
                # ------------------------------------

                if exists(path_join(GEM.Local, ".lock")):
                    remove(path_join(GEM.Local, ".lock"))

            else:
                gem.logger.critical(_("Cannot launch GEM without display"))

    except ImportError as error:
        gem.logger.critical(_("Cannot import modules: %s") % str(error))
        return True

    except KeyboardInterrupt as error:
        gem.logger.warning(_("Terminate by keyboard interrupt"))
        return True

    except Exception as error:
        gem.logger.critical(_("An error occur during exec: %s") % str(error))
        return True

    return False

if __name__ == "__main__":
    main()
