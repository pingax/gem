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
from gem.ui.widgets.widgets import PreferencesItem

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

        self.set_size(640, 480)

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
        self.entry_name.set_icon_from_icon_name(
            Gtk.EntryIconPosition.PRIMARY, Icons.Symbolic.Save)
        self.entry_name.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, Icons.Symbolic.Error)

        # ------------------------------------
        #   Optional data
        # ------------------------------------

        self.label_data = Gtk.Label()

        self.frame_options = Gtk.Frame()
        self.scroll_options = Gtk.ScrolledWindow()
        self.listbox_options = Gtk.ListBox()

        self.widget_database = PreferencesItem()
        self.switch_database = Gtk.Switch()

        self.widget_savestate = PreferencesItem()
        self.switch_savestate = Gtk.Switch()

        self.widget_screenshot = PreferencesItem()
        self.switch_screenshot = Gtk.Switch()

        self.widget_note = PreferencesItem()
        self.switch_note = Gtk.Switch()

        self.widget_memory = PreferencesItem()
        self.switch_memory = Gtk.Switch()

        # Properties
        self.label_data.set_markup(
            "<b>%s</b>" % _("Optional data to duplicate"))
        self.label_data.set_margin_top(12)
        self.label_data.set_hexpand(True)
        self.label_data.set_use_markup(True)
        self.label_data.set_single_line_mode(True)
        self.label_data.set_halign(Gtk.Align.CENTER)
        self.label_data.set_ellipsize(Pango.EllipsizeMode.END)

        self.listbox_options.set_activate_on_single_click(True)
        self.listbox_options.set_selection_mode(
            Gtk.SelectionMode.NONE)

        self.widget_database.set_widget(self.switch_database)
        self.widget_database.set_option_label(
            _("Database"))
        self.widget_database.set_description_label(
            _("Duplicate game data from database"))

        self.widget_savestate.set_widget(self.switch_savestate)
        self.widget_savestate.set_option_label(
            _("Savestates"))
        self.widget_savestate.set_description_label(
            _("Duplicate savestates files"))

        self.widget_screenshot.set_widget(self.switch_screenshot)
        self.widget_screenshot.set_option_label(
            _("Screenshots"))
        self.widget_screenshot.set_description_label(
            _("Duplicate screenshots files"))

        self.widget_note.set_widget(self.switch_note)
        self.widget_note.set_option_label(
            _("Note"))
        self.widget_note.set_description_label(
            _("Duplicate game note file"))

        self.widget_memory.set_widget(self.switch_memory)
        self.widget_memory.set_option_label(
            _("Flash memory"))
        self.widget_memory.set_description_label(
            _("Duplicate flash memory file"))

        # ------------------------------------
        #   Integrate widgets
        # ------------------------------------

        self.listbox_options.add(self.widget_database)
        self.listbox_options.add(self.widget_savestate)
        self.listbox_options.add(self.widget_screenshot)
        self.listbox_options.add(self.widget_note)

        # Check extension and emulator for GBA game on mednafen
        if self.game.extension.lower() == ".gba" and \
            "mednafen" in self.emulator.binary and \
            self.parent.get_mednafen_status():
            self.listbox_options.add(self.widget_memory)

        self.scroll_options.add(self.listbox_options)

        self.frame_options.add(self.scroll_options)

        self.pack_start(self.label_title, False, False)
        self.pack_start(self.label_name, False, False)
        self.pack_start(self.entry_name, False, False)
        self.pack_start(self.label_data, False, False)
        self.pack_start(self.frame_options)


    def __init_signals(self):
        """ Initialize widgets signals
        """

        self.entry_name.connect("changed", self.check_filename)

        self.listbox_options.connect(
            "row-activated", self.on_activate_listboxrow)


    def __start_interface(self):
        """ Load data and start interface
        """

        self.add_button(_("Cancel"), Gtk.ResponseType.CANCEL)
        self.add_button(_("Accept"), Gtk.ResponseType.APPLY, Gtk.Align.END)

        self.entry_name.set_text(self.game.filename)

        self.check_filename()


    def get_data(self):
        """ Retrieve data to duplicate from user choices

        Returns
        -------
        dict
            Data to duplicate
        """

        # Retrieve the new file name
        filename = self.entry_name.get_text()

        # Retrieve the new file path
        filepath = path_join(self.game.path[0], filename + self.game.extension)

        data = {
            "paths": list(),
            "filepath": filepath,
            "database": False
        }

        # ------------------------------------
        #   Game file
        # ------------------------------------

        data["paths"].append((self.game.filepath, filepath))

        # ------------------------------------
        #   Savestates
        # ------------------------------------

        if self.switch_savestate.get_active():
            for path in self.emulator.get_savestates(self.game):
                data["paths"].append(
                    (path, path.replace(self.game.filename, filename)))

        # ------------------------------------
        #   Screenshots
        # ------------------------------------

        if self.switch_screenshot.get_active():
            for path in self.emulator.get_screenshots(self.game):
                data["paths"].append(
                    (path, path.replace(self.game.filename, filename)))

        # ------------------------------------
        #   Notes
        # ------------------------------------

        if self.switch_note.get_active():
            path = self.parent.api.get_local(self.game.note)

            if exists(path):
                data["paths"].append((path, self.parent.api.get_local(
                    "notes", generate_identifier(filename) + ".txt")))

        # ------------------------------------
        #   Memory type
        # ------------------------------------

        if self.switch_memory.get_active():
            path = self.parent.get_mednafen_memory_type(self.game)

            if exists(path):
                data["paths"].append(
                    (path, path.replace(self.game.filename, filename)))

        # ------------------------------------
        #   Database
        # ------------------------------------

        if self.switch_database.get_active():
            data["database"] = True

        return data


    def check_filename(self, *args):
        """ Check filename in game folder to detect if a file already exists
        """

        # Retrieve the new file name
        filename = self.entry_name.get_text()

        # Retrieve the new file path
        filepath = path_join(self.game.path[0], filename + self.game.extension)

        # Check if the new filename path not exists
        if exists(filepath) or len(filename) == 0:
            self.entry_name.set_icon_from_icon_name(
                Gtk.EntryIconPosition.SECONDARY, Icons.Symbolic.Error)

            self.set_response_sensitive(Gtk.ResponseType.APPLY, False)

        else:
            self.entry_name.set_icon_from_icon_name(
                Gtk.EntryIconPosition.SECONDARY, None)

            self.set_response_sensitive(Gtk.ResponseType.APPLY, True)
