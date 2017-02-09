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
from os.path import exists
from os.path import expanduser

from sys import version_info

# Configuration
if(version_info[0] >= 3):
    from configparser import SafeConfigParser
else:
    from ConfigParser import SafeConfigParser

# Translation
from gettext import lgettext as _
from gettext import textdomain
from gettext import bindtextdomain

# ------------------------------------------------------------------
#   Modules - GEM
# ------------------------------------------------------------------

try:
    from gem import *
    from gem.utils import get_data

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

class Configuration(SafeConfigParser):

    def __init__(self, path):
        """
        Constructor

        :param str path: Configuration file path
        """

        SafeConfigParser.__init__(self)

        # ------------------------------------
        #   Variables
        # ------------------------------------

        self.path = path

        # ------------------------------------
        #   Read contents
        # ------------------------------------

        if not exists(path):
            raise IOError(_("Cannot open %s file" % path))

        self.read(path)


    def item(self, section, option, default=None):
        """
        Return an item from configuration

        :param str section: Section name
        :param str option: Option name
        :param str default: Default value to return

        :return: Option value
        :rtype: str/None
        """

        if self.has_section(section) and self.has_option(section, option):
            return self.get(section, option)

        return default


    def append(self, section, option, value):
        """
        Append a new section to configuration

        :param str section: Section name
        :param str option: Option name
        :param str value: Option value
        """

        if not self.has_section(section):
            self.add_section(section)
            self.set(section, option, str(value))


    def modify(self, section, option, value):
        """
        Modify a section from configuration

        :param str section: Section name
        :param str option: Option name
        :param str value: Option value
        """

        if self.has_section(section):
            self.set(section, option, str(value))

        else:
            self.append(section, option, str(value))


    def rename(self, section, new_name):
        """
        Rename a section from configuration

        :param str section: Old section name
        :param str new_name: New section name
        """

        if self.has_section(section) and not self.has_section(new_name):

            for (option, value) in self.items(section):
                self.modify(new_name, option, value)

            self.remove(section)


    def remove(self, section):
        """
        Remove a section from configuration

        :param str section: Section name
        """

        if self.has_section(section):
            self.remove_section(section)


    def update(self):
        """
        Write all data from cache into configuration file
        """

        with open(self.path, 'w') as pipe:
            self.write(pipe)


    def add_missing_data(self, path):
        """
        Append to configuration all missing data from another configuration

        :param str path: Other configuration file path
        """

        if exists(expanduser(path)):
            config = Configuration(path)

            for section in config.sections():

                if not self.has_section(section):
                    self.add_section(section)

                for option in config.options(section):

                    if not self.has_option(section, option):
                        self.set(section, option, config.get(section, option))

            self.update()
