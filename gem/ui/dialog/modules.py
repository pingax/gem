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
from gem.ui import *
from gem.ui.data import *

from gem.ui.widgets.window import CommonWindow

# Translation
from gettext import gettext as _

# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class ModulesDialog(CommonWindow):

    def __init__(self, parent):
        """ Constructor

        Parameters
        ----------
        parent : Gtk.Window
            Parent object
        game : gem.api.Game
            Game object instance
        """

        classic_theme = False
        if parent is not None:
            classic_theme = parent.use_classic_theme

        CommonWindow.__init__(
            self, parent, _("Modules"), Icons.Symbolic.Addon, classic_theme)

        # ------------------------------------
        #   Initialize variables
        # ------------------------------------

        self.interface = parent

        self.modules = parent.modules

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

        self.set_size(520, 520)

        self.set_spacing(12)

        # ------------------------------------
        #   Filter
        # ------------------------------------

        self.entry_filter = Gtk.SearchEntry()

        # ------------------------------------
        #   Modules list
        # ------------------------------------

        self.scroll_listbox = Gtk.ScrolledWindow()

        self.frame_listbox = Gtk.Frame()

        self.listbox = Gtk.ListBox()

        # Properties
        self.scroll_listbox.set_policy(
            Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        # ------------------------------------
        #   Description
        # ------------------------------------

        self.textbuffer = Gtk.TextBuffer()

        self.textview = Gtk.TextView.new_with_buffer(self.textbuffer)

        # Properties
        self.textview.set_size_request(-1, 150)
        self.textview.set_no_show_all(True)

        # ------------------------------------
        #   Integrate widgets
        # ------------------------------------

        self.frame_listbox.add(self.scroll_listbox)
        self.scroll_listbox.add(self.listbox)

        self.pack_start(self.entry_filter, False, False)
        self.pack_start(self.frame_listbox, True, True)
        self.pack_start(self.textview, False, False)


    def __init_signals(self):
        """ Initialize widgets signals
        """

        self.listbox.connect("row-selected", self.__on_select_row)


    def __start_interface(self):
        """ Load data and start interface
        """

        self.add_button(_("Close"), Gtk.ResponseType.CLOSE, Gtk.Align.END)

        self.__append_modules()


    def __append_modules(self):
        """ Append modules into listbox
        """

        for name, module in self.modules.items():
            row = ModulesRow(name, module)

            self.listbox.add(row)


    def __on_select_row(self, widget, row):
        """ Select a specific row in modules listbox

        Parameters
        ----------
        widget : Gtk.ListBox
            Object which received the signal
        row : gem.ui.dialog.modules.ModulesRow
            Selected row
        """

        if row is not None:
            self.textview.show()

            self.textbuffer.set_text(row.module.get_description())

        else:
            self.textview.hide()


class ModulesRow(Gtk.ListBoxRow):

    def __init__(self, name, module):
        """ Constructor
        """

        Gtk.ListBoxRow.__init__(self)

        # ------------------------------------
        #   Initialize variables
        # ------------------------------------

        self.module_name = name

        self.module = module

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

        # ------------------------------------
        #   Grid
        # ------------------------------------

        self.grid = Gtk.Box()

        # Properties
        self.grid.set_homogeneous(False)
        self.grid.set_border_width(6)
        self.grid.set_spacing(6)

        # ------------------------------------
        #   Label
        # ------------------------------------

        self.label = Gtk.Label()

        # Properties
        self.label.set_markup("<b>%s</b>" %  self.module_name)
        self.label.set_halign(Gtk.Align.START)
        self.label.set_use_markup(True)

        # ------------------------------------
        #   Switch
        # ------------------------------------

        self.switch = Gtk.Switch()

        # ------------------------------------
        #   Integrate widgets
        # ------------------------------------

        self.add(self.grid)

        self.grid.pack_start(self.label, True, True, 0)
        self.grid.pack_start(self.switch, False, False, 0)


    def __start_interface(self):
        """ Load data and start interface
        """

        self.grid.show_all()

