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

    def __init__(self):
        """ Constructor
        """

        self.inner_grid = None
        self.inner_widgets = dict()

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

    def has_widget(self, widget_key):
        """ Check if a specific widget exists in internal container

        Parameters
        ----------
        widget_key : str
            Internal widget keys, contains in self.inner_widgets

        Returns
        -------
        bool
            True if widget exists, False otherwise
        """

        return widget_key in self.inner_widgets.keys()

    def get_widget(self, widget_key):
        """ Retrieve a specific widget from internal container

        Parameters
        ----------
        widget_key : str
            Internal widget keys, contains in self.inner_widgets

        Returns
        -------
        Gtk.Widget or None
            Widget from internal container

        Raises
        ------
        KeyError
            When specified widget do not exists in widget
        """

        if not self.has_widget(widget_key):
            raise KeyError(f"Cannot found {widget_key} in {self} widgets")

        return self.inner_widgets.get(widget_key, None)

    def get_active(self, widget=None):
        """ Returns the widget active entry

        Parameters
        ----------
        widget : str, optionnal
            Internal widget keys, contains in self.inner_widgets

        Returns
        -------
        Gtk.Widget
            The activated widget from internal container
        """

        if widget is None:
            return super().get_active()

        elif self.has_widget(widget):
            return self.get_widget(widget).get_active()

        return None

    def set_active(self, value, widget=None):
        """ Set the active value for a specific widget

        Parameters
        ----------
        value : bool or int
            The new activate value for specified widget
        widget : str, optionnal
            Internal widget keys, contains in self.inner_widgets
        """

        if widget is None:
            super().set_active(value)

        elif self.has_widget(widget):
            self.get_widget(widget).set_active(value)

    def get_sensitive(self, widget=None):
        """ Returns the widget sensitivity

        Parameters
        ----------
        widget : str, optionnal
            Internal widget keys, contains in self.inner_widgets

        Returns
        -------
        bool
            True if the widget is sensitive, False otherwise
        """

        if widget is None:
            return super().get_sensitive()

        elif self.has_widget(widget):
            return self.get_widget(widget).get_sensitive()

        return True

    def set_sensitive(self, sensitive, widget=None):
        """ Set the widget sensitivity

        Parameters
        ----------
        sensitive : bool
            The new internal widget sensitive status
        widget : str, optionnal
            Internal widget keys, contains in self.inner_widgets
        """

        if widget is None:
            super().set_sensitive(sensitive)

        elif self.has_widget(widget):
            self.get_widget(widget).set_sensitive(sensitive)

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
        TypeError
            When specified visibility_status type is not a boolean
        """

        if not isinstance(visibility_status, bool):
            raise TypeError(
                "The visibility_status parameter must be a boolean")

        widget = self.get_widget(widget_key)

        if visibility_status:
            widget.show()
        else:
            widget.hide()
