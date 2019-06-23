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

# Database
import sqlite3

# Filesystem
from pathlib import Path

# GEM
from gem.engine.lib.configuration import Configuration

# Logging
from logging import Logger


# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class Database(object):

    def __init__(self, db_path, configuration, logger):
        """ Constructor

        Parameters
        ----------
        db_path : pathlib.Path
            Database filepath
        configuration : gem.engine.lib.configuration.Configuration
            Configuration file which contains database scheme
        logger : logging.Logger
            Logging object

        Raises
        ------
        TypeError
            If scheme type is not gem.engine.lib.Configuration
            If logger type is not logging.Logger
        """

        if not isinstance(db_path, Path):
            raise TypeError("Expected %s type for db_path, get %s" % (
                "pathlib.Path", type(db_path)))

        if type(configuration) is not Configuration:
            raise TypeError("Expected %s type for configuration, get %s" % (
                "gem.engine.lib.Configuration", type(configuration)))

        if type(logger) is not Logger:
            raise TypeError("Expected %s type for logger, get %s" % (
                "logging.Logger", type(logger)))

        # ------------------------------------
        #   Variables
        # ------------------------------------

        self.path = db_path.expanduser()

        self.configuration = configuration

        self.logger = logger

        self.sql_types = {
            "NULL": None,
            "BOOL": int,
            "INTEGER": int,
            "REAL": float,
            "TEXT": str,
            "BLOB": memoryview
        }

        # ------------------------------------
        #   Intialization
        # ------------------------------------

        if not self.path.exists():
            for table in self.configuration.sections():
                self.create_table(table)

        else:
            tables = self.select("sqlite_master", ["name"], {"type": "table"})
            if not type(tables) is list:
                tables = [tables]

            tables = list(set(self.configuration.sections()) - set(tables))

            for table in tables:
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

        database = sqlite3.connect(str(self.path))
        cursor = database.cursor()

        for option in self.configuration.items(table):
            request.append(" ".join(option))

        try:
            with database:
                cursor.execute("CREATE TABLE %(table)s (%(data)s);" % {
                    "table": table,
                    "data": ", ".join(request)
                })

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

        database = sqlite3.connect(str(self.path))
        cursor = database.cursor()

        try:
            cursor.execute("ALTER TABLE %(table)s RENAME TO %(name)s;" % {
                "table": table,
                "name": name
            })

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

        database = sqlite3.connect(str(self.path))
        cursor = database.cursor()

        try:
            cursor.execute("DROP TABLE IF EXISTS %(table)s;" % {
                "table": table
            })

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

        database = sqlite3.connect(str(self.path))
        cursor = database.cursor()

        try:
            with database:
                cursor.execute(
                    "ALTER TABLE %(table)s ADD COLUMN %(name)s %(type)s;" % {
                        "table": table,
                        "name": name,
                        "type": sql_type
                    })

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

        database = sqlite3.connect(str(self.path))
        cursor = database.cursor()

        try:
            with database:
                request = cursor.execute("PRAGMA table_info(%(table)s);" % {
                    "table": table
                })

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

        database = sqlite3.connect(str(self.path))
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
                cursor.execute(
                    "INSERT INTO %(table)s (%(columns)s) VALUES (%(data)s);" % {
                        "table": table,
                        "columns": ", ".join(columns),
                        "data": ", ".join(values)
                    })

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

        database = sqlite3.connect(str(self.path))
        cursor = database.cursor()

        try:
            values = self.__generate_request(table, data)
            conditions = self.__generate_request(table, where)

            with database:
                cursor.execute(
                    "UPDATE %(table)s SET %(data)s WHERE %(where)s;" % {
                        "table": table,
                        "data": ", ".join(values),
                        "where": " AND ".join(conditions)
                    })

        except Exception as error:
            self.logger.critical(str(error))

        database.commit()
        cursor.close()

    def select(self, table, columns, where=None):
        """ Get rows from the database

        This function do a request for specific columns from database with
        where dict which use keys as columns.

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

        database = sqlite3.connect(str(self.path))
        cursor = database.cursor()

        try:
            if where is None:
                request = cursor.execute(
                    "SELECT %(columns)s FROM %(table)s;" % {
                        "table": table,
                        "columns": ", ".join(columns)
                    })

            else:
                conditions = self.__generate_request(table, where)

                request = cursor.execute(
                    "SELECT %(columns)s FROM %(table)s WHERE %(where)s;" % {
                        "table": table,
                        "columns": ", ".join(columns),
                        "where": " AND ".join(conditions)
                    })

            value = request.fetchall()

            if len(columns) == 1 and '*' not in columns:
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

        database = sqlite3.connect(str(self.path))
        cursor = database.cursor()

        try:
            with database:
                conditions = self.__generate_request(table, where)

                cursor.execute("DELETE FROM %(table)s WHERE %(where)s;" % {
                    "table": table,
                    "where": " AND ".join(conditions)
                })

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

        tables = self.select("sqlite_master", ["name"], {"type": "table"})
        if not type(tables) is list:
            tables = [tables]

        if not sorted(tables) == sorted(self.configuration.sections()):
            return False

        for table in tables:
            columns = self.configuration.options(table)

            if not self.get_columns(table) == columns:
                return False

        return True
