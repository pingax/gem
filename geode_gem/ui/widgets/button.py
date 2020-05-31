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
from geode_gem.ui.widgets.menu import GeodeGtkMenu

# GObject
from gi.repository import Gtk


# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class CommonButton(GeodeGtkCommon):

    def __init__(self, subclass, identifier, label, *args, **kwargs):
        """ Constructor

        Parameters
        ----------
        subclass : Gtk.Button
            Subclass widget type
        identifier : str
            String to identify this object in internal container
        label : str
            Button label
        """

        GeodeGtkCommon.__init__(self, identifier)
        subclass.__init__(self)

        # Inner widgets
        self.image = None
        # Button image icon name
        self.icon_name = kwargs.get("icon_name", None)
        # Button class style
        self.current_style = None

        # ------------------------------------
        #   Properties
        # ------------------------------------

        if "tooltip" in kwargs:
            self.set_tooltip_text(kwargs.get("tooltip"))

        if self.icon_name is None:
            self.set_label(label)

        else:
            self.set_tooltip_text(label)

            self.image = Gtk.Image.new_from_icon_name(self.icon_name,
                                                      Gtk.IconSize.BUTTON)
            setattr(self.image, "identifier", f"{identifier}_image")

        # ------------------------------------
        #   Packing
        # ------------------------------------

        if self.image is not None:
            self.append_widget(self.image)
            self.add(self.image)


    def set_style(self, style=None):
        """ Define a specific class for current button

        Parameters
        ----------
        style : str, optional
            Class style name
        """

        if self.current_style is not None and not self.current_style == style:
            self.get_style_context().remove_class(self.current_style)

        if style is not None and not self.current_style == style:
            self.get_style_context().add_class(style)

        self.current_style = style


class GeodeGtkButton(CommonButton, Gtk.Button):

    def __init__(self, identifier, label, *args, **kwargs):
        """ Constructor

        Parameters
        ----------
        identifier : str
            String to identify this object in internal container
        label : str
            Menu button label
        """

        CommonButton.__init__(
            self, Gtk.Button, identifier, label, *args, **kwargs)
        Gtk.Button.__init__(self)


class GeodeGtkMenuButton(CommonButton, Gtk.MenuButton):

    def __init__(self, identifier, label, *args, **kwargs):
        """ Constructor

        Parameters
        ----------
        identifier : str
            String to identify this object in internal container
        label : str
            Menu button label
        """

        CommonButton.__init__(
            self, Gtk.MenuButton, identifier, label, *args, **kwargs)
        Gtk.MenuButton.__init__(self)

        # Inner widgets
        self.submenu = None

        # ------------------------------------
        #   Properties
        # ------------------------------------

        self.set_use_popover(kwargs.get("use_popover", False))

        if args:
            self.submenu = GeodeGtkMenu(identifier, *args)
            self.append_widget(self.submenu)

        # ------------------------------------
        #   Packing
        # ------------------------------------

        if self.submenu is not None:
            self.set_popup(self.submenu)
            self.submenu.show_all()


class GeodeGtkToggleButton(CommonButton, Gtk.ToggleButton):

    def __init__(self, identifier, label, *args, **kwargs):
        """ Constructor

        Parameters
        ----------
        identifier : str
            String to identify this object in internal container
        label : str
            Menu button label
        """

        CommonButton.__init__(
            self, Gtk.ToggleButton, identifier, label, *args, **kwargs)
        Gtk.ToggleButton.__init__(self)
