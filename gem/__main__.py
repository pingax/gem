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

from gem.ui.data import *

# Mimetypes
from gem.ui.utils import magic_from_file

# System
from argparse import ArgumentParser

from os import remove
from os import environ

from sys import exit as sys_exit

# Translation
from gettext import textdomain
from gettext import bindtextdomain
from gettext import gettext as _

# ------------------------------------------------------------------------------
#   Launcher
# ------------------------------------------------------------------------------

def init_environment():
    """ Initialize main environment
    """

    # Initialize localization
    bindtextdomain("gem", get_data("i18n"))
    textdomain("gem")

    # Initialize metadata
    metadata = Configuration(get_data("config", "metadata.conf"))

    # Retrieve metadata informations
    for key, value in metadata.items("metadata"):
        setattr(Metadata, key.upper(), value)

    # Retrieve icons informations
    for key, value in metadata.items("icons"):
        setattr(Icons, key.upper(), value)
        setattr(Icons.Symbolic, key.upper(), "%s-symbolic" % value)

    # Retrieve columns informations
    setattr(Columns, "ORDER",
        metadata.get("misc", "columns_order", fallback=str()))

    for key, value in metadata.items("list"):
        setattr(Columns.List, key.upper(), int(value))

    for key, value in metadata.items("grid"):
        setattr(Columns.Grid, key.upper(), int(value))


def init_configuration(gem):
    """ Initialize user configuration

    Parameters
    ----------
    gem : gem.engine.api.GEM
        GEM API instance
    """

    move_collection = False

    icon_sizes = {
        "consoles": ("22x22", "24x24", "48x48", "64x64", "96x96"),
        "emulators": ("22x22", "48x48", "64x64"),
        "games": ("22x22", "96x96")
    }

    # ----------------------------------------
    #   Configuration
    # ----------------------------------------

    for filename in ("gem.conf", "consoles.conf", "emulators.conf"):
        path = Folders.CONFIG.joinpath(filename)

        if not path.exists():
            gem.logger.debug("Copy default %s" % path)

            # Copy default configuration
            copy(get_data("config", filename), path)

    # ----------------------------------------
    #   Local
    # ----------------------------------------

    for folder in ("logs", "notes"):
        path = Folders.LOCAL.joinpath(folder)

        if not path.exists():
            gem.logger.debug("Generate %s folder" % path)

            path.mkdir(mode=0o755, parents=True)

    # ----------------------------------------
    #   Cache
    # ----------------------------------------

    for name, sizes in icon_sizes.items():

        for size in sizes:
            path = Folders.CACHE.joinpath(name, size)

            if not path.exists():
                gem.logger.debug("Generate %s" % path)

                path.mkdir(mode=0o755, parents=True)

    # ----------------------------------------
    #   Icons
    # ----------------------------------------

    icons_path = Folders.LOCAL.joinpath("icons")

    # Create icons storage folder
    if not icons_path.exists():
        icons_path.mkdir(mode=0o755, parents=True)

        move_collection = True

    # Remove older icons collections folders (GEM < 1.0)
    else:

        for folder in ("consoles", "emulators"):
            path = icons_path.joinpath(folder)

            if path.exists() and path.is_dir():
                remove(path)

                move_collection = True

    # Copy default icons
    if move_collection:
        gem.logger.debug("Generate consoles icons folder")

        for filename in get_data("icons").glob("*.png"):

            if filename.is_file():

                # Check the file mime-type to avoid non-image file
                mime = magic_from_file(filename, mime=True)

                if mime.startswith("image/"):
                    copy(filename, icons_path.joinpath(filename.name))


def main():
    """ Main launcher
    """

    # Initialize environment
    init_environment()

    # ----------------------------------------
    #   Generate arguments
    # ----------------------------------------

    parser = ArgumentParser(epilog=Metadata.COPYLEFT,
        description="%s - %s" % (Metadata.NAME, Metadata.VERSION),
        conflict_handler="resolve")

    parser.add_argument("-v", "--version", action="version",
        version="%s %s (%s) - %s" % (Metadata.NAME, Metadata.VERSION,
            Metadata.CODE_NAME, Metadata.LICENSE),
        help="show the current version")
    parser.add_argument("-d", "--debug", action="store_true",
        help="launch gem with debug flag")

    parser_api = parser.add_argument_group("api arguments")
    parser_api.add_argument("--cache", action="store", metavar="FOLDER",
        default=Folders.Default.CACHE,
        help="set cache folder (default: ~/.cache/)")
    parser_api.add_argument("--config", action="store", metavar="FOLDER",
        default=Folders.Default.CONFIG,
        help="set configuration folder (default: ~/.config/)")
    parser_api.add_argument("--local", action="store", metavar="FOLDER",
        default=Folders.Default.LOCAL,
        help="set data folder (default: ~/.local/share/)")

    arguments = parser.parse_args()

    # ----------------------------------------
    #   Initialize paths
    # ----------------------------------------

    setattr(Folders, "CACHE",
        Path(arguments.cache, "gem").expanduser().resolve())
    if not Folders.CACHE.exists():
        Folders.CACHE.mkdir(mode=0o755, parents=True)

    setattr(Folders, "CONFIG",
        Path(arguments.config, "gem").expanduser().resolve())
    if not Folders.CONFIG.exists():
        Folders.CONFIG.mkdir(mode=0o755, parents=True)

    setattr(Folders, "LOCAL",
        Path(arguments.local, "gem").expanduser().resolve())
    if not Folders.LOCAL.exists():
        Folders.LOCAL.mkdir(mode=0o755, parents=True)

    # ----------------------------------------
    #   Launch interface
    # ----------------------------------------

    try:
        gem = GEM(Folders.CONFIG, Folders.LOCAL, arguments.debug)

        if not gem.is_locked():

            # Check display settings
            if "DISPLAY" in environ and len(environ["DISPLAY"]) > 0:

                # Initialize main configuration files
                init_configuration(gem)

                gem.logger.debug("Start GEM with PID %s" % gem.pid)

                # Start splash
                from gem.ui.splash import Splash
                Splash(gem)

                # Start interface
                from gem.ui.interface import MainWindow
                MainWindow(gem, Folders.CACHE)

                # Remove lock
                gem.free_lock()

            else:
                gem.logger.critical(_("Cannot launch GEM without display"))

        else:
            try:
                # Show a GTK+ dialog to alert user
                from gi import require_version

                require_version("Gtk", "3.0")

                from gi.repository import Gtk

                dialog = Gtk.MessageDialog()
                dialog.set_transient_for(None)

                dialog.set_markup(
                    _("An instance already exists"))
                dialog.format_secondary_text(
                    _("GEM is already running with PID %d") % gem.pid)

                dialog.add_button(_("Close"), Gtk.ResponseType.CLOSE)

                dialog.run()
                dialog.destroy()

            except Exception as error:
                pass

            finally:
                sys_exit(_("GEM is already running with PID %d") % gem.pid)

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
