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

# GObject
from gi.repository import Gtk


# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class GeodeGtkCommon():

    inner_grid = None
    inner_widgets = dict()

    def do_show(self):
        """ Virtual method called when self.show() method is called
        """

        if hasattr(self, "do_show"):
            super().do_show(self)

        # Ensure to show all internal widgets
        if isinstance(self.inner_grid, Gtk.Container):
            self.inner_grid.show_all()

    def hide_widget(self, widget_key):
        """ See self.set_widget_visibility method
        """

        self.set_widget_visibility(widget_key, False)

    def show_widget(self, widget_key):
        """ See self.set_widget_visibility method
        """

        self.set_widget_visibility(widget_key, True)

    def set_widget_visibility(self, widget_key, visibility_status):
        """ Define an internal widget visibility status

        Parameters
        ----------
        widget_key : str
            Internal widget keys, contains in self.inner_widgets
        visibility_status : bool
            The new internal widget visibility status

        Raises
        ------
        KeyError
            When specified widget do not exists in widget
        TypeError
            When specified visibility_status type is not a boolean
        """

        if widget_key not in self.inner_widgets.keys():
            raise KeyError(f"Cannot found {widget_key} in {self} widgets")

        if not isinstance(visibility_status, bool):
            raise TypeError(
                "The visibility_status parameter must be a boolean")

        widget = self.inner_widgets.get(widget_key)

        if visibility_status:
            widget.show()
        else:
            widget.hide()
