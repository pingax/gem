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

# Geode
from geode_gem.ui.widgets.common import GeodeGtkCommon

# GObject
from gi.repository import Gtk


# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class GeodeGtkMenu(GeodeGtkCommon, Gtk.Menu):

    def __init__(self, identifier, *args):
        """ Constructor

        Parameters
        ----------
        identifier : str
            String to identify this object in internal container
        """

        GeodeGtkCommon.__init__(self, identifier)
        Gtk.Menu.__init__(self)

        for index, element in enumerate(args):
            widget_id, widget = self.__parse_menu_entry(element)

            # Generate a dynamic name for Gtk.SeparatorMenuItem
            if widget_id == "separator":
                widget_id = f"{identifier}_{widget_id}_{index}"

            # Ensure native Gtk.Widget to have self.identifier
            if not hasattr(widget, "identifier"):
                setattr(widget, "identifier", widget_id)

            self.append_widget(widget)
            self.append(self.get_widget(widget_id))

    def __parse_menu_entry(self, entry):
        """ Retrieve identifier and widget from specifiec entry

        Parameters
        ----------
        entry : Gtk.Widget or None or tuple()
            Entry element to parse

        Returns
        -------
        tuple
            Parsed identifier and widget as tuple
        """

        if entry is None:
            return ("separator", Gtk.SeparatorMenuItem.new())

        if isinstance(entry, Gtk.MenuItem):
            return (entry.identifier, entry)

        identifier, subtitle, *data = entry

        # Retrieve specified widget from data or take a native Gtk.MenuItem
        widget = Gtk.MenuItem if not data else data[0]

        # Radio menu item must have dedicated group to work together
        if widget is Gtk.RadioMenuItem:
            group = self.get_widget(data[1]) if len(data) > 1 else None

            return (identifier,
                    widget.new_with_mnemonic_from_widget(group, subtitle))

        return (identifier, widget.new_with_mnemonic(subtitle))


class GeodeGtkMenuItem(GeodeGtkCommon, Gtk.MenuItem):

    def __init__(self, identifier, title, *args):
        """ Constructor

        Parameters
        ----------
        identifier : str
            String to identify this object in internal container
        title : str
            Menuitem title label
        """

        GeodeGtkCommon.__init__(self, identifier)
        Gtk.MenuItem.__init__(self)

        # Properties
        self.set_label(title)
        self.set_use_underline(True)

        if args:
            submenu = GeodeGtkMenu(f"{self.identifier}_menu", *args)

            self.append_widget(submenu)
            self.set_submenu(submenu)
