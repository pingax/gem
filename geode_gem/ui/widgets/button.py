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
from geode_gem.ui.widgets.menu import GeodeGtkMenu

# GObject
from gi.repository import Gtk


# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class GeodeGtkMenuButton(GeodeGtkCommon, Gtk.MenuButton):

    def __init__(self,
                 identifier, title, *args, icon_name=None, use_popover=False):
        """ Constructor

        Parameters
        ----------
        identifier : str
            String to identify this object in internal container
        """

        GeodeGtkCommon.__init__(self)
        Gtk.MenuButton.__init__(self)

        self.identifier = identifier

        # ------------------------------------
        #   Properties
        # ------------------------------------

        self.set_use_popover(use_popover)

        if args:
            submenu = GeodeGtkMenu(identifier, *args)

            self.inner_widgets.update(submenu.inner_widgets)

        if icon_name is None:
            self.set_label(title)

        else:
            self.set_tooltip_text(title)

            self.inner_widgets[f"{identifier}_image"] = \
                Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.BUTTON)

        # ------------------------------------
        #   Packing
        # ------------------------------------

        if args:
            self.set_popup(submenu)

            submenu.show_all()

        if icon_name:
            self.add(self.get_widget(f"{identifier}_image"))
