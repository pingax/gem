# -*- coding: utf-8 -*-
# ------------------------------------------------------------------
#
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
#
# ------------------------------------------------------------------

# ------------------------------------------------------------------
#   Modules
# ------------------------------------------------------------------

# System
from copy import deepcopy
from os.path import exists

# Database
import sqlite3

# Translation
from gettext import gettext as _
from gettext import textdomain
from gettext import bindtextdomain

# ------------------------------------------------------------------
#   Modules - GEM
# ------------------------------------------------------------------

try:
    from gem.utils import *
    from gem.configuration import Configuration

except ImportError as error:
    sys_exit("Cannot found gem module: %s" % str(error))

# ------------------------------------------------------------------
#   Translation
# ------------------------------------------------------------------

bindtextdomain("gem", get_data("i18n"))
textdomain("gem")

# ------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------

class Database(object):

    def __init__(self, db_path, configuration_path, logger):
        """
        Constructor

        :param str db_path: Database path
        :param str configuration_path: Database configuration path
        :param logging.Logger logger: Logging object
        """

        # ------------------------------------
        #   Variables
        # ------------------------------------

        self.path = db_path
        self.configuration = Configuration(configuration_path)

        self.sql_types = {
            "NULL": None,
            "BOOL": int,
            "INTEGER": int,
            "REAL": float,
            "TEXT": str,
            "BLOB": memoryview }

        # ------------------------------------
        #   Logger
        # ------------------------------------

        self.logger = logger

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
        """
        Generate a container with parameters which contains request strings

        :param str table: Table name
        :param dict data: Columns and values data (Dict keys are columns)

        :return: Request strings list
        :rtype: list
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
        """
        Create a new table into database

        :param str table: Table name
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
        """
        Rename a table from database

        :param str table: Table name
        :param str name: New table name
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
        """
        Remove a table from database

        :param str table: Table name
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
        """
        Add a new column into database

        :param str table: Table name
        :param str name: Column name
        :param str sql_type: Column type
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
        """
        Get all the columns from database

        :param str table: Table name

        :return: Columns list
        :rtype: list
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
        """
        Insert a new row into database

        :param str table: Table name
        :param dict data: Columns and values data (Dict keys are columns)
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
        """
        Update a row from database

        :param str table: Table name
        :param dict data: Columns and values data (Dict keys are columns)
        :param dict where: Update conditions (Dict keys are columns)
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
        """
        Get rows from the database

        :param str table: Table name
        :param list columns: Columns name
        :param dict where: Search conditions (Dict keys are columns)

        :return: Database rows
        :rtype: str/bool/None
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
        """
        Remove data from database

        :param str table: Table name
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
        """
        Set a specific data in main table
        """

        request = self.select(table, list(data.keys()), where)

        if request is None:
            if where is not None:
                data.update(where)

            self.__insert(table, data)

        else:
            self.__update(table, data, where)


    def get(self, table, data):
        """
        Get all the data for a specific entry in database

        :param str table: Table name

        :return: Entry data
        :rtype: list
        """

        result = None

        values = self.select(table, ['*'], data)

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
        """
        Check if database respect configuration schema

        :return: Integrity status
        :rtype: bool
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


    def migrate(self, table, renamed_columns=None, function=None):
        """
        Migrate old data from a database

        :param str table: Table name
        :param dict renamed_columns: In case of some columns need to change
            their name (Keys are old names, Values are new names)
        :param def function: Function to call every new insert into database
        """

        columns_index = dict()

        old_columns = self.__get_columns(table)
        old_data = self.select(table, ['*'])

        self.__rename_table(table, "_%s" % table)
        self.__create_table(table)

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

        if old_data is not None:
            self.logger.info(_("Start to migrate %d entries" % len(old_data)))

            for row in old_data:
                columns = deepcopy(columns_data)

                for column in list(columns.keys()):
                    if column in columns_index:
                        columns[column] = row[columns_index[column]]

                    else:
                        columns[column] = None

                self.__insert(table, columns)

                if function is not None:
                    function()

        self.__remove_table("_%s" % table)
