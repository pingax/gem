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

# ------------------------------------------------------------------------------
#   Modules
# ------------------------------------------------------------------------------

# Collections
from collections import OrderedDict

# Datetime
from datetime import time
from datetime import date
from datetime import timedelta

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
from shutil import move
from shutil import copy2 as copy

# Logging
import logging
from logging.config import fileConfig

# System
from sys import exit as sys_exit
from shlex import split as shlex_split

# ------------------------------------------------------------------------------
#   Modules - XDG
# ------------------------------------------------------------------------------

try:
    from xdg.BaseDirectory import xdg_data_home
    from xdg.BaseDirectory import xdg_config_home

except ImportError as error:
    from os import environ

    if "XDG_DATA_HOME" in environ:
        xdg_data_home = environ["XDG_DATA_HOME"]
    else:
        xdg_data_home = expanduser("~/.local/share")

    if "XDG_CONFIG_HOME" in environ:
        xdg_config_home = environ["XDG_CONFIG_HOME"]
    else:
        xdg_config_home = expanduser("~/.config")

# ------------------------------------------------------------------------------
#   Modules - GEM
# ------------------------------------------------------------------------------

try:
    from gem.utils import get_data
    from gem.utils import get_binary_path
    from gem.utils import generate_identifier
    from gem.database import Database
    from gem.configuration import Configuration

except ImportError as error:
    sys_exit("Cannot find gem module: %s" % str(error))

# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class GEM(object):

    # Informations
    Name        = "Graphical Emulators Manager"
    Description = "Manage your emulators easily and have fun"
    Version     = "0.7"
    CodeName    = "Vampire hunter"
    Website     = "https://gem.tuxfamily.org/"
    Copyleft    = "Copyleft 2017 - Kawa Team"
    Acronym     = "GEM"
    Icon        = "gem"

    # Files
    Log         = "gem.log"
    Logger      = "log.conf"
    Consoles    = "consoles.conf"
    Emulators   = "emulators.conf"
    Databases   = "databases.conf"

    # Paths
    Local       = path_join(expanduser(xdg_data_home), "gem")
    Config      = path_join(expanduser(xdg_config_home), "gem")

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

        # Data list
        self.__data = dict(
            consoles=list(),
            emulators=list()
        )

        # Configurations
        self.__configurations = dict(
            consoles=None,
            emulators=None
        )

        # ----------------------------
        #   Initialize logger
        # ----------------------------

        # Define log path with a global variable
        logging.log_path = path_join(GEM.Local, GEM.Log)

        # Save older log file to ~/.local/share/gem/gem.log.old
        if(exists(logging.log_path)):
            copy(logging.log_path, path_join(GEM.Local, GEM.Log + ".old"))

        # Generate logger from log.conf
        fileConfig(get_data(path_join("config", GEM.Logger)))

        self.logger = logging.getLogger("gem")

        if not self.debug:
            self.logger.setLevel(logging.INFO)

        # ----------------------------
        #   Initialize database
        # ----------------------------

        if not exists(GEM.Local):
            self.logger.debug("Create %s folder" % GEM.Local)
            mkdir(GEM.Local)

        try:
            # Check GEM database file
            self.database = Database(path_join(GEM.Local, "gem.db"),
                get_data(path_join("config", GEM.Databases)), self.logger)

            # Check current GEM version
            version = self.database.select("gem", "version")

            # Check Database inner version and GEM version
            if not version == GEM.Version:
                if version is None:
                    self.logger.info("Generate a new database")
                    version = GEM.Version

                else:
                    self.logger.info(
                        "Update database to version %s" % GEM.Version)

                self.database.modify("gem",
                    { "version": GEM.Version, "codename": GEM.CodeName },
                    { "version": version })

            else:
                self.logger.debug("Use GEM API v.%s" % GEM.Version)

            # Check integrity and migrate if necessary
            self.logger.info("Check database integrity")
            if not self.database.check_integrity():
                self.logger.warning("Database need to be migrate")

                self.logger.info("Start database migration")
                self.database.migrate("games", dict())

                self.logger.info("Migration complete")

            else:
                self.logger.info("Current database is up-to-date")

        except OSError as error:
            self.logger.critical("OSError: %s" % str(error))
            sys_exit(error)

        except ValueError as error:
            self.logger.critical("ValueError: %s" % str(error))
            sys_exit(error)

        except Exception as error:
            self.logger.critical("Exception: %s" % str(error))
            sys_exit(error)

        # ----------------------------
        #   Initialize data
        # ----------------------------

        self.init_data()


    def __init_configurations(self):
        """ Initalize configuration
        """

        if not exists(GEM.Config):
            self.logger.debug("Create %s folder" % GEM.Config)
            mkdir(GEM.Config)

        # Check GEM configuration files
        for path in [ GEM.Consoles, GEM.Emulators ]:
            # Get configuration filename for storage
            name, ext = splitext(path)

            # Configuration file not exists
            if not exists(path_join(GEM.Config, path)):
                self.logger.debug("Copy %s to %s" % (path, GEM.Config))
                copy(path, path_join(GEM.Config, path))

            self.logger.debug("Read %s configuration file" % path)

            # Store Configuration object
            self.__configurations[name] = Configuration(
                path_join(GEM.Config, path))


    def __init_emulators(self):
        """ Initalize emulators
        """

        self.__data["emulators"] = dict()

        data = self.__configurations["emulators"]

        for section in data.sections():
            # Configuration
            configuration = data.get(section, "configuration", fallback=None)
            if configuration is not None:
                # Empty string
                if len(configuration) == 0:
                    configuration = None
                # Need to expanduser path
                else:
                    configuration = expanduser(configuration)

            # Savestates
            savestates = data.get(section, "save", fallback=None)
            if savestates is not None and len(savestates) == 0:
                savestates = None

            # Screenshots
            screenshots = data.get(section, "snaps", fallback=None)
            if screenshots is not None and len(screenshots) == 0:
                screenshots = None

            # Default
            default = data.get(section, "default", fallback=None)
            if default is not None and len(default) == 0:
                default = None

            # Windowed
            windowed = data.get(section, "windowed", fallback=None)
            if windowed is not None and len(windowed) == 0:
                windowed = None

            # Fullscreen
            fullscreen = data.get(section, "fullscreen", fallback=None)
            if fullscreen is not None and len(fullscreen) == 0:
                fullscreen = None

            self.add_emulator({
                "id": generate_identifier(section),
                "name": section,
                "binary": expanduser(data.get(
                    section, "binary", fallback=str())),
                "icon": data.get(
                    section, "icon", fallback=str()),
                "configuration": configuration,
                "savestates": savestates,
                "screenshots": screenshots,
                "default": default,
                "windowed": windowed,
                "fullscreen": fullscreen
            })

        self.logger.debug(
            "%d emulator(s) has been founded" % len(self.emulators))


    def __init_consoles(self):
        """ Initalize consoles
        """

        self.__data["consoles"] = dict()

        data = self.__configurations["consoles"]

        for section in data.sections():
            emulator = data.get(section, "emulator", fallback=None)

            # Emulator exists in GEM storage
            if emulator is not None and emulator in self.__data["emulators"]:
                emulator = self.__data["emulators"][emulator]

            self.add_console({
                "id": generate_identifier(section),
                "name": section,
                "path": expanduser(data.get(
                    section, "roms", fallback=str())),
                "icon": data.get(
                    section, "icon", fallback=str()),
                "extensions": data.get(
                    section, "exts", fallback=str()).split(';'),
                "emulator": emulator
            })

        self.logger.debug(
            "%d console(s) has been founded" % len(self.consoles))


    def init_data(self):
        """ Initalize data from configuration files
        """

        self.__init_configurations()

        self.__init_emulators()

        self.__init_consoles()


    def write_data(self):
        """ Write data into configuration files

        Returns
        -------
        bool
            return True if files are successfully writed, False otherwise

        Notes
        -----
        Previous files are backup
        """

        self.logger.debug("Store GEM data into disk")

        try:
            # Check GEM configuration files
            for path in [ GEM.Consoles, GEM.Emulators ]:
                # Get configuration filename for storage
                name, ext = splitext(path)

                # Backup configuration file
                self.logger.debug("Backup ~%s configuration file" % path)
                move(path_join(GEM.Config, path),
                    path_join(GEM.Config, '~' + path))

                # Create a new configuration object
                config = Configuration(path_join(GEM.Config, path))

                # Feed configuration with new data
                for element in sorted(self.__data[name]):
                    section, structure = self.__data[name][element].as_dict()

                    for key, value in sorted(structure.items()):
                        if value is None:
                            value = str()

                        config.modify(section, key, value)

                # Write new configuration file
                self.logger.info("Write %s configuration file" % path)
                config.update()

        except Exception as error:
            self.logger.critical(
                "An error occur during GEM.write_data: %s" % str(error))

            return False

        return True


    @property
    def consoles(self):
        """ Return consoles list

        Returns
        -------
        list
            Consoles list
        """

        return self.__data["consoles"]


    @property
    def emulators(self):
        """ Return emulators list

        Returns
        -------
        list
            emulators list
        """

        return self.__data["emulators"]


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

        if emulator is not None and len(emulator) > 0:

            if emulator in self.__data["emulators"].keys():
                return self.__data["emulators"].get(emulator, None)

            # Check if emulator use name instead of identifier
            identifier = generate_identifier(console)

            if identifier in self.__data["emulators"].keys():
                return self.__data["emulators"].get(identifier, None)

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

        if data["name"] in self.__data["emulators"].keys():
            raise ValueError("Emulator %s already exists" % data["name"])

        # ----------------------------
        #   Generate emulator
        # ----------------------------

        emulator = Emulator()

        for key, value in data.items():
            if value is not None and len(value) == 0:
                value = None

            setattr(emulator, key, value)

        # Remove useless keys
        emulator.check_keys()

        # Store the new emulator
        self.__data["emulators"][data["id"]] = emulator


    def delete_emulator(self, emulator):
        """ Delete a specific emulator

        Parameters
        ----------
        emulator : str
            Emulator name
        """

        if not emulator in self.__data["emulators"].keys():
            raise IndexError("Cannot access to %s in emulators list" % emulator)

        del self.__data["emulators"][emulator]


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
        >>> g = GEM()
        >>> g.get_console("nintendo-nes")
        <gem.api.Console object at 0x7f174a986b00>
        """

        if console is not None and len(console) > 0:

            if console in self.__data["consoles"].keys():
                return self.__data["consoles"].get(console, None)

            # Check if console use name instead of identifier
            identifier = generate_identifier(console)

            if identifier in self.__data["consoles"].keys():
                return self.__data["consoles"].get(identifier, None)

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

        if data["name"] in self.__data["consoles"].keys():
            raise ValueError("Console %s already exists" % data["name"])

        # ----------------------------
        #   Generate console
        # ----------------------------

        console = Console()

        for key, value in data.items():
            if type(value) is not Emulator and \
                value is not None and len(value) == 0:
                value = None

            setattr(console, key, value)

        # Remove useless keys
        console.check_keys()

        # Set consoles games
        console.set_games(self)

        # Store the new emulator
        self.__data["consoles"][data["id"]] = console


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

        if not console in self.__data["consoles"].keys():
            raise IndexError("Cannot access to %s in consoles list" % console)

        del self.__data["consoles"][console]


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
        >>> g = GEM()
        >>> g.get_game("nintendo-nes", "Teenage Mutant Hero Turtles")
        <gem.api.Game object at 0x7f174a986f60>
        """

        if not console in self.__data["consoles"]:
            raise IndexError("Cannot access to %s in consoles list" % console)

        # Check console games list
        return self.__data["consoles"][console].get_game(game)


    def update_game(self, game):
        """ Update a game in database

        Parameters
        ----------
        game : gem.api.Game
            Game object

        Returns
        -------
        bool
            return True if update successfully, False otherwise

        Raises
        ------
        TypeError
            if game type is not gem.api.Game
        """

        if type(game) is not Game:
            raise TypeError("Wrong type for game, expected gem.api.Game")

        # Store game data
        name, data = game.as_dict()

        # Translate value as string for database
        for key, value in data.items():

            # Strange case where type(None) is NoneType :D
            if type(value) == type(None):
                data[key] = str()

            elif type(value) is bool:
                data[key] = str(int(value))

            elif type(value) is int:
                data[key] = str(value)

            elif type(value) is Emulator:
                data[key] = str(value.name)

        # Update game in database
        self.logger.info("Update database for %s" % game.name)

        self.database.modify("games", data, { "filename": game.path[1] })


    def delete_game(self, game):
        """ Delete a specific game

        Parameters
        ----------
        game : gem.api.Game
            Game object

        Raises
        -------
        TypeError
            if game type is not gem.api.Game
        """

        if type(game) is not Game:
            raise TypeError("Wrong type for game, expected gem.api.Game")

        results = self.database.get("games", { "filename": game.path[1] })

        if results is not None and len(results) > 0:
            self.logger.info("Remove %s from database" % game.name)

            self.database.remove("games", { "filename": game.path[1] })


class GEMObject(object):

    def __init__(self):
        """ Constructor
        """

        for key, value in self.attributes.items():
            setattr(self, key, value)


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


class Emulator(GEMObject):

    attributes = {
        "id": str(),
        "name": str(),
        "icon": str(),
        "binary": str(),
        "configuration": None,
        "savestates": None,
        "screenshots": None,
        "default": None,
        "windowed": None,
        "fullscreen": None
    }

    def __init__(self):
        """ Constructor
        """

        super(Emulator, self).__init__()


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


    def __get_content(self, key, game):
        """ Get content list for a specific game

        Parameters
        ----------
        game : gem.api.Game
            Game object

        Returns
        -------
        list
            return a list

        Raises
        ------
        TypeError
            if game type is not gem.api.Game
        """

        if type(game) is not Game:
            raise TypeError("Wrong type for game, expected gem.api.Game")

        if key is not None:
            if "<rom_path>" in key:
                pattern = key.replace("<rom_path>", game.path[0])

            if "<lname>" in key:
                pattern = key.replace("<lname>", game.filename).lower()
            else:
                pattern = key.replace("<name>", game.filename)

            return glob(pattern)

        return list()


    def get_screenshots(self, game):
        """ Get screenshots list for a specific game

        Parameters
        ----------
        game : gem.api.Game
            Game object

        See Also
        --------
        gem.api.Emulator.__get_content()
        """

        return self.__get_content(self.screenshots, game)


    def get_savestates(self, game):
        """ Get savestates list for a specific game

        Parameters
        ----------
        game : gem.api.Game
            Game object

        See Also
        --------
        gem.api.Emulator.__get_content()
        """

        return self.__get_content(self.savestates, game)


    def command(self, game, fullscreen=False):
        """ Generate a launch command

        Parameters
        ----------
        game : gem.api.Game
            Game object

        Other parameters
        ----------------
        fullscreen : bool
            use fullscreen parameters

        Returns
        -------
        list
            Command launcher parameters list

        Raises
        ------
        TypeError
            if game type is not gem.api.Game
        """

        if type(game) is not Game:
            raise TypeError("Wrong type for game, expected gem.api.Game")

        # ----------------------------
        #   Check emulator binary
        # ----------------------------

        if not self.exists:
            raise OSError(2, "Emulator binary %s not found" % self.binary)

        command = str()

        # ----------------------------
        #   Default arguments
        # ----------------------------

        if game.default is not None:
            command += " %s" % str(game.default)
        else:
            command += " %s" % str(self.default)

        # ----------------------------
        #   Set fullscreen mode
        # ----------------------------

        if fullscreen and self.fullscreen is not None:
            command += " %s" % str(self.fullscreen)
        elif not fullscreen and self.windowed is not None:
            command += " %s" % str(self.windowed)

        # ----------------------------
        #   Replace special parameters
        # ----------------------------

        use_filepath = True

        if "<conf_path>" in command and self.configuration is not None:
            command = command.replace("<conf_path>", self.configuration)

        if "<rom_path>" in command:
            command = command.replace("<rom_path>", game.path[0])

            use_filepath = False

        if "<rom_name>" in command:
            name, extension = splitext(game.path[-1])

            command = command.replace("<rom_name>", name)

            use_filepath = False

        if "<rom_file>" in command:
            command = command.replace("<rom_file>", game.filepath)

            use_filepath = False

        # ----------------------------
        #   Generate correct command
        # ----------------------------

        command_data = list()

        # Append binaries
        command_data.extend(shlex_split(self.binary))

        # Append arguments
        if len(command) > 0:
            command_data.extend(shlex_split(command))

        # Append game file
        if use_filepath:
            command_data.append(game.filepath)

        return command_data


    def as_dict(self):
        """ Return object as dictionary structure

        Returns
        -------
        tuple
            return name and data as tuple
        """

        return (self.name, {
            "binary": self.binary,
            "configuration": self.configuration,
            "icon": self.icon,
            "save": self.savestates,
            "snaps": self.screenshots,
            "default": self.default,
            "windowed": self.windowed,
            "fullscreen": self.fullscreen
        })


class Console(GEMObject):

    attributes = {
        "id": str(),
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


    def as_dict(self):
        """ Return object as dictionary structure

        Returns
        -------
        tuple
            return name and data as tuple
        """

        return (self.name, {
            "icon": self.icon,
            "roms": expanduser(self.path),
            "exts": ';'.join(self.extensions),
            "emulator": self.emulator.name
        })


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
        for extension in set(self.extensions):

            # List available files
            for filename in set(glob("%s/*.%s" % (self.path, extension))):

                # Get data from database
                data = database.get("games", {"filename": basename(filename) })

                # Generate Game object
                game = Game()

                game_name = splitext(basename(filename))[0]

                game_data = {
                    "id": generate_identifier(game_name),
                    "filepath": filename,
                    "name": game_name
                }

                # This game exists in database
                if data is not None:

                    # Set game name
                    name = game_data["name"]
                    if len(data["name"]) > 0:
                        name = data["name"]

                    # Set play time
                    play_time = data["play_time"]
                    if len(play_time) > 0:
                        microseconds = int()

                        # Parse microseconds
                        if '.' in play_time:
                            play_time, microseconds = play_time.split('.')

                        hours, minutes, seconds = play_time.split(':')

                        play_time = time(
                            int(hours),
                            int(minutes),
                            int(seconds))
                    else:
                        play_time = time()

                    # Set last play date
                    last_launch_date = data["last_play"]
                    if len(last_launch_date) > 0:

                        # Old GEM format
                        if len(last_launch_date) > 10:
                            day, month, year = \
                                last_launch_date.split()[0].split('-')

                        # ISO 8601 format
                        else:
                            year, month, day = last_launch_date.split('-')

                        last_launch_date = date(
                            int(year),
                            int(month),
                            int(day))
                    else:
                        last_launch_date = None

                    # Set last play time
                    last_launch_time = data["last_play_time"]
                    if len(last_launch_time) > 0:
                        microseconds = int()

                        # Parse microseconds
                        if '.' in last_launch_time:
                            last_launch_time, microseconds = \
                                last_launch_time.split('.')

                        hours, minutes, seconds = last_launch_time.split(':')

                        last_launch_time = time(
                            int(hours),
                            int(minutes),
                            int(seconds))
                    else:
                        last_launch_time = time()

                    # Set game emulator
                    emulator = data["emulator"]
                    if len(emulator) > 0 and emulator in emulators:
                        emulator = emulators[emulator]
                    else:
                        emulator = None

                    # Set game arguments
                    arguments = data["arguments"]
                    if len(arguments) == 0:
                        arguments = None

                    game_data.update({
                        "id": generate_identifier(name),
                        "name": name,
                        "favorite": bool(data["favorite"]),
                        "multiplayer": bool(data["multiplayer"]),
                        "played": int(data["play"]),
                        "play_time": play_time,
                        "last_launch_date": last_launch_date,
                        "last_launch_time": last_launch_time,
                        "emulator": emulator,
                        "default": arguments,
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
        >>> g = GEM()
        >>> g.get_console("nintendo-nes").get_game("Metroid")
        <gem.api.Game object at 0x7f174a98e828>
        """

        for game in self.games:
            if game.filename == name:
                return game

        return None


class Game(GEMObject):

    attributes = {
        "id": str(),
        "filepath": str(),
        "name": str(),
        "favorite": bool(),
        "multiplayer": bool(),
        "played": int(),
        "play_time": time(),
        "last_launch_time": time(),
        "last_launch_date": None,
        "emulator": None,
        "default": None
    }

    def __init__(self):
        """ Constructor
        """

        super(Game, self).__init__()


    def as_dict(self):
        """ Return object as dictionary structure

        Returns
        -------
        tuple
            return name and data as tuple
        """

        return (self.name, {
            "filename": self.path[-1],
            "name": self.name,
            "favorite": self.favorite,
            "multiplayer": self.multiplayer,
            "play": self.played,
            "play_time": self.play_time,
            "last_play_time": self.last_launch_time,
            "last_play": self.last_launch_date,
            "emulator": self.emulator,
            "arguments": self.default
        })


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
        >>> g = GEM()
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

    @property
    def filename(self):
        """ Return filename without extension from filepath

        Returns
        -------
        str
            filename
        """

        if self.filepath is None:
            raise TypeError("Wrong type for filepath, expected str")

        return splitext(basename(expanduser(self.filepath)))[0]

if __name__ == "__main__":
    """ Debug GEM API
    """

    gem = GEM(debug=True)

    gem.logger.info("Found %d consoles" % len(gem.consoles))
    gem.logger.info("Found %d emulators" % len(gem.emulators))

    games = int()
    for console in sorted(gem.consoles):
        games += len(gem.get_console(console).games)

    gem.logger.info("Found %d games" % games)

