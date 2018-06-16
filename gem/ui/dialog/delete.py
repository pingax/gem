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

class DeleteDialog(CommonWindow):

    def __init__(self, parent, game, emulator):
        """ Constructor

        Parameters
        ----------
        parent : Gtk.Window
            Parent object
        game : gem.api.Game
            Game object
        """

        classic_theme = False
        if parent is not None:
            classic_theme = parent.use_classic_theme

        CommonWindow.__init__(self,
            parent, _("Remove a game"), Icons.Symbolic.Delete, classic_theme)

        # ------------------------------------
        #   Variables
        # ------------------------------------

        self.game = game
        self.emulator = emulator

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
        #   Description
        # ------------------------------------

        self.label_description = Gtk.Label()

        # Properties
        self.label_description.set_text(_("The following game going to be "
            "removed from your harddrive. This action is irreversible !"))
        self.label_description.set_line_wrap(True)
        self.label_description.set_max_width_chars(8)
        self.label_description.set_single_line_mode(False)
        self.label_description.set_justify(Gtk.Justification.FILL)
        self.label_description.set_line_wrap_mode(Pango.WrapMode.WORD)

        # ------------------------------------
        #   Options
        # ------------------------------------

        self.label_data = Gtk.Label()

        self.label_database = Gtk.Label()
        self.switch_database = Gtk.Switch()

        self.label_desktop = Gtk.Label()
        self.switch_desktop = Gtk.Switch()

        self.label_savestate = Gtk.Label()
        self.switch_savestate = Gtk.Switch()

        self.label_screenshots = Gtk.Label()
        self.switch_screenshots = Gtk.Switch()

        self.label_memory = Gtk.Label()
        self.switch_memory = Gtk.Switch()

        # Properties
        self.label_data.set_markup(
            "<b>%s</b>" % _("Optional data to remove"))
        self.label_data.set_margin_top(12)
        self.label_data.set_hexpand(True)
        self.label_data.set_use_markup(True)
        self.label_data.set_single_line_mode(True)
        self.label_data.set_halign(Gtk.Align.CENTER)
        self.label_data.set_ellipsize(Pango.EllipsizeMode.END)

        self.label_database.set_margin_top(12)
        self.label_database.set_halign(Gtk.Align.START)
        self.label_database.set_label(_("Game's data from database"))
        self.label_database.get_style_context().add_class("dim-label")
        self.switch_database.set_margin_top(12)

        self.label_desktop.set_margin_top(12)
        self.label_desktop.set_halign(Gtk.Align.START)
        self.label_desktop.set_label(_("Desktop file"))
        self.label_desktop.get_style_context().add_class("dim-label")
        self.switch_desktop.set_margin_top(12)

        self.label_savestate.set_margin_top(12)
        self.label_savestate.set_halign(Gtk.Align.START)
        self.label_savestate.set_label(_("Save files"))
        self.label_savestate.get_style_context().add_class("dim-label")
        self.switch_savestate.set_margin_top(12)

        self.label_screenshots.set_halign(Gtk.Align.START)
        self.label_screenshots.set_label(_("Game screenshots"))
        self.label_screenshots.get_style_context().add_class("dim-label")

        self.label_memory.set_margin_top(12)
        self.label_memory.set_halign(Gtk.Align.START)
        self.label_memory.set_label(_("Memory file"))
        self.label_memory.get_style_context().add_class("dim-label")
        self.label_memory.set_no_show_all(True)
        self.switch_memory.set_margin_top(12)
        self.switch_memory.set_no_show_all(True)

        # ------------------------------------
        #   Integrate widgets
        # ------------------------------------

        self.grid_switch.attach(self.switch_database, 0, 1, 1, 1)
        self.grid_switch.attach(self.label_database, 1, 1, 1, 1)
        self.grid_switch.attach(self.switch_desktop, 0, 2, 1, 1)
        self.grid_switch.attach(self.label_desktop, 1, 2, 1, 1)
        self.grid_switch.attach(self.switch_savestate, 0, 3, 1, 1)
        self.grid_switch.attach(self.label_savestate, 1, 3, 1, 1)
        self.grid_switch.attach(self.switch_screenshots, 0, 4, 1, 1)
        self.grid_switch.attach(self.label_screenshots, 1, 4, 1, 1)
        self.grid_switch.attach(self.switch_memory, 0, 5, 1, 1)
        self.grid_switch.attach(self.label_memory, 1, 5, 1, 1)

        self.pack_start(self.label_title, False, False)
        self.pack_start(self.label_description, False, False)
        self.pack_start(self.label_data, False, False)
        self.pack_start(self.grid_switch)


    def __start_interface(self):
        """ Load data and start interface
        """

        self.add_button(_("No"), Gtk.ResponseType.NO)
        self.add_button(_("Yes"), Gtk.ResponseType.YES, Gtk.Align.END)

        self.switch_database.set_active(True)
        self.switch_desktop.set_active(True)

        # Check extension and emulator for GBA game on mednafen
        if self.game.extension.lower() == ".gba" and \
            "mednafen" in self.emulator.binary and \
            self.parent.get_mednafen_status():
            self.switch_memory.show()
            self.label_memory.show()


    def get_data(self):
        """ Retrieve data to remove from user choices

        Returns
        -------
        dict
            Data to remove
        """

        data = {
            "paths": list(),
            "database": False
        }

        # ------------------------------------
        #   Game file
        # ------------------------------------

        data["paths"].append(self.game.filepath)

        # ------------------------------------
        #   Savestates
        # ------------------------------------

        if self.switch_savestate.get_active():
            data["paths"].extend(self.emulator.get_savestates(self.game))

        # ------------------------------------
        #   Screenshots
        # ------------------------------------

        if self.switch_screenshots.get_active():
            data["paths"].extend(self.emulator.get_screenshots(self.game))

        # ------------------------------------
        #   Desktop
        # ------------------------------------

        if self.switch_desktop.get_active():
            if self.parent.check_desktop(self.game.filename):
                data["paths"].append(
                    path_join(Folders.Apps, "%s.desktop" % self.game.filename))

        # ------------------------------------
        #   Memory type
        # ------------------------------------

        if self.switch_memory.get_active():
            path = self.parent.get_mednafen_memory_type(self.game)

            if exists(path):
                data["paths"].append(path)

        # ------------------------------------
        #   Database
        # ------------------------------------

        if self.switch_database.get_active():
            data["database"] = True

        return data
