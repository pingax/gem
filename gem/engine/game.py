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

# Datetime
from datetime import date
from datetime import datetime
from datetime import timedelta

# Filesystem
from os.path import getctime

from pathlib import Path

# GEM
from gem.engine.utils import parse_timedelta
from gem.engine.utils import generate_identifier

from gem.engine.emulator import Emulator

# Regex
from re import compile as re_compile

# System
from shlex import split as shlex_split


# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class Game(object):

    attributes = {
        "id": str,
        "name": str,
        "key": str,
        "default": str,
        "cover": Path,
        "emulator": Emulator,
        "score": int,
        "played": int,
        "play_time": timedelta,
        "last_launch_time": timedelta,
        "last_launch_date": date,
        "installed": date,
        "tags": list,
        "environment": dict,
        "favorite": bool,
        "multiplayer": bool,
        "finish": bool
    }

    def __init__(self, parent, filename):
        """ Constructor

        Parameters
        ----------
        parent : gem.engine.api.GEM
            API instance
        filename : pathlib.Path
            Game file path
        """

        # ----------------------------------------
        #   Variables
        # ----------------------------------------

        self.__parent = parent

        self.__path = filename

        # ----------------------------------------
        #   Initialization
        # ----------------------------------------

        # Initialize attributes
        self.__init_attributes()

        # Initialize variables
        if self.__parent is not None:
            self.__init_from_database()

    def __init_attributes(self):
        """ Initialize object attributes
        """

        for key, key_type in self.attributes.items():

            if key_type is Emulator or key_type is Path:
                setattr(self, key, None)

            elif key_type is date and key == "installed":
                setattr(self, key, None)

            elif key_type is date:
                setattr(self, key, date(1, 1, 1))

            elif key_type is bool:
                setattr(self, key, False)

            else:
                setattr(self, key, key_type())

        setattr(self, "id", generate_identifier(self.__path))

        setattr(self, "name", self.__path.stem)

        setattr(self, "installed",
                datetime.fromtimestamp(getctime(self.__path)).date())

        self.environment.clear()
        if self.__parent is not None:
            environment = self.__parent.environment

            if self.id in environment.keys():
                for option in environment.options(self.id):
                    self.environment[option.upper()] = environment.get(
                        self.id, option, fallback=str())

    def __init_from_database(self):
        """ Initialize object with database results
        """

        # Retrieve data from database
        data = self.__parent.database.get(
            "games", {"filename": self.__path.name})

        if data is not None:

            # Retrieve time from a string (HH:MM:SS.MS)
            regex = re_compile(r"(\d+):(\d+):(\d+)[\.\d*]?")

            # Convert old column name from database to the new object scheme
            convert_keys = dict(
                play="played",
                arguments="default",
                last_play="last_launch_date",
                last_play_time="last_launch_time")

            for key, value in data.items():

                if key in convert_keys.keys():
                    key = convert_keys[key]

                if key in self.attributes.keys():
                    key_type = self.attributes[key]

                    if key_type is Path and type(value) is str:

                        path = Path(value).expanduser().resolve()
                        if len(value) == 0:
                            path = None

                        setattr(self, key, path)

                    elif key_type is Emulator and type(value) is str:
                        setattr(self, key, self.__parent.get_emulator(value))

                    elif key_type is int:
                        setattr(self, key, int(value))

                    elif key_type is bool:
                        setattr(self, key, bool(value))

                    elif key_type is list and type(value) is str:

                        if len(value) > 0:
                            value = list(set(value.strip().split(';')))
                            value.sort()

                            setattr(self, key, value)

                    elif key_type is dict:
                        pass

                    elif key_type is date:
                        day, month, year = 1, 1, 1

                        # Old GEM format
                        if len(value) > 10:
                            day, month, year = value.split()[0].split('-')

                        # ISO 8601 format
                        elif len(value) > 0:
                            year, month, day = value.split('-')

                        setattr(self, key,
                                date(int(year), int(month), int(day)))

                    elif key_type is timedelta:
                        result = regex.match(value)

                        if result is not None:
                            hours, minutes, seconds = result.groups()

                            setattr(self, key, timedelta(
                                    hours=int(hours),
                                    minutes=int(minutes),
                                    seconds=int(seconds)))

                    elif key_type is str and len(value) > 0:
                        setattr(self, key, value)

    def __get_content(self, pattern):
        """ Get content list for a specific game

        Parameters
        ----------
        pattern : str
            Game content path

        Returns
        -------
        list
            return a list
        """

        files = list()

        path = getattr(self.emulator, pattern, None)

        if path is not None:
            pattern = str(path)

            if "<rom_path>" in pattern:
                pattern = pattern.replace("<rom_path>", str(self.path.parent))

            if "<lname>" in pattern:
                pattern = pattern.replace("<lname>", self.path.stem.lower())

            elif "<name>" in pattern:
                pattern = pattern.replace("<name>", self.path.stem)

            if "<key>" in pattern and len(self.key) > 0:
                pattern = pattern.replace("<key>", self.key)

            path = Path(pattern).expanduser().resolve()

            # Check if parent path exists and is a directory
            if path.parent.exists() and path.parent.is_dir():

                for filename in path.parent.glob(path.name):

                    # Only retrieve files which exists and are not directories
                    if filename.exists() and filename.is_file():
                        files.append(filename)

        return files

    def __str__(self):
        """ Return a formatted string when using print function
        """

        return "[%s] %s" % (self.id, self.__path)

    def as_dict(self):
        """ Return object as dictionary structure

        Returns
        -------
        dict
            Data structure
        """

        return {
            "name": self.name,
            "filename": self.path.name,
            "favorite": self.favorite,
            "multiplayer": self.multiplayer,
            "finish": self.finish,
            "score": self.score,
            "play": self.played,
            "play_time": parse_timedelta(self.play_time),
            "last_play_time": parse_timedelta(self.last_launch_time),
            "last_play": self.last_launch_date,
            "emulator": self.emulator,
            "arguments": self.default,
            "tags": ';'.join(self.tags),
            "key": self.key,
            "cover": self.cover
        }

    def copy(self, filename):
        """ Copy game data into a new instance

        Parameters
        ----------
        filename : pathlib.Path
            Game file path

        Returns
        -------
        gem.engine.game.Game
            Game object
        """

        game = Game(self.__parent, filename)

        for key in self.attributes.keys():
            setattr(game, key, getattr(self, key, None))

        game.name = filename.stem

        return game

    def reset(self):
        """ Reset game attributes
        """

        self.__init_attributes()

    @property
    def path(self):
        """ Return the game absolute file path

        Returns
        -------
        pathlib.Path
            Game file path
        """

        return self.__path

    @property
    def extension(self):
        """ Return extension from filepath

        Returns
        -------
        str
            filename
        """

        extension = str()

        # Only retrieve extensions and not part of the name
        for subextension in self.__path.suffixes:
            if subextension not in self.__path.stem:
                extension += subextension.lower()

        return extension

    @property
    def screenshots(self):
        """ Get screenshots list

        See Also
        --------
        gem.engine.game.Game.__get_content()
        """

        return self.__get_content("screenshots")

    @property
    def savestates(self):
        """ Get savestates list

        See Also
        --------
        gem.engine.game.Game.__get_content()
        """

        return self.__get_content("savestates")

    def command(self, fullscreen=False):
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

        if self.emulator is not None:

            # Check emulator binary
            if not self.emulator.exists:
                raise OSError(2, "Cannot found emulator binary",
                              str(self.emulator.binary))

            # ----------------------------------------
            #   Retrieve default parameters
            # ----------------------------------------

            arguments = shlex_split(str(self.emulator.binary))

            # Retrieve fullscreen mode
            if fullscreen and self.emulator.fullscreen is not None:
                arguments.append(" %s" % str(self.emulator.fullscreen))
            elif not fullscreen and self.emulator.windowed is not None:
                arguments.append(" %s" % str(self.emulator.windowed))

            # Retrieve default or specific arguments
            if len(self.default) > 0:
                arguments.append(" %s" % str(self.default))
            elif len(self.emulator.default) > 0:
                arguments.append(" %s" % str(self.emulator.default))

            # ----------------------------------------
            #   Replace pattern substitutes
            # ----------------------------------------

            command = ' '.join(arguments).strip()

            need_gamefile = True

            keys = {
                "conf_path": self.emulator.configuration,
                "rom_name": self.path.stem,
                "rom_file": self.path,
                "rom_path": self.path.parent,
                "key": self.key
            }

            for key, value in keys.items():
                substring = "<%s>" % key

                if value is not None and substring in command:
                    command = command.replace(substring, str(value))

                    if key in ("rom_path", "rom_name", "rom_file"):
                        need_gamefile = False

            # ----------------------------------------
            #   Generate subprocess compatible command
            # ----------------------------------------

            arguments = shlex_split(command)

            if need_gamefile:
                arguments.append(str(self.path))

            return arguments

        return None

    def update_installation_date(self):
        """ Reload installation date from game file
        """

        setattr(self, "installed",
                datetime.fromtimestamp(getctime(self.__path)).date())
