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

# Collections
from collections import OrderedDict

# Filesystem
from pathlib import Path
from os.path import splitext

# GEM
from geode_gem.engine.utils import (are_equivalent_timestamps,
                                    copy,
                                    generate_identifier,
                                    get_data,
                                    get_boot_datetime_as_timestamp)

from geode_gem.engine.game import Game
from geode_gem.engine.console import Console
from geode_gem.engine.emulator import Emulator

from geode_gem.engine.lib.database import Database
from geode_gem.engine.lib.configuration import Configuration

# Logging
import logging

from logging.config import fileConfig

# System
from fcntl import flock, LOCK_EX, LOCK_NB
from os import getpid
from os import name as os_name
from sys import exit as sys_exit


# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class GEM(object):

    Instance = "gem"
    Version = "0.10.3"

    Log = "gem.log"
    Logger = "log.conf"
    Consoles = "consoles.conf"
    Emulators = "emulators.conf"
    Databases = "databases.conf"
    Environment = "environment.conf"

    def __init__(self, config, local, debug=False):
        """ Constructor

        Parameters
        ----------
        config : pathlib.Path or str
            Default config folder
        local : pathlib.Path or str
            Default data folder
        debug : bool, optional
            Debug mode status (default: False)
        """

        if isinstance(config, str):
            config = Path(config)

        if isinstance(local, str):
            local = Path(local)

        if type(debug) is not bool:
            debug = False

        # ----------------------------------------
        #   Variables
        # ----------------------------------------

        # Debug mode
        self.debug = debug

        # Migration mode
        self.__need_migration = False

        # Data list
        self.__data = dict(
            consoles=dict(),
            emulators=dict(),
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

        # Process identifier
        self.__pid = int()
        self.__lock = False

        # ----------------------------------------
        #   Initialize filepaths
        # ----------------------------------------

        self.__config = config.joinpath(GEM.Instance).expanduser()
        self.__local = local.joinpath(GEM.Instance).expanduser()

        self.__log_path = self.__local.joinpath(f"{GEM.Instance}.log")
        self.__lock_path = self.__local.joinpath(".lock")

        self.__backup_path = self.__local.joinpath(f"backup.{GEM.Instance}.db")
        self.__database_path = self.__local.joinpath(f"{GEM.Instance}.db")

        for folder in (self.__config, self.__local):
            if not folder.exists():
                folder.mkdir(mode=0o755, parents=True)

        # ----------------------------------------
        #   Initialize objects
        # ----------------------------------------

        # Initialize lock file
        self.__lock = self.__init_lock()

        # Avoid to initialize a new instance if an existing one is present
        if not self.__lock:

            # Initialize logging module
            self.__init_logger()

            # Initialize sqlite database
            self.__init_database()

            self.logger.debug(f"Set local folder as {self.__local}")
            self.logger.debug(f"Set config folder as {self.__config}")

    def __init_lock(self):
        """ Initialize lock file

        Create a lock file which avoid to access to the database with multiple
        instance simultaneous

        The .lock file is stored into the XDG_DATA_HOME/gem directory.

        Inside, we store these values: "GEM_PID BOOT_TIMESTAMP".
        """

        if not os_name == "posix":
            logging.getLogger(self.Instance).warning(
                "Your operating system do not support POSIX standard")
            return False

        proc_path = Path("/proc")
        if not proc_path.exists():
            logging.getLogger(self.Instance).warning(
                "Your operating system do not support process file system")
            return False

        # Retrieve current boot session timestamp
        try:
            timestamp = get_boot_datetime_as_timestamp()
            if timestamp is None:
                return False

        except FileNotFoundError:
            return False

        # A lock file already exists on file system
        if self.__lock_path.exists():
            # Ensure to always retrieve the first line which contains PID
            with self.__lock_path.open('r') as pipe:
                content = pipe.read().split()

            if content:
                self.__pid, *more = content[0:]

                # Check if specified PID still alive
                if proc_path.joinpath(self.__pid).exists():

                    # No way to check if this PID is really owned by GEM
                    if not more or not more[0]:
                        return True

                    if are_equivalent_timestamps(timestamp, more[0], delta=4):
                        return True

        # Generate a new lock file
        self.__pid = getpid()

        with self.__lock_path.open('wb') as pipe:
            # Register current PID into file
            pipe.write(bytes(f"{self.__pid} {timestamp}", "UTF-8"))
            # Perform the lock operation on file
            flock(pipe, LOCK_EX | LOCK_NB)

        return False

    def __init_logger(self):
        """ Initialize logger

        Create a logger object based on logging library
        """

        if self.__log_path.exists():
            copy(self.__log_path, str(self.__log_path) + ".old")

        # Define log path with a global variable
        logging.log_path = str(self.__log_path)

        # Generate logger from log.conf
        fileConfig(str(get_data("data", "config", GEM.Logger)))

        self.logger = logging.getLogger("gem")
        if not self.debug:
            self.logger.setLevel(logging.INFO)

    def __init_database(self):
        """ Initialize database

        Check GEM database from local folder and update if needed columns and
        data
        """

        try:
            config = Configuration(
                get_data("data", "config", GEM.Databases), strict=False)

            # Check GEM database file
            self.database = Database(
                self.__database_path, config, self.logger)

            # Check current GEM version
            version = self.database.select("gem", "version")

            # Check Database inner version and GEM version
            if not version == GEM.Version:
                if version is None:
                    self.logger.info("Generate a new database")
                    version = GEM.Version

                else:
                    self.logger.info(f"Update database to v.{GEM.Version}")

                self.database.modify("gem",
                                     {"version": GEM.Version},
                                     {"version": version})

            else:
                self.logger.debug(f"Use GEM API v.{GEM.Version}")

            # Check integrity and migrate if necessary
            self.logger.info("Check database integrity")
            if not self.database.check_integrity():
                self.logger.warning("Database need a migration")
                self.__need_migration = True

            else:
                self.logger.info("Current database is up-to-date")
                self.__need_migration = False

        except OSError as error:
            self.logger.exception(f"Cannot access to database: {error}")
            sys_exit(error)

        except ValueError as error:
            self.logger.exception(f"A wrong value occur: {error}")
            sys_exit(error)

        except Exception as error:
            self.logger.exception(f"An error occur: {error}")
            sys_exit(error)

    def __init_configurations(self):
        """ Initalize configuration

        Check consoles.conf and emulators.conf from user config folder and copy
        default one if not exists
        """

        if not self.__config.exists():
            self.logger.debug(f"Generate {self.__config} folder")

            self.__config.mkdir(mode=0o755, parents=True)

        # Check GEM configuration files
        for filename in (GEM.Consoles, GEM.Emulators):
            path = Path(self.get_config(filename))

            # Configuration file not exists
            if not path.exists():
                raise FileNotFoundError(f"Cannot found {path} file")

            self.logger.debug(f"Read {path} configuration file")

            # Store Configuration object
            self.__configurations[path.stem] = Configuration(path,
                                                             strict=False)

        path = Path(self.get_config(GEM.Environment))

        self.logger.debug(f"Read {path} configuration file")

        self.__configurations[path.stem] = Configuration(path)

    def __init_emulators(self):
        """ Initalize emulators

        Load emulators.conf from user config folder and generate Emulator
        objects from data
        """

        self.__data["emulators"].clear()

        emulators = self.__configurations["emulators"]

        for section in emulators.sections():
            self.add_emulator(section, emulators.items(section))

        self.logger.debug(
            f"{len(self.emulators)} emulator(s) has been founded")

    def __init_consoles(self):
        """ Initalize consoles

        Load consoles.conf from user config folder and generate Console objects
        from data
        """

        self.__data["consoles"].clear()

        consoles = self.__configurations["consoles"]

        for section in consoles.sections():
            self.add_console(section, consoles.items(section))

        self.logger.debug(
            f"{len(self.consoles)} console(s) has been founded")

    def init(self):
        """ Initalize data from configuration files

        This function allow to reset API by reloading default configuration
        files
        """

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

            # Database backup
            copy(self.__database_path, self.__backup_path)

            # Remove previous database
            self.__database_path.unlink()

            # ----------------------------------------
            #   Initialize new database
            # ----------------------------------------

            try:
                config = Configuration(
                    get_data("data", "config", GEM.Databases))

                previous_database = Database(
                    self.__backup_path, config, self.logger)

                new_database = Database(
                    self.__database_path, config, self.logger)

                new_database.insert("gem", {"version": GEM.Version})

                # ----------------------------------------
                #   Migrate data from previous database
                # ----------------------------------------

                self.logger.info("Start database migration")

                # ----------------------------------------
                #   Migrate game by game
                # ----------------------------------------

                games = previous_database.select("games", ['*'])

                if games is not None:

                    # Get current table columns
                    old_columns_name = previous_database.get_columns("games")

                    # Get new table columns
                    new_columns_name = new_database.get_columns("games")

                    if updater is not None:
                        updater.init(len(games))

                    counter = int()
                    for row in games:
                        counter += 1

                        row_data = dict()

                        for element in row:
                            column = old_columns_name[row.index(element)]

                            # Avoid to retrieve columns which are no more used
                            if column in new_columns_name:
                                row_data[column] = element

                        new_database.insert("games", row_data)

                        if updater is not None:
                            updater.update(counter)

                # ----------------------------------------
                #   Remove backup
                # ----------------------------------------

                self.logger.info("Migration complete")
                self.__need_migration = False

                del previous_database
                del self.database

                setattr(self, "database", new_database)

            except Exception as error:
                self.logger.exception(
                    f"An error occurs during migration: {error}")

                self.logger.info("Restore database backup")

                copy(self.__backup_path, self.__database_path)

            # Remove backup
            self.get_local("save.gem.db").unlink()

        if updater is not None:
            updater.close()

    def write_object(self, data):
        """ Write data into a specific configuration file

        Parameters
        ----------
        data : object
            Data structure to save

        Returns
        -------
        bool
            return True if object was successfully writed, False otherwise
        """

        config = None

        if isinstance(data, Console):
            config = self.__configurations["consoles"]

        elif isinstance(data, Emulator):
            config = self.__configurations["emulators"]

        if config is not None:
            structure = data.as_dict()

            for key, value in structure.items():
                if value is None:
                    value = str()

                if type(value) is bool:

                    if value:
                        value = "yes"

                    else:
                        value = "no"

                if type(value) is Emulator:
                    value = value.id

                config.modify(data.name, key, value)

            config.update()

    def write_data(self, *files):
        """ Write data into configuration files and database

        Returns
        -------
        bool
            return True if files were successfully writed, False otherwise

        Notes
        -----
        Previous files are backup
        """

        self.logger.debug("Store GEM data into disk")

        # ----------------------------------------
        #   Configuration files
        # ----------------------------------------

        try:
            # Check GEM configuration files
            for path in files:

                # Get configuration filename for storage
                name, ext = splitext(path)

                # Backup configuration file
                if self.get_config(path).exists():
                    self.logger.debug(f"Backup {path} file")

                    copy(self.get_config(path), self.get_config(f"~{path}"))

                    self.get_config(path).unlink()

                # Create a new configuration object
                config = Configuration(self.get_config(path))

                # Feed configuration with new data
                for element in sorted(self.__data[name]):
                    structure = self.__data[name][element].as_dict()

                    for key, value in sorted(structure.items()):
                        if value is None:
                            value = str()

                        if type(value) is bool:
                            if value:
                                value = "yes"
                            else:
                                value = "no"

                        elif type(value) is Emulator:
                            value = value.id

                        config.modify(
                            self.__data[name][element].name, key, value)

                # Write new configuration file
                self.logger.info(f"Write configuration into {path} file")
                config.update()

        except Exception as error:
            self.logger.exception(f"Cannot write configuration: {error}")
            return False

        # ----------------------------------------
        #   Database file
        # ----------------------------------------

        try:
            for previous, emulator in self.__rename.items():

                # Update games which use a renamed emulator
                self.database.update("games",
                                     {"emulator": emulator.id},
                                     {"emulator": previous})

                self.logger.info(f"Update old {previous} references from "
                                 f"database to {emulator.id}")

        except Exception as error:
            self.logger.exception(f"Cannot write database: {error}")
            return False

        return True

    def get_config(self, *args):
        """ Retrieve configuration data

        Parameters
        ----------
        args : str, optional
            Optional path
        """

        return self.__config.joinpath(*args).expanduser()

    def get_local(self, *args):
        """ Retrieve local data

        Parameters
        ----------
        args : str, optional
            Optional path
        """

        return self.__local.joinpath(*args).expanduser()

    def is_locked(self):
        """ Check if database is locked

        Returns
        -------
        bool
            Lock status
        """

        return self.__lock

    def free_lock(self):
        """ Remove lock file if present
        """

        if self.__lock_path.exists():
            self.__lock_path.unlink()

    @property
    def pid(self):
        """ Return application process identifier

        Returns
        -------
        int
            Process identifier
        """

        return self.__pid

    @property
    def log(self):
        """ Return application log filepath

        Returns
        -------
        pathlib.Path
            Log file instance
        """

        return self.__log_path

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

    def add_emulator(self, name, informations):
        """ Add a new emulator

        Parameters
        ----------
        name : str
            Emulator name
        informations : dict
            Emulator information as dictionary

        Returns
        -------
        gem.engine.emulator.Emulator
            New emulator object
        """

        data = dict(name=name)

        for option, value in informations:
            convert_keys = dict(
                save="savestates",
                snaps="screenshots")

            if option in convert_keys.keys():
                option = convert_keys[option]

            if value is not None:
                data[option] = value

        emulator = Emulator(**data)

        self.__data["emulators"][emulator.id] = emulator

        return emulator

    def update_emulator(self, emulator):
        """ Update a specific emulator

        Parameters
        ----------
        emulator : gem.engine.emulator.Emulator
            Emulator instance
        """

        if emulator is not None:
            self.__data["emulators"][emulator.id] = emulator

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

        if emulator not in self.__data["emulators"].keys():
            raise IndexError(f"Cannot access to {emulator} in emulators list")

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

            if identifier not in self.__data["emulators"].keys():
                raise IndexError(
                    f"Cannot access to {identifier} in emulators list")

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
        gem.engine.api.Console or None
            Found console

        Examples
        --------
        >>> g = GEM()
        >>> g.init()
        >>> g.get_console("nintendo-nes")
        <gem.engine.api.Console object at 0x7f174a986b00>
        """

        if console is not None and len(console) > 0:

            if console in self.__data["consoles"].keys():
                return self.__data["consoles"].get(console, None)

            # Check if console use name instead of identifier
            identifier = generate_identifier(console)

            if identifier in self.__data["consoles"].keys():
                return self.__data["consoles"].get(identifier, None)

        return None

    def add_console(self, name, informations):
        """ Add a new console

        Parameters
        ----------
        name : str
            Console name
        informations : dict
            Console information as dictionary

        Returns
        -------
        gem.engine.console.Console
            New console object
        """

        data = dict(name=name)

        for option, value in informations:
            convert_keys = dict(
                roms="path",
                exts="extensions",
                save="savestates",
                snaps="screenshots")

            if option in convert_keys.keys():
                option = convert_keys[option]

            if value is not None:
                data[option] = value

        console = Console(self, **data)

        self.__data["consoles"][console.id] = console

        return console

    def update_console(self, console):
        """ Update a specific console

        Parameters
        ----------
        console : gem.engine.console.Console
            Console instance
        """

        if console is not None:
            self.__data["consoles"][console.id] = console

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

        if console not in self.__data["consoles"].keys():
            raise IndexError(f"Cannot access to {console} in consoles list")

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
            games.extend(console.get_games())

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
        gem.engine.api.Game or None
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
        <gem.engine.api.Game object at 0x7f174a986f60>
        """

        if console not in self.__data["consoles"]:
            raise IndexError(f"Cannot access to {console} in consoles list")

        # Check console games list
        return self.__data["consoles"][console].get_game(game)

    def get_game_tags(self):
        """ Retrieve avaialable game tags from database

        Returns
        -------
        list
            Tags list
        """

        result = self.database.select("games", "tags")

        if result is not None:
            tags = list()

            for tag in result:
                tags.extend(tag.split(';'))

            return sorted(list(set(tags)))

        return list()

    def update_game(self, game):
        """ Update a game in database

        Parameters
        ----------
        game : gem.engine.api.Game
            Game object

        Returns
        -------
        bool
            return True if update successfully, False otherwise

        Raises
        ------
        TypeError
            if game type is not gem.engine.api.Game
        """

        if type(game) is not Game:
            raise TypeError(
                "Wrong type for game, expected gem.engine.api.Game")

        # Store game data
        data = game.as_dict()

        # Translate value as string for database
        for key, value in data.items():

            if value is None:
                data[key] = str()

            elif type(value) is bool:
                data[key] = str(int(value))

            elif type(value) is int:
                data[key] = str(value)

            elif type(value) is Emulator:
                data[key] = str(value.name)

        # Update game in database
        self.logger.debug(f"Update {game.name} database entry")

        self.database.modify("games", data, {"filename": game.path.name})

        # Update game environment variables
        self.logger.debug(f"Update {game.name} environment variables")

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
        game : gem.engine.api.Game
            Game object

        Raises
        -------
        TypeError
            if game type is not gem.api.Game
        """

        if type(game) is not Game:
            raise TypeError(
                "Wrong type for game, expected gem.engine.api.Game")

        results = self.database.get("games", {"filename": game.path.name})

        if results is not None and len(results) > 0:
            self.logger.info(f"Remove {game.name} from database")

            self.database.remove("games", {"filename": game.path.name})

        # Update game environment variables
        self.logger.debug(f"Remove {game.name} environment variables")

        self.environment.remove_section(game.id)

        self.environment.update()
