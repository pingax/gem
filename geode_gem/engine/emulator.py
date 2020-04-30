# ------------------------------------------------------------------------------
#  Copyleft 2015-2020  PacMiam
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
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

# GEM
from geode_gem.engine.utils import get_binary_path
from geode_gem.engine.utils import generate_identifier

# System
from shlex import split as shlex_split


# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class Emulator(object):

    attributes = {
        "id": str,
        "name": str,
        "default": str,
        "windowed": str,
        "fullscreen": str,
        "icon": Path,
        "binary": Path,
        "configuration": Path,
        "savestates": Path,
        "screenshots": Path
    }

    def __init__(self, **kwargs):
        """ Constructor
        """

        # ----------------------------------------
        #   Initialization
        # ----------------------------------------

        # Initialize variables
        self.__init_keys(**kwargs)

    def __init_keys(self, **kwargs):
        """ Initialize object attributes
        """

        for key, key_type in self.attributes.items():

            if key in kwargs.keys():
                value = kwargs[key]

            elif key_type is Path:
                value = None

            else:
                value = key_type()

            setattr(self, key, value)

            if key_type is Path and type(value) is str:

                path = Path(value).expanduser()
                if len(value) == 0:
                    path = None

                setattr(self, key, path)

        setattr(self, "id", generate_identifier(self.name))

    def __get_content(self, attribute, game):
        """ Get content list for a specific game

        Parameters
        ----------
        attribute : pathlib.Path
            Emulator path attribute
        game : gem.engine.game.Game
            Game object

        Returns
        -------
        list
            return a files list
        """

        pattern = str(attribute)

        if "<rom_path>" in pattern:
            pattern = pattern.replace("<rom_path>", str(game.path.parent))

        if "<lname>" in pattern:
            pattern = pattern.replace("<lname>", game.path.stem.lower())

        elif "<name>" in pattern:
            pattern = pattern.replace("<name>", game.path.stem)

        if "<key>" in pattern and len(game.key) > 0:
            pattern = pattern.replace("<key>", game.key)

        files = list()

        path = Path(pattern).expanduser().resolve()

        # Check if parent path exists and is a directory
        if path.parent.exists() and path.parent.is_dir():

            for filename in path.parent.glob(path.name):

                # Only retrieve files which exists and are not directories
                if filename.exists() and filename.is_file():
                    files.append(filename)

        return files

    def as_dict(self):
        """ Return object as dictionary structure

        Returns
        -------
        dict
            Data structure
        """

        return {
            "binary": self.binary,
            "configuration": self.configuration,
            "icon": self.icon,
            "save": self.savestates,
            "snaps": self.screenshots,
            "default": self.default,
            "windowed": self.windowed,
            "fullscreen": self.fullscreen
        }

    @property
    def exists(self):
        """ Check if emulator binary exists in user system

        Returns
        -------
        bool
            return True if binary exist, False otherwise
        """

        if len(get_binary_path(self.binary)) > 0:
            return True

        return False

    def get_screenshots(self, game):
        """ Get screenshots list

        Parameters
        ----------
        game : gem.engine.game.Game
            Game object

        Returns
        -------
        list
            Files list

        See Also
        --------
        gem.engine.emulator.Emulator.__get_content()
        """

        return self.__get_content(self.screenshots, game)

    def get_savestates(self, game):
        """ Get savestates list

        Parameters
        ----------
        game : gem.engine.game.Game
            Game object

        Returns
        -------
        list
            Files list

        See Also
        --------
        gem.engine.emulator.Emulator.__get_content()
        """

        return self.__get_content(self.savestates, game)

    def get_command_line(self, game, fullscreen=False):
        """ Generate a launch command

        Parameters
        ----------
        fullscreen : bool, optional
            Use fullscreen parameters (Default: False)

        Returns
        -------
        list or None
            Command launcher parameters list, None otherwise
        """

        # Check emulator binary
        if not self.exists:
            raise FileNotFoundError(
                f"Cannot found emulator binary '{self.binary}'")

        # ----------------------------------------
        #   Retrieve default parameters
        # ----------------------------------------

        arguments = shlex_split(str(self.binary))

        # Retrieve fullscreen mode
        if fullscreen and self.fullscreen is not None:
            arguments.append(f" {self.fullscreen}")

        elif not fullscreen and self.windowed is not None:
            arguments.append(f" {self.windowed}")

        # Retrieve default or specific arguments
        if game.default:
            arguments.append(f" {game.default}")

        elif self.default:
            arguments.append(f" {self.default}")

        # ----------------------------------------
        #   Replace pattern substitutes
        # ----------------------------------------

        command = ' '.join(arguments).strip()

        need_gamefile = True

        keys = {
            "conf_path": self.configuration,
            "rom_name": game.path.stem,
            "rom_file": game.path,
            "rom_path": game.path.parent,
            "key": game.key
        }

        for key, value in keys.items():
            substring = f"<{key}>"

            if value is not None and substring in command:
                command = command.replace(substring, str(value))

                if key in ("rom_path", "rom_name", "rom_file"):
                    need_gamefile = False

        # ----------------------------------------
        #   Generate subprocess compatible command
        # ----------------------------------------

        arguments = shlex_split(command)
        if need_gamefile:
            arguments.append(str(game.path))

        return arguments
