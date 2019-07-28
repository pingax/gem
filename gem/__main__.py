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

from shutil import rmtree

# GEM
from gem.engine.api import GEM
from gem.engine.utils import copy
from gem.engine.utils import get_data
from gem.engine.lib.configuration import Configuration

from gem.ui.data import Icons
from gem.ui.data import Columns
from gem.ui.data import Folders
from gem.ui.data import Metadata

# Logging
from logging import getLogger

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

def init_environment():
    """ Initialize main environment
    """

    # Initialize localization
    bindtextdomain("gem", str(get_data("data", "i18n")))
    textdomain("gem")

    # Initialize metadata
    metadata = Configuration(get_data("data", "config", "metadata.conf"))

    # Retrieve metadata informations
    if metadata.has_section("metadata"):
        for key, value in metadata.items("metadata"):
            setattr(Metadata, key.upper(), value)

    # Retrieve icons informations
    if metadata.has_section("icons"):
        for key, value in metadata.items("icons"):
            setattr(Icons, key.upper(), value)
            setattr(Icons.Symbolic, key.upper(), "%s-symbolic" % value)

    if metadata.has_section("icon-sizes"):
        for key, value in metadata.items("icon-sizes"):
            setattr(Icons.Size, key.upper(), value.split())

    # Retrieve columns informations
    if metadata.has_section("misc"):
        setattr(Columns, "ORDER",
                metadata.get("misc", "columns_order", fallback=str()))

    if metadata.has_section("list"):
        for key, value in metadata.items("list"):
            setattr(Columns.List, key.upper(), int(value))

    if metadata.has_section("grid"):
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

    # ----------------------------------------
    #   Configuration
    # ----------------------------------------

    for filename in ("gem.conf", "consoles.conf", "emulators.conf"):
        path = Folders.CONFIG.joinpath(filename)

        if not path.exists():
            gem.logger.debug("Copy default %s" % path)

            # Copy default configuration
            copy(get_data("data", "config", filename), path)

    # ----------------------------------------
    #   Local
    # ----------------------------------------

    for folder in ("logs", "notes"):
        path = Folders.LOCAL.joinpath(folder)

        if not path.exists():
            gem.logger.debug("Generate %s folder" % path)

            try:
                path.mkdir(mode=0o755, parents=True)

            except FileExistsError:
                gem.logger.error("Path %s already exists" % str(path))

    # ----------------------------------------
    #   Cache
    # ----------------------------------------

    for name in ("consoles", "emulators", "games"):
        sizes = getattr(Icons.Size, name.upper(), list())

        for size in sizes:
            path = Folders.CACHE.joinpath(name, "%sx%s" % (size, size))

            if not path.exists():
                gem.logger.debug("Generate %s" % path)

                try:
                    path.mkdir(mode=0o755, parents=True)

                except FileExistsError:
                    gem.logger.error("Path %s already exists" % str(path))

    # ----------------------------------------
    #   Icons
    # ----------------------------------------

    icons_path = Folders.LOCAL.joinpath("icons")

    # Create icons storage folder
    if not icons_path.exists():
        gem.logger.debug("Generate %s" % icons_path)

        try:
            icons_path.mkdir(mode=0o755, parents=True)

        except FileExistsError:
            gem.logger.error("Path %s already exists" % str(icons_path))

        finally:
            move_collection = True

    # Remove older icons collections folders (GEM < 1.0)
    else:

        for folder in ("consoles", "emulators"):
            path = icons_path.joinpath(folder)

            if path.exists():

                if path.is_dir():
                    rmtree(path)

                elif path.is_symlink():
                    path.unlink()

                move_collection = True

    # Copy default icons
    if move_collection:
        gem.logger.debug("Generate consoles icons folder")

        for filename in get_data("data", "icons").glob("*.png"):

            if filename.is_file():

                # Check the file mime-type to avoid non-image file
                mime = magic_from_file(filename, mime=True)

                if mime.startswith("image/"):
                    new_path = icons_path.joinpath(filename.name)

                    if not new_path.exists():
                        gem.logger.debug("Copy %s" % str(new_path))

                        copy(filename, new_path)


def main():
    """ Main launcher
    """

    # Initialize environment
    init_environment()

    # ----------------------------------------
    #   Generate arguments
    # ----------------------------------------

    parser = ArgumentParser(epilog=Metadata.COPYLEFT,
                            description="%s - %s" % (Metadata.NAME,
                                                     Metadata.VERSION),
                            conflict_handler="resolve")

    parser.add_argument("-v", "--version", action="version",
                        version="%s %s (%s) - %s" % (Metadata.NAME,
                                                     Metadata.VERSION,
                                                     Metadata.CODE_NAME,
                                                     Metadata.LICENSE),
                        help="show the current version")
    parser.add_argument("-d", "--debug", action="store_true",
                        help="launch gem with debug flag")

    parser_api = parser.add_argument_group("api arguments")
    parser_api.add_argument("--cache", action="store", metavar="FOLDER",
                            default=Folders.Default.CACHE,
                            help="set cache folder (default: %s)" % (
                                Path('~/.cache').expanduser())),
    parser_api.add_argument("--config", action="store", metavar="FOLDER",
                            default=Folders.Default.CONFIG,
                            help="set configuration folder (default: %s)" % (
                                Path('~/.config').expanduser())),
    parser_api.add_argument("--local", action="store", metavar="FOLDER",
                            default=Folders.Default.LOCAL,
                            help="set data folder (default: %s)" % (
                                Path('~/.local/share').expanduser()))

    parser_maintenance = parser.add_argument_group("maintenance arguments")
    parser_maintenance.add_argument("--clean-cache", action="store_true",
                                    help="clean icons cache directory")

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
    #   Maintenance
    # ----------------------------------------

    if Folders.CACHE.exists() and arguments.clean_cache:

        if Folders.CACHE.is_dir():
            rmtree(Folders.CACHE)

        if not Folders.CACHE.exists():
            Folders.CACHE.mkdir(mode=0o755, parents=True)

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

                getLogger("gem").info("Start GEM with PID %s" % gem.pid)

                # Start splash
                from gem.ui.splash import Splash
                Splash(gem)

                # Start interface
                from gem.ui.interface import MainWindow
                MainWindow(gem, Folders.CACHE)

                # Remove lock
                gem.free_lock()

            else:
                getLogger("gem").critical("Cannot launch GEM without display")

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

            except Exception:
                getLogger("gem").critical("Cannot start dialog instance")

            finally:
                sys_exit("GEM is already running with PID %d" % gem.pid)

    except ImportError:
        getLogger("gem").exception("An error occur durint modules importation")
        return True

    except KeyboardInterrupt:
        getLogger("gem").warning("Terminate by keyboard interrupt")
        return True

    except Exception:
        getLogger("gem").exception("An error occur during execution")
        return True

    return False


if __name__ == "__main__":
    main()
