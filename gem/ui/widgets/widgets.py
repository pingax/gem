# ------------------------------------------------------------------------------
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License.
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

# GEM
from gem.engine.api import Console
from gem.engine.api import Emulator
from gem.engine.utils import *

from gem.ui import *
from gem.ui.utils import *

# Translation
from gettext import gettext as _

# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class ListBoxPopover(Gtk.Popover):

    def __init__(self):
        """ Constructor
        """

        Gtk.Popover.__init__(self)

        # ------------------------------------
        #   Prepare interface
        # ------------------------------------

        # Init widgets
        self.__init_widgets()

        # Init packing
        self.__init_packing()

        # Start interface
        self.__start_interface()


    def __init_widgets(self):
        """ Initialize interface widgets
        """

        # ------------------------------------
        #   Grid
        # ------------------------------------

        self.grid_popover = Gtk.Box()

        # Properties
        self.grid_popover.set_orientation(Gtk.Orientation.VERTICAL)
        self.grid_popover.set_border_width(12)
        self.grid_popover.set_spacing(12)

        # ------------------------------------
        #   Content
        # ------------------------------------

        self.entry_selector = Gtk.SearchEntry()

        self.frame_selector = Gtk.Frame()
        self.scroll_selector = Gtk.ScrolledWindow()
        self.listbox_selector = Gtk.ListBox()

        # Properties
        self.entry_selector.set_placeholder_text("%s…" % _("Filter"))

        self.scroll_selector.set_size_request(-1, 256)
        self.scroll_selector.set_policy(
            Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)


    def __init_packing(self):
        """ Initialize widgets packing in main window
        """

        self.add(self.grid_popover)

        self.frame_selector.add(self.scroll_selector)
        self.scroll_selector.add(self.listbox_selector)

        self.grid_popover.pack_start(
            self.frame_selector, True, True, 0)
        self.grid_popover.pack_start(
            self.entry_selector, False, False, 0)


    def __start_interface(self):
        """ Load data and start interface
        """

        self.grid_popover.show_all()


    def append_row(self, row):
        """ Append a new row into listbox

        Parameters
        ----------
        row : gem.gtk.widgets.ListBoxSelectorItem
            Row object
        """

        self.listbox_selector.add(row)


class ListBoxSelector(Gtk.MenuButton):

    def __init__(self, size=256, use_static_size=False):
        """ Constructor

        Parameters
        ----------
        size : int, optional
            Widget size request in pixels (Default: 256)
        use_static_size : bool, optional
            Set widget static size mode (Default: False)
        """

        Gtk.MenuButton.__init__(self)

        # ------------------------------------
        #   Initialize variables
        # ------------------------------------

        self.size = size

        self.use_static_size = use_static_size

        # ------------------------------------
        #   Prepare interface
        # ------------------------------------

        # Init widgets
        self.__init_widgets()

        # Init packing
        self.__init_packing()

        # Start interface
        self.__start_interface()


    def __init_widgets(self):
        """ Initialize interface widgets
        """

        if self.use_static_size:
            self.set_size_request(self.size, -1)

        self.set_use_popover(True)

        # ------------------------------------
        #   Grid
        # ------------------------------------

        self.grid_selector = Gtk.Box()

        # Properties
        self.grid_selector.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.grid_selector.set_spacing(12)

        # ------------------------------------
        #   Selector
        # ------------------------------------

        self.label_selector_name = Gtk.Label()

        self.image_selector_icon = Gtk.Image()
        self.image_selector_status = Gtk.Image()

        # Properties
        self.label_selector_name.set_halign(Gtk.Align.START)
        self.image_selector_icon.set_halign(Gtk.Align.CENTER)
        self.image_selector_icon.set_valign(Gtk.Align.CENTER)
        self.image_selector_status.set_halign(Gtk.Align.CENTER)
        self.image_selector_status.set_valign(Gtk.Align.CENTER)

        if self.use_static_size:
            self.label_selector_name.set_ellipsize(Pango.EllipsizeMode.END)

        # ------------------------------------
        #   Popover
        # ------------------------------------

        self.popover_selector = ListBoxPopover()

        self.entry_selector = self.popover_selector.entry_selector

        self.frame_selector = self.popover_selector.frame_selector
        self.scroll_selector = self.popover_selector.scroll_selector
        self.listbox_selector = self.popover_selector.listbox_selector


    def __init_packing(self):
        """ Initialize widgets packing in main window
        """

        self.add(self.grid_selector)

        self.set_popover(self.popover_selector)

        self.grid_selector.pack_start(
            self.image_selector_icon, False, False, 0)
        self.grid_selector.pack_start(
            self.label_selector_name, True, True, 0)
        self.grid_selector.pack_start(
            self.image_selector_status, False, False, 0)


    def __start_interface(self):
        """ Load data and start interface
        """

        self.show_all()

        self.grid_selector.show_all()


    def __on_update_data(self, *args):
        """ Reload consoles list when user set a filter
        """

        self.listbox_selector.invalidate_sort()
        self.listbox_selector.invalidate_filter()


    def append_row(self, data, icon, status):
        """ Append a new row into selector

        Parameters
        ----------
        data : gem.api.Console or gem.api.Emulator
            GEM data instance
        icon : GdkPixbuf.Pixbuf
            Console icon
        status : GdkPixbuf.Pixbuf
            Console status icon

        Returns
        -------
        gem.gtk.widgets.ListBoxSelectorItem
            Generated row
        """

        row = ListBoxSelectorItem(data, icon, status)

        self.popover_selector.append_row(row)

        return row


    def clear(self):
        """ Clear listbox items
        """

        children = self.listbox_selector.get_children()

        for child in children:
            self.listbox_selector.remove(child)


    def get_entry(self):
        """ Retrieve entry instance

        Returns
        -------
        Gtk.SearchEntry
            Search entry widget instance
        """

        return self.entry_selector


    def get_listbox(self):
        """ Retrieve listbox instance

        Returns
        -------
        Gtk.ListBox
            Listbox widget instance
        """

        return self.listbox_selector


    def get_selected_row(self):
        """ Retrieve selected row in listbox

        Returns
        -------
        gem.gtk.widgets.ListBoxSelectorItem
            Selected row
        """

        return self.listbox_selector.get_selected_row()


    def invalidate_filter(self):
        """ Filter again listbox content
        """

        self.listbox_selector.invalidate_filter()


    def invalidate_sort(self):
        """ Sort again listbox content
        """

        self.listbox_selector.invalidate_sort()


    def select_row(self, row):
        """ Select a specific row into listbox

        Parameters
        ----------
        row : gem.gtk.widgets.ListBoxSelectorItem
            Row to select
        """

        self.listbox_selector.select_row(row)

        self.label_selector_name.set_label(row.get_label_text())

        self.image_selector_icon.set_from_pixbuf(row.get_icon_pixbuf())
        self.image_selector_status.set_from_pixbuf(row.get_status_pixbuf())


    def set_row_icon(self, row, pixbuf):
        """ Set the icon pixbuf for a specific row

        Parameters
        ----------
        row : gem.gtk.widgets.ListBoxSelectorItem
            Row to modify
        pixbuf : GdkPixbuf.Pixbuf
            Pixbuf instance
        """

        if self.listbox_selector.get_selected_row() == row:
            self.image_selector_icon.set_from_pixbuf(pixbuf)

        row.set_icon_from_pixbuf(pixbuf)


    def set_row_status(self, row, pixbuf):
        """ Set the status pixbuf for a specific row

        Parameters
        ----------
        row : gem.gtk.widgets.ListBoxSelectorItem
            Row to modify
        pixbuf : GdkPixbuf.Pixbuf
            Pixbuf instance
        """

        if self.listbox_selector.get_selected_row() == row:
            self.image_selector_status.set_from_pixbuf(pixbuf)

        row.set_status_from_pixbuf(pixbuf)


    def set_filter_func(self, *args):
        """ Set a filter function to listbox
        """

        self.listbox_selector.set_filter_func(*args)


    def set_sort_func(self, *args):
        """ Set a sort function to listbox
        """

        self.listbox_selector.set_sort_func(*args)


class ListBoxSelectorItem(Gtk.ListBoxRow):

    def __init__(self, data, icon, status):
        """ Constructor

        Parameters
        ----------
        data : gem.api.Console or gem.api.Emulator
            GEM data instance
        icon : GdkPixbuf.Pixbuf
            Console icon
        status : GdkPixbuf.Pixbuf
            Console status icon
        """

        Gtk.ListBoxRow.__init__(self)

        # ------------------------------------
        #   Initialize variables
        # ------------------------------------

        self.data = data

        self.pixbuf_icon = icon
        self.pixbuf_status = status

        # ------------------------------------
        #   Prepare interface
        # ------------------------------------

        # Init widgets
        self.__init_widgets()

        # Init packing
        self.__init_packing()

        # Start interface
        self.__start_interface()


    def __init_widgets(self):
        """ Initialize interface widgets
        """

        # ------------------------------------
        #   Grid
        # ------------------------------------

        self.grid = Gtk.Box()

        # Properties
        self.grid.set_border_width(6)
        self.grid.set_spacing(12)

        # ------------------------------------
        #   Row
        # ------------------------------------

        self.image = Gtk.Image()
        self.status = Gtk.Image()

        self.label = Gtk.Label()

        # Properties
        self.image.set_from_pixbuf(self.pixbuf_icon)
        self.image.set_halign(Gtk.Align.CENTER)
        self.image.set_valign(Gtk.Align.CENTER)

        self.status.set_from_pixbuf(self.pixbuf_status)
        self.status.set_halign(Gtk.Align.CENTER)
        self.status.set_valign(Gtk.Align.CENTER)

        self.label.set_halign(Gtk.Align.START)
        self.label.set_text(self.data.name)


    def __init_packing(self):
        """ Initialize widgets packing in main window
        """

        self.add(self.grid)

        self.grid.pack_start(self.image, False, False, 0)
        self.grid.pack_start(self.label, True, True, 0)
        self.grid.pack_start(self.status, False, False, 0)


    def __start_interface(self):
        """ Load data and start interface
        """

        self.show_all()


    def get_label(self):
        """ Retrieve label instance

        Returns
        -------
        Gtk.Label
            Label widget instance
        """

        return self.label


    def get_label_text(self):
        """ Retrieve label content

        Returns
        -------
        str
            Label content
        """

        return self.label.get_text()


    def get_icon_pixbuf(self):
        """ Retrieve icon pixbuf instance

        Returns
        -------
        GdkPixbuf.Pixbuf
            Icon pixbuf widget instance
        """

        return self.image.get_pixbuf()


    def get_status_pixbuf(self):
        """ Retrieve status pixbuf instance

        Returns
        -------
        GdkPixbuf.Pixbuf
            Status pixbuf widget instance
        """

        return self.status.get_pixbuf()


    def set_icon_from_pixbuf(self, pixbuf):
        """ Set the icon pixbuf

        Parameters
        ----------
        row : gem.gtk.widgets.ListBoxSelectorItem
            Row to modify
        pixbuf : GdkPixbuf.Pixbuf
            Pixbuf instance
        """

        self.pixbuf_icon = pixbuf

        self.image.set_from_pixbuf(pixbuf)


    def set_status_from_pixbuf(self, pixbuf):
        """ Set the status pixbuf

        Parameters
        ----------
        row : gem.gtk.widgets.ListBoxSelectorItem
            Row to modify
        pixbuf : GdkPixbuf.Pixbuf
            Pixbuf instance
        """

        self.pixbuf_status = pixbuf

        self.status.set_from_pixbuf(pixbuf)


    def update(self, data, icon, status):
        """ Update row data with a specific console

        Parameters
        ----------
        console : gem.api.Console
            Console instance
        """

        if not self.data == data:
            self.data = data

            self.pixbuf_icon = icon
            self.pixbuf_status = status

            self.label.set_text(data.name)

            self.image.set_from_pixbuf(icon)
            self.status.set_from_pixbuf(status)


class PreferencesItem(Gtk.ListBoxRow):

    def __init__(self):
        """ Constructor
        """

        Gtk.ListBoxRow.__init__(self)

        # ------------------------------------
        #   Initialize variables
        # ------------------------------------

        self.__widget = None

        # ------------------------------------
        #   Prepare interface
        # ------------------------------------

        # Init widgets
        self.__init_widgets()

        # Init packing
        self.__init_packing()


    def __init_widgets(self):
        """ Initialize interface widgets
        """

        # ------------------------------------
        #   Grids
        # ------------------------------------

        self.grid = Gtk.Box()
        self.grid_labels = Gtk.Box()

        # Properties
        self.grid.set_homogeneous(False)
        self.grid.set_border_width(6)
        self.grid.set_spacing(12)

        self.grid_labels.set_orientation(Gtk.Orientation.VERTICAL)
        self.grid_labels.set_homogeneous(False)
        self.grid_labels.set_spacing(2)

        # ------------------------------------
        #   Labels
        # ------------------------------------

        self.label_title = Gtk.Label()

        self.label_description = Gtk.Label()

        # Properties
        self.label_title.set_line_wrap(True)
        self.label_title.set_halign(Gtk.Align.START)
        self.label_title.set_valign(Gtk.Align.END)
        self.label_title.set_justify(Gtk.Justification.FILL)
        self.label_title.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)

        self.label_description.set_hexpand(True)
        self.label_description.set_line_wrap(True)
        self.label_description.set_use_markup(True)
        self.label_description.set_no_show_all(True)
        self.label_description.set_halign(Gtk.Align.START)
        self.label_description.set_valign(Gtk.Align.START)
        self.label_description.set_justify(Gtk.Justification.FILL)
        self.label_description.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.label_description.get_style_context().add_class("dim-label")


    def __init_packing(self):
        """ Initialize widgets packing in main window
        """

        self.add(self.grid)

        self.grid.pack_start(self.grid_labels, True, True, 0)

        self.grid_labels.pack_start(self.label_title, True, True, 0)
        self.grid_labels.pack_start(self.label_description, True, True, 0)


    def set_option_label(self, text):
        """ Set the option label text

        Parameters
        ----------
        text : str
            Label text
        """

        self.label_title.set_text(text)


    def get_option_label(self):
        """ Retrieve the option label text

        Returns
        -------
        str
            Label text
        """

        return self.label_title.get_text()


    def set_description_label(self, text):
        """ Set the description label text

        Parameters
        ----------
        text : str
            Label text
        """

        self.label_description.set_markup(
            "<span size=\"small\">%s</span>" % text)
        self.label_description.set_visible(len(text) > 0)


    def set_widget(self, widget):
        """ Set a new internal widget

        Parameters
        ----------
        widget : Gtk.Widget
            Internal widget to set
        """

        # Remove previous widget
        if self.__widget is not None:
            self.grid.remove(self.__widget)

        # Add new widget
        if widget is not None:
            widget.set_valign(Gtk.Align.CENTER)

            if not type(widget) in [Gtk.Switch, Gtk.SpinButton]:
                widget.set_halign(Gtk.Align.FILL)
                widget.set_hexpand(True)

                self.grid.set_homogeneous(True)

                self.grid.pack_start(widget, True, True, 0)

            else:
                widget.set_halign(Gtk.Align.END)
                widget.set_hexpand(False)

                self.grid.set_homogeneous(False)

                self.grid.pack_start(widget, False, False, 0)

        self.__widget = widget


    def get_widget(self):
        """ Retrieve internal widget

        Returns
        -------
        Gtk.Widget
            Internal widget
        """

        return self.__widget
