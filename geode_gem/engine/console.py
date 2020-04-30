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
from os import access, R_OK
from pathlib import Path

# GEM
from geode_gem.engine.utils import generate_extension, generate_identifier
from geode_gem.engine.game import Game
from geode_gem.engine.emulator import Emulator

# Regex
from re import IGNORECASE
from re import compile as re_compile


# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class Console(object):

    attributes = {
        "id": str,
        "name": str,
        "icon": Path,
        "path": Path,
        "emulator": Emulator,
        "ignores": list,
        "extensions": list,
        "favorite": bool,
        "recursive": bool
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

        for key, key_type in self.attributes.items():

            if key in kwargs.keys():
                value = kwargs[key]

            elif key_type is Emulator or key_type is Path:
                value = None

            elif key_type is bool:
                value = False

            else:
                value = key_type()

            setattr(self, key, value)

            if key_type is Path and type(value) is str:
                if "<local>" in value and hasattr(self.__parent, "get_local"):
                    value = value.replace(
                        "<local>", str(self.__parent.get_local()))

                path = Path(value).expanduser()
                if len(value) == 0:
                    path = None

                setattr(self, key, path)

            elif key_type is Emulator and type(value) is str:
                setattr(self, key, self.__parent.get_emulator(value))

            elif key_type is bool:

                if value == "yes":
                    setattr(self, key, True)

                elif value == "no":
                    setattr(self, key, False)

            elif key_type is list and type(value) is str:
                setattr(self, key, key_type())

                if len(value.strip()) > 0:
                    value = list(set(value.strip().split(';')))
                    value.sort()

                    setattr(self, key, value)

        if not self.name and self.path:
            setattr(self, "name", self.path.stem)

        setattr(self, "id", generate_identifier(self.name))

        if not self.name:
            setattr(self, "name", self.id)

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
        FileNotFoundError
            when path directory was not founded
        NotADirectoryError
            when path is not a directory
        PermissionError
            when path did not have read access
        """

        if self.path is not None:

            if not self.path.exists():
                raise FileNotFoundError(
                    f"Cannot found '{self.path}' in filesystem")

            elif not self.path.is_dir():
                raise NotADirectoryError(
                    f"'{self.path} is not a directory")

            elif not access(self.path, R_OK):
                raise PermissionError(
                    f"Read permission not available for '{self.path}'")

            # Rest games list
            self.__games.clear()

            for extension in self.extensions:
                pattern = f"*.{generate_extension(extension)}"

                if self.recursive:
                    files = self.path.rglob(pattern)

                else:
                    files = self.path.glob(pattern)

                # Retrieve files from games directory
                for filename in sorted(files):
                    self.add_game(filename)

    def add_game(self, filename):
        """ Add a new game

        Parameters
        ----------
        filename : str or pathlib.Path
            Game filepath

        Returns
        -------
        gem.engine.game.Game
            Game instance

        Raises
        ------
        ValueError
            when the filename was already added to Console collection
        """

        game = Game(self.__parent, filename)

        if self.get_game(game.id):
            raise ValueError(f"The Game ID '{game.id}' already exists in "
                             f"console '{self.name}'")

        if game.emulator is None:
            game.emulator = self.emulator

        self.__games.append(game)

        return game

    def delete_game(self, game):
        """ Remove a game from console storage

        Parameters
        ----------
        game : gem.engine.game.Game
            Game instance
        """

        if not isinstance(game, Game):
            raise TypeError(f"Cannot use specified game parameter, must be a "
                            f"{repr(Game)} object")

        if game not in self.__games:
            raise KeyError(
                f"Cannot remove game '{game.name}' from '{self.id}' console")

        self.__games.remove(game)

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
        list
            Found games list
        """

        regex = re_compile(key, IGNORECASE)

        return list(game for game in self.__games
                    if regex.search(game.name) or regex.search(game.id))
