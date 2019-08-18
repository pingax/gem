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

# Filesystem
from pathlib import Path

# System
from configparser import ConfigParser


# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class Configuration(ConfigParser):

    def __init__(self, filepath, **kwargs):
        """ Constructor

        Parameters
        ----------
        filepath : pathlib.Path
            Configuration file path

        Raises
        ------
        TypeError
            If filepath instance is not pathlib.Path
        """

        if not isinstance(filepath, Path):
            raise TypeError("Expected %s type for filepath, get %s" % (
                "pathlib.Path", type(filepath)))

        # ------------------------------------
        #   Variables
        # ------------------------------------

        ConfigParser.__init__(self, kwargs)

        self.path = filepath.expanduser()

        if self.path.exists():
            self.read(str(self.path))

    def __str__(self):
        """ Formated informations

        Returns
        -------
        str
            Formated string
        """

        text = list()

        for section in sorted(self.sections()):
            text.append("[%s]" % section)

            for key in sorted(self.options(section)):
                text.append("%s = %s" % (
                    key, self.get(section, key, fallback=str())))

        return '\n'.join(text)

    def reload(self):
        """ Read again the configuration file if exists
        """

        if self.path.exists():
            self.read(self.path)

    def item(self, section, option, default=None):
        """ Return an item from configuration

        Parameters
        ----------
        section : str
            Section name
        option : str
            Option name
        default : str, optional
            Fallback value to return if nothing has been founded
            (default: None)

        Returns
        -------
        str or None
            Value from section option
        """

        if self.has_section(section) and self.has_option(section, option):
            return self.get(section, option)

        return default

    def append(self, section, option, value):
        """ Append a new section to configuration

        Parameters
        ----------
        section : str
            Section name
        option : str
            Option name
        value : str
            Value to set

        Raises
        ------
        IndexError
            If the configuration file not has section
        """

        if self.has_section(section):
            raise IndexError("Cannot find %s section" % section)

        self.add_section(section)
        self.set(section, option, str(value))

    def modify(self, section, option, value):
        """ Modify a section from configuration

        This function append or update a section into configuration

        Parameters
        ----------
        section : str
            Section name
        option : str
            Option name
        value : object
            Value to set
        """

        # Set a specific value for bool variables
        if type(value) is bool:
            if value:
                value = "yes"
            else:
                value = "no"

        if self.has_section(section):
            self.set(section, option, str(value))

        else:
            self.append(section, option, str(value))

    def rename(self, section, new_name):
        """ Rename a section from configuration

        Parameters
        ----------
        section : str
            Previous section name
        new_name : str
            New section name
        """

        if self.has_section(section) and not self.has_section(new_name):

            for (option, value) in self.items(section):
                self.modify(new_name, option, value)

            self.remove(section)

    def remove(self, section):
        """ Remove a section from configuration

        Parameters
        ----------
        section : str
            Section name
        """

        if self.has_section(section):
            self.remove_section(section)

    def update(self):
        """ Write all data from cache into configuration file

        This function need to be exec after each modifications to update file
        content
        """

        with self.path.open('w') as pipe:
            self.write(pipe)

    def add_missing_data(self, secondary_path):
        """ Append to configuration all missing data from another configuration

        Parameters
        ----------
        secondary_path : str
            Configuration file where to get missing sections/options

        Raises
        ------
        OSError
            If the configuration filepath not exists
        """

        if not secondary_path.exists():
            raise OSError(2, "Cannot find file", str(secondary_path))

        config = Configuration(secondary_path)

        for section in config.sections():

            if not self.has_section(section):
                self.add_section(section)

            for option in config.options(section):

                if not self.has_option(section, option):
                    self.set(section, option, config.get(section, option))

        self.update()
