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
from gi.repository import Gtk, Pango


# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class GeodeGtkStatusbar(Gtk.Statusbar):

    pixbuf_widgets = ("savestates", "screenshots", "properties")

    def __init__(self):
        """ Constructor
        """

        Gtk.Statusbar.__init__(self)

        self.__inner_grid = self.get_message_area()

        self.__inner_widgets = {
            "console": self.__inner_grid.get_children()[0],
            "emulator": Gtk.Label.new(None),
            "game": Gtk.Label.new(None),
            "properties": Gtk.Image.new(),
            "screenshots": Gtk.Image.new(),
            "savestates": Gtk.Image.new(),
            "progressbar": Gtk.ProgressBar.new(),
        }

        # ------------------------------------
        #   Properties
        # ------------------------------------

        self.__inner_grid.set_spacing(12)
        self.__inner_grid.set_margin_top(0)
        self.__inner_grid.set_margin_end(0)
        self.__inner_grid.set_margin_start(0)
        self.__inner_grid.set_margin_bottom(0)

        for widget in self.__inner_widgets.values():

            if type(widget) is Gtk.Label:
                widget.set_use_markup(True)
                widget.set_halign(Gtk.Align.START)
                widget.set_valign(Gtk.Align.CENTER)

            elif type(widget) is Gtk.Image:
                widget.set_from_icon_name(None, Gtk.IconSize.LARGE_TOOLBAR)

            elif type(widget) is Gtk.ProgressBar:
                widget.set_no_show_all(True)
                widget.set_show_text(True)

        self.__inner_widgets.get("game").set_ellipsize(Pango.EllipsizeMode.END)

        # ------------------------------------
        #   Packing
        # ------------------------------------

        self.__inner_grid.pack_start(
            self.__inner_widgets.get("emulator"), False, False, 0)
        self.__inner_grid.pack_start(
            self.__inner_widgets.get("game"), True, True, 0)

        for name in ("progressbar",) + self.pixbuf_widgets:
            self.__inner_grid.pack_end(
                self.__inner_widgets.get(name), False, False, 0)

    def do_show(self):
        """ Virtual method called when self.show() method is called
        """

        Gtk.Statusbar.do_show(self)

        # Ensure to show all internal widgets
        self.__inner_grid.show_all()

    def set_widget_value(self, widget_key, **kwargs):
        """ Set an internal widget value

        The new value is set with the kwargs structure and based on widget type

        Gtk.Label → markup, text
        Gtk.Image → image, toolip
        Gtk.ProgressBar → index, length

        Parameters
        ----------
        widget_key : str
            Internal widget keys, contains in self.__inner_widgets

        Raises
        ------
        KeyError
            When specified widget do not exists in widget
        """

        if widget_key not in self.__inner_widgets.keys():
            raise KeyError(f"Cannot found {widget_key} in {self} widgets")

        widget = self.__inner_widgets.get(widget_key)

        if type(widget) is Gtk.Label:
            if "markup" in kwargs.keys():
                widget.set_markup(kwargs.get("markup").strip())
            elif "text" in kwargs.keys():
                widget.set_text(kwargs.get("text").strip())

        elif type(widget) is Gtk.Image:
            widget.set_from_pixbuf(kwargs.get("image", None))
            widget.set_tooltip_text(kwargs.get("tooltip", str()).strip())

        elif type(widget) is Gtk.ProgressBar:
            index = kwargs.get("index", int())
            length = kwargs.get("length", int())

            widget.set_text(f"{index}/{length}")
            widget.set_fraction(index / length)

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
            Internal widget keys, contains in self.__inner_widgets
        visibility_status : bool
            The new internal widget visibility status

        Raises
        ------
        KeyError
            When specified widget do not exists in widget
        TypeError
            When specified visibility_status type is not a boolean
        """

        if widget_key not in self.__inner_widgets.keys():
            raise KeyError(f"Cannot found {widget_key} in {self} widgets")

        if not isinstance(visibility_status, bool):
            raise TypeError(
                "The visibility_status parameter must be a boolean")

        widget = self.__inner_widgets.get(widget_key)

        if visibility_status:
            widget.show()
        else:
            widget.hide()
