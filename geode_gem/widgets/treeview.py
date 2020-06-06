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
from geode_gem.widgets.view import CommonView

# GObject
from gi.repository import Gtk


# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class GeodeGtkTreeView(CommonView, Gtk.TreeView):

    def __init__(self, identifier, model, *args, **kwargs):
        """ Constructor

        Parameters
        ----------
        identifier : str
            String to identify this object in internal container
        """

        CommonView.__init__(self, identifier, model, *args, **kwargs)
        Gtk.TreeView.__init__(self)

        # ------------------------------------
        #   Properties
        # ------------------------------------

        self.set_enable_search(kwargs.get("enable_search", True))
        self.set_has_tooltip(kwargs.get("has_tooltip", False))
        self.set_headers_clickable(kwargs.get("headers_clickable", True))
        self.set_headers_visible(kwargs.get("headers_visible", True))
        self.set_search_column(kwargs.get("search_column", -1))
        self.set_show_expanders(kwargs.get("show_expanders", True))

        # ------------------------------------
        #   Packing
        # ------------------------------------

        for element in args:
            if self.is_sorterable and element.sort_column_id is not None:
                element.set_sort_column_id(element.sort_column_id)

                self.sorted_games_list.set_sort_func(
                    element.sort_column_id, self.sort_func, element)

            cells = element.get_cells()
            if cells and element.cell_data_func is not None:
                element.set_cell_data_func(cells[0], element.cell_data_func)

            self.append_widget(element)
            self.append_column(element)

        # ------------------------------------
        #   Settings
        # ------------------------------------

        self.set_model(self.inner_model)

    def set_columns_order(self, *columns):
        """ Set columns order based on column widget keys

        Parameters
        ----------
        columns : list
            Columns widget key list
        """

        for index, key in enumerate(columns):
            if not self.has_widget(key):
                continue

            column_widget = self.get_widget(key)
            self.remove_column(column_widget)
            self.insert_column(column_widget, index)


class GeodeGtkTreeViewColumn(GeodeGtkCommon, Gtk.TreeViewColumn):

    def __init__(self, identifier, title, *args, **kwargs):
        """ Constructor

        Parameters
        ----------
        identifier : str
            String to identify this object in internal container
        """

        GeodeGtkCommon.__init__(self, identifier)
        Gtk.TreeViewColumn.__init__(self)

        self.sort_column_id = kwargs.get("sort_column_id", None)

        self.cell_data_func = kwargs.get("cell_data_func", None)

        # ------------------------------------
        #   Properties
        # ------------------------------------

        if title is not None:
            self.set_title(title)

        self.set_alignment(kwargs.get("alignment", 0.5))
        self.set_expand(kwargs.get("expand", False))
        self.set_fixed_width(kwargs.get("fixed_width", -1))
        self.set_max_width(kwargs.get("max_width", -1))
        self.set_min_width(kwargs.get("min_width", -1))
        self.set_resizable(kwargs.get("resizable", True))
        self.set_reorderable(kwargs.get("reorderable", True))
        self.set_sizing(
            kwargs.get("sizing", Gtk.TreeViewColumnSizing.GROW_ONLY))

        # ------------------------------------
        #   Packing
        # ------------------------------------

        for index, element in enumerate(args):
            self.pack_start(element, element.is_expandable)

            if element.column_index is not None:
                self.add_attribute(element, element.mode, element.column_index)

            self.append_widget(element)
