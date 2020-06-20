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

class GeodeGtkLabel(GeodeGtkCommon, Gtk.Label):

    def __init__(self, identifier, **kwargs):
        """ Constructor

        Parameters
        ----------
        identifier : str
            String to identify this object in internal container
        """

        GeodeGtkCommon.__init__(self)
        Gtk.Label.__init__(self)

        # ------------------------------------
        #   Properties
        # ------------------------------------

        if "text" in kwargs:
            self.set_text(kwargs.get("text"))

        elif "text_with_mnemonic" in kwargs:
            self.set_text_with_mnemonic(kwargs.get("text_with_mnemonic"))

        self.set_use_markup(kwargs.get("use_markup", True))
        self.set_use_underline(kwargs.get("use_underline", True))
