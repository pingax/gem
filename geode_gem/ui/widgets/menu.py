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

class CommonMenuItem(GeodeGtkCommon):

    def __init__(self, subclass, identifier, title, *args, **kwargs):
        """ Constructor

        Parameters
        ----------
        subclass : Gtk.MenuItem
            Subclass widget type
        identifier : str
            String to identify this object in internal container
        title : str
            Menu item label
        """

        GeodeGtkCommon.__init__(self, identifier)
        subclass.__init__(self)

        # Properties
        self.set_label(title)
        self.set_tooltip_text(kwargs.get("tooltip", str()))
        self.set_use_underline(kwargs.get("use_underline", True))

        if args:
            submenu = GeodeGtkMenu(f"{self.identifier}_menu", *args)

            self.append_widget(submenu)
            self.set_submenu(submenu)


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

            # Generate a dynamic name for Gtk.SeparatorMenuItem
            if element is None:
                widget_id = f"{identifier}_separator_{index}"
                element = Gtk.SeparatorMenuItem.new()

            elif isinstance(element, Gtk.RadioMenuItem):
                if element.group is not None:
                    element.join_group(self.get_widget(element.group))

            self.append_widget(element)
            self.append(element)


class GeodeGtkMenuItem(CommonMenuItem, Gtk.MenuItem):

    def __init__(self, *args, **kwargs):
        """ See geode_gem.ui.widgets.menu.CommonMenuItem
        """

        CommonMenuItem.__init__(self, Gtk.MenuItem, *args, **kwargs)
        Gtk.MenuItem.__init__(self)


class GeodeGtkCheckMenuItem(CommonMenuItem, Gtk.CheckMenuItem):

    def __init__(self, *args, **kwargs):
        """ See geode_gem.ui.widgets.menu.CommonMenuItem
        """

        CommonMenuItem.__init__(self, Gtk.CheckMenuItem, *args, **kwargs)
        Gtk.CheckMenuItem.__init__(self)


class GeodeGtkRadioMenuItem(CommonMenuItem, Gtk.RadioMenuItem):

    def __init__(self, *args, **kwargs):
        """ See geode_gem.ui.widgets.menu.CommonMenuItem
        """

        CommonMenuItem.__init__(self, Gtk.RadioMenuItem, *args, **kwargs)
        Gtk.RadioMenuItem.__init__(self)

        self.group = kwargs.get("group", None)
