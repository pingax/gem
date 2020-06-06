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
from geode_gem.widgets.common import GeodeGtkCommon

# GObject
from gi.repository import Gtk


# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class CommonView(GeodeGtkCommon):

    def __init__(self, identifier, model, *args, **kwargs):
        """ Constructor

        Parameters
        ----------
        identifier : str
            String to identify this object in internal container
        model : Gtk.TreeStore
            View model
        """

        GeodeGtkCommon.__init__(self, identifier)

        self.list_model = model
        self.filtered_model = model.filter_new()
        self.sorted_model = Gtk.TreeModelSort(model=self.filtered_model)

        self.is_sorterable = kwargs.get("sorterable", False)
        self.is_filterable = kwargs.get("filterable", False)

        # ------------------------------------
        #   Models
        # ------------------------------------

        self.inner_model = self.list_model

        if self.is_sorterable:
            self.inner_model = self.sorted_model

        elif self.is_filterable:
            self.inner_model = self.filtered_model

        # ------------------------------------
        #   Settings
        # ------------------------------------

        if self.is_sorterable:
            self.inner_model.set_sort_column_id(
                kwargs.get("sorting_column", self.get_text_column()),
                kwargs.get("sorting_order", Gtk.SortType.ASCENDING))

        elif self.is_filterable and "visible_func" in kwargs:
            self.inner_model.set_visible_func(kwargs.get("visible_func"))

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

        if treeiter is not None:
            return self.inner_model.get_path(treeiter)

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
