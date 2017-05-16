# ------------------------------------------------------------------
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
# ------------------------------------------------------------------

# ------------------------------------------------------------------
#   Modules
# ------------------------------------------------------------------

# System
from os.path import join as path_join

# ------------------------------------------------------------------
#   Modules - XDG
# ------------------------------------------------------------------

try:
    from xdg.BaseDirectory import xdg_data_home
    from xdg.BaseDirectory import xdg_config_home

except ImportError as error:
    from os import environ
    from os.path import expanduser

    if "XDG_DATA_HOME" in environ:
        xdg_data_home = environ["XDG_DATA_HOME"]
    else:
        xdg_data_home = expanduser("~/.local/share")

    if "XDG_CONFIG_HOME" in environ:
        xdg_config_home = environ["XDG_CONFIG_HOME"]
    else:
        xdg_config_home = expanduser("~/.config")

# ------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------

class Gem:
    Id          = 1337
    Name        = "Graphical Emulators Manager"
    Acronym     = "GEM"
    Version     = "0.7"
    CodeName    = "Vampire hunter"
    Icon        = "gem"
    Website     = "https://gem.tuxfamily.org/"
    Copyleft    = "Copyleft 2017 - Kawa Team"
    Description = "Manage your emulators easily and have fun"

    OldColumns  = dict()


class Path:
    User        = path_join(xdg_config_home, "gem")
    Data        = path_join(xdg_data_home, "gem")
    Apps        = path_join(xdg_data_home, "applications")
    Lock        = path_join(xdg_data_home, "gem", ".lock")
    Roms        = path_join(xdg_data_home, "gem", "roms")
    Logs        = path_join(xdg_data_home, "gem", "logs")
    Notes       = path_join(xdg_data_home, "gem", "notes")
    Icons       = path_join(xdg_data_home, "gem", "icons")
    Consoles    = path_join(xdg_data_home, "gem", "icons", "consoles")
    Emulators   = path_join(xdg_data_home, "gem", "icons", "emulators")


class Conf:
    Log         = path_join("config", "log.conf")
    Desktop     = path_join("config", "template.desktop")
    Default     = path_join("config", "gem.conf")
    Consoles    = path_join("config", "consoles.conf")
    Emulators   = path_join("config", "emulators.conf")
    Databases   = path_join("config", "databases.conf")

