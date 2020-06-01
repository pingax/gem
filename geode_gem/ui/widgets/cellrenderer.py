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
from gi.repository import Gtk, Pango


# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class CommonCellRenderer(GeodeGtkCommon):

    # Used to specified the Gtk.CellRenderer mode
    mode = None

    def __init__(self, subclass, identifier, **kwargs):
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

        # Store expandable status for current cell
        self.is_expandable = kwargs.get("expand", False)
        # Store column index where the cell is stored
        self.column_index = kwargs.get("index", None)

        # Properties
        self.set_alignment(*kwargs.get("alignment", (.5, .5)))
        self.set_padding(*kwargs.get("padding", (0, 0)))


class GeodeGtkCellRendererPixbuf(CommonCellRenderer, Gtk.CellRendererPixbuf):

    mode = "pixbuf"

    def __init__(self, identifier, **kwargs):
        """ See geode_gem.ui.widgets.treeview.CommonCellRenderer
        """

        CommonCellRenderer.__init__(
            self, Gtk.CellRendererPixbuf, identifier, **kwargs)
        Gtk.CellRendererPixbuf.__init__(self)


class GeodeGtkCellRendererText(CommonCellRenderer, Gtk.CellRendererText):

    mode = "text"

    def __init__(self, identifier, **kwargs):
        """ See geode_gem.ui.widgets.treeview.CommonCellRenderer
        """

        CommonCellRenderer.__init__(
            self, Gtk.CellRendererText, identifier, **kwargs)
        Gtk.CellRendererText.__init__(self)

        self.set_property(
            "editable", kwargs.get("editable", False))
        self.set_property(
            "ellipsize", kwargs.get("ellipsize", Pango.EllipsizeMode.END))
