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

        GeodeGtkCommon.__init__(self)
        Gtk.Menu.__init__(self)

        separator, item = int(), int()
        for element in args:

            if element is None:
                widget_id = f"{identifier}_separator_{separator}"
                widget = Gtk.SeparatorMenuItem.new()
                separator += 1

            elif isinstance(element, Gtk.MenuItem):
                widget_id, widget = element.identifier, element
                item += 1

                self.inner_widgets.update(element.inner_widgets)

            else:
                widget_id, subtitle, *data = element

                widget_type = Gtk.MenuItem if not data else data[0]

                if widget_type is Gtk.RadioMenuItem:
                    group = None
                    if len(data) > 1:
                        group = self.get_widget(data[1])

                    widget = widget_type.new_with_mnemonic_from_widget(
                        group, subtitle)

                else:
                    widget = widget_type.new_with_mnemonic(subtitle)

            self.inner_widgets[widget_id] = widget
            self.append(self.get_widget(widget_id))


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

        GeodeGtkCommon.__init__(self)
        Gtk.MenuItem.__init__(self)

        self.identifier = identifier

        if args:
            submenu = GeodeGtkMenu(identifier, *args)
            self.inner_widgets.update(submenu.inner_widgets)

        # ------------------------------------
        #   Properties
        # ------------------------------------

        self.set_label(title)
        self.set_use_underline(True)

        if args:
            self.set_submenu(submenu)
