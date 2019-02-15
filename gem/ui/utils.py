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
from gem.ui import *
from gem.ui.data import *

# Regex
from re import findall as re_findall

# ------------------------------------------------------------------------------
#   Misc functions
# ------------------------------------------------------------------------------

def icon_from_data(path, fallback=None, width=24, height=24):
    """ Load an icon from path

    This function search if an icon is available in GEM icons folder and return
    a generate Pixbuf from the icon path. If no icon was found, return an empty
    generate Pixbuf.

    Parameters
    ----------
    path : str
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

    if path is not None and exists(expanduser(path)):

        try:
            return Pixbuf.new_from_file_at_size(expanduser(path), width, height)
        except:
            pass

    # Return an empty icon
    if fallback is None:
        fallback = Pixbuf.new(Colorspace.RGB, True, 8, width, height)
        fallback.fill(0x00000000)

    return fallback


def icon_load(name, size=16, fallback=Icons.Missing):
    """ Load an icon from IconTheme

    This function search an icon in current user icons theme. If founded, return
    a generate Pixbuf from the icon name, else, return a generate Pixbuf from
    the fallback icon name.

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
        Icons.Missing, size, Gtk.IconLookupFlags.FORCE_SVG)


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

    new_pixbuf = Pixbuf.new(Colorspace.RGB, True, 8, width, height)
    new_pixbuf.fill(0x00000000)

    try:
        pixbuf.composite(new_pixbuf, 0, 0, width, height, 0, 0, 1, 1,
            InterpType.NEAREST, opacity)
    except:
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
        row : gem.widgets.widgets.PreferencesItem
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

    commands = ["file", str(filename)]

    if mime:
        commands.insert(1, "--mime-type")

    with Popen(commands, stdout=PIPE, stdin=PIPE,
        stderr=STDOUT, universal_newlines=True) as pipe:

        output, error_output = pipe.communicate()

    result = re_findall(r"^%s\:\s+(.*)$" % str(filename), output[:-1])

    if len(result) > 0:
        return result[0]

    return str()
