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
from gi.repository import Gtk, Pango


# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class GeodeGtkStatusbar(GeodeGtkCommon, Gtk.Statusbar):

    pixbuf_widgets = list()

    def __init__(self, identifier, *args, **kwargs):
        """ Constructor
        """

        GeodeGtkCommon.__init__(self, identifier)
        Gtk.Statusbar.__init__(self)

        self.inner_grid = self.get_message_area()

        # Ensure to remove the default label widget from legacy Gtk.Statusbar
        label = self.inner_grid.get_children()[0]
        self.inner_grid.remove(label)
        label.destroy()

        for index, widget in enumerate(args):
            expand = False

            if widget is None:
                widget = Gtk.SeparatorToolItem.new()
                widget.set_expand(True)
                widget.set_draw(False)

                setattr(
                    widget, "identifier", f"{identifier}_separator_{index}")

                expand = True

            elif isinstance(widget, Gtk.Label):
                widget.set_halign(Gtk.Align.START)

            elif isinstance(widget, Gtk.Image):
                self.pixbuf_widgets.append(widget.identifier)

            self.append_widget(widget)
            self.inner_grid.pack_start(widget, expand, expand, 0)

        # ------------------------------------
        #   Properties
        # ------------------------------------

        self.inner_grid.set_spacing(kwargs.get("spacing", 12))
        self.inner_grid.set_margin_top(kwargs.get("margin", 0))
        self.inner_grid.set_margin_end(kwargs.get("margin", 0))
        self.inner_grid.set_margin_start(kwargs.get("margin", 0))
        self.inner_grid.set_margin_bottom(kwargs.get("margin", 0))

    def set_widget_value(self, widget_key, **kwargs):
        """ Set an internal widget value

        The new value is set with the kwargs structure and based on widget type

        Gtk.Label → markup, text
        Gtk.Image → image, toolip
        Gtk.ProgressBar → index, length

        Parameters
        ----------
        widget_key : str
            Internal widget keys, contains in self.__dict__
        """

        widget = self.get_widget(widget_key)

        if isinstance(widget, Gtk.Label):
            text = kwargs.get("text", str()).strip()

            if widget.get_use_markup():
                widget.set_markup(text)
            else:
                widget.set_text(text)

        elif isinstance(widget, Gtk.Image):
            widget.set_tooltip_text(kwargs.get("tooltip", str()).strip())

            value = kwargs.get("image", None)
            if isinstance(value, tuple) and value:
                widget.set_from_icon_name(*value)
                value = value[0]
            else:
                widget.set_from_pixbuf(value)

            if value is None:
                widget.hide()
            else:
                widget.show()

        elif type(widget) is Gtk.ProgressBar:
            index = kwargs.get("index", int())
            length = kwargs.get("length", int())

            if length > 0:
                widget.set_text(f"{index}/{length}")
                widget.set_fraction(index / length)
