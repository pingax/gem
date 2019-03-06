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

# Filesystem
from pathlib import Path

from shutil import copy2 as copy

# GEM
from gem.engine.api import GEM
from gem.engine.utils import get_data

from gem.engine.lib.configuration import Configuration

from gem.ui.data import Folders

# Mimetypes
from gem.ui.utils import magic_from_file

# System
from argparse import ArgumentParser

from os import environ

from sys import exit as sys_exit

# Translation
from gettext import textdomain
from gettext import bindtextdomain
from gettext import gettext as _

# ------------------------------------------------------------------------------
#   Launcher
# ------------------------------------------------------------------------------

def main():
    """ Main launcher
    """

    # ----------------------------------------
    #   Initialize environment
    # ----------------------------------------

    # Initialize localization
    bindtextdomain("gem", get_data("i18n"))
    textdomain("gem")

    # Initialize metadata
    metadata = Configuration(get_data("config", "metadata.conf"))

    # ----------------------------------------
    #   Generate arguments
    # ----------------------------------------

    parser = ArgumentParser(
        description="%s - %s" % (
            metadata.get("metadata", "name", fallback=str()),
            metadata.get("metadata", "version", fallback=str())),
        epilog=metadata.get("metadata", "copyleft", fallback=str()),
        conflict_handler="resolve")

    parser.add_argument("-v", "--version", action="version",
        version="%s %s (%s) - %s" % (
            metadata.get("metadata", "name", fallback=str()),
            metadata.get("metadata", "version", fallback=str()),
            metadata.get("metadata", "code_name", fallback=str()),
            metadata.get("metadata", "license", fallback=str())),
        help="show the current version")
    parser.add_argument("-d", "--debug", action="store_true",
        help="launch gem with debug flag")

    parser_api = parser.add_argument_group("api arguments")
    parser_api.add_argument("--cache", action="store",
        metavar="FOLDER",
        default=Folders.Cache,
        help="set cache folder (default: ~/.cache/gem/)")
    parser_api.add_argument("--config", action="store",
        metavar="FOLDER",
        default=Folders.Config,
        help="set configuration folder (default: ~/.config/gem/)")
    parser_api.add_argument("--local", action="store",
        metavar="FOLDER",
        default=Folders.Local,
        help="set data folder (default: ~/.local/share/gem/)")

    arguments = parser.parse_args()

    # ----------------------------------------
    #   Initialize GEM API
    # ----------------------------------------

    cache_path = Path(arguments.cache).expanduser()
    if not cache_path.exists():
        cache_path.mkdir(mode=0o755, parents=True)

    config_path = Path(arguments.config).expanduser()
    if not config_path.exists():
        config_path.mkdir(mode=0o755, parents=True)

    local_path = Path(arguments.local).expanduser()
    if not local_path.exists():
        local_path.mkdir(mode=0o755, parents=True)

    gem = GEM(config_path, local_path, arguments.debug)

    # ----------------------------------------
    #   Check lock
    # ----------------------------------------

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

    # ----------------------------------------
    #   Launch interface
    # ----------------------------------------

    try:
        # Default configuration files
        for filename in ("gem.conf", "consoles.conf", "emulators.conf"):
            path = Path(gem.get_config(filename)).expanduser()

            if not path.exists():
                gem.logger.debug("Copy default %s" % path)

                # Copy default configuration
                copy(get_data("config", filename), path)

        # ----------------------------------------
        #   Cache folders
        # ----------------------------------------

        icon_sizes = {
            "consoles": ("22x22", "24x24", "48x48", "64x64", "96x96"),
            "emulators": ("22x22", "48x48", "64x64"),
            "games": ("22x22", "96x96")
        }

        for name, sizes in icon_sizes.items():

            for size in sizes:
                path = Path(arguments.cache, name, size).expanduser()

                if not path.exists():
                    gem.logger.debug("Generate %s" % path)

                    path.mkdir(mode=0o755, parents=True)

        # ----------------------------------------
        #   GTK interface
        # ----------------------------------------

        # Check display settings
        if "DISPLAY" in environ and len(environ["DISPLAY"]) > 0:

            # Default folders
            for folder in ("logs", "notes"):
                path = Path(gem.get_local(folder)).expanduser()

                if not path.exists():
                    gem.logger.debug("Generate %s folder" % path)

                    path.mkdir(mode=0o755, parents=True)

            # ----------------------------------------
            #   GEM version < 1.0
            # ----------------------------------------

            move_collection = False

            # Remove older icons collections folders
            for folder in ("consoles", "emulators"):
                path = Path(gem.get_local("icons", folder)).expanduser()

                if path.exists() and path.is_dir():

                    # Remove files content
                    for filename in path.glob("*.png"):
                        filename.unlink()

                    # Remove folder
                    path.rmdir()

                    move_collection = True

            # ----------------------------------------
            #   Consoles icons
            # ----------------------------------------

            icons_path = Path(gem.get_local("icons")).expanduser()

            if not icons_path.exists():
                icons_path.mkdir(mode=0o755, parents=True)

                move_collection = True

            # Copy default icons
            if move_collection:
                gem.logger.debug("Generate consoles icons folder")

                path = Path(get_data("icons")).expanduser()

                for filename in path.glob("*.png"):

                    if filename.is_file():

                        # Check the file mime-type to avoid non-image file
                        mime = magic_from_file(filename, mime=True)

                        if mime.startswith("image/"):
                            copy(filename, icons_path.joinpath(filename.name))

            # ----------------------------------------
            #   Launch interface
            # ----------------------------------------

            gem.logger.debug("Start GEM with PID %s" % gem.pid)

            # Start splash
            from gem.ui.splash import Splash
            Splash(gem, metadata)

            # Start interface
            from gem.ui.interface import MainWindow
            MainWindow(gem, metadata, cache_path)

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
