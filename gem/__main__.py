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

# GEM
from gem.engine import *

from gem.engine.api import GEM
from gem.engine.utils import get_data

# System
from argparse import ArgumentParser

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

    parser_api = parser.add_argument_group("api arguments")
    parser_api.add_argument("--config", metavar="FOLDER", default=None,
        action="store", help="set configuration folder (default: ~/.config)")
    parser_api.add_argument("--local", metavar="FOLDER", default=None,
        action="store", help="set data folder (default: ~/.local/share)")
    parser_api.add_argument("--create-folders",
        action="store_true", help="create folders if not exists")

    parser_interface = parser.add_argument_group("interface arguments")
    parser_interface.add_argument("-i", "--gtk-ui", default=True,
        action="store_true", help="launch gem with GTK+ interface (default)")
    parser_interface.add_argument("-p", "--gtk-config",
        action="store_true", help="configure gem with GTK+ interface")

    args = parser.parse_args()

    # ------------------------------------
    #   Initialize GEM API
    # ------------------------------------

    if args.create_folders:

        if args.config is not None and not exists(args.config):
            makedirs(args.config)

        if args.local is not None and not exists(args.local):
            makedirs(args.local)

    gem = GEM(config=args.config, local=args.local, debug=args.debug)

    # ------------------------------------
    #   Initialize lock
    # ------------------------------------

    if exists(gem.get_local(".lock")):
        gem_pid = int()

        # Read lock content
        with open(gem.get_local(".lock"), 'r') as pipe:
            gem_pid = pipe.read()

        # Lock PID still exists
        if len(gem_pid) > 0 and exists(path_join("/proc", gem_pid)):
            path = path_join("/proc", gem_pid, "cmdline")

            # Check process command line
            if exists(path):
                with open(path, 'r') as pipe:
                    content = pipe.read()

                # Check if lock process is gem
                if "gem" in content or "gem-ui" in content:
                    sys_exit("GEM is already running with PID %s" % gem_pid)

    # ------------------------------------
    #   Launch interface
    # ------------------------------------

    try:
        # Default configuration files
        for path in [ "gem.conf", "consoles.conf", "emulators.conf" ]:

            if not exists(gem.get_config(path)):
                gem.logger.debug("Copy default %s" % path)

                # Copy default configuration
                copy(get_data(path_join("config", path)), gem.get_config(path))

        # ------------------------------------
        #   GTK interface
        # ------------------------------------

        if args.gtk_ui or args.gtk_config:
            bindtextdomain("gem", get_data("i18n"))
            textdomain("gem")

            # Check display settings
            if "DISPLAY" in environ and len(environ["DISPLAY"]) > 0:

                # Default folders
                for folder in [ "icons", "logs", "notes", "plugins" ]:
                    if not exists(gem.get_local(folder)):
                        gem.logger.debug("Generate %s folder" % folder)

                        mkdir(gem.get_local(folder))

                # Icons folders
                for path in [ "consoles", "emulators" ]:

                    if not exists(gem.get_local("icons", path)):
                        gem.logger.debug("Copy default %s icons" % path)

                        mkdir(gem.get_local("icons", path))

                        # Copy default icons
                        for filename in glob(
                            path_join(get_data("icons"), path, "*")):

                            if isfile(filename):
                                copy(filename, gem.get_local(
                                    "icons", path, basename(filename)))

                # ------------------------------------
                #   Manage lock
                # ------------------------------------

                # Save current PID into lock file
                with open(gem.get_local(".lock"), 'w') as pipe:
                    pipe.write(str(getpid()))

                gem.logger.debug("Start GEM with PID %s" % getpid())

                # ------------------------------------
                #   Launch interface
                # ------------------------------------

                # Start splash
                from gem.ui.splash import Splash
                Splash(gem)

                # Start preferences
                if args.gtk_config:
                    from gem.ui.preferences.interface import PreferencesWindow
                    PreferencesWindow(gem).run()

                # Start interface
                elif args.gtk_ui:
                    from gem.ui.interface import MainWindow
                    MainWindow(gem)

                # ------------------------------------
                #   Remove lock
                # ------------------------------------

                if exists(gem.get_local(".lock")):
                    remove(gem.get_local(".lock"))

            else:
                gem.logger.critical(_("Cannot launch GEM without display"))

    except ImportError as error:
        gem.logger.exception("Cannot import modules: %s" % str(error))
        return True

    except KeyboardInterrupt as error:
        gem.logger.warning("Terminate by keyboard interrupt")
        return True

    except Exception as error:
        gem.logger.exception("An error occur during exec: %s") % str(error)
        return True

    return False

if __name__ == "__main__":
    main()
