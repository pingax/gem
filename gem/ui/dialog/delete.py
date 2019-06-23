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
from gem.ui.data import Folders
from gem.ui.utils import replace_for_markup
from gem.ui.widgets.window import CommonWindow
from gem.ui.widgets.widgets import ListBoxItem

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

class DeleteDialog(CommonWindow):

    def __init__(self, parent, game):
        """ Constructor

        Parameters
        ----------
        parent : Gtk.Window
            Parent object
        game : gem.engine.game.Game
            Game object
        """

        classic_theme = False
        if parent is not None:
            classic_theme = parent.use_classic_theme

        CommonWindow.__init__(self,
                              parent,
                              _("Remove a game"),
                              Icons.Symbolic.DELETE,
                              classic_theme)

        # ------------------------------------
        #   Variables
        # ------------------------------------

        self.game = game

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
            "<span weight='bold' size='large'>%s</span>" % (
                replace_for_markup(self.game.name)))
        self.label_title.set_use_markup(True)
        self.label_title.set_halign(Gtk.Align.CENTER)
        self.label_title.set_ellipsize(Pango.EllipsizeMode.END)

        # ------------------------------------
        #   Description
        # ------------------------------------

        self.label_description = Gtk.Label()

        # Properties
        self.label_description.set_text(
            _("The following game going to be removed from your harddrive. "
              "This action is irreversible !"))
        self.label_description.set_line_wrap(True)
        self.label_description.set_max_width_chars(8)
        self.label_description.set_single_line_mode(False)
        self.label_description.set_justify(Gtk.Justification.FILL)
        self.label_description.set_line_wrap_mode(Pango.WrapMode.WORD)

        # ------------------------------------
        #   Options
        # ------------------------------------

        self.label_data = Gtk.Label()

        self.frame_options = Gtk.Frame()
        self.scroll_options = Gtk.ScrolledWindow()
        self.listbox_options = Gtk.ListBox()

        self.widget_database = ListBoxItem()
        self.switch_database = Gtk.Switch()

        self.widget_desktop = ListBoxItem()
        self.switch_desktop = Gtk.Switch()

        self.widget_savestate = ListBoxItem()
        self.switch_savestate = Gtk.Switch()

        self.widget_screenshots = ListBoxItem()
        self.switch_screenshots = Gtk.Switch()

        self.widget_cache = ListBoxItem()
        self.switch_cache = Gtk.Switch()

        self.widget_memory = ListBoxItem()
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

        self.listbox_options.set_activate_on_single_click(True)
        self.listbox_options.set_selection_mode(
            Gtk.SelectionMode.NONE)

        self.widget_database.set_widget(self.switch_database)
        self.widget_database.set_option_label(
            _("Database"))
        self.widget_database.set_description_label(
            _("Delete game data from database"))

        self.widget_desktop.set_widget(self.switch_desktop)
        self.widget_desktop.set_option_label(
            _("Menu entry"))
        self.widget_desktop.set_description_label(
            _("Delete desktop file"))

        self.widget_savestate.set_widget(self.switch_savestate)
        self.widget_savestate.set_option_label(
            _("Savestates"))
        self.widget_savestate.set_description_label(
            _("Delete savestates files"))

        self.widget_screenshots.set_widget(self.switch_screenshots)
        self.widget_screenshots.set_option_label(
            _("Screenshots"))
        self.widget_screenshots.set_description_label(
            _("Delete screenshots files"))

        self.widget_cache.set_widget(self.switch_cache)
        self.widget_cache.set_option_label(
            _("Icons cache"))
        self.widget_cache.set_description_label(
            _("Delete generated icons from cache"))

        self.widget_memory.set_widget(self.switch_memory)
        self.widget_memory.set_option_label(
            _("Flash memory"))
        self.widget_memory.set_description_label(
            _("Delete flash memory file"))

        # ------------------------------------
        #   Integrate widgets
        # ------------------------------------

        self.listbox_options.add(self.widget_database)
        self.listbox_options.add(self.widget_desktop)
        self.listbox_options.add(self.widget_cache)
        self.listbox_options.add(self.widget_savestate)
        self.listbox_options.add(self.widget_screenshots)

        if self.game.emulator is not None:

            # Check extension and emulator for GBA game on mednafen
            if self.parent.get_mednafen_status() \
               and self.game.extension == ".gba" \
               and "mednafen" in str(self.game.emulator.binary):
                self.listbox_options.add(self.widget_memory)

        self.scroll_options.add(self.listbox_options)

        self.frame_options.add(self.scroll_options)

        self.pack_start(self.label_title, False, False)
        self.pack_start(self.label_description, False, False)
        self.pack_start(self.label_data, False, False)
        self.pack_start(self.frame_options)

    def __init_signals(self):
        """ Initialize widgets signals
        """

        self.listbox_options.connect(
            "row-activated", self.on_activate_listboxrow)

    def __start_interface(self):
        """ Load data and start interface
        """

        self.add_button(_("No"), Gtk.ResponseType.NO)
        self.add_button(_("Yes"), Gtk.ResponseType.YES, Gtk.Align.END)

        self.switch_database.set_active(True)
        self.switch_desktop.set_active(True)
        self.switch_cache.set_active(True)

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

        data["paths"].append(self.game.path)

        # ------------------------------------
        #   Savestates
        # ------------------------------------

        if self.switch_savestate.get_active():
            data["paths"].extend(self.game.savestates)

        # ------------------------------------
        #   Screenshots
        # ------------------------------------

        if self.switch_screenshots.get_active():
            data["paths"].extend(self.game.screenshots)

        # ------------------------------------
        #   Desktop
        # ------------------------------------

        if self.switch_desktop.get_active():
            if self.parent.check_desktop(self.game.path):
                data["paths"].append(Folders.APPLICATIONS.joinpath(
                    "%s.desktop" % self.game.path.stem))

        # ------------------------------------
        #   Cache
        # ------------------------------------

        if self.switch_cache.get_active():

            for size in ("22x22", "96x96"):
                path = self.parent.get_icon_from_cache(
                    "games", size, "%s.png" % self.game.id)

                if path.exists():
                    data["paths"].append(path)

        # ------------------------------------
        #   Memory type
        # ------------------------------------

        if self.switch_memory.get_active():
            path = self.parent.get_mednafen_memory_type(self.game)

            if path.exists():
                data["paths"].append(path)

        # ------------------------------------
        #   Database
        # ------------------------------------

        if self.switch_database.get_active():
            data["database"] = True

        return data
