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
from gem.ui.data import Icons
from gem.ui.widgets.window import CommonWindow

# GObject
try:
    from gi import require_version

    require_version("Gtk", "3.0")

    from gi.repository import Gtk
    from gi.repository import Pango

except ImportError as error:
    from sys import exit

    exit("Cannot found python3-gobject module: %s" % str(error))

# Translation
from gettext import gettext as _


# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class MednafenDialog(CommonWindow):

    def __init__(self, parent, name, data):
        """ Constructor

        Parameters
        ----------
        parent : Gtk.Window
            Parent object
        name : str
            Game name
        data : dict
            Backup memory type dictionary (with type as key)
        """

        classic_theme = False
        if parent is not None:
            classic_theme = parent.use_classic_theme

        CommonWindow.__init__(self,
                              parent,
                              _("Backup Memory Type"),
                              Icons.Symbolic.SAVE,
                              classic_theme)

        # ------------------------------------
        #   Initialize variables
        # ------------------------------------

        self.data = data

        self.name = name

        self.memory_list = ["eeprom", "flash", "rtc", "sensor", "sram"]

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

        self.set_size(640, 420)

        # ------------------------------------
        #   Grid
        # ------------------------------------

        grid = Gtk.Grid()

        # Properties
        grid.set_row_spacing(6)
        grid.set_column_spacing(12)

        # ------------------------------------
        #   Description
        # ------------------------------------

        label = Gtk.Label()
        label_game = Gtk.Label()

        # Properties
        label.set_text(_("This dialog allow you to specify specific backup "
                         "memory type for the following game:"))
        label.set_line_wrap(True)
        label.set_max_width_chars(8)
        label.set_single_line_mode(False)
        label.set_justify(Gtk.Justification.FILL)
        label.set_line_wrap_mode(Pango.WrapMode.WORD)

        label_game.set_text(self.name)
        label_game.set_margin_bottom(12)
        label_game.set_single_line_mode(True)
        label_game.set_ellipsize(Pango.EllipsizeMode.END)
        label_game.get_style_context().add_class("dim-label")

        # ------------------------------------
        #   Buttons
        # ------------------------------------

        buttons = Gtk.Box()

        self.image_add = Gtk.Image()
        self.button_add = Gtk.Button()

        self.image_remove = Gtk.Image()
        self.button_remove = Gtk.Button()

        # Properties
        Gtk.StyleContext.add_class(
            buttons.get_style_context(), "linked")
        buttons.set_spacing(-1)
        buttons.set_orientation(Gtk.Orientation.VERTICAL)

        self.image_add.set_from_icon_name(
            Icons.Symbolic.ADD, Gtk.IconSize.MENU)
        self.button_add.set_image(self.image_add)

        self.image_remove.set_from_icon_name(
            Icons.Symbolic.REMOVE, Gtk.IconSize.MENU)
        self.button_remove.set_image(self.image_remove)

        # ------------------------------------
        #   Link
        # ------------------------------------

        link = Gtk.LinkButton()

        # Properties
        link.set_label(_("Mednafen GBA documentation"))
        link.set_uri("https://mednafen.github.io/documentation/gba.html"
                     "#Section_backupmem_type")

        # ------------------------------------
        #   Content list
        # ------------------------------------

        frame = Gtk.Frame()
        scroll = Gtk.ScrolledWindow()
        view = Gtk.Viewport()

        self.adjustment_value = Gtk.Adjustment()

        self.model_memory_keys = Gtk.ListStore(str)

        self.model = Gtk.ListStore(str, int)
        self.treeview = Gtk.TreeView()

        column = Gtk.TreeViewColumn()

        self.cell_key = Gtk.CellRendererCombo()
        self.cell_value = Gtk.CellRendererSpin()

        # Properties
        self.adjustment_value.set_lower(0)
        self.adjustment_value.set_upper(2147483647)  # INT_MAX
        self.adjustment_value.set_step_increment(16)
        self.adjustment_value.set_page_increment(1024)

        self.treeview.set_hexpand(True)
        self.treeview.set_vexpand(True)
        self.treeview.set_model(self.model)
        self.treeview.set_headers_clickable(False)
        self.treeview.set_headers_visible(False)
        self.treeview.set_show_expanders(False)
        self.treeview.set_has_tooltip(False)

        column.set_expand(True)
        column.pack_start(self.cell_key, True)
        column.pack_start(self.cell_value, True)

        column.add_attribute(self.cell_key, "text", 0)
        column.add_attribute(self.cell_value, "text", 1)

        self.cell_key.set_padding(12, 6)
        self.cell_key.set_alignment(0, .5)
        self.cell_key.set_property("text-column", 0)
        self.cell_key.set_property("editable", True)
        self.cell_key.set_property("has-entry", False)
        self.cell_key.set_property("model", self.model_memory_keys)

        self.cell_value.set_padding(12, 6)
        self.cell_value.set_alignment(1, .5)
        self.cell_value.set_property("editable", True)
        self.cell_value.set_property("adjustment", self.adjustment_value)

        # ------------------------------------
        #   Integrate widgets
        # ------------------------------------

        frame.add(self.treeview)

        scroll.add(view)
        view.add(grid)

        self.treeview.append_column(column)

        buttons.add(self.button_add)
        buttons.add(self.button_remove)

        grid.attach(label, 0, 0, 2, 1)
        grid.attach(label_game, 0, 1, 2, 1)
        grid.attach(buttons, 0, 2, 1, 1)
        grid.attach(frame, 1, 2, 1, 1)
        grid.attach(link, 0, 3, 2, 1)

        self.pack_start(scroll, True, True)

    def __init_signals(self):
        """ Initialize widgets signals
        """

        self.button_add.connect("clicked", self.__on_append_item)
        self.button_remove.connect("clicked", self.__on_remove_item)

        self.cell_key.connect("edited", self.__on_edited_cell)
        self.cell_value.connect("edited", self.__on_edited_cell)

    def __start_interface(self):
        """ Load data and start interface
        """

        self.add_button(_("Cancel"), Gtk.ResponseType.CLOSE)
        self.add_button(_("Apply"), Gtk.ResponseType.APPLY, Gtk.Align.END)

        for key in self.memory_list:
            self.model_memory_keys.append([key])

        for key, value in self.data.items():
            self.model.append([key, value])

        self.show_all()

    def __on_append_item(self, widget):
        """ Append a new row in treeview

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        self.model.append([self.memory_list[0], int()])

    def __on_remove_item(self, widget):
        """ Remove a row in treeview

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        model, treeiter = self.treeview.get_selection().get_selected()
        if treeiter is not None:
            self.model.remove(treeiter)

    def __on_edited_cell(self, widget, path, text):
        """ Update treerow when a cell has been edited

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        path : str
            Path identifying the edited cell
        text : str
            New text
        """

        if type(widget) == Gtk.CellRendererCombo:
            self.model[path][0] = str(text)

        elif type(widget) == Gtk.CellRendererSpin:
            self.model[path][1] = int(text)
