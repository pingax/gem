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

class GeodeGtkListBox(GeodeGtkCommon, Gtk.ListBox):

    def __init__(self, identifier, *args, **kwargs):
        """ Constructor

        Parameters
        ----------
        identifier : str
            String to identify this object in internal container
        """

        GeodeGtkCommon.__init__(self, identifier)
        Gtk.ListBox.__init__(self)

        # Properties
        self.set_activate_on_single_click(
            kwargs.get("activate_on_single_click", True))
        self.set_selection_mode(
            kwargs.get("selection_mode", Gtk.SelectionMode.NONE))

        # Packing
        for element in args:
            self.add(element)

    def add(self, child):
        """ Append a new child in container

        Parameters
        ----------
        child : Gtk.Widget
            New widget to add into container
        """

        self.append_widget(child)

        super().add(child)

    def do_row_activated(self, row):
        """ Activate inner widget for specified row

        Parameters
        ----------
        row : Gtk.ListBoxRow
            Activated row widget
        """

        if row.activatable:
            row.activate()


class GeodeGtkListBoxItem(GeodeGtkCommon, Gtk.ListBoxRow):

    # Used to specified if Gtk.ListBox.do_activate works with this item
    activatable = False

    def __init__(self, identifier, label, *args, **kwargs):
        """ Constructor

        Parameters
        ----------
        identifier : str
            String to identify this object in internal container
        """

        GeodeGtkCommon.__init__(self, identifier)
        Gtk.ListBoxRow.__init__(self)

        self.inner_grid = Gtk.Box.new(
            kwargs.get("orientation", Gtk.Orientation.HORIZONTAL),
            kwargs.get("spacing", 12))

        self.inner_widgets = {
            "label_grid": Gtk.Box.new(Gtk.Orientation.VERTICAL, 2),
            "title": Gtk.Label.new(None),
            "description": Gtk.Label.new(None),
        }

        self.set_text(label, kwargs.get("description", None))

        # ------------------------------------
        #   Properties
        # ------------------------------------

        self.set_activatable(True)

        self.inner_grid.set_border_width(kwargs.get("border_width", 6))
        self.inner_grid.set_homogeneous(kwargs.get("homogeneous", False))

        self.get_widget("label_grid").set_homogeneous(False)

        for key in ("title", "description"):
            self.get_widget(key).set_halign(Gtk.Align.START)
            self.get_widget(key).set_justify(Gtk.Justification.FILL)
            self.get_widget(key).set_line_wrap(True)
            self.get_widget(key).set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)

        self.get_widget("description").set_hexpand(True)
        self.get_widget("description").set_use_markup(True)
        self.get_widget("description").set_no_show_all(True)
        self.get_widget("description").set_valign(Gtk.Align.START)
        self.get_widget("description").get_style_context().add_class(
            "dim-label")

        # ------------------------------------
        #   Packing
        # ------------------------------------

        self.get_widget("label_grid").pack_start(
            self.get_widget("title"), True, True, 0)
        self.get_widget("label_grid").pack_start(
            self.get_widget("description"), True, True, 0)

        self.inner_grid.add(self.get_widget("label_grid"))

        self.add(self.inner_grid)

    def set_text(self, title, description=None):
        """ Set labels item content

        Parameters
        ----------
        title : str
            Title label string
        description : str, optionnal
            Description label string
        """

        title_widget = self.get_widget("title")
        title_widget.set_label(title)
        title_widget.set_valign(
            Gtk.Align.END if description is not None else Gtk.Align.CENTER)

        description_widget = self.get_widget("description")
        description_widget.set_visible(description is not None)

        if description is not None:
            description_widget.set_markup(
                f"<span size='small'>{description}</span>")


class GeodeGtkListBoxCheckItem(GeodeGtkListBoxItem):

    activatable = True

    def __init__(self, identifier, label, *args, **kwargs):
        """ See geode_gem.ui.widgets.listbox.GeodeGtkListBoxItem
        """

        GeodeGtkListBoxItem.__init__(self, identifier, label, *args, **kwargs)

        self.__identifier = f"{identifier}_switch"

        self.inner_widgets[self.__identifier] = Gtk.Switch.new()

        # Properties
        self.get_widget(self.__identifier).set_halign(Gtk.Align.END)
        self.get_widget(self.__identifier).set_hexpand(False)
        self.get_widget(self.__identifier).set_valign(Gtk.Align.CENTER)
        self.get_widget(self.__identifier).set_active(
            kwargs.get("activate", True))

        self.inner_grid.pack_end(
            self.get_widget(self.__identifier), False, False, 0)

    def do_activate(self):
        """ See Gtk.Switch.do_activate()
        """

        self.get_widget(self.__identifier).activate()
