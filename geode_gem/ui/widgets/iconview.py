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
from geode_gem.ui.widgets.view import CommonView

# GObject
from gi.repository import Gtk


# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class GeodeGtkIconView(CommonView, Gtk.IconView):

    def __init__(self, identifier, model, **kwargs):
        """ Constructor

        Parameters
        ----------
        identifier : str
            String to identify this object in internal container
        """

        CommonView.__init__(self, identifier, model, **kwargs)
        Gtk.IconView.__init__(self)

        # ------------------------------------
        #   Properties
        # ------------------------------------

        self.set_column_spacing(kwargs.get("column_spacing", 0))
        self.set_has_tooltip(kwargs.get("has_tooltip", False))
        self.set_item_width(kwargs.get("item_width", 32))
        self.set_row_spacing(kwargs.get("row_spacing", 0))
        self.set_selection_mode(
            kwargs.get("selection_mode", Gtk.SelectionMode.SINGLE))
        self.set_spacing(kwargs.get("spacing", 0))

        if "pixbuf_column" in kwargs:
            self.set_pixbuf_column(kwargs.get("pixbuf_column"))
        if "text_column" in kwargs:
            self.set_text_column(kwargs.get("text_column"))

        # ------------------------------------
        #   Settings
        # ------------------------------------

        if self.is_sorterable:
            self.inner_model.set_sort_column_id(
                kwargs.get("sorting_column", self.get_text_column()),
                kwargs.get("sorting_order", Gtk.SortType.ASCENDING))

        elif self.is_filterable and "visible_func" in kwargs:
            self.inner_model.set_visible_func(kwargs.get("visible_func"))

        self.set_model(self.inner_model)

    def get_selected_treeiter(self):
        """ Retrieve current selected item from icon view

        Returns
        -------
        Gtk.TreeIter
            Selected item, None otherwise
        """

        items_list = self.get_selected_items()

        if items_list:
            return self.inner_model.get_iter(items_list[0])

        return None
