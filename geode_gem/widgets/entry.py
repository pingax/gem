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

class GeodeGtkEntryCompletion(GeodeGtkCommon, Gtk.EntryCompletion):

    def __init__(self, identifier, model, *args, **kwargs):
        """ Constructor

        Parameters
        ----------
        identifier : str
            String to identify this object in internal container
        model : Gtk.TreeStore
            Completion model
        """

        GeodeGtkCommon.__init__(self, identifier)
        Gtk.EntryCompletion.__init__(self)

        self.list_model = model

        # ------------------------------------
        #   Properties
        # ------------------------------------

        self.set_popup_completion(kwargs.get("popup_completion", True))
        self.set_popup_single_match(kwargs.get("popup_single_match", True))

        if "text_column" in kwargs:
            self.set_text_column(kwargs.get("text_column"))

        self.sort_func = kwargs.get("match_func", None)
        if self.sort_func:
            self.set_match_func(self.sort_func)

        # ------------------------------------
        #   Settings
        # ------------------------------------

        self.set_model(model)


class GeodeGtkSearchEntry(GeodeGtkCommon, Gtk.SearchEntry):

    def __init__(self, identifier, *args, **kwargs):
        """ Constructor

        Parameters
        ----------
        identifier : str
            String to identify this object in internal container
        """

        GeodeGtkCommon.__init__(self, identifier)
        Gtk.SearchEntry.__init__(self)

        # ------------------------------------
        #   Properties
        # ------------------------------------

        self.set_hexpand(kwargs.get("expand", False))
        self.set_placeholder_text(kwargs.get("placeholder", str()))

        # ------------------------------------
        #   Packing
        # ------------------------------------

        for element in args:
            self.append_widget(element)

            if isinstance(element, GeodeGtkEntryCompletion):
                self.set_completion(element)

    def set_completion_data(self, identifier, *args):
        """ Set entry completion data

        Parameters
        ----------
        identifier : str
            String to identify this object in internal container
        """

        if not self.get_completion() or not self.has_widget(identifier):
            return

        widget = self.get_widget(identifier)

        widget.list_model.clear()
        for element in args:
            widget.list_model.append([element])
