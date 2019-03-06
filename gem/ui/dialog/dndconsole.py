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
    from gi.repository import GdkPixbuf
    from gi.repository import Pango

except ImportError as error:
    from sys import exit

    exit("Cannot found python3-gobject module: %s" % str(error))

# Translation
from gettext import gettext as _

# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class DnDConsoleDialog(CommonWindow):

    def __init__(self, parent, filename, consoles, previous=None):
        """ Constructor

        Parameters
        ----------
        parent : Gtk.Window
            Parent object
        filename : str
            File name
        consoles : list
            Consoles list
        previous : str or None, optional
            Previous selected console (Default: None)
        """

        classic_theme = False
        if parent is not None:
            classic_theme = parent.use_classic_theme

        CommonWindow.__init__(self,
            parent, _("Drag & Drop"), Icons.Symbolic.GAMING, classic_theme)

        # ------------------------------------
        #   Initialize variables
        # ------------------------------------

        self.current = None

        self.api = parent.api

        self.filename = filename

        self.consoles = consoles
        self.previous = previous

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

        self.set_size(640, 480)

        self.set_spacing(0)

        # ------------------------------------
        #   Grids
        # ------------------------------------

        grid = Gtk.Box()

        grid_checkbutton = Gtk.Box()

        # Properties
        grid.set_spacing(6)
        grid.set_homogeneous(False)
        grid.set_orientation(Gtk.Orientation.VERTICAL)

        grid_checkbutton.set_spacing(12)
        grid_checkbutton.set_margin_top(12)
        grid_checkbutton.set_homogeneous(False)
        grid_checkbutton.set_orientation(Gtk.Orientation.HORIZONTAL)

        # ------------------------------------
        #   Scroll
        # ------------------------------------

        self.scroll_consoles = Gtk.ScrolledWindow()
        self.view_consoles = Gtk.Viewport()

        # ------------------------------------
        #   Description
        # ------------------------------------

        self.label_description = Gtk.Label()
        self.label_game = Gtk.Label()

        # Properties
        self.label_description.set_label(_("The following game can be "
            "installed on multiple consoles. Select the console where to "
            "install this game:"))
        self.label_description.set_line_wrap(True)
        self.label_description.set_max_width_chars(8)
        self.label_description.set_single_line_mode(False)
        self.label_description.set_justify(Gtk.Justification.FILL)
        self.label_description.set_line_wrap_mode(Pango.WrapMode.WORD)

        self.label_game.set_label(self.filename)
        self.label_game.set_margin_bottom(12)
        self.label_game.set_single_line_mode(True)
        self.label_game.set_ellipsize(Pango.EllipsizeMode.END)
        self.label_game.get_style_context().add_class("dim-label")

        # ------------------------------------
        #   Consoles
        # ------------------------------------

        self.model_consoles = Gtk.ListStore(bool, GdkPixbuf.Pixbuf, str)
        self.treeview_consoles = Gtk.TreeView()

        self.column_consoles = Gtk.TreeViewColumn()

        self.cell_consoles_status = Gtk.CellRendererToggle()
        self.cell_consoles_icon = Gtk.CellRendererPixbuf()
        self.cell_consoles_name = Gtk.CellRendererText()

        # Properties
        self.model_consoles.set_sort_column_id(2, Gtk.SortType.ASCENDING)

        self.treeview_consoles.set_model(self.model_consoles)
        self.treeview_consoles.set_headers_visible(False)

        self.column_consoles.set_expand(True)
        self.column_consoles.pack_start(self.cell_consoles_status, False)
        self.column_consoles.pack_start(self.cell_consoles_icon, False)
        self.column_consoles.pack_start(self.cell_consoles_name, True)

        self.column_consoles.add_attribute(
            self.cell_consoles_status, "active", 0)
        self.column_consoles.add_attribute(
            self.cell_consoles_icon, "pixbuf", 1)
        self.column_consoles.add_attribute(
            self.cell_consoles_name, "text", 2)

        self.cell_consoles_status.set_padding(6, 6)
        self.cell_consoles_status.set_activatable(True)
        self.cell_consoles_status.set_radio(True)

        self.cell_consoles_icon.set_padding(6, 6)
        self.cell_consoles_icon.set_alignment(0, .5)

        self.cell_consoles_name.set_padding(6, 6)
        self.cell_consoles_name.set_alignment(0, .5)

        self.treeview_consoles.append_column(self.column_consoles)

        # ------------------------------------
        #   CheckButton
        # ------------------------------------

        self.switch = Gtk.Switch()

        self.label_checkbutton = Gtk.Label()
        self.label_explanation = Gtk.Label()

        # Properties
        self.label_checkbutton.set_label(
            _("Keep this selection for every games in queue"))
        self.label_checkbutton.set_line_wrap(True)
        self.label_checkbutton.set_single_line_mode(False)
        self.label_checkbutton.set_halign(Gtk.Align.START)
        self.label_checkbutton.set_justify(Gtk.Justification.FILL)
        self.label_checkbutton.set_line_wrap_mode(Pango.WrapMode.WORD)

        self.label_explanation.set_label(
            _("Be careful, this option cannot be undo during the process."))
        self.label_explanation.set_line_wrap(True)
        self.label_explanation.set_single_line_mode(False)
        self.label_explanation.set_halign(Gtk.Align.START)
        self.label_explanation.set_justify(Gtk.Justification.FILL)
        self.label_explanation.set_line_wrap_mode(Pango.WrapMode.WORD)
        self.label_explanation.get_style_context().add_class("dim-label")

        # ------------------------------------
        #   Integrate widgets
        # ------------------------------------

        self.scroll_consoles.add(self.view_consoles)
        self.view_consoles.add(self.treeview_consoles)

        grid.pack_start(self.label_description, False, False, 0)
        grid.pack_start(self.label_game, False, False, 0)
        grid.pack_start(self.scroll_consoles, True, True, 0)
        grid.pack_start(grid_checkbutton, False, False, 0)
        grid.pack_start(self.label_explanation, False, False, 0)

        grid_checkbutton.pack_start(self.label_checkbutton, True, True, 0)
        grid_checkbutton.pack_start(self.switch, False, False, 0)

        self.pack_start(grid, True, True)


    def __init_signals(self):
        """ Initialize widgets signals
        """

        self.cell_consoles_status.connect("toggled", self.on_cell_toggled)


    def __start_interface(self):
        """ Load data and start interface
        """

        self.add_button(_("Cancel"), Gtk.ResponseType.CLOSE)
        self.add_button(_("Accept"), Gtk.ResponseType.APPLY, Gtk.Align.END)

        self.set_response_sensitive(Gtk.ResponseType.APPLY, False)

        self.window.show_all()

        for console in self.consoles:
            status = False
            if self.previous is not None and self.previous.name == console.name:
                status = True

                self.current = console
                self.set_response_sensitive(Gtk.ResponseType.APPLY, True)

            icon = console.icon

            if not icon.exists():
                icon = self.api.get_local("icons", "%s.png" % icon)

            # Get console icon
            icon = icon_from_data(icon, self.parent.empty)

            self.model_consoles.append([status, icon, console.name])


    def on_cell_toggled(self, widget, path):
        """ Toggled a radio cell in treeview

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        path : Gtk.TreePath
            Path to be activated
        """

        self.set_response_sensitive(Gtk.ResponseType.APPLY, True)

        selected_path = Gtk.TreePath(path)

        treeiter = self.model_consoles.get_iter(selected_path)
        self.current = self.model_consoles.get_value(treeiter, 2)

        for row in self.model_consoles:
            row[0] = (row.path == selected_path)
