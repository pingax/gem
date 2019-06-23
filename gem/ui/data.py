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

# ------------------------------------------------------------------------------
#   Modules - XDG
# ------------------------------------------------------------------------------

try:
    from xdg.BaseDirectory import xdg_data_home
    from xdg.BaseDirectory import xdg_cache_home
    from xdg.BaseDirectory import xdg_config_home

except ImportError:
    from os import environ

    if "XDG_DATA_HOME" in environ:
        xdg_data_home = Path(environ["XDG_DATA_HOME"]).expanduser()
    else:
        xdg_data_home = Path.home().joinpath(".local", "share")

    if "XDG_CACHE_HOME" in environ:
        xdg_cache_home = Path(environ["XDG_CACHE_HOME"]).expanduser()
    else:
        xdg_cache_home = Path.home().joinpath(".cache")

    if "XDG_CONFIG_HOME" in environ:
        xdg_config_home = Path(environ["XDG_CONFIG_HOME"]).expanduser()
    else:
        xdg_config_home = Path.home().joinpath(".config")


# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class Metadata:
    """ Store application informations
    """


class Folders:
    """ Store application paths
    """

    APPLICATIONS = Path(xdg_data_home, "applications").expanduser()

    class Default:
        """ Store default application paths
        """

        CACHE = Path(xdg_cache_home).expanduser()
        CONFIG = Path(xdg_config_home).expanduser()
        LOCAL = Path(xdg_data_home).expanduser()


class Icons:
    """ Store icons name
    """

    class Size:
        """ Store icons cache subdirectories
        """

    class Symbolic:
        """ Store symbolic icons name

        Store icon symbolic version which are available in GNOME icons theme
        gnome-icon-theme-symbolic
        """


class Columns:
    """ Store games views informations
    """

    class Key:
        """ Store view flags name
        """

        List = "list"
        Grid = "grid"

    class List:
        """ Store treeview model column index
        """

    class Grid:
        """ Store grid model column index
        """
