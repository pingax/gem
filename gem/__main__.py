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

from gem.ui.data import Icons
from gem.ui.data import Folders

# System
from argparse import ArgumentParser

# Translation
from gettext import gettext as _

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
    parser.add_argument(
        "-d", "--debug", action="store_true", help="launch gem with debug flag")

    parser_api = parser.add_argument_group("api arguments")
    parser_api.add_argument(
        "--cache", metavar="FOLDER", default=Folders.Cache, action="store",
        help="set cache folder (default: ~/.cache/gem/)")
    parser_api.add_argument(
        "--config", metavar="FOLDER", default=Folders.Config, action="store",
        help="set configuration folder (default: ~/.config/gem/)")
    parser_api.add_argument(
        "--local", metavar="FOLDER", default=Folders.Local, action="store",
        help="set data folder (default: ~/.local/share/gem/)")

    args = parser.parse_args()

    # ------------------------------------
    #   Initialize GEM API
    # ------------------------------------

    # Initialize localization
    bindtextdomain("gem", get_data("i18n"))
    textdomain("gem")

    if args.cache is not None and not exists(args.cache):
        makedirs(args.cache)

    if args.config is not None and not exists(args.config):
        makedirs(args.config)

    if args.local is not None and not exists(args.local):
        makedirs(args.local)

    gem = GEM(config=args.config, local=args.local, debug=args.debug)

    # ------------------------------------
    #   Check lock
    # ------------------------------------

    if gem.is_locked():

        try:
            # Show a GTK+ dialog to alert user
            from gi import require_version

            require_version("Gtk", "3.0")

            from gi.repository import Gtk

            dialog = Gtk.MessageDialog(None, 0, Gtk.MessageType.INFO,
                Gtk.ButtonsType.OK, _("A GEM instance already exists"))
            dialog.format_secondary_text(
                _("GEM is already running with PID %d") % gem.pid)

            dialog.run()
            dialog.destroy()

        except Exception:
            pass

        finally:
            sys_exit("GEM is already running with PID %d" % gem.pid)

    # ------------------------------------
    #   Launch interface
    # ------------------------------------

    try:
        # Default configuration files
        for path in ("gem.conf", "consoles.conf", "emulators.conf"):

            if not exists(gem.get_config(path)):
                gem.logger.debug("Copy default %s" % path)

                # Copy default configuration
                copy(get_data(path_join("config", path)), gem.get_config(path))

        # ------------------------------------
        #   Cache folders
        # ------------------------------------

        icon_sizes = {
            "consoles": ("22x22", "24x24", "48x48", "64x64", "96x96"),
            "emulators": ("22x22", "48x48", "64x64"),
            "games": ("22x22", "96x96")
        }

        for name, sizes in icon_sizes.items():

            for size in sizes:
                path = expanduser(path_join(args.cache, name, size))

                if not exists(path):
                    gem.logger.debug("Generate %s" % path)

                    makedirs(path)

        # ------------------------------------
        #   GTK interface
        # ------------------------------------

        # Check display settings
        if "DISPLAY" in environ and len(environ["DISPLAY"]) > 0:

            # Default folders
            for folder in ("icons", "logs", "notes"):

                if not exists(gem.get_local(folder)):
                    gem.logger.debug("Generate %s folder" % folder)

                    makedirs(gem.get_local(folder))

            # ------------------------------------
            #   GEM version < 1.0
            # ------------------------------------

            move_collection = False

            # Remove older icons collections folders
            for folder in ("consoles", "emulators"):
                path = gem.get_local("icons", folder)

                if exists(path) and isdir(path):
                    rmtree(path)

                    move_collection = True

            # ------------------------------------
            #   Consoles icons
            # ------------------------------------

            icons_path = expanduser(gem.get_local("icons"))

            if not exists(icons_path):
                makedirs(icons_path)

                move_collection = True

            # Copy default icons
            if move_collection:
                gem.logger.debug("Generate consoles icons folder")

                for path in glob(path_join(icons_path, "*.%s" % Icons.Ext)):

                    # Check the file mime-type to avoid non-image file
                    if isfile(path) and magic_from_file(
                        path, mime=True).startswith("image/"):

                        copy(path, gem.get_local("icons", basename(path)))

            # ------------------------------------
            #   Launch interface
            # ------------------------------------

            gem.logger.debug("Start GEM with PID %s" % gem.pid)

            # Start splash
            from gem.ui.splash import Splash
            Splash(gem)

            # Start interface
            from gem.ui.interface import MainWindow
            MainWindow(gem, args.cache)

            # Remove lock
            gem.free_lock()

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
