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

# Collections
from collections import OrderedDict

# Filesystem
from pathlib import Path

from os.path import splitext

# GEM
from gem.engine.utils import copy
from gem.engine.utils import get_data
from gem.engine.utils import generate_identifier

from gem.engine.game import Game
from gem.engine.console import Console
from gem.engine.emulator import Emulator

from gem.engine.lib.database import Database
from gem.engine.lib.configuration import Configuration

# Logging
import logging

from logging.config import fileConfig

# System
from os import getpid

from sys import exit as sys_exit


# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class GEM(object):

    Version = "0.10.0"

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
        config : pathlib.Path
            Default config folder
        local : pathlib.Path
            Default data folder
        debug : bool, optional
            Debug mode status (default: False)

        Raises
        ------
        TypeError
            if config type is not pathlib.Path or None
            if local type is not pathlib.Path or None
            if debug type is not bool
        """

        if not isinstance(config, Path):
            raise TypeError("Wrong type for config, expected pathlib.Path")

        if not isinstance(local, Path):
            raise TypeError("Wrong type for local, expected pathlib.Path")

        if type(debug) is not bool:
            raise TypeError("Wrong type for debug, expected bool")

        # ----------------------------------------
        #   Variables
        # ----------------------------------------

        # Debug mode
        self.debug = debug

        # Lock mode
        self.__lock = False

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

        # API configuration path
        self.__config = config.expanduser()

        # API local path
        self.__local = local.expanduser()

        # API roms folder path
        self.__roms = self.__local.joinpath("roms")

        # Process identifier
        self.__pid = int()

        # ----------------------------------------
        #   Initialize folders
        # ----------------------------------------

        for folder in [self.__config, self.__local, self.__roms]:

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

            self.logger.debug("Set local folder as %s" % str(self.__local))
            self.logger.debug("Set config folder as %s" % str(self.__config))

    def __init_lock(self):
        """ Initialize lock file

        Create a lock file which avoid to access to the database with multiple
        instance simultaneous
        """

        lock_path = self.get_local(".lock")

        if lock_path.exists():
            self.__pid = int()

            # Read lock content
            with lock_path.open('r') as pipe:
                self.__pid = int(pipe.read())

            proc_path = Path("/proc", str(self.__pid))

            # Lock PID still exists
            if proc_path.exists():
                path = proc_path.joinpath("cmdline")

                # Check process command line
                if path.exists():
                    with path.open('r') as pipe:
                        content = pipe.read()

                    # Check if lock process is gem
                    if "gem" in content or "gem-ui" in content:
                        return True

        self.__pid = getpid()

        # Save current PID into lock file
        with lock_path.open('w') as pipe:
            pipe.write(str(self.__pid))

        return False

    def __init_logger(self):
        """ Initialize logger

        Create a logger object based on logging library
        """

        log_path = self.get_local(GEM.Log)

        # Save older log file to ~/.local/share/gem/gem.log.old
        if log_path.exists():
            copy(log_path, self.get_local(GEM.Log + ".old"))

        # Define log path with a global variable
        logging.log_path = str(log_path)

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
            config = Configuration(get_data("data", "config", GEM.Databases))

            # Check GEM database file
            self.database = Database(
                self.get_local("gem.db"), config, self.logger)

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
                                     {"version": GEM.Version},
                                     {"version": version})

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

        if not self.__config.exists():
            self.logger.debug("Generate %s folder" % str(self.__config))

            self.__config.mkdir(mode=0o755, parents=True)

        # Check GEM configuration files
        for filename in (GEM.Consoles, GEM.Emulators):
            path = Path(self.get_config(filename))

            # Configuration file not exists
            if not path.exists():
                raise OSError(2, "Cannot found %s file" % path)

            self.logger.debug("Read %s configuration file" % path)

            # Store Configuration object
            self.__configurations[path.stem] = Configuration(path)

        path = Path(self.get_config(GEM.Environment))

        self.logger.debug("Read %s configuration file" % path)

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
            "%d emulator(s) has been founded" % len(self.emulators))

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
            "%d console(s) has been founded" % len(self.consoles))

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
            copy(self.get_local("gem.db"), self.get_local("save.gem.db"))

            # Remove previous database
            self.get_local("gem.db").unlink()

            # ----------------------------------------
            #   Initialize new database
            # ----------------------------------------

            try:
                config = Configuration(
                    get_data("data", "config", GEM.Databases))

                previous_database = Database(
                    self.get_local("save.gem.db"), config, self.logger)

                new_database = Database(
                    self.get_local("gem.db"), config, self.logger)

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
                    "An error occurs during migration: %s" % str(error))

                self.logger.info("Restore database backup")

                copy(self.get_local("save.gem.db"), self.get_local("gem.db"))

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
                    self.logger.debug("Backup %s file" % path)

                    copy(self.get_config(path), self.get_config('~' + path))

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
                self.logger.info("Write configuration into %s file" % path)
                config.update()

        except Exception as error:
            self.logger.exception(
                "Cannot write configuration: %s" % str(error))

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

        lock_path = self.get_local(".lock")

        if lock_path.exists():
            lock_path.unlink()

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

        emulator = Emulator(self, **data)

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
            raise IndexError(
                "Cannot access to %s in emulators list" % emulator)

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
        self.logger.debug("Update %s database entry" % game.name)

        self.database.modify("games", data, {"filename": game.path.name})

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
            self.logger.info("Remove %s from database" % game.name)

            self.database.remove("games", {"filename": game.path.name})

        # Update game environment variables
        self.logger.debug("Remove %s environment variables" % game.name)

        self.environment.remove_section(game.id)

        self.environment.update()


if __name__ == "__main__":
    """ Debug GEM API
    """

    root = Path("test", "gem")

    config_path = root.joinpath("config")

    if not config_path.exists():
        config_path.mkdir(mode=0o755, parents=True)

        for filename in (GEM.Consoles, GEM.Emulators):
            copy(get_data("data", "config", filename),
                 config_path.joinpath(filename))

    gem = GEM(config_path, root.joinpath("local"), debug=True)

    if not gem.is_locked():
        gem.init()

        gem.logger.info("Found %d consoles" % len(gem.consoles))
        gem.logger.info("Found %d emulators" % len(gem.emulators))
        gem.logger.info("Found %d games" % len(gem.get_games()))

        gem.free_lock()
