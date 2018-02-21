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

from os.path import isdir
from os.path import exists
from os.path import dirname
from os.path import basename
from os.path import splitext
from os.path import expanduser
from os.path import join as path_join

from glob import glob
from copy import deepcopy
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
    from gem.utils import parse_timedelta
    from gem.utils import get_binary_path
    from gem.utils import generate_extension
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
    Version     = "1.0"
    CodeName    = "Space Fox"
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
    Environment = "environment.conf"

    # Paths
    Local       = path_join(expanduser(xdg_data_home), "gem")
    Config      = path_join(expanduser(xdg_config_home), "gem")

    def __init__(self, config=None, local=None, debug=False):
        """ Constructor

        By default, GEM use paths defined with xdg:

        Config → ~/.config
        Local  → ~/.local/share

        Parameters
        ----------
        config : str, optional
            Default config folder (default: None)
        local : str, optional
            Default data folder (default: None)
        debug : bool, optional
            Debug mode status (default: False)

        Raises
        ------
        TypeError
            if debug type is not bool
        """

        if type(debug) is not bool:
            raise TypeError("Wrong type for debug, expected bool")

        # ----------------------------
        #   Variables
        # ----------------------------

        # Debug mode
        self.debug = debug

        # Migration mode
        self.__need_migration = False

        # Data list
        self.__data = dict(
            consoles=list(),
            emulators=list(),
            environment=list()
        )

        # Rename list
        self.__rename = OrderedDict()

        # Configurations
        self.__configurations = dict(
            consoles=None,
            emulators=None,
            environment=None
        )

        # API configuration path
        if config is not None:
            config = expanduser(config)
        else:
            config = GEM.Config

        self.__config = config

        # API local path
        if local is not None:
            local = expanduser(local)
        else:
            local = GEM.Local

        self.__local = local

        # ----------------------------
        #   Initialize folders
        # ----------------------------

        for folder in [ self.__config, self.__local, self.get_local("roms") ]:
            if not exists(folder):
                makedirs(folder, 0o755)

        # ----------------------------
        #   Initialize logger
        # ----------------------------

        self.__init_logger()


    def __init_logger(self):
        """ Initialize logger

        Create a logger object based on logging library
        """

        # Define log path with a global variable
        logging.log_path = self.get_local(GEM.Log)

        # Save older log file to ~/.local/share/gem/gem.log.old
        if(exists(logging.log_path)):
            copy(logging.log_path, self.get_local(GEM.Log + ".old"))

        # Generate logger from log.conf
        fileConfig(get_data(path_join("config", GEM.Logger)))

        self.logger = logging.getLogger("gem")

        if not self.debug:
            self.logger.setLevel(logging.INFO)


    def __init_database(self):
        """ Initialize database

        Check GEM database from local folder and update if needed columns and
        data
        """

        try:
            # Check GEM database file
            self.database = Database(self.get_local("gem.db"),
                get_data(path_join("config", GEM.Databases)), self.logger)

            # Check current GEM version
            version = self.database.select("gem", "version")

            # Check Database inner version and GEM version
            if not version == GEM.Version:
                if version is None:
                    self.logger.info("Generate a new database")
                    version = GEM.Version

                else:
                    self.logger.info("Update database to v.%s" % GEM.Version)

                self.database.modify("gem",
                    { "version": GEM.Version, "codename": GEM.CodeName },
                    { "version": version })

            else:
                self.logger.debug("Use GEM API v.%s" % GEM.Version)

            # Check integrity and migrate if necessary
            self.logger.info("Check database integrity")
            if not self.database.check_integrity():
                self.logger.warning("Database need a migration")
                self.__need_migration = True

            else:
                self.logger.info("Current database is up-to-date")
                self.__need_migration = False

        except OSError as error:
            self.logger.exception("Cannot access to database: %s" % str(error))
            sys_exit(error)

        except ValueError as error:
            self.logger.exception("A wrong value occur: %s" % str(error))
            sys_exit(error)

        except Exception as error:
            self.logger.exception("An error occur: %s" % str(error))
            sys_exit(error)


    def __init_configurations(self):
        """ Initalize configuration

        Check consoles.conf and emulators.conf from user config folder and copy
        default one if not exists
        """

        if not exists(self.__config):
            self.logger.debug("Generate %s folder" % self.__config)
            mkdir(self.__config)

        # Check GEM configuration files
        for path in [ GEM.Consoles, GEM.Emulators, GEM.Environment ]:
            # Get configuration filename for storage
            name, ext = splitext(path)

            # Configuration file not exists
            if not exists(self.get_config(path)):

                # Check if a default configuration file exists
                if exists(get_data(path_join("config", path))):
                    self.logger.debug("Copy %s to %s" % (path, self.__config))

                    copy(get_data(path_join("config", path)),
                        self.get_config(path))

            self.logger.debug("Read %s configuration file" % path)

            # Store Configuration object
            self.__configurations[name] = Configuration(self.get_config(path))


    def __init_emulators(self):
        """ Initalize emulators

        Load emulators.conf from user config folder and generate Emulator
        objects from data
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

        Load consoles.conf from user config folder and generate Console objects
        from data
        """

        self.__data["consoles"] = dict()

        data = self.__configurations["consoles"]

        for section in data.sections():
            emulator = data.get(section, "emulator", fallback=None)

            if emulator is not None:

                # Emulator exists in GEM storage
                if emulator in self.__data["emulators"]:
                    emulator = self.__data["emulators"][emulator]
                else:
                    emulator = None

            roms_path = expanduser(data.get(section, "roms", fallback=str()))
            roms_path = roms_path.replace("<local>", self.get_local())

            # Check consoles roms path folder
            if not exists(roms_path):

                try:
                    makedirs(roms_path)

                except Exception as error:
                    self.logger.exception("Cannot create %s folder" % roms_path)

            # Check if roms_path exists and is a directory
            if exists(roms_path) and isdir(roms_path):
                self.add_console({
                    "id": generate_identifier(section),
                    "name": section,
                    "path": roms_path,
                    "icon": data.get(
                        section, "icon", fallback=str()),
                    "ignores": data.get(
                        section, "ignores", fallback=str()).split(';'),
                    "extensions": data.get(
                        section, "exts", fallback=str()).split(';'),
                    "recursive": data.getboolean(
                        section, "recursive", fallback=False),
                    "favorite": data.getboolean(
                        section, "favorite", fallback=False),
                    "emulator": emulator
                })

        self.logger.debug(
            "%d console(s) has been founded" % len(self.consoles))


    def init(self):
        """ Initalize data from configuration files

        This function allow to reset API by reloading default configuration
        files
        """

        # Initialize sqlite database
        self.__init_database()

        if self.__need_migration:
            raise RuntimeError("GEM database need a migration")

        # Check if default configuration file exists
        self.__init_configurations()

        # Load user emulators
        self.__init_emulators()
        # Load user consoles
        self.__init_consoles()


    def check_database(self, updater=None):
        """ Check database and migrate to lastest GEM version if needed

        Parameters
        ----------
        updater : class, optionnal
            Class to call when database is modified
        """

        if self.__need_migration:
            self.logger.info("Backup database")

            copy(self.get_local("gem.db"), self.get_local("save.gem.db"))

            try:
                self.logger.info("Start database migration")

                # Get current table columns
                previous_columns = self.database.get_columns("games")
                # Get current table rows
                previous_data = self.database.select("games", ['*'])

                # ----------------------------
                #   Backup database tables
                # ----------------------------

                self.database.rename_table("games", "_%s" % "games")
                self.database.create_table("games")

                # ----------------------------
                #   Check columns
                # ----------------------------

                # Columns data
                data = dict()
                # Columns template for deepcopy
                template = dict()

                # Check previous table for new columns
                for column in previous_columns:
                    if column in self.database.get_columns("games"):
                        data[column] = previous_columns.index(column)

                # Set columns template
                for column in self.database.get_columns("games"):
                    template[column] = str()

                # ----------------------------
                #   Migrate database
                # ----------------------------

                if previous_data is not None:
                    counter = int()

                    if updater is not None:
                        updater.init(len(previous_data))

                    # Check each row from previous database
                    for row in previous_data:
                        counter += 1

                        # Copy default template
                        columns = deepcopy(template)

                        # Check each column from row
                        for column in list(columns.keys()):

                            # There is data for this row column
                            if column in data:
                                columns[column] = row[data[column]]

                            # No data for this row column
                            else:
                                columns[column] = None

                        # Insert row in new database
                        self.database.insert("games", columns)

                        if updater is not None:
                            updater.update(counter)

                # ----------------------------
                #   Remove backup
                # ----------------------------

                self.database.remove_table("_%s" % "games")

                self.logger.info("Migration complete")
                self.__need_migration = False

            except Exception as error:
                self.logger.exception(
                    "An error occurs during migration: %s" % str(error))

                self.logger.info("Restore database backup")

                copy(self.get_local("save.gem.db"), self.get_local("gem.db"))

        if updater is not None:
            updater.close()


    def write_data(self):
        """ Write data into configuration files and database

        Returns
        -------
        bool
            return True if files are successfully writed, False otherwise

        Notes
        -----
        Previous files are backup
        """

        self.logger.debug("Store GEM data into disk")

        # ----------------------------
        #   Configuration files
        # ----------------------------

        try:
            # Check GEM configuration files
            for path in [ GEM.Consoles, GEM.Emulators, GEM.Environment ]:
                # Get configuration filename for storage
                name, ext = splitext(path)

                # Backup configuration file
                if exists(self.get_config(path)):
                    self.logger.debug("Backup %s file" % path)
                    move(self.get_config(path), self.get_config('~' + path))

                # Create a new configuration object
                config = Configuration(self.get_config(path))

                # Feed configuration with new data
                for element in sorted(self.__data[name]):
                    section, structure = self.__data[name][element].as_dict()

                    for key, value in sorted(structure.items()):
                        if value is None:
                            value = str()

                        if type(value) is bool:
                            if value:
                                value = "yes"
                            else:
                                value = "no"

                        if type(value) is Emulator:
                            value = value.id

                        config.modify(section, key, value)

                # Write new configuration file
                self.logger.info("Write configuration into %s file" % path)
                config.update()

        except Exception as error:
            self.logger.exception("Cannot write configuration: %s" % str(error))

            return False

        # ----------------------------
        #   Database file
        # ----------------------------

        try:
            for previous, emulator in self.__rename.items():

                # Update games which use a renamed emulator
                self.database.update("games",
                    { "emulator": emulator.id },
                    { "emulator": previous })

                self.logger.info(
                    "Update old %s references from database to %s" % (
                        previous, emulator.id))

        except Exception as error:
            self.logger.exception("Cannot write database: %s" % str(error))

            return False

        return True


    def get_config(self, *args):
        """ Retrieve configuration data

        Parameters
        ----------
        args : str, optional
            Optional path
        """

        return path_join(self.__config, *args)


    def get_local(self, *args):
        """ Retrieve local data

        Parameters
        ----------
        args : str, optional
            Optional path
        """

        return path_join(self.__local, *args)


    @property
    def emulators(self):
        """ Return emulators dict

        Returns
        -------
        dict
            emulators dictionary with identifier as keys
        """

        return self.__data["emulators"]


    def get_emulators(self):
        """ Return emulators list

        Returns
        -------
        list
            Emulators list
        """

        return list(self.__data["emulators"].values())


    def get_emulator(self, emulator):
        """ Get a specific emulator

        Parameters
        ----------
        emulator : str
            Emulator identifier or name

        Returns
        -------
        Emulator or None
            Found emulator
        """

        if emulator is not None and len(emulator) > 0:

            if emulator in self.__data["emulators"].keys():
                return self.__data["emulators"].get(emulator, None)

            # Check if emulator use name instead of identifier
            identifier = generate_identifier(emulator)

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
        NameError
            if id, name or binary not exist in data dictionary
        ValueError
            if identifier already exist in emulators dictionary
        """

        if type(data) is not dict:
            raise TypeError("Wrong type for data, expected dict")

        if not "id" in data.keys():
            raise NameError("Missing id key in data dictionary")

        if not "name" in data.keys():
            raise NameError("Missing name key in data dictionary")

        if not "binary" in data.keys():
            raise NameError("Missing binary key in data dictionary")

        if data["id"] in self.__data["emulators"].keys():
            raise ValueError("Emulator %s already exists" % data["id"])

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
            Emulator identifier

        Raises
        ------
        IndexError
            if emulator not exists
        """

        if not emulator in self.__data["emulators"].keys():
            raise IndexError("Cannot access to %s in emulators list" % emulator)

        del self.__data["emulators"][emulator]


    def rename_emulator(self, previous, identifier):
        """ Rename an emulator and all associate objects (consoles and games)

        Parameters
        ----------
        previous : str
            Emulator previous identifier
        identifier : str
            Emulator new identifier

        Raises
        ------
        IndexError
            if emulator not exists
        """

        # Avoid to rename an emulator with the same name :D
        if not previous == identifier:

            if not identifier in self.__data["emulators"].keys():
                raise IndexError(
                    "Cannot access to %s in emulators list" % identifier)

            # Retrieve emulator object
            self.__rename[previous] = self.__data["emulators"][identifier]

            # Update consoles which use previous emulator
            for console_identifier in self.__data["consoles"].keys():
                console = self.__data["consoles"][console_identifier]

                if console is not None and console.emulator.id == previous:
                    console.emulator = self.__rename[previous]


    @property
    def consoles(self):
        """ Return consoles dict

        Returns
        -------
        dict
            Consoles dictionary with identifier as keys
        """

        return self.__data["consoles"]


    def get_consoles(self):
        """ Return consoles list

        Returns
        -------
        list
            Consoles list
        """

        return list(self.__data["consoles"].values())


    def get_console(self, console):
        """ Get a specific console

        Parameters
        ----------
        console : str
            Console identifier or name

        Returns
        -------
        gem.api.Console or None
            Found console

        Examples
        --------
        >>> g = GEM()
        >>> g.init()
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
        NameError
            if id or name not exist in data dictionary
        ValueError
            if identifier already exist in consoles dictionary
        """

        if type(data) is not dict:
            raise TypeError("Wrong type for data, expected dict")

        if not "id" in data.keys():
            raise NameError("Missing id key in data dictionary")

        if not "name" in data.keys():
            raise NameError("Missing name key in data dictionary")

        if data["id"] in self.__data["consoles"].keys():
            raise ValueError("Console %s already exists" % data["id"])

        # ----------------------------
        #   Generate console
        # ----------------------------

        console = Console()

        for key, value in data.items():

            # Avoid to have a list with an empty string
            if type(value) is list:
                if len(value) == 1 and len(value[0]) == 0:
                    value = list()

            elif type(value) is not Emulator and type(value) is not bool:
                if value is not None and len(value) == 0:
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
            Console identifier

        Raises
        ------
        IndexError
            if console not exists
        """

        if not console in self.__data["consoles"].keys():
            raise IndexError("Cannot access to %s in consoles list" % console)

        del self.__data["consoles"][console]


    @property
    def environment(self):
        """ Return environment dict

        Returns
        -------
        dict
            environment dictionary
        """

        return self.__configurations["environment"]


    def get_games(self):
        """ List all games from register consoles

        Returns
        -------
        list
            Games list
        """

        games = list()

        for identifier, console in self.consoles.items():
            games.extend(list(console.games.values()))

        return games


    def get_game(self, console, game):
        """ Get game from a specific console

        Parameters
        ----------
        console : str
            Console identifier
        game : str
            Game identifier

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
        >>> g.init()
        >>> g.get_game("nintendo-nes", "gremlins-2-the-new-batch-usa")
        <gem.api.Game object at 0x7f174a986f60>
        """

        if not console in self.__data["consoles"]:
            raise IndexError("Cannot access to %s in consoles list" % console)

        # Check console games list
        return self.__data["consoles"][console].get_game(game)


    def get_game_tags(self):
        """ Retrieve avaialable game tags from database

        Returns
        -------
        list
            Tags list
        """

        tags = list()

        for tag in self.database.select("games", "tags"):

            for element in tag.split(';'):

                if len(element) > 0 and not element in tags:
                    tags.append(element)

        return sorted(tags)


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
        self.logger.debug("Update %s database entry" % game.name)

        self.database.modify("games", data, { "filename": game.path[1] })

        # Update game environment variables
        self.logger.debug("Update %s environment variables" % game.name)

        self.environment.remove_section(game.id)

        if len(game.environment) > 0:
            self.environment.add_section(game.id)

            for key, value in game.environment.items():
                self.environment.set(game.id, key.upper(), value)

        self.environment.update()


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
                    if len(value) > 0:
                        value = ', '.join(value)

                if type(value) is dict or type(value) is OrderedDict:
                    value = list(value.keys())

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
        key : str
            Game content path
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
                key = key.replace("<rom_path>", game.path[0])

            if "<lname>" in key:
                key = key.replace("<lname>", game.filename.lower())

            elif "<name>" in key:
                key = key.replace("<name>", game.filename)

            if "<key>" in key and game.key is not None:
                key = key.replace("<key>", game.key)

            if not isdir(expanduser(key)):
                return glob(expanduser(key).replace('[', '?').replace(']', '?'))

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
        fullscreen : bool, optional
            Use fullscreen parameters (Default: False)

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
            raise OSError(2, "Emulator binary %s was not found" % self.binary)

        command = str()

        # ----------------------------
        #   Default arguments
        # ----------------------------

        if game.default is not None:
            command += " %s" % str(game.default)
        elif self.default is not None:
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

        if "<key>" in command and game.key is not None:
            command = command.replace("<key>", game.key)

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
        "ignores": list(),
        "extensions": list(),
        "games": list(),
        "recursive": False,
        "favorite": False,
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
            "ignores": ';'.join(self.ignores),
            "emulator": self.emulator,
            "favorite": self.favorite,
            "recursive": self.recursive
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

        self.games = OrderedDict()

        # Check each extensions in games path
        for extension in set(self.extensions):

            regex = "%s/*.%s"
            if self.recursive:
                regex = "%s/**/*.%s"

            files = set(glob(regex % (self.path, generate_extension(extension)),
                recursive=self.recursive))

            # List available files
            for filename in sorted(files):

                # Get data from database
                data = database.get("games", { "filename": basename(filename) })

                # Generate Game object
                game = Game.new(filename)

                game_data = {
                    "id": game.id,
                    "name": game.name,
                    "filepath": game.filepath,
                    "environment": dict()
                }

                # Set game environment variables
                if game.id in parent.environment.sections():

                    for option in parent.environment.options(game.id):
                        game_data["environment"][option.upper()] = \
                            parent.environment.get(
                            game.id, option, fallback=str())

                # This game exists in database
                if data is not None:

                    # Set game name
                    name = game_data["name"]
                    if len(data["name"]) > 0:
                        name = data["name"]

                    # Set play time
                    play_time = timedelta()
                    if "play_time" in data and len(data["play_time"]) > 0:
                        play_time = data["play_time"]
                        microseconds = int()

                        # Parse microseconds
                        if '.' in play_time:
                            play_time, microseconds = play_time.split('.')

                        hours, minutes, seconds = play_time.split(':')

                        play_time = timedelta(
                            hours=int(hours),
                            minutes=int(minutes),
                            seconds=int(seconds))

                    # Set last play date
                    last_launch_date = None
                    if "last_play" in data and len(data["last_play"]) > 0:
                        last_launch_date = data["last_play"]

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

                    # Set last play time
                    last_launch_time = timedelta()
                    if "last_play_time" in data and \
                        len(data["last_play_time"]) > 0:
                        last_launch_time = data["last_play_time"]
                        microseconds = int()

                        # Parse microseconds
                        if '.' in last_launch_time:
                            last_launch_time, microseconds = \
                                last_launch_time.split('.')

                        hours, minutes, seconds = last_launch_time.split(':')

                        last_launch_time = timedelta(
                            hours=int(hours),
                            minutes=int(minutes),
                            seconds=int(seconds))

                    # Set game emulator
                    emulator = None
                    if "emulator" in data and len(data["emulator"]) > 0 and \
                        data["emulator"] in emulators:
                        emulator = emulators[data["emulator"]]

                    # Set game arguments
                    arguments = None
                    if "arguments" in data and len(data["arguments"]) > 0:
                        arguments = data["arguments"]

                    # Set savestates regex
                    key = None
                    if "key" in data and len(data["key"]) > 0:
                        key = data["key"]

                    # Set game tags
                    tags = list()
                    if "tags" in data and len(data["tags"]) > 0:
                        tags = data["tags"].split(';')

                    # Set game cover image
                    cover = None
                    if "cover" in data and len(data["cover"]) > 0:
                        cover = expanduser(data["cover"])

                    game_data.update({
                        "name": name,
                        "favorite": bool(data["favorite"]),
                        "multiplayer": bool(data["multiplayer"]),
                        "finish": bool(data["finish"]),
                        "rating": int(),
                        "played": int(data["play"]),
                        "play_time": play_time,
                        "last_launch_date": last_launch_date,
                        "last_launch_time": last_launch_time,
                        "emulator": emulator,
                        "default": arguments,
                        "tags": tags,
                        "key": key,
                        "cover": cover
                    })

                for key, value in game_data.items():
                    setattr(game, key, value)

                # Remove useless keys
                game.check_keys()

                self.games[game.id] = game


    def get_game(self, identifier):
        """ Return specific game from current console

        Parameters
        ----------
        identifier : str
            Game identifier

        Returns
        -------
        gem.api.Game or None
            Game object

        Examples
        --------
        >>> g = GEM()
        >>> g.init()
        >>> g.get_console("nintendo-nes").get_game("metroid-usa")
        <gem.api.Game object at 0x7f174a98e828>
        """

        if identifier in self.games.keys():
            return self.games[identifier]

        return None


    def get_games(self):
        """ List all games

        Returns
        -------
        list
            Games list
        """

        return list(self.games.values())


class Game(GEMObject):

    attributes = {
        "id": str(),
        "filepath": str(),
        "name": str(),
        "favorite": bool(),
        "multiplayer": bool(),
        "finish": bool(),
        "rating": int(),
        "played": int(),
        "play_time": timedelta(),
        "last_launch_time": timedelta(),
        "last_launch_date": None,
        "emulator": None,
        "default": None,
        "key": None,
        "tags": list(),
        "environment": dict(),
        "cover": None
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
            "finish": self.finish,
            "rating": self.rating,
            "play": self.played,
            "play_time": parse_timedelta(self.play_time),
            "last_play_time": parse_timedelta(self.last_launch_time),
            "last_play": self.last_launch_date,
            "emulator": self.emulator,
            "arguments": self.default,
            "tags": ';'.join(self.tags),
            "key": self.key,
            "cover": self.cover
        })

    @staticmethod
    def new(path):
        """ Define a new Game object from game file path

        Parameters
        ----------
        path : str
            Game file path
        """

        game = Game()

        name = splitext(basename(path))[0]

        game.id = generate_identifier(basename(path))
        game.name = name
        game.filepath = path

        return game


    def reset(self):
        """ Reset game data
        """

        # Get default data
        path = self.filepath
        name = splitext(basename(path))[0]

        # Replace all data with default values
        for key, value in self.attributes.items():
            setattr(self, key, value)

        # Set default game values
        self.id = generate_identifier(name)
        self.name = name
        self.filepath = path


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
        >>> g.init()
        >>> g.get_console("nintendo-nes").get_game("Asterix").path
        ("~/.local/share/gem/roms/nes", "asterix.nes")
        """

        if self.filepath is None:
            raise TypeError("Wrong type for filepath, expected str")

        if len(self.filepath) == 0:
            raise ValueError("File path length is empty")

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


    @property
    def extension(self):
        """ Return extension from filepath

        Returns
        -------
        str
            filename
        """

        if self.filepath is None:
            raise TypeError("Wrong type for filepath, expected str")

        return splitext(basename(expanduser(self.filepath)))[-1]


    @property
    def log(self):
        """ Return relative log file path

        Returns
        -------
        str
            filepath
        """

        return path_join("logs", self.path[-1] + ".log")


if __name__ == "__main__":
    """ Debug GEM API
    """

    gem = GEM(debug=True)
    gem.init()

    gem.logger.info("Found %d consoles" % len(gem.consoles))
    gem.logger.info("Found %d emulators" % len(gem.emulators))
    gem.logger.info("Found %d games" % len(gem.get_games()))

