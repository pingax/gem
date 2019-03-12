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
from os import R_OK
from os import access

from pathlib import Path

# GEM
from gem.engine.utils import generate_identifier

from gem.engine.game import Game
from gem.engine.emulator import Emulator

# Regex
from re import IGNORECASE
from re import compile as re_compile

# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class Console(object):

    attributes = {
        "id": (str, str()),
        "name": (str, str()),
        "icon": (Path, None),
        "path": (Path, None),
        "emulator": (Emulator, None),
        "ignores": (list, list()),
        "extensions": (list, list()),
        "favorite": (bool, False),
        "recursive": (bool, False)
    }


    def __init__(self, parent, **kwargs):
        """ Constructor

        Parameters
        ----------
        parent : gem.engine.api.GEM
            API instance
        """

        # ----------------------------------------
        #   Variables
        # ----------------------------------------

        self.__parent = parent

        self.__games = list()

        # ----------------------------------------
        #   Initialization
        # ----------------------------------------

        # Initialize variables
        self.__init_keys(**kwargs)


    def __init_keys(self, **kwargs):
        """ Initialize object attributes
        """

        for key, (key_type, default) in self.attributes.items():

            value = default
            if key in kwargs.keys():
                value = kwargs[key]

            setattr(self, key, value)

            if key_type is Path and type(value) is str:
                value = value.replace("<local>", str(self.__parent.get_local()))

                setattr(self, key, Path(value).expanduser())

            elif key_type is Emulator and type(value) is str:
                setattr(self, key, self.__parent.get_emulator(value))

            elif key_type is bool:

                if value == "yes":
                    setattr(self, key, True)

                elif value == "no":
                    setattr(self, key, False)

            elif key_type is list and type(value) is str:
                setattr(self, key, default)

                if len(value.strip()) > 0:
                    setattr(self, key, list(set(value.strip().split(';'))))

        setattr(self, "id", generate_identifier(self.name))


    def as_dict(self):
        """ Return object as dictionary structure

        Returns
        -------
        dict
            Data structure
        """

        return {
            "icon": str(self.icon),
            "roms": str(self.path),
            "exts": ';'.join(self.extensions),
            "ignores": ';'.join(self.ignores),
            "emulator": self.emulator,
            "favorite": self.favorite,
            "recursive": self.recursive
        }


    def init_games(self):
        """ Initialize games list from path directory

        Raises
        ------
        OSError
            when path directory was not founded
            when path is not a directory
            when path did not have read access
        """

        if self.path is not None:

            if not self.path.exists():
                raise OSError(2, "Directory not found", str(self.path))

            elif not self.path.is_dir():
                raise OSError(20, "Not a directory", str(self.path))

            elif not access(self.path, R_OK):
                raise OSError(1, "Operation not permitted", str(self.path))

            # Rest games list
            self.__games.clear()

            for extension in self.extensions:
                pattern = "*.%s" % extension

                if self.recursive:
                    files = self.path.rglob(pattern)

                else:
                    files = self.path.glob(pattern)

                # Retrieve files from games directory
                for filename in sorted(files):
                    game = Game(self.__parent, filename)

                    if game.emulator is None:
                        game.emulator = self.emulator

                    self.__games.append(game)


    def get_games(self):
        """ Retrieve games list

        Returns
        -------
        list
            Games list
        """

        return self.__games


    def get_game(self, key):
        """ Return specific game from current console

        Parameters
        ----------
        key : str
            Game identifier key

        Returns
        -------
        gem.engine.game.Game or None
            Game instance if found, None otherwise
        """

        return next((game for game in self.__games if game.id == key), None)


    def search_game(self, key):
        """ Search games from a specific key

        Parameters
        ----------
        key : str
            Key to search in games list (based on identifier and name)

        Returns
        -------
        generator
            Game instances
        """

        regex = re_compile(key, IGNORECASE)

        return (game for game in self.__games \
            if regex.search(game.name) or regex.search(game.id))