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

# ------------------------------------------------------------------------------
#   Modules
# ------------------------------------------------------------------------------

# System
from sys import exit as sys_exit

# ------------------------------------------------------------------------------
#   Modules - Interface
# ------------------------------------------------------------------------------

try:
    from gi import require_version

    require_version("Gtk", "3.0")

    from gi.repository import Gtk
    from gi.repository import Gdk
    from gi.repository import Pango

except ImportError as error:
    sys_exit("Import error with python3-gobject module: %s" % str(error))

# ------------------------------------------------------------------------------
#   Modules - GEM
# ------------------------------------------------------------------------------

try:
    from gem.utils import *

    from gem.gtk import *
    from gem.gtk.windows import Dialog
    from gem.gtk.windows import Question

except ImportError as error:
    sys_exit("Import error with gem module: %s" % str(error))

# ------------------------------------------------------------------------------
#   Modules - Translation
# ------------------------------------------------------------------------------

from gettext import gettext as _
from gettext import textdomain
from gettext import bindtextdomain

bindtextdomain("gem", get_data("i18n"))
textdomain("gem")

# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class DialogMednafenMemory(Dialog):

    def __init__(self, parent, title, data):
        """ Constructor

        Parameters
        ----------
        parent : Gtk.Window
            Parent object
        title : str
            Dialog title
        data : dict
            Backup memory type dictionary (with type as key)
        """

        Dialog.__init__(self, parent, title, Icons.Save)

        # ------------------------------------
        #   Initialize variables
        # ------------------------------------

        self.interface = parent

        self.data = data

        # ------------------------------------
        #   Prepare interface
        # ------------------------------------

        # Init widgets
        self.__init_widgets()

        # Init signals
        self.__init_signals()

        # Start interface
        self.__start_interface()


    def __init_widgets(self):
        """ Initialize interface widgets
        """

        self.set_size(520, 420)

        self.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.APPLY)

        # ------------------------------------
        #   Grid
        # ------------------------------------

        grid = Gtk.Grid()

        # Properties
        grid.set_row_spacing(8)
        grid.set_column_spacing(8)

        # ------------------------------------
        #   Description
        # ------------------------------------

        label = Gtk.Label()

        # Properties
        label.set_text(_("You can set multiple memory types for this game."))
        label.set_line_wrap(True)
        label.set_single_line_mode(False)
        label.set_line_wrap_mode(Pango.WrapMode.CHAR)

        # ------------------------------------
        #   Buttons
        # ------------------------------------

        buttons = Gtk.ButtonBox()

        self.image_add = Gtk.Image()
        self.button_add = Gtk.Button()

        self.image_modify = Gtk.Image()
        self.button_modify = Gtk.Button()

        self.image_remove = Gtk.Image()
        self.button_remove = Gtk.Button()

        # Properties
        buttons.set_spacing(8)
        buttons.set_layout(Gtk.ButtonBoxStyle.START)
        buttons.set_orientation(Gtk.Orientation.VERTICAL)

        self.image_add.set_margin_right(4)
        self.image_add.set_from_icon_name(
            Icons.Add, Gtk.IconSize.MENU)
        self.button_add.set_image(self.image_add)
        self.button_add.set_label(_("Add"))

        self.image_modify.set_margin_right(4)
        self.image_modify.set_from_icon_name(
            Icons.Properties, Gtk.IconSize.MENU)
        self.button_modify.set_image(self.image_modify)
        self.button_modify.set_label(_("Modify"))

        self.image_remove.set_margin_right(4)
        self.image_remove.set_from_icon_name(
            Icons.Remove, Gtk.IconSize.MENU)
        self.button_remove.set_image(self.image_remove)
        self.button_remove.set_label(_("Remove"))

        # ------------------------------------
        #   Link
        # ------------------------------------

        link = Gtk.LinkButton()

        # Properties
        link.set_alignment(1, .5)
        link.set_label(_("Mednafen GBA documentation"))
        link.set_uri("https://mednafen.github.io/documentation/gba.html"
            "#Section_backupmem_type")

        # ------------------------------------
        #   Content list
        # ------------------------------------

        scroll = Gtk.ScrolledWindow()
        view = Gtk.Viewport()

        self.model = Gtk.ListStore(str, int)
        self.treeview = Gtk.TreeView()

        column = Gtk.TreeViewColumn()

        cell_key = Gtk.CellRendererText()
        cell_value = Gtk.CellRendererText()

        # Properties
        self.treeview.set_hexpand(True)
        self.treeview.set_vexpand(True)
        self.treeview.set_model(self.model)
        self.treeview.set_headers_clickable(False)
        self.treeview.set_headers_visible(False)
        self.treeview.set_show_expanders(False)
        self.treeview.set_has_tooltip(False)

        column.set_expand(True)
        column.pack_start(cell_key, True)
        column.pack_start(cell_value, False)

        column.add_attribute(cell_key, "text", 0)
        column.add_attribute(cell_value, "text", 1)

        cell_key.set_padding(8, 8)
        cell_key.set_alignment(0, .5)
        cell_value.set_padding(8, 8)
        cell_value.set_alignment(0, .5)

        # ------------------------------------
        #   Integrate widgets
        # ------------------------------------

        scroll.add(view)
        view.add(grid)

        self.treeview.append_column(column)

        buttons.add(self.button_add)
        buttons.add(self.button_modify)
        buttons.add(self.button_remove)

        grid.attach(label, 0, 0, 2, 1)
        grid.attach(buttons, 0, 1, 1, 1)
        grid.attach(self.treeview, 1, 1, 1, 1)
        grid.attach(link, 0, 2, 2, 1)

        self.dialog_box.pack_start(scroll, True, True, 0)


    def __init_signals(self):
        """ Initialize widgets signals
        """

        self.button_add.connect("clicked", self.__on_push_button)
        self.button_modify.connect("clicked", self.__on_push_button)
        self.button_remove.connect("clicked", self.__on_push_button)


    def __start_interface(self):
        """ Load data and start interface
        """

        for key, value in self.data.items():
            self.model.append([key, value])

        self.show_all()


    def __on_push_button(self, widget):
        """
        """

        key, value = None, None

        if not widget == self.button_add:
            model, treeiter = self.treeview.get_selection().get_selected()

            # No selection in treeview
            if treeiter is None:
                return False

            key = model.get_value(treeiter, 0)
            value = model.get_value(treeiter, 1)

        self.set_sensitive(False)

        if not widget == self.button_remove:

            dialog = DialogMednafenMemoryType(self.interface,
                _("Specify a memory type"), key, value)

            if dialog.run() == Gtk.ResponseType.APPLY:
                key = dialog.combo_key.get_active_id()
                value = dialog.spin_value.get_value()

                if widget == self.button_add:
                    self.model.append([key, int(value)])

                elif widget == self.button_modify and treeiter is not None:
                    self.model.set_value(treeiter, 0, key)
                    self.model.set_value(treeiter, 1, value)

        else:
            dialog = Question(self.interface, _("Remove a memory type"),
                _("Do you want to remove this memory type ?"))

            if dialog.run() == Gtk.ResponseType.YES:
                self.model.remove(treeiter)

        dialog.hide()

        self.set_sensitive(True)

        return True


class DialogMednafenMemoryType(Dialog):

    def __init__(self, parent, title, key=None, value=None):
        """ Constructor

        Parameters
        ----------
        parent : Gtk.Window
            Parent object
        title : str
            Dialog title
        key : str
            Backup memory type (default: None)
        value : str
            Backup memory value (default: None)
        """

        Dialog.__init__(self, parent, title, Icons.Save)

        # ------------------------------------
        #   Initialize variables
        # ------------------------------------

        self.key = key
        self.value = value

        # ------------------------------------
        #   Prepare interface
        # ------------------------------------

        # Init widgets
        self.__init_widgets()

        # Start interface
        self.__start_interface()


    def __init_widgets(self):
        """ Initialize interface widgets
        """

        self.set_size(420, -1)

        self.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_APPLY, Gtk.ResponseType.APPLY)

        # ------------------------------------
        #   Grids
        # ------------------------------------

        grid = Gtk.Grid()

        # Properties
        grid.set_row_spacing(8)
        grid.set_column_spacing(8)
        grid.set_column_homogeneous(False)

        # ------------------------------------
        #   Widgets
        # ------------------------------------

        label_key = Gtk.Label()

        self.model_key = Gtk.ListStore(str)
        self.combo_key = Gtk.ComboBox()
        cell_key = Gtk.CellRendererText()

        label_value = Gtk.Label()

        self.spin_value = Gtk.SpinButton()

        # Properties
        label_key.set_hexpand(True)
        label_key.set_alignment(0, .5)
        label_key.set_text(_("Type"))

        self.model_key.set_sort_column_id(0, Gtk.SortType.ASCENDING)

        self.combo_key.set_hexpand(True)
        self.combo_key.set_model(self.model_key)
        self.combo_key.set_id_column(0)
        self.combo_key.pack_start(cell_key, False)
        self.combo_key.add_attribute(cell_key, "text", 0)

        label_value.set_alignment(0, .5)
        label_value.set_text(_("Value"))

        self.spin_value.set_range(0, pow(2, 32))
        self.spin_value.set_increments(32, 64)

        # ------------------------------------
        #   Integrate widgets
        # ------------------------------------

        grid.attach(label_key, 0, 0, 1, 1)
        grid.attach(self.combo_key, 1, 0, 1, 1)
        grid.attach(label_value, 0, 1, 1, 1)
        grid.attach(self.spin_value, 1, 1, 1, 1)

        self.dialog_box.pack_start(grid, True, True, 0)


    def __start_interface(self):
        """ Load data and start interface
        """

        for element in [ "sram", "flash", "eeprom", "sensor", "rtc" ]:
            self.model_key.append([element])

        if self.key is None:
            self.combo_key.set_active(0)
        else:
            self.combo_key.set_active_id(self.key)

        if self.value is None:
            self.spin_value.set_value(0)
        else:
            self.spin_value.set_value(self.value)

        self.show_all()
