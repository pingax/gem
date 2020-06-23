# ------------------------------------------------------------------------------
#  Copyleft 2015-2020  PacMiam
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
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

# Datetime
from datetime import date
from datetime import timedelta

# Geode
from geode_gem.engine.utils import get_binary_path

# GObject
try:
    from gi import require_version

    require_version("Gtk", "3.0")

    from gi.repository import Gtk
    from gi.repository import GdkPixbuf

except ImportError as error:
    from sys import exit

    exit("Cannot found python3-gobject module: %s" % str(error))

# Processus
from subprocess import PIPE, Popen, STDOUT

# Regex
from re import escape as re_escape
from re import findall as re_findall

# Translation
from gettext import gettext as _
from gettext import ngettext


# ------------------------------------------------------------------------------
#   Misc functions
# ------------------------------------------------------------------------------

def call_external_application(*command):
    """ Call an external application from operating system

    Parameters
    ----------
    command : list
        Command execution parameters as string list

    Returns
    -------
    str
        Splited output if executed, None otherwise
    """

    if get_binary_path(command[0]):
        proc = Popen(
            command,
            stdin=PIPE,
            stdout=PIPE,
            stderr=STDOUT,
            universal_newlines=True)

        output, error_output = proc.communicate()
        if output:
            return output.split('\n')[0]

    return None


def icon_from_data(path, fallback=None, width=24, height=24):
    """ Load an icon from path

    This function search if an icon is available in GEM icons folder and return
    a generate Pixbuf from the icon path. If no icon was found, return an empty
    generate Pixbuf.

    Parameters
    ----------
    path : pathlib.Path
        Absolute or relative icon path
    fallback : GdkPixbuf.Pixbuf, optional
        Fallback icon to return instead of empty (Default: None)
    width : int, optional
        Icon width in pixels (Default: 24)
    height : int, optional
        Icon height in pixels (Default: 24)

    Returns
    -------
    GdkPixbuf.Pixbuf
        Pixbuf icon object
    """

    if path.exists():

        try:
            return GdkPixbuf.Pixbuf.new_from_file_at_size(
                str(path), width, height)
        except Exception:
            pass

    # Return an empty icon
    if fallback is None:
        fallback = GdkPixbuf.Pixbuf.new(
            GdkPixbuf.Colorspace.RGB, True, 8, width, height)
        fallback.fill(0x00000000)

    return fallback


def icon_load(name, size=16, fallback="image-missing"):
    """ Load an icon from IconTheme

    This function search an icon in current user icons theme. If founded,
    return a generate Pixbuf from the icon name, else, return a generate Pixbuf
    from the fallback icon name.

    Parameters
    ----------
    icon : str
        Icon name
    width : int, optional
        Icon width in pixels (Default: 16)
    fallback : str or GdkPixbuf.Pixbuf, optional
        Fallback icon to return instead of empty (Default: image-missing)

    Returns
    -------
    GdkPixbuf.Pixbuf
        Pixbuf icon object
    """

    icons_theme = Gtk.IconTheme.get_default()

    # Check if specific icon name is in icons theme
    if icons_theme.has_icon(name):
        try:
            return icons_theme.load_icon(
                name, size, Gtk.IconLookupFlags.FORCE_SVG)

        except Exception:
            if type(fallback) == GdkPixbuf.Pixbuf:
                return fallback

            return icons_theme.load_icon(
                fallback, size, Gtk.IconLookupFlags.FORCE_SVG)

    # Return fallback icon (in the case where is a Pixbuf)
    if type(fallback) == GdkPixbuf.Pixbuf:
        return fallback

    # Find fallback icon in icons theme
    if icons_theme.has_icon(fallback):
        return icons_theme.load_icon(
            fallback, size, Gtk.IconLookupFlags.FORCE_SVG)

    # Instead, return default image
    return icons_theme.load_icon(
        "image-missing", size, Gtk.IconLookupFlags.FORCE_SVG)


def set_pixbuf_opacity(pixbuf, opacity):
    """ Changes the opacity of pixbuf

    This function generate a new Pixbuf from another one and change his opacity
    by combining the two Pixbufs.

    Thanks to Rick Spencer:
    https://theravingrick.blogspot.fr/2011/01/changing-opacity-of-gtkpixbuf.html

    Parameters
    ----------
    pixbuf : GdkPixbuf.Pixbuf
        Original Pixbuf
    opacity : int
        The degree of desired opacity (between 0 and 255)

    Returns
    -------
    GdkPixbuf.Pixbuf
        Pixbuf icon object
    """

    width, height = pixbuf.get_width(), pixbuf.get_height()

    new_pixbuf = GdkPixbuf.Pixbuf.new(
        GdkPixbuf.Colorspace.RGB, True, 8, width, height)
    new_pixbuf.fill(0x00000000)

    try:
        pixbuf.composite(new_pixbuf, 0, 0, width, height, 0, 0, 1, 1,
                         GdkPixbuf.InterpType.NEAREST, opacity)
    except Exception:
        pass

    return new_pixbuf


def on_change_theme(status=False):
    """ Change dark status of interface theme

    Parameters
    ----------
    status : bool, optional
        Use dark theme (Default: False)
    """

    Gtk.Settings.get_default().set_property(
        "gtk-application-prefer-dark-theme", status)


def on_entry_clear(widget, pos, event):
    """ Reset an entry widget when secondary icon is clicked

    Parameters
    ----------
    widget : Gtk.Entry
        Entry widget
    pos : Gtk.EntryIconPosition
        Position of the clicked icon
    event : Gdk.EventButton or Gdk.EventKey
        Event which triggered this signal

    Returns
    -------
    bool
        Function state
    """

    if type(widget) is not Gtk.Entry:
        return False

    if pos == Gtk.EntryIconPosition.SECONDARY and len(widget.get_text()) > 0:
        widget.set_text(str())

        return True

    return False


def on_activate_listboxrow(listbox, row):
    """ Activate internal widget when a row has been activated

    Parameters
    ----------
    listbox : Gtk.ListBox
        Object which receive signal
    row : gem.widgets.widgets.ListBoxItem
        Activated row
    """

    widget = row.get_widget()

    if type(widget) == Gtk.ComboBox:
        widget.popup()

    elif type(widget) == Gtk.Entry:
        widget.grab_focus()

    elif type(widget) == Gtk.FileChooserButton:
        widget.activate()

    elif type(widget) in [Gtk.Button, Gtk.FontButton]:
        widget.clicked()

    elif type(widget) == Gtk.SpinButton:
        widget.grab_focus()

    elif type(widget) == Gtk.Switch:
        widget.set_active(not widget.get_active())


def string_from_date(date_object):
    """ Convert a datetime to a pretty string

    Get a pretty string from the interval between NOW() and the wanted date

    Parameters
    ----------
    date_object : datetime.datetime
        Date to compare with NOW()

    Returns
    -------
    str or None
        Convert value
    """

    if date_object is None:
        return None

    days = (date.today() - date_object).days

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


def string_from_time(time_object):
    """ Convert a time to a pretty string

    Get a pretty string from the interval between NOW() and the wanted date

    Parameters
    ----------
    time_object : datetime.datetime
        Date to compare with NOW()

    Returns
    -------
    str or None
        Convert value
    """

    if time_object is None:
        return None

    hours, minutes, seconds = int(), int(), int()

    if type(time_object) is timedelta:
        hours, seconds = divmod(time_object.seconds, 3600)

        if seconds > 0:
            minutes, seconds = divmod(seconds, 60)

        hours += time_object.days * 24

    if hours == 0 and minutes == 0 and seconds == 0:
        return str()

    elif hours == 0 and minutes == 0:
        return ngettext(_("1 second"), _("%d seconds") % seconds, seconds)

    elif hours == 0:
        return ngettext(_("1 minute"), _("%d minutes") % minutes, minutes)

    return ngettext(_("1 hour"), _("%d hours") % hours, hours)


def replace_for_markup(text):
    """ Replace some characters in text for markup compatibility

    Parameters
    ----------
    text : str
        Text to parser

    Returns
    -------
    str
        Replaced text
    """

    characters = {
        '&': "&amp;",
        '<': "&lt;",
        '>': "&gt;",
    }

    for key, value in characters.items():
        text = text.replace(key, value)

    return text


def magic_from_file(filename, mime=False):
    """ Fallback function to retrieve file type when python-magic is missing

    Parameters
    ----------
    filename : str
        File path to read
    mime : bool
        Retrieve the file mimetype, otherwise a readable name (Default: False)

    Returns
    -------
    str
        File type result as human readable name or mimetype
    """

    # Use dereference to follow symlink
    commands = ["file", "--dereference", str(filename)]
    if mime:
        commands.insert(1, "--mime-type")

    output = call_external_application(*commands)
    if output:
        output = output[:-1]

        result = re_findall(fr"^{re_escape(str(filename))}\:\s+(.*)$", output)
        if result:
            return result[0]

    return str()
