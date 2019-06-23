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

# GEM
from gem.engine.utils import get_binary_path
from gem.engine.utils import generate_identifier


# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class Emulator(object):

    attributes = {
        "id": str,
        "name": str,
        "default": str,
        "windowed": str,
        "fullscreen": str,
        "icon": Path,
        "binary": Path,
        "configuration": Path,
        "savestates": Path,
        "screenshots": Path
    }

    def __init__(self, parent, **kwargs):
        """ Constructor

        Parameters
        ----------
        parent : gem.engine.api.GEM
            API instance
        """

        # ----------------------------------------
        #   Variables
        # ----------------------------------------

        self.__parent = parent

        # ----------------------------------------
        #   Initialization
        # ----------------------------------------

        # Initialize variables
        self.__init_keys(**kwargs)

    def __init_keys(self, **kwargs):
        """ Initialize object attributes
        """

        for key, key_type in self.attributes.items():

            if key in kwargs.keys():
                value = kwargs[key]

            elif key_type is Path:
                value = None

            else:
                value = key_type()

            setattr(self, key, value)

            if key_type is Path and type(value) is str:

                path = Path(value).expanduser()
                if len(value) == 0:
                    path = None

                setattr(self, key, path)

        setattr(self, "id", generate_identifier(self.name))

    def as_dict(self):
        """ Return object as dictionary structure

        Returns
        -------
        dict
            Data structure
        """

        return {
            "binary": self.binary,
            "configuration": self.configuration,
            "icon": self.icon,
            "save": self.savestates,
            "snaps": self.screenshots,
            "default": self.default,
            "windowed": self.windowed,
            "fullscreen": self.fullscreen
        }

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
