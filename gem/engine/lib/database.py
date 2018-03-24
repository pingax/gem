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

# Database
import sqlite3

# GEM
from gem.engine.lib import *

from gem.engine.lib.configuration import Configuration

# Logging
from logging import Logger

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
                self.create_table(table)

        else:
            tables = self.select("sqlite_master", ["name"], { "type": "table" })
            if not type(tables) is list:
                tables = [tables]

            for table in list(set(self.configuration.sections()) - set(tables)):
                self.create_table(table)


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


    def create_table(self, table):
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


    def rename_table(self, table, name):
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


    def remove_table(self, table):
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


    def add_column(self, table, name, sql_type):
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


    def get_columns(self, table):
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


    def insert(self, table, data):
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


    def update(self, table, data, where):
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
        where : dict, optional
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
        where : dict, optional
            Request conditions (Default: None)
        """

        request = self.select(table, list(data.keys()), where)

        if request is None:
            if where is not None:
                data.update(where)

            self.insert(table, data)

        else:
            self.update(table, data, where)


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
            columns = self.get_columns(table)

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
            if not self.get_columns(table) == \
                self.configuration.options(table):
                return False

        return True