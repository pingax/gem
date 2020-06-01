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

class GeodeGtkIconView(GeodeGtkCommon, Gtk.IconView):

    def __init__(self, identifier, model, **kwargs):
        """ Constructor

        Parameters
        ----------
        identifier : str
            String to identify this object in internal container
        """

        GeodeGtkCommon.__init__(self, identifier)
        Gtk.IconView.__init__(self)

        self.list_model = model
        self.filtered_model = model.filter_new()
        self.sorted_model = Gtk.TreeModelSort(model=self.filtered_model)

        self.is_sorterable = kwargs.get("sorterable", False)
        self.is_filterable = kwargs.get("filterable", False)

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

        self.inner_model = self.list_model

        if self.is_sorterable:
            self.inner_model = self.sorted_model

            self.inner_model.set_sort_column_id(
                kwargs.get("sorting_column", self.get_text_column()),
                kwargs.get("sorting_order", Gtk.SortType.ASCENDING))

        elif self.is_filterable:
            self.inner_model = self.filtered_model

            if "visible_func" in kwargs:
                self.inner_model.set_visible_func(kwargs.get("visible_func"))

        self.set_model(self.inner_model)

    def append(self, data=None):
        """ Append a new item in main model

        Parameters
        ----------
        data : list, optional
            Data object to append

        Returns
        -------
        Gtk.TreeIter
            Appended row
        """

        return self.list_model.append(row=data)

    def remove(self, treeiter):
        """ Remove a specific iter from main model

        Parameters
        ----------
        treeiter : Gtk.TreeIter
            Iter object to remove
        """

        self.list_model.remove(treeiter)

    def clear(self):
        """ Clear the main model
        """

        self.list_model.clear()

    def convert_child_iter_to_iter(self, treeiter):
        """ Convert a child iter to main model iter

        Parameters
        ----------
        treeiter : Gtk.TreeIter
            Iter object to convert

        Returns
        -------
        Gtk.TreeIter
            Converted iter, None otherwise
        """

        if self.is_filterable:
            status, treeiter = \
                self.filtered_model.convert_child_iter_to_iter(treeiter)

            if not status:
                return None

        if self.is_sorterable:
            status, treeiter = \
                self.sorted_model.convert_child_iter_to_iter(treeiter)

            if not status:
                return None

        return treeiter

    def get_path_from_treeiter(self, treeiter):
        """ Retrieve path from a specific iter from main model

        Parameters
        ----------
        treeiter : Gtk.TreeIter
            Iter object to retrieve

        Returns
        -------
        Gtk.TreePath
            Retrieved iter path, None otherwise
        """

        treeiter = self.convert_child_iter_to_iter(treeiter)

        if self.list_model.iter_is_valid(treeiter):
            return self.list_model.get_path(treeiter)

        return None

    def get_selected_item(self):
        """ Retrieve current selected item from icon view

        Returns
        -------
        Gtk.TreeIter
            Selected item, None otherwise
        """

        items_list = self.get_selected_items()

        if items_list:
            return self.list_model.get_iter(items_list[0])

        return None

    def set_value(self, path, column, value):
        """ Set new value for a specific entry from main model

        Parameters
        ----------
        path : Gtk.TreePath
            Entry path from main model
        column : int
            Column index to update
        value : object
            New value to set
        """

        if path in self.list_model and column in self.list_model[path]:
            self.list_model[path][column] = value

    def refilter(self):
        """ Refilter the filtered model if available

        Raises
        ------
        ValueError
            When the filtered model is not available
        """

        if not self.is_filterable:
            raise ValueError(f"{type(self)} is not a filterable widget")

        self.filtered_model.refilter()
