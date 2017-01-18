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
from os import environ

from os.path import exists
from os.path import basename
from os.path import splitext
from os.path import expanduser
from os.path import join as path_join

from datetime import datetime

# Translation
from gettext import gettext as _
from gettext import textdomain
from gettext import bindtextdomain

# ------------------------------------------------------------------
#   Modules - Packages
# ------------------------------------------------------------------

try:
    from pkg_resources import resource_filename
    from pkg_resources import DistributionNotFound

except ImportError as error:
    sys_exit("Cannot found python3-pkg-resources module: %s" % str(error))

# ------------------------------------------------------------------
#   Modules - Interface
# ------------------------------------------------------------------

try:
    from gi import require_version

    require_version("Gtk", "3.0")

    from gi.repository import Gtk
    from gi.repository.GdkPixbuf import Pixbuf
    from gi.repository.GdkPixbuf import Colorspace

except ImportError as error:
    sys_exit("Cannot found python3-gobject module: %s" % str(error))

# ------------------------------------------------------------------
#   Modules - XDG
# ------------------------------------------------------------------

try:
    from xdg.BaseDirectory import xdg_data_home
    from xdg.BaseDirectory import xdg_config_home

except ImportError as error:
    sys_exit("Cannot found pyxdg module: %s" % str(error))

# ------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------

class Gem:
    Name        = "Graphical Emulators Manager"
    Version     = "0.6"
    CodeName    = "Magicball"
    Website     = "https://gem.tuxfamily.org/"
    Copyleft    = "Copyleft 2017 - Kawa Team"
    Description = _("Manage your emulators easily and have fun")

    OldColumns  = dict()

class Icons:
    Ext         = "png"
    Misc        = "applications-other"
    Error       = "dialog-error"
    Warning     = "dialog-warning"
    Properties  = "document-properties"
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
    Roms        = path_join(xdg_data_home, "gem", "roms")
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

    :param str path: File path
    :param str egg: Python egg name

    :return: Path
    :rtype: str/None
    """

    try:
        data = resource_filename(egg, path)

        if exists(data):
            return data

        return path

    except DistributionNotFound as error:
        return path

    return None


def icon_from_data(icon, fallback=None, width=24, height=24, subfolder=None):
    """
    Load an icon or return an empty icon if not found

    :param str icon: Icon path
    :param GdkPixbuf.Pixbuf fallback: Fallback icon to return if wanted icon
        was not found
    :param int width: Icon width
    :param int height: Icon height
    :param str subfolder: Subfolder in Path.Icons

    :return: Icon object
    :rtype: GdkPixbuf.Pixbuf
    """

    if icon is not None:
        path = icon

        if not exists(expanduser(icon)):
            path = path_join(Path.Icons, "%s.%s" % (icon, Icons.Ext))

            if subfolder is not None:
                path = path_join(
                    Path.Icons, subfolder, "%s.%s" % (icon, Icons.Ext))

        if path is not None and exists(expanduser(path)):
            try:
                return Pixbuf.new_from_file_at_size(
                    expanduser(path), width, height)
            except GError:
                pass

    # Return an empty icon
    if fallback is None:
        fallback = Pixbuf.new(Colorspace.RGB, True, 8, width, height)
        fallback.fill(0x00000000)

    return fallback


def icon_load(name, size=16, fallback="image-missing"):
    """
    Get an icon from data folder

    :param str name: Icon name in icons theme
    :param int size: Icon width and height
    :param str/GdkPixbuf.Pixbuf fallback: Fallback icon to return if wanted icon
        was not found

    :return: Icon from icons theme
    :rtype: GdkPixbuf.Pixbuf
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
    Get a pretty string from the interval between NOW() and the wanted date

    :param datetime date: Date to compare with NOW()
    :param str date_format: Date string format

    :return: Pretty string
    :rtype: str/None
    """

    if date is None:
        return None

    if type(date) is str:
        date = datetime.strptime(str(date), date_format)

    days = (datetime.now() - date).days

    if days == 0:
        return _("Today")
    elif days == 1:
        return _("Yesterday")
    elif days < 30:
        return _("%d days ago") % int(days)

    months = int(days / 30)

    if months == 1:
        return _("Last month")
    elif months < 12:
        return _("%d months ago") % int(months)

    years = int(months / 12)

    if years < 2:
        return _("Last year")

    return _("%d years ago") % int(years)


def string_from_time(date, date_format="%H:%M:%S"):
    """
    Get a pretty string from date

    :param datetime date: Date to compare with NOW()
    :param str date_format: Date string format

    :return: Pretty string
    :rtype: str/None
    """

    if date is None:
        return None

    if type(date) is str:
        date = datetime.strptime(str(date), date_format)

    if date.hour == 0:
        if date.minute == 0:
            if date.second == 0:
                return str()
            elif date.second == 1:
                return _("%d second" % date.second)
            else:
                return _("%d seconds" % date.second)

        elif date.minute == 1:
            return _("%d minute" % date.minute)
        else:
            return _("%d minutes" % date.minute)

    elif date.hour == 1:
        return _("%d hour" % date.hour)

    return _("%d hours" % date.hour)


def on_entry_clear(widget, pos, event):
    """
    Reset an entry widget when specific icon is clicked

    :param Gtk.Entry widget: Entry widget
    :param Gtk.EntryIconPosition pos: Specific icon from entry widget
    :param Gdk.Event event: Wdget event

    :return: Function state
    :rtype: bool
    """

    if type(widget) is not Gtk.Entry:
        return False

    if pos == Gtk.EntryIconPosition.SECONDARY and len(widget.get_text()) > 0:
        widget.set_text(str())

        return True

    return False


def on_change_theme(status=False):
    """
    Change dark status of interface theme

    :param bool status: Use dark theme
    """

    Gtk.Settings.get_default().set_property(
        "gtk-application-prefer-dark-theme", status)


def get_binary_path(binary):
    """
    Get a list of available binary paths from $PATH variable

    :param str binary: Binary name or path

    :return: List of available path
    :rtype: list
    """

    available = list()

    if len(binary) == 0:
        return available

    if exists(expanduser(binary)):
        available.append(binary)
        binary = basename(binary)

    for path in set(environ["PATH"].split(':')):
        binary_path = expanduser(path_join(path, binary))

        if exists(binary_path) and not binary_path in available:
            available.append(binary_path)

    return available
