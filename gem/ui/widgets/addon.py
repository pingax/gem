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

# GEM
from gem.engine import *
from gem.engine.lib.configuration import Configuration

# System
from sys import modules

# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class Addon(object):

    # Manage game launch process
    STARTED = "on_game_started"
    TERMINATE = "on_game_terminate"

    def __init__(self):
        """ Constructor
        """

        # ------------------------------------
        #   Initialize variables
        # ------------------------------------

        self.__root = dirname(modules[self.__class__.__module__].__file__)

        self.__manifest = path_join(self.__root, "manifest.conf")

        # ------------------------------------
        #   Initialize logger
        # ------------------------------------

        self.logger = logging.getLogger("gem")

        # ------------------------------------
        #   Check data
        # ------------------------------------

        if not exists(self.__manifest):
            raise IOError(2, "Cannot found manifest.conf")

        self.__config = Configuration(self.__manifest)

        self.__name = self.__config.get(
            "plugin", "name", fallback=str())

        self.__author = self.__config.get(
            "plugin", "author", fallback=str())

        self.__version = self.__config.get(
            "plugin", "version", fallback=str())

        self.__description = self.__config.get(
            "plugin", "description", fallback=str())

        self.__depends = self.__config.get(
            "plugin", "depends", fallback=str()).split()


    def __str__(self):
        """ Formated informations

        Returns
        -------
        str
            Formated string
        """

        return "%(name)s v%(version)s by %(author)s" % {
            "name": self.__name,
            "author": self.__author,
            "version": self.__version,
        }


    def call_function(self, name, *args):
        """ Call a function with a specific name

        Parameters
        ----------
        name : str
            Module name
        """

        if self.has_function(name):
            getattr(self, name)(*args)


    def has_function(self, name):
        """ Check if module has a specific function name

        Parameters
        ----------
        name : str
            Module name

        Returns
        -------
        bool
            Function exists status
        """

        return(hasattr(self, name))


    def get_name(self):
        """ Retrieve plugin name

        Returns
        -------
        str
            Addon name
        """

        return self.__name


    def get_author(self):
        """ Retrieve plugin author

        Returns
        -------
        str
            Addon author
        """

        return self.__author


    def get_version(self):
        """ Retrieve plugin version

        Returns
        -------
        str
            Addon version
        """

        return self.__version


    def get_depends(self):
        """ Retrieve plugin depends

        Returns
        -------
        list
            Addon depends
        """

        return self.__depends


    def get_description(self):
        """ Retrieve plugin description

        Returns
        -------
        list
            Addon description
        """

        return self.__description
