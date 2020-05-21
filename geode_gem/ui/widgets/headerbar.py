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

class GeodeGtkHeaderBar(GeodeGtkCommon, Gtk.HeaderBar):

    def __init__(self, identifier, title, *args, subtitle=None):
        """ Constructor

        Parameters
        ----------
        identifier : str
            String to identify this object in internal container
        """

        GeodeGtkCommon.__init__(self)
        Gtk.HeaderBar.__init__(self)

        # ------------------------------------
        #   Properties
        # ------------------------------------

        self.set_title(title)
        if subtitle is not None:
            self.set_subtitle(subtitle)

        # ------------------------------------
        #   Packing
        # ------------------------------------

        for widget in args:
            self.inner_widgets[widget.identifier] = widget
            self.inner_widgets.update(widget.inner_widgets)

            self.pack_start(widget)
