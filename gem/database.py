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

# System
from copy import deepcopy

from os.path import exists
from os.path import expanduser

from logging import Logger

# Database
import sqlite3

# ------------------------------------------------------------------------------
#   Modules - GEM
# ------------------------------------------------------------------------------

try:
    from gem.configuration import Configuration

except ImportError as error:
    sys_exit("Import error with gem module: %s" % str(error))

# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class Database(object):
    """ Manage a sqlite3 database

    Attributes
    ----------
    path : str
        Database file path
    configuration : configuration.Configuration
        Database schema configuration object
    logger : logging.Logger
        Logger object
    sql_types : dict
        Sqlite sql types correspondance with python types
    """

    def __init__(self, db_path, configuration_path, logger):
        """ Constructor

        Parameters
        ----------
        db_path : str
            Database filepath
        configuration_path : str
            Configuration file which contains database schema
        logger : logging.Logger
            Logging object

        Raises
        ------
        OSError
            If the configuration path not exists
        ValueError
            If logger type is not logging.Logger
        """

        if not exists(expanduser(configuration_path)):
            raise OSError(2, "Cannot find file", configuration_path)

        if type(logger) is not Logger:
            raise ValueError(
                "Expected logging.Logger type, get %s" % type(logger))

        # ------------------------------------
        #   Variables
        # ------------------------------------

        self.path = expanduser(db_path)

        self.configuration = Configuration(expanduser(configuration_path))

        self.logger = logger

        self.sql_types = {
            "NULL": None,
            "BOOL": int,
            "INTEGER": int,
            "REAL": float,
            "TEXT": str,
            "BLOB": memoryview }

        # ------------------------------------
        #   Intialization
        # ------------------------------------

        if not exists(self.path):
            for table in self.configuration.sections():
                self.__create_table(table)

        else:
            tables = self.select("sqlite_master", ["name"], { "type": "table" })
            if not type(tables) is list:
                tables = [tables]

            for table in list(set(self.configuration.sections()) - set(tables)):
                self.__create_table(table)


    def __generate_request(self, table, data):
        """ Generate a request to database

        This function generate a correct sql request from data dict which use
        keys as columns.

        Parameters
        ----------
        table : str
            Table name
        data : dict
            Columns keys with values

        Returns
        -------
        list
            Request strings list
        """

        values = list()

        if self.configuration.has_section(table):

            for column, value in data.items():
                sql_type = self.configuration.get(table, column).split()[0]

                if sql_type.upper() in list(self.sql_types.keys()):

                    if self.sql_types.get(sql_type.upper()) is str:
                        values.append("%s = \"%s\"" % (
                            str(column), str(data.get(column))))
                    else:
                        values.append("%s = %s" % (
                            str(column), str(data.get(column))))

        else:
            for column, value in data.items():
                values.append("%s = \"%s\"" % (
                    str(column), str(data.get(column))))

        return values


    def __create_table(self, table):
        """ Create a new table into database

        Parameters
        ----------
        table : str
            Table name
        """

        request = list()

        database = sqlite3.connect(self.path)
        cursor = database.cursor()

        for option in self.configuration.items(table):
            request.append(" ".join(option))

        try:
            with database:
                cursor.execute("CREATE TABLE %s (%s);" % (
                    table, ", ".join(request)))

        except Exception as error:
            self.logger.critical(str(error))

        database.commit()
        cursor.close()


    def __rename_table(self, table, name):
        """ Rename a table from database

        Parameters
        ----------
        table : str
            Previous table name
        name : str
            New table name
        """

        database = sqlite3.connect(self.path)
        cursor = database.cursor()

        try:
            cursor.execute("ALTER TABLE %s RENAME TO %s;" % (table, name))

        except Exception as error:
            self.logger.critical(str(error))

        database.commit()
        cursor.close()


    def __remove_table(self, table):
        """ Remove a table from database

        Parameters
        ----------
        table : str
            Table name
        """

        database = sqlite3.connect(self.path)
        cursor = database.cursor()

        try:
            cursor.execute("DROP TABLE IF EXISTS %s;" % (table))

        except Exception as error:
            self.logger.critical(str(error))

        database.commit()
        cursor.close()


    def __add_column(self, table, name, sql_type):
        """ Add a new column into database

        Parameters
        ----------
        table : str
            Table name
        name : str
            Column name
        sql_type : str
            Column type
        """

        database =  sqlite3.connect(self.path)
        cursor = database.cursor()

        try:
            with database:
                cursor.execute("ALTER TABLE %s ADD COLUMN %s %s;" % (
                    table, name, sql_type))

        except Exception as error:
            self.logger.critical(str(error))

        database.commit()
        cursor.close()


    def __get_columns(self, table):
        """ Get all the columns from database

        Parameters
        ----------
        table : str
            Table name

        Returns
        -------
        list
            Columns list
        """

        columns = list()

        database =  sqlite3.connect(self.path)
        cursor = database.cursor()

        try:
            with database:
                request = cursor.execute("PRAGMA table_info(%s);" % (table))

                for data in request.fetchall():
                    columns.append(data[1])

        except Exception as error:
            self.logger.critical(str(error))

        database.commit()
        cursor.close()

        return columns


    def __insert(self, table, data):
        """ Insert a new row into database

        This function insert a new row into database from data dict which use
        keys as columns.

        Parameters
        ----------
        table : str
            Table name
        data : dict
            Columns keys and values
        """

        database = sqlite3.connect(self.path)
        cursor = database.cursor()

        try:
            values, columns = list(), list()

            for column in list(data.keys()):
                sql_type = self.configuration.get(table, column).split()[0]

                if sql_type.upper() in list(self.sql_types.keys()):

                    if self.sql_types.get(sql_type.upper()) is str:
                        if data.get(column) is not None:
                            columns.append(column)
                            values.append("\"%s\"" % str(data.get(column)))

                    elif data.get(column) is not None:
                        columns.append(column)
                        values.append(str(data.get(column)))

            with database:
                cursor.execute("INSERT INTO %s (%s) VALUES (%s);" % (table,
                    ", ".join(columns), ", ".join(values)))

        except Exception as error:
            self.logger.critical(str(error))

        database.commit()
        cursor.close()


    def __update(self, table, data, where):
        """ Update a row from database

        This function update a row from database with data and where dict which
        use keys as columns.

        Parameters
        ----------
        table : str
            Table name
        data : dict
            Columns keys and values
        where : dict
            Request conditions
        """

        database = sqlite3.connect(self.path)
        cursor = database.cursor()

        try:
            values = self.__generate_request(table, data)
            conditions = self.__generate_request(table, where)

            with database:
                cursor.execute("UPDATE %s SET %s WHERE %s;" % (table,
                    ", ".join(values), " AND ".join(conditions)))

        except Exception as error:
            self.logger.critical(str(error))

        database.commit()
        cursor.close()


    def select(self, table, columns, where=None):
        """ Get rows from the database

        This function do a request for specific columns from database with where
        dict which use keys as columns.

        Parameters
        ----------
        table : str
            Table name
        columns : list
            Columns name list
        where : dict
            Request conditions (default: None)

        Returns
        -------
        object or None
            Database rows

        Examples
        --------
        >>> database.get("main", ["age"], {"name": "doe"})
        {'age': 42}
        """

        value = None

        if type(columns) is not list:
            columns = [columns]

        database = sqlite3.connect(self.path)
        cursor = database.cursor()

        try:
            if where is None:
                request = cursor.execute("SELECT %s FROM %s;" % (
                    ", ".join(columns), table))

            else:
                conditions = self.__generate_request(table, where)

                request = cursor.execute("SELECT %s FROM %s WHERE %s;" % (
                    ", ".join(columns), table, " AND ".join(conditions)))

            value = request.fetchall()

            if len(columns) == 1 and not '*' in columns:
                value = [index[0] for index in value]

        except Exception as error:
            self.logger.critical(str(error))

        database.commit()
        cursor.close()

        if value is not None and len(value) == 0:
            return None
        elif value is not None and len(value) == 1:
            return value[0]

        return value


    def remove(self, table, where):
        """ Remove data from database

        This function remove a row from database with where dict which use keys
        as columns.

        Parameters
        ----------
        table : str
            Table name
        where : dict
            Request conditions
        """

        database =  sqlite3.connect(self.path)
        cursor = database.cursor()

        try:
            with database:
                conditions = self.__generate_request(table, where)

                cursor.execute("DELETE FROM %s WHERE %s;" % (table,
                    " AND ".join(conditions)))

        except Exception as error:
            self.logger.critical(str(error))

        database.commit()
        cursor.close()


    def modify(self, table, data, where=None):
        """ Set a specific data in main table

        This function insert or update a row from database with data and where
        dict which use keys as columns.

        Parameters
        ----------
        table : str
            Table name
        data : dict
            Columns keys and values
        where : dict
            Request conditions (Default: None)
        """

        request = self.select(table, list(data.keys()), where)

        if request is None:
            if where is not None:
                data.update(where)

            self.__insert(table, data)

        else:
            self.__update(table, data, where)


    def get(self, table, where):
        """ Get rows from database

        This function request rows from database with where dict which use keys
        as columns.

        Parameters
        ----------
        table : str
            Table name
        where : dict
            Request conditions

        Returns
        -------
        dict
            Rows data

        Examples
        --------
        >>> database.get("main", {"name": "doe"})
        {'first_name': 'john', 'age': 42}
        """

        result = None

        values = self.select(table, ['*'], where)

        if values is not None:
            columns = self.__get_columns(table)

            result = dict()
            for column in columns:
                value = values[columns.index(column)]
                if value == "None":
                    value = None

                result[column] = value

        return result


    def check_integrity(self):
        """ Check if database respect configuration schema

        Returns
        -------
        bool
            Integrity status
        """

        tables = self.select("sqlite_master", ["name"], { "type": "table" })
        if not type(tables) is list:
            tables = [tables]

        if not tables == self.configuration.sections():
            return False

        for table in tables:
            if not self.__get_columns(table) == \
                self.configuration.options(table):
                return False

        return True


    def migrate(self, table, renamed_columns=None, splash=None):
        """ Migrate old data from a database

        This function check if the database need to update his schema by
        checking configuration schema and possible renamed columns

        Parameters
        ----------
        table : str
            Table name
        renamed_columns : dict
            In case of some columns need to change their name (Keys are old
            names, Values are new names)
        splash : class
            Class which contains functions update and close to call when
            database is modified
        """

        columns_index = dict()

        # Get current table columns
        old_columns = self.__get_columns(table)
        # Get current table rows
        old_data = self.select(table, ['*'])

        # Backup current table and create a new one
        self.__rename_table(table, "_%s" % table)
        self.__create_table(table)

        # Check old table if new columns are available
        for column in old_columns:
            if column in self.__get_columns(table):
                columns_index[column] = old_columns.index(column)

            if renamed_columns is not None and \
                column in list(renamed_columns.keys()):

                columns_index[renamed_columns[column]] = \
                    old_columns.index(column)

        columns_data = dict()
        for column in self.__get_columns(table):
            columns_data[column] = str()

        # Migrate rows from previous database to new one
        if old_data is not None:
            counter = 1

            if splash is not None:
                splash.init(len(old_data))

            for row in old_data:
                columns = deepcopy(columns_data)

                for column in list(columns.keys()):

                    # There is data for this row column
                    if column in columns_index:
                        columns[column] = row[columns_index[column]]

                    # No data for this row column
                    else:
                        columns[column] = None

                # Insert row in new database
                self.__insert(table, columns)

                if splash is not None:
                    splash.update(counter)

                counter += 1

        # Remove backup table
        self.__remove_table("_%s" % table)
