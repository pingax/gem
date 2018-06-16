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
from gem.engine.utils import *

from gem.ui import *
from gem.ui.data import *

from gem.ui.widgets.window import CommonWindow

# Translation
from gettext import gettext as _

# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class DuplicateDialog(CommonWindow):

    def __init__(self, parent, game, emulator):
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

        CommonWindow.__init__(self,
            parent, _("Duplicate a game"), Icons.Symbolic.Copy, classic_theme)

        # ------------------------------------
        #   Initialize variables
        # ------------------------------------

        self.game = game
        self.emulator = emulator

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

        self.set_size(520, -1)

        self.set_spacing(6)

        self.set_resizable(True)

        # ------------------------------------
        #   Grid
        # ------------------------------------

        self.grid_switch = Gtk.Grid()

        # Properties
        self.grid_switch.set_column_spacing(12)
        self.grid_switch.set_row_spacing(6)

        # ------------------------------------
        #   Title
        # ------------------------------------

        self.label_title = Gtk.Label()

        # Properties
        self.label_title.set_markup(
            "<span weight='bold' size='large'>%s</span>" % \
            replace_for_markup(self.game.name))
        self.label_title.set_use_markup(True)
        self.label_title.set_halign(Gtk.Align.CENTER)
        self.label_title.set_ellipsize(Pango.EllipsizeMode.END)

        # ------------------------------------
        #   Filename
        # ------------------------------------

        self.label_name = Gtk.Label()

        self.entry_name = Gtk.Entry()

        # Properties
        self.label_name.set_markup("<b>%s</b>" % _("New filename"))
        self.label_name.set_margin_top(12)
        self.label_name.set_hexpand(True)
        self.label_name.set_use_markup(True)
        self.label_name.set_single_line_mode(True)
        self.label_name.set_halign(Gtk.Align.CENTER)
        self.label_name.set_ellipsize(Pango.EllipsizeMode.END)

        self.entry_name.set_hexpand(True)
        self.entry_name.set_text(self.game.filename)
        self.entry_name.set_icon_from_icon_name(
            Gtk.EntryIconPosition.PRIMARY, Icons.Symbolic.Save)
        self.entry_name.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, Icons.Symbolic.Error)

        # ------------------------------------
        #   Optional data
        # ------------------------------------

        self.label_data = Gtk.Label()

        self.switch_savestate = Gtk.Switch()
        self.label_savestate = Gtk.Label()

        self.switch_screenshot = Gtk.Switch()
        self.label_screenshot = Gtk.Label()

        self.switch_database = Gtk.Switch()
        self.label_database = Gtk.Label()

        self.switch_notes = Gtk.Switch()
        self.label_notes = Gtk.Label()

        self.switch_memory = Gtk.Switch()
        self.label_memory = Gtk.Label()

        # Properties
        self.label_data.set_markup(
            "<b>%s</b>" % _("Optional data to duplicate"))
        self.label_data.set_margin_top(12)
        self.label_data.set_hexpand(True)
        self.label_data.set_use_markup(True)
        self.label_data.set_single_line_mode(True)
        self.label_data.set_halign(Gtk.Align.CENTER)
        self.label_data.set_ellipsize(Pango.EllipsizeMode.END)

        self.label_savestate.set_text(_("Save files"))
        self.label_savestate.set_halign(Gtk.Align.START)
        self.label_savestate.get_style_context().add_class("dim-label")

        self.label_screenshot.set_text(_("Game screenshots"))
        self.label_screenshot.set_halign(Gtk.Align.START)
        self.label_screenshot.get_style_context().add_class("dim-label")

        self.label_database.set_text(_("Game's data from database"))
        self.label_database.set_halign(Gtk.Align.START)
        self.label_database.get_style_context().add_class("dim-label")

        self.label_notes.set_text(_("Notes"))
        self.label_notes.set_margin_top(12)
        self.label_notes.set_halign(Gtk.Align.START)
        self.label_notes.get_style_context().add_class("dim-label")
        self.switch_notes.set_margin_top(12)

        self.label_memory.set_text(_("Memory file"))
        self.label_memory.set_margin_top(12)
        self.label_memory.set_halign(Gtk.Align.START)
        self.label_memory.get_style_context().add_class("dim-label")
        self.label_memory.set_no_show_all(True)
        self.switch_memory.set_margin_top(12)
        self.switch_memory.set_no_show_all(True)

        # ------------------------------------
        #   Integrate widgets
        # ------------------------------------

        self.grid_switch.attach(self.switch_savestate, 0, 1, 1, 1)
        self.grid_switch.attach(self.label_savestate, 1, 1, 2, 1)
        self.grid_switch.attach(self.switch_screenshot, 0, 2, 1, 1)
        self.grid_switch.attach(self.label_screenshot, 1, 2, 2, 1)
        self.grid_switch.attach(self.switch_database, 0, 3, 1, 1)
        self.grid_switch.attach(self.label_database, 1, 3, 2, 1)
        self.grid_switch.attach(self.switch_notes, 0, 4, 1, 1)
        self.grid_switch.attach(self.label_notes, 1, 4, 2, 1)
        self.grid_switch.attach(self.switch_memory, 0, 5, 1, 1)
        self.grid_switch.attach(self.label_memory, 1, 5, 2, 1)

        self.pack_start(self.label_title, False, False)
        self.pack_start(self.label_name, False, False)
        self.pack_start(self.entry_name, False, False)
        self.pack_start(self.label_data, False, False)
        self.pack_start(self.grid_switch)


    def __init_signals(self):
        """ Initialize widgets signals
        """

        self.entry_name.connect("changed", self.check_filename)


    def __start_interface(self):
        """ Load data and start interface
        """

        self.add_button(_("Cancel"), Gtk.ResponseType.CANCEL)
        self.add_button(_("Accept"), Gtk.ResponseType.APPLY, Gtk.Align.END)

        self.set_response_sensitive(Gtk.ResponseType.APPLY, False)

        # Check extension and emulator for GBA game on mednafen
        if self.game.extension.lower() == ".gba" and \
            "mednafen" in self.emulator.binary and \
            self.parent.get_mednafen_status():
            self.switch_memory.show()
            self.label_memory.show()


    def check_filename(self, *args):
        """ Check filename in game folder to detect if a file already exists
        """

        # Retrieve game folder path
        filename = self.entry_name.get_text() + self.game.extension

        # Check if the new filename path not exists
        if not exists(path_join(self.game.path[0], filename)):
            self.entry_name.set_icon_from_icon_name(
                Gtk.EntryIconPosition.SECONDARY, None)

            self.set_response_sensitive(Gtk.ResponseType.APPLY, True)

        else:
            self.entry_name.set_icon_from_icon_name(
                Gtk.EntryIconPosition.SECONDARY, Icons.Symbolic.Error)

            self.set_response_sensitive(Gtk.ResponseType.APPLY, False)
