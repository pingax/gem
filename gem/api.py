# ------------------------------------------------------------------
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
# ------------------------------------------------------------------

# ------------------------------------------------------------------
#   Modules
# ------------------------------------------------------------------

# Collections
from collections import OrderedDict

# Datetime
from datetime import time
from datetime import date

# Filesystem
from os import mkdir
from os import makedirs

from os.path import exists
from os.path import dirname
from os.path import basename
from os.path import splitext
from os.path import expanduser
from os.path import join as path_join

from glob import glob
from shutil import copy2 as copy

# Logging
import logging
from logging.config import fileConfig

# System
from sys import exit as sys_exit

# ------------------------------------------------------------------
#   Modules - GEM
# ------------------------------------------------------------------

try:
    from gem import Gem
    from gem import Conf
    from gem import Path
    from gem.utils import get_data
    from gem.database import Database
    from gem.configuration import Configuration

except ImportError as error:
    sys_exit("Cannot find gem module: %s" % str(error))

# ------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------

class GEM(object):

    def __init__(self, debug=False):
        """ Constructor

        Other parameters
        ----------------
        debug : bool
            Debug mode status (default: False)
        """

        if type(debug) is not bool:
            raise TypeError("Wrong type for debug, expected bool")

        # ----------------------------
        #   Variables
        # ----------------------------

        # Debug mode
        self.debug = debug

        # Consoles list
        self.consoles = dict()
        # Emulators list
        self.emulators = dict()

        # Configurations
        self.configurations = dict(
            consoles=None,
            emulators=None
        )

        # ----------------------------
        #   Initialize logger
        # ----------------------------

        # Define log path with a global variable
        logging.log_path = expanduser(path_join(Path.Data, "gem.log"))

        # Save older log file to ~/.local/share/gem/gem.log.old
        if(exists(logging.log_path)):
            copy(logging.log_path,
                expanduser(path_join(Path.Data, "gem.log.old")))

        # Generate logger from log.conf
        fileConfig(get_data(Conf.Log))

        self.logger = logging.getLogger("gem")

        if not self.debug:
            self.logger.setLevel(logging.INFO)

        # ----------------------------
        #   Initialize configuration
        # ----------------------------

        if not exists(expanduser(Path.User)):
            self.logger.debug("Create %s folder" % expanduser(Path.User))
            mkdir(expanduser(Path.User))

        # Check GEM configuration files
        for data in [ Conf.Consoles, Conf.Emulators ]:
            # Get configuration file without dirname
            path = basename(expanduser(data))
            # Get configuration filename for storage
            name, ext = splitext(path)

            # Configuration file not exists
            if not exists(expanduser(path_join(Path.User, path))):
                self.logger.debug(
                    "Copy %s to %s" % (path, expanduser(Path.User)))
                copy(data, expanduser(path_join(Path.User, path)))

            # Store Configuration object
            self.configurations[name] = Configuration(
                expanduser(path_join(Path.User, path)))

        # ----------------------------
        #   Initialize database
        # ----------------------------

        if not exists(expanduser(Path.Data)):
            self.logger.debug("Create %s folder" % expanduser(Path.Data))
            mkdir(expanduser(Path.Data))

        try:
            # Check GEM database file
            self.database = Database(expanduser(path_join(Path.Data, "gem.db")),
                get_data(Conf.Databases), self.logger)

            # Check current GEM version
            version = self.database.select("gem", "version")
            if not version == Gem.Version:
                if version is None:
                    version = Gem.Version

                    self.logger.info("Generate a new database")

                else:
                    self.logger.info("Update v%(old)s database to v%(new)s." % {
                        "old": version, "new": Gem.Version })

                self.database.modify("gem",
                    { "version": Gem.Version, "codename": Gem.CodeName },
                    { "version": version })

            # Migrate old databases
            if not self.database.check_integrity():
                self.logger.warning("Current database need to be updated")

                self.logger.info("Start database migration")
                self.database.migrate("games", Gem.OldColumns)

                self.logger.info("Migration complete")

        except OSError as error:
            sys_exit(error)

        except ValueError as error:
            sys_exit(error)

        # ----------------------------
        #   Initialize data
        # ----------------------------

        self.init_data()


    def __init_emulators(self):
        """ Initalize emulators
        """

        self.emulators = dict()

        data = self.configurations["emulators"]

        for section in data.sections():
            self.add_emulator({
                "name": section,
                "binary": data.get(
                    section, "binary", fallback=str()),
                "icon": data.get(
                    section, "icon", fallback=str()),
                "configuration": data.get(
                    section, "configuration", fallback=str()),
                "save": data.get(
                    section, "save", fallback=str()),
                "snaps": data.get(
                    section, "snaps", fallback=str()),
                "default": data.get(
                    section, "default", fallback=str()),
                "windowed": data.get(
                    section, "windowed", fallback=str()),
                "fullscreen": data.get(
                    section, "fullscreen", fallback=str())
            })


    def __init_consoles(self):
        """ Initalize consoles
        """

        self.consoles = dict()

        data = self.configurations["consoles"]

        for section in data.sections():

            emulator = data.get(section, "emulator", fallback=None)
            if emulator is not None and emulator in self.emulators:
                emulator = self.emulators[emulator]

            self.add_console({
                "name": section,
                "path": data.get(
                    section, "roms", fallback=str()),
                "icon": data.get(
                    section, "icon", fallback=str()),
                "extensions": data.get(
                    section, "exts", fallback=str()).split(';'),
                "emulator": emulator
            })


    def init_data(self):
        """ Initalize data from configuration files
        """

        self.__init_emulators()

        self.__init_consoles()


    def get_emulator(self, emulator):
        """ Get a specific emulator

        Parameters
        ----------
        emulator : str
            Emulator name

        Returns
        -------
        Emulator or None
            Found emulator
        """

        if emulator in self.emulators.keys():
            return self.emulators.get(emulator, None)

        return None


    def add_emulator(self, data):
        """ Add a new emulator

        Parameters
        ----------
        data : dict
            Emulator information as dictionary

        Raises
        ------
        TypeError
            if data type is not dict
        """

        if type(data) is not dict:
            raise TypeError("Wrong type for data, expected dict")

        if not "name" in data.keys():
            raise NameError("Missing name key in data dictionary")

        if not "binary" in data.keys():
            raise NameError("Missing binary key in data dictionary")

        if data["name"] in self.emulators.keys():
            raise ValueError("Emulator %s already exists" % data["name"])

        # ----------------------------
        #   Generate emulator
        # ----------------------------

        emulator = Emulator()

        for key, value in data.items():
            setattr(emulator, key, value)

        # Remove useless keys
        emulator.check_keys()

        # Store the new emulator
        self.emulators[data["name"].lower().replace(' ', '-')] = emulator


    def delete_emulator(self, emulator):
        """ Delete a specific emulator

        Parameters
        ----------
        emulator : str
            Emulator name
        """

        if not emulator in self.emulators.keys():
            raise IndexError("Cannot access to %s in emulators list" % emulator)

        del self.emulators[emulator]


    def get_console(self, console):
        """ Get a specific console

        Parameters
        ----------
        console : str
            Console name

        Returns
        -------
        gem.api.Console or None
            Found console

        Examples
        --------
        >>> g.get_console("nintendo-nes")
        <gem.api.Console object at 0x7f174a986b00>
        """

        if console in self.consoles.keys():
            return self.consoles.get(console, None)

        return None


    def add_console(self, data):
        """ Add a new console

        Parameters
        ----------
        data : dict
            Console information as dictionary

        Raises
        ------
        TypeError
            if data type is not dict
        """

        if type(data) is not dict:
            raise TypeError("Wrong type for data, expected dict")

        if not "name" in data.keys():
            raise NameError("Missing name key in data dictionary")

        if data["name"] in self.consoles.keys():
            raise ValueError("Console %s already exists" % data["name"])

        # ----------------------------
        #   Generate console
        # ----------------------------

        console = Console()

        for key, value in data.items():
            setattr(console, key, value)

        # Remove useless keys
        console.check_keys()

        # Set consoles games
        console.set_games(self)

        # Store the new emulator
        self.consoles[data["name"].lower().replace(' ', '-')] = console


    def delete_console(self, console):
        """ Delete a specific console

        Parameters
        ----------
        console : str
            Console name

        Raises
        ------
        IndexError
            if console not exists
        """

        if not console in self.consoles.keys():
            raise IndexError("Cannot access to %s in consoles list" % console)

        del self.consoles[console]


    def get_game(self, console, game):
        """ Get game from a specific console

        Parameters
        ----------
        console : str
            Console name
        game : str
            Game name

        Returns
        -------
        gem.api.Game or None
            Game object

        Raises
        ------
        IndexError
            if console not exists

        Examples
        --------
        >>> g.get_game("nintendo-nes", "Teenage Mutant Hero Turtles")
        <gem.api.Game object at 0x7f174a986f60>
        """

        if not console in self.consoles:
            raise IndexError("Cannot access to %s in consoles list" % console)

        # Check console games list
        return self.consoles[console].get_game(game)


class GEMObject(object):

    def __init__(self):
        """ Constructor
        """

        for key, value in self.attributes.items():
            setattr(self, key, value)


    def check_keys(self):
        """ Check every object attributes to eliminate useless keys
        """

        # Keys list to remove
        keys = list()

        # List object attributes
        for key in self.__dict__.keys():
            if not key in self.attributes.keys():
                keys.append(key)

        # Remove useless key
        for key in keys:
            delattr(self, key)


    def __str__(self):
        """ Formated informations

        Returns
        -------
        str
            Formated string
        """

        data = self.__dict__

        text = [ ":: %s ::" % self.name ]

        for key in OrderedDict(sorted(data.items(), key=lambda t: t[0])):
            if not key == "name" and not key[0] == '_':
                value = data[key]

                if type(value) is list:
                    value = len(value)

                if type(value) is Emulator:
                    value = value.name

                text.append("%s: %s" % (key, value))

        return '\n'.join(text)


class Emulator(GEMObject):

    attributes = {
        "name": str(),
        "icon": str(),
        "binary": str(),
        "configuration": str()
    }

    def __init__(self):
        """ Constructor
        """

        super(Emulator, self).__init__()


class Console(GEMObject):

    attributes = {
        "name": str(),
        "icon": str(),
        "path": str(),
        "extensions": list(),
        "games": list(),
        "emulator": None
    }

    def __init__(self):
        """ Constructor
        """

        super(Console, self).__init__()


    def set_games(self, parent):
        """ Set games from console roms path

        Parameters
        ----------
        parent : gem.api.GEM
            GEM API object

        Raises
        ------
        TypeError
            if database type is not gem.database.Database
        """

        # Get data from GEM
        database = parent.database
        emulators = parent.emulators

        # ----------------------------
        #   Check parameters
        # ----------------------------

        if type(database) is not Database:
            raise TypeError(
                "Wrong type for database, expected gem.database.Database")

        # ----------------------------
        #   Check games
        # ----------------------------

        self.games = list()

        # Check each extensions in games path
        for extension in self.extensions:

            # List available files
            for filename in set(glob("%s/*.%s" % (self.path, extension))):

                # Get data from database
                data = database.get("games", {"filename": basename(filename) })

                # Generate Game object
                game = Game()

                game_data = {
                    "filepath": filename,
                    "name": splitext(basename(filename))[0]
                }

                # This game exists in database
                if data is not None:

                    # Set game name
                    name = game_data["name"]
                    if len(data["name"]) > 0:
                        name = data["name"]

                    # Set game emulator
                    emulator = data["emulator"]
                    if len(emulator) > 0 and emulator in emulators:
                        emulator = emulators[emulator]

                    game_data.update({
                        "name": name,
                        "favorite": bool(data["favorite"]),
                        "multiplayer": bool(data["multiplayer"]),
                        "played": int(data["play"]),
                        "play_time": data["play_time"],
                        "last_launch_date": data["last_play"],
                        "last_launch_time": data["last_play_time"],
                        "emulator": emulator,
                        "arguments": data["arguments"],
                    })

                for key, value in game_data.items():
                    setattr(game, key, value)

                # Remove useless keys
                game.check_keys()

                self.games.append(game)

        # Sort games by name
        self.games = sorted(self.games, key=lambda game: game.name)


    def get_game(self, name):
        """ Return specific game from current console

        Parameters
        ----------
        name : str
            Game name

        Returns
        -------
        gem.api.Game or None
            Game object

        Examples
        --------
        >>> g.get_console("nintendo-nes").get_game("Metroid")
        <gem.api.Game object at 0x7f174a98e828>
        """

        for game in self.games:
            if game.name == name:
                return game

        return None


class Game(GEMObject):

    attributes = {
        "name": str(),
        "filepath": str(),
        "favorite": bool(),
        "multiplayer": bool(),
        "played": int(),
        "play_time": time(),
        "last_launch_time": None,
        "last_launch_date": None,
        "emulator": str(),
        "arguments": str()
    }

    def __init__(self):
        """ Constructor
        """

        super(Game, self).__init__()


    @property
    def path(self):
        """ Return basename and dirname from filepath

        Returns
        -------
        tuple
            Tuple which contains dirname and basename

        Raises
        ------
        ValueError
            If the filepath is empty or None

        Examples
        --------
        >>> g.get_console("nintendo-nes").get_game("Asterix").path
        ("~/.local/share/gem/roms/nes", "asterix.nes")
        """

        if self.filepath is None:
            raise TypeError("Wrong type for filepath, expected str")

        if len(self.filepath) == 0:
            raise ValueError("Found null length for filepath")

        return (
            dirname(expanduser(self.filepath)),
            basename(expanduser(self.filepath))
        )

if __name__ == "__main__":
    """ Debug GEM API
    """

    gem = GEM(debug=True)

    gem.logger.info("Found %d consoles" % len(gem.consoles))
    gem.logger.info("Found %d emulators" % len(gem.emulators))

    games = int()
    for console in gem.consoles:
        games += len(gem.get_console(console).games)

    gem.logger.info("Found %d games" % games)
