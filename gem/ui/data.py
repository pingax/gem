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

except ImportError as error:
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

class Documents:
    Desktop     = "template.desktop"

class Folders:
    Apps        = Path(xdg_data_home, "applications").expanduser()
    Cache       = Path(xdg_cache_home, "gem").expanduser()
    Local       = Path(xdg_data_home, "gem").expanduser()
    Config      = Path(xdg_config_home, "gem").expanduser()

class Icons:
    class Symbolic:
        pass

class Columns:

    Order = "favorite:multiplayer:finish:name:play:play_time:last_play:" \
        "score:installed:flags"

    class Key:
        List            = "list"
        Grid            = "grid"

    class List:
        Favorite        = 0
        Multiplayer     = 1
        Finish          = 2
        Name            = 3
        Played          = 4
        LastPlay        = 5
        LastTimePlay    = 6
        TimePlay        = 7
        Score           = 8
        Installed       = 9
        Except          = 10
        Snapshots       = 11
        Save            = 12
        Object          = 13
        Thumbnail       = 14

    class Grid:
        Icon            = 0
        Name            = 1
        Object          = 2
