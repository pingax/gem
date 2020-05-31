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

class GeodeGtkToolbar(GeodeGtkCommon, Gtk.Box):

    def __init__(self, identifier, *args, **kwargs):
        """ Constructor

        Parameters
        ----------
        identifier : str
            String to identify this object in internal container
        """

        GeodeGtkCommon.__init__(self, identifier)
        Gtk.Box.__init__(self)

        # ------------------------------------
        #   Properties
        # ------------------------------------

        self.set_spacing(kwargs.get("spacing", 0))
        self.set_border_width(kwargs.get("border_width", 0))

        self.set_orientation(kwargs.get("orientation",
                                        Gtk.Orientation.HORIZONTAL))

        # ------------------------------------
        #   Packing
        # ------------------------------------

        for index, widget in enumerate(args):
            expand = False

            if widget is None:
                widget = Gtk.SeparatorToolItem.new()
                widget.set_expand(True)
                widget.set_draw(False)

                setattr(self, "identifier", f"{identifier}_separator_{index}")

                expand = True

            elif len(args) == 1:
                expand = True

            self.append_widget(widget)
            self.pack_start(widget, expand, expand, 0)


class GeodeGtkToolbarBox(GeodeGtkCommon, Gtk.Box):

    def __init__(self, identifier, *args, **kwargs):
        """ Constructor

        Parameters
        ----------
        identifier : str
            String to identify this object in internal container
        """

        GeodeGtkCommon.__init__(self, identifier)
        Gtk.Box.__init__(self)

        # ------------------------------------
        #   Properties
        # ------------------------------------

        self.set_spacing(kwargs.get("spacing", 0))
        self.set_border_width(kwargs.get("border_width", 0))

        self.set_orientation(kwargs.get("orientation",
                                        Gtk.Orientation.HORIZONTAL))

        if kwargs.get("merge", False):
            Gtk.StyleContext.add_class(self.get_style_context(), "linked")

        # ------------------------------------
        #   Packing
        # ------------------------------------

        method = "get_hexpand"
        if self.get_orientation() == Gtk.Orientation.VERTICAL:
            method = "get_vexpand"

        for widget in args:
            expand = False
            if hasattr(widget, method):
                expand = getattr(widget, method)()

            self.append_widget(widget)
            self.pack_start(widget, expand, expand, 0)


class GeodeGtkToolbarSwitch(GeodeGtkToolbarBox):

    def __init__(self, identifier, *args, **kwargs):
        """ Constructor

        Parameters
        ----------
        identifier : str
            String to identify this object in internal container
        """

        GeodeGtkToolbarBox.__init__(self, identifier, *args, **kwargs)
