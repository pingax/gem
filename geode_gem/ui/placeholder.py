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
from geode_gem.ui.data import Icons
from geode_gem.widgets.common import GeodeGtkCommon
from geode_gem.widgets import GeodeGtk

# GObject
from gi.repository import Gtk

# Translation
from gettext import gettext as _


# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class GeodeGEMPlaceholder(GeodeGtkCommon, Gtk.ScrolledWindow):

    def __init__(self, interface):
        """ Constructor

        Parameters
        ----------
        interface : geode_gem.ui.interface.MainWindow
            Main interface instance
        """

        GeodeGtkCommon.__init__(self, "placeholder")
        Gtk.ScrolledWindow.__init__(self)

        self.__interface = interface

        self.inner_grid = Gtk.Box.new(Gtk.Orientation.VERTICAL, 12)
        self.inner_grid.set_border_width(18)

        # ------------------------------------
        #   Widgets
        # ------------------------------------

        self.image = GeodeGtk.Image(
            "image",
            from_icon_name=(Icons.Symbolic.GAMING, Gtk.IconSize.DIALOG))

        self.label = GeodeGtk.Label(
            "label",
            text=_("Start to play by drag & drop some files into interface"))

        # Properties
        self.image.set_pixel_size(256)
        self.image.set_halign(Gtk.Align.CENTER)
        self.image.set_valign(Gtk.Align.END)
        self.image.set_style("dim-label")

        self.label.set_halign(Gtk.Align.CENTER)
        self.label.set_valign(Gtk.Align.START)

        # ------------------------------------
        #   Packing
        # ------------------------------------

        self.inner_grid.pack_start(self.image, True, True, 0)
        self.append_widget(self.image)

        self.inner_grid.pack_start(self.label, True, True, 0)
        self.append_widget(self.label)

        self.add(self.inner_grid)
