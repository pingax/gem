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

class GeodeGtkImage(GeodeGtkCommon, Gtk.Image):

    set_modes = (
        "from_animation",
        "from_file",
        "from_gicon",
        "from_icon_name",
        "from_icon_set",
        "from_pixbuf",
        "from_resource",
        "from_stock",
        "from_surface",
        "pixel_size",
    )

    def __init__(self, identifier, **kwargs):
        """ Constructor

        Parameters
        ----------
        identifier : str
            String to identify this object in internal container
        """

        GeodeGtkCommon.__init__(self)
        Gtk.Image.__init__(self)

        # ------------------------------------
        #   Properties
        # ------------------------------------

        for option, values in kwargs.items():
            if option not in self.set_modes:
                continue

            getattr(self, f"set_{option}")(*values)
