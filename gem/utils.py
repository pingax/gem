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
from os.path import exists
from os.path import basename
from os.path import splitext
from os.path import expanduser
from os.path import join as path_join

from datetime import datetime

# Interface
from gi.repository import Gtk
from gi.repository.GdkPixbuf import Pixbuf
from gi.repository.GdkPixbuf import Colorspace

# Package
from pkg_resources import resource_filename
from pkg_resources import DistributionNotFound

# Translation
from gettext import gettext as _
from gettext import textdomain
from gettext import bindtextdomain

# XDG
from xdg.BaseDirectory import xdg_data_home
from xdg.BaseDirectory import xdg_config_home

# ------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------

class Gem:
    Version     = "0.5"
    CodeName    = "Rich Duck"
    OldColumns  = dict(
        played="play",
        last_played="last_play",
        last_played_time="last_play_time" )

class Icons:
    Ext         = "png"
    Misc        = "applications-other"
    Snap        = "emblem-photos"
    Save        = "emblem-downloads"
    File        = "emblem-documents"
    Except      = "emblem-important"
    Favorite    = "emblem-favorite"
    Game        = "input-gaming"
    System      = "preferences-system"
    Emulator    = "preferences-desktop"
    Keyboard    = "preferences-desktop-keyboard"
    Users       = "system-users"
    Multiplayer = "system-users"
    Output      = "utilities-terminal"

class Path:
    User        = path_join(xdg_config_home, "gem")
    Data        = path_join(xdg_data_home, "gem")
    Apps        = path_join(xdg_data_home, "applications")
    Logs        = path_join(xdg_data_home, "gem", "logs")
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

class Columns:
    Favorite        = 0
    Icon            = 1
    Name            = 2
    Played          = 3
    LastPlay        = 4
    LastTimePlay    = 5
    TimePlay        = 6
    Installed       = 7
    Except          = 8
    Snapshots       = 9
    Multiplayer     = 10
    Save            = 11
    Filename        = 12

# ------------------------------------------------------------------
#   Methods
# ------------------------------------------------------------------

def get_data(path, egg="gem"):
    """
    Provides easy access to data in a python egg

    Thanks Deluge :)
    """

    try:
        data = resource_filename(egg, path)

        if exists(data):
            return data

        return path

    except DistributionNotFound as error:
        return path

    except KeyError as error:
        return None


def icon_from_data(icon, default=None, width=24, height=24, folder=None):
    """
    Load an icon or return an empty icon if not found
    """

    if icon is not None:
        icon_name = splitext(basename(icon))[0]

        path = icon
        if not exists(expanduser(icon)):
            path = path_join(Path.Icons, "%s.%s" % (icon, Icons.Ext))
            if folder is not None:
                path = path_join(
                    Path.Icons, folder, "%s.%s" % (icon, Icons.Ext))

        if path is not None and exists(expanduser(path)):
            try:
                return Pixbuf.new_from_file_at_size(
                    expanduser(path), width, height)
            except GError:
                pass

    if default is None:
        default = Pixbuf.new(Colorspace.RGB, True, 8, width, height)
        default.fill(0x00000000)

    return default


def icon_load(name, size=16, fallback="image-missing"):
    """
    Get an icon from data folder
    """

    icons_theme = Gtk.IconTheme.get_default()

    # Check if specific icon name is in icons theme
    if icons_theme.has_icon(name):
        try:
            return icons_theme.load_icon(
                name, size, Gtk.IconLookupFlags.FORCE_SVG)

        except:
            if type(fallback) == Pixbuf:
                return fallback

            return icons_theme.load_icon(
                fallback, size, Gtk.IconLookupFlags.FORCE_SVG)

    # Return fallback icon (in the case where is a Pixbuf)
    if type(fallback) == Pixbuf:
        return fallback

    # Find fallback icon in icons theme
    if icons_theme.has_icon(fallback):
        return icons_theme.load_icon(
            fallback, size, Gtk.IconLookupFlags.FORCE_SVG)

    # Instead, return default image
    return icons_theme.load_icon(
        "image-missing", size, Gtk.IconLookupFlags.FORCE_SVG)


def string_from_date(date, date_format="%d-%m-%Y %H:%M:%S"):
    """
    Get time since last play
    """

    date_string = None

    if date is not None:

        now = datetime.now()
        game_date = datetime.strptime(str(date), date_format)

        value = (now - game_date).days

        if value == 0:
            return _("Today")
        elif value == 1:
            return _("Yesterday")
        elif value < 30:
            return _("%d days ago") % int(value)
        else:
            months = int(value / 30)

            if months == 1:
                return _("Last month")
            elif months < 12:
                return _("%d months ago") % int(months)
            else:
                years = int(value / 365)

                if years < 2:
                    return _("Last year")

                return _("%d years ago") % int(years)

    return None


def on_entry_clear(widget, pos, event):
    """
    Reset entry filter when icon was clicked
    """

    if pos == Gtk.EntryIconPosition.SECONDARY and len(widget.get_text()) > 0:
        widget.set_text(str())
