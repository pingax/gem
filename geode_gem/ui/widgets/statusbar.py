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
from gi.repository import Gtk, Pango


# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class GeodeGtkStatusbar(GeodeGtkCommon, Gtk.Statusbar):

    pixbuf_widgets = ("savestates", "screenshots", "properties")

    def __init__(self):
        """ Constructor
        """

        Gtk.Statusbar.__init__(self)

        self.inner_grid = self.get_message_area()

        self.inner_widgets = {
            "console": self.inner_grid.get_children()[0],
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

        self.inner_grid.set_spacing(12)
        self.inner_grid.set_margin_top(0)
        self.inner_grid.set_margin_end(0)
        self.inner_grid.set_margin_start(0)
        self.inner_grid.set_margin_bottom(0)

        for widget in self.inner_widgets.values():

            if type(widget) is Gtk.Label:
                widget.set_use_markup(True)
                widget.set_halign(Gtk.Align.START)
                widget.set_valign(Gtk.Align.CENTER)

            elif type(widget) is Gtk.Image:
                widget.set_from_icon_name(None, Gtk.IconSize.LARGE_TOOLBAR)

            elif type(widget) is Gtk.ProgressBar:
                widget.set_no_show_all(True)
                widget.set_show_text(True)

        self.inner_widgets.get("game").set_ellipsize(Pango.EllipsizeMode.END)

        # ------------------------------------
        #   Packing
        # ------------------------------------

        self.inner_grid.pack_start(
            self.inner_widgets.get("emulator"), False, False, 0)
        self.inner_grid.pack_start(
            self.inner_widgets.get("game"), True, True, 0)

        for name in ("progressbar",) + self.pixbuf_widgets:
            self.inner_grid.pack_end(
                self.inner_widgets.get(name), False, False, 0)

    def set_widget_value(self, widget_key, **kwargs):
        """ Set an internal widget value

        The new value is set with the kwargs structure and based on widget type

        Gtk.Label → markup, text
        Gtk.Image → image, toolip
        Gtk.ProgressBar → index, length

        Parameters
        ----------
        widget_key : str
            Internal widget keys, contains in self.inner_widgets

        Raises
        ------
        KeyError
            When specified widget do not exists in widget
        """

        if widget_key not in self.inner_widgets.keys():
            raise KeyError(f"Cannot found {widget_key} in {self} widgets")

        widget = self.inner_widgets.get(widget_key)

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
