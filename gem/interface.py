# ------------------------------------------------------------------
#
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
#
# ------------------------------------------------------------------

# ------------------------------------------------------------------
#   Modules
# ------------------------------------------------------------------

# Path
from os import W_OK
from os import walk
from os import mkdir
from os import access
from os import remove
from os import listdir

from os.path import exists
from os.path import dirname
from os.path import getctime
from os.path import splitext
from os.path import basename
from os.path import expanduser
from os.path import join as path_join

from glob import glob

from shutil import copy2 as copy

from urllib.parse import urlparse
from urllib.request import url2pathname

# System
from sys import exit as sys_exit

from shlex import split as shlex_split
from shutil import move as rename
from platform import system

from datetime import datetime
from datetime import time as dtime

from subprocess import PIPE
from subprocess import Popen
from subprocess import STDOUT

# Regex
from re import match

# Threading
from threading import Thread

# Translation
from gettext import gettext as _
from gettext import textdomain
from gettext import bindtextdomain

# ------------------------------------------------------------------
#   Modules - Interface
# ------------------------------------------------------------------

try:
    from gi import require_version

    require_version("Gtk", "3.0")

    from gi.repository import Gtk
    from gi.repository import Gdk

    from gi.repository.Gdk import EventType

    from gi.repository.GLib import idle_add
    from gi.repository.GLib import timeout_add
    from gi.repository.GLib import threads_init
    from gi.repository.GLib import source_remove

    from gi.repository.GObject import MainLoop
    from gi.repository.GObject import SIGNAL_RUN_FIRST

    from gi.repository.GdkPixbuf import Pixbuf
    from gi.repository.GdkPixbuf import InterpType
    from gi.repository.GdkPixbuf import Colorspace

except ImportError as error:
    sys_exit("Cannot found python3-gobject module: %s" % str(error))

# ------------------------------------------------------------------
#   Modules - GEM
# ------------------------------------------------------------------

try:
    from gem import *
    from gem.utils import *
    from gem.windows import *
    from gem.database import Database
    from gem.preferences import Preferences
    from gem.configuration import Configuration

except ImportError as error:
    sys_exit("Cannot found gem module: %s" % str(error))

# ------------------------------------------------------------------
#   Translation
# ------------------------------------------------------------------

bindtextdomain("gem", get_data("i18n"))
textdomain("gem")

# ------------------------------------------------------------------
#   Functions
# ------------------------------------------------------------------

def launch_gem(logger, reconstruct_db=False):
    """
    Launch GEM and manage his database
    """

    # ------------------------------------
    #   Database
    # ------------------------------------

    # Connect database
    database = Database(expanduser(path_join(Path.Data, "gem.db")),
        get_data(Conf.Databases), logger)

    version = database.select("gem", "version")
    if not version == Gem.Version:
        if version is None:
            version = Gem.Version

            logger.info(_("Generate a new database"))

        else:
            logger.info(_("Update v%(old)s database to v%(new)s.") % {
                "old": version, "new": Gem.Version })

        database.modify("gem",
            { "version": Gem.Version, "codename": Gem.CodeName },
            { "version": version })

    # Migrate old databases
    if not database.check_integrity() or reconstruct_db:
        logger.warning(_("Current database need to be updated"))

        logger.info(_("Start database migration"))
        if database.select("games", '*') is not None:
            splash = Splash(len(database.select("games", '*')))

            database.migrate("games", Gem.OldColumns, splash.update)

            splash.window.destroy()

        else:
            database.migrate("games", Gem.OldColumns)

        logger.info(_("Migration complete"))

    # ------------------------------------
    #   Launch interface
    # ------------------------------------

    logger.info(_("Launch interface"))

    interface = Interface(logger, database)

# ------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------

class Interface(Gtk.Builder):

    __gsignals__ = {
        "game_close": (SIGNAL_RUN_FIRST, None, (bool, str, str, object)) }

    def __init__(self, logger, database):
        """
        Constructor
        """

        Gtk.Builder.__init__(self)

        # Load glade file
        try:
            self.add_from_file(get_data(path_join("ui", "interface.glade")))

        except OSError as error:
            logger.critical(_("Cannot open interface: %s" % error))
            sys_exit()

        # ------------------------------------
        #   Initialize variables
        # ------------------------------------

        self.title = "%s - %s (%s)" % (Gem.Name, Gem.Version, Gem.CodeName)

        self.list_thread = int()

        self.configurators = dict()
        self.available_configurators = dict()

        self.icons = dict()
        self.alternative = dict()
        self.notes = dict()
        self.threads = dict()
        self.selection = dict()
        self.shortcuts_data = dict()

        self.keys = list()

        # ------------------------------------
        #   Initialize logger
        # ------------------------------------

        self.logger = logger

        # ------------------------------------
        #   Initialize Databases
        # ------------------------------------

        self.database = database

        # ------------------------------------
        #   Initialize icons
        # ------------------------------------

        # Get user icon theme
        self.icons_theme = Gtk.IconTheme.get_default()

        self.icons_theme.append_search_path(get_data(path_join("ui", "icons")))

        self.icons_data = {
            "save": Icons.Save,
            "snap": Icons.Snap,
            "except": Icons.Except,
            "warning": Icons.Warning,
            "favorite": Icons.Favorite,
            "multiplayer": Icons.Multiplayer }

        for icon in self.icons_data.keys():
            self.icons[icon] = icon_load(self.icons_data[icon], 22)

            self.alternative[icon] = None

        # HACK: Create an empty image to avoid g_object_set_qdata warning
        self.empty = Pixbuf.new(Colorspace.RGB, True, 8, 22, 22)
        self.empty.fill(0x00000000)

        # ------------------------------------
        #   Shortcuts
        # ------------------------------------

        self.shortcuts_group = Gtk.AccelGroup()

        # ------------------------------------
        #   Targets
        # ------------------------------------

        self.targets = [ Gtk.TargetEntry.new("text/uri-list", 0, Gem.Id) ]

        # ------------------------------------
        #   Prepare interface
        # ------------------------------------

        # Init widgets
        self.__init_widgets()

        # Init signals
        self.__init_signals()

        # Start interface
        self.__start_interface()

        # ------------------------------------
        #   Main loop
        # ------------------------------------

        self.main_loop = MainLoop()
        self.main_loop.run()


    def __init_widgets(self):
        """
        Initialize interface widgets
        """

        # ------------------------------------
        #   Main window
        # ------------------------------------

        self.window = self.get_object("window")

        # Properties
        self.window.set_title(self.title)
        self.window.set_icon_name(Gem.Icon)
        self.window.set_wmclass(Gem.Acronym.upper(), Gem.Acronym.lower())

        self.window.add_accel_group(self.shortcuts_group)

        # ------------------------------------
        #   Clipboard
        # ------------------------------------

        self.clipboard = Gtk.Clipboard.get(Gdk.Atom.intern("CLIPBOARD", False))

        # ------------------------------------
        #   Headerbar
        # ------------------------------------

        self.headerbar = self.get_object("headerbar")

        self.grid_options = self.get_object("box_header_options")

        # Properties
        self.headerbar.set_title(self.title)
        self.headerbar.set_subtitle(str())

        Gtk.StyleContext.add_class(
            self.grid_options.get_style_context(), "linked")

        # ------------------------------------
        #   Toolbar items
        # ------------------------------------

        self.tool_item_launch = self.get_object("button_launch")
        self.tool_item_fullscreen = self.get_object("button_fullscreen")
        self.tool_item_parameters = self.get_object("button_arguments")
        self.tool_item_screenshots = self.get_object("button_screenshots")
        self.tool_item_output = self.get_object("button_output")
        self.tool_item_notes = self.get_object("button_notes")

        self.tool_item_properties = self.get_object("tool_properties")

        self.entry_filter = self.get_object("entry_search")

        self.tool_filter_favorite = self.get_object("tool_favorite")
        self.tool_filter_multiplayer = self.get_object("tool_multiplayer")

        # Properties
        self.tool_item_launch.set_tooltip_text(_("Launch selected game"))
        self.tool_item_fullscreen.set_tooltip_text(_("Switch fullscreen mode"))
        self.tool_item_parameters.set_tooltip_text(_("Set custom parameters"))
        self.tool_item_screenshots.set_tooltip_text(
            _("Show selected game screenshots"))
        self.tool_item_output.set_tooltip_text(
            _("Show selected game output log"))
        self.tool_item_notes.set_tooltip_text(_("Show selected game notes"))

        self.tool_item_properties.set_tooltip_text(_("Edit emulator"))

        self.tool_filter_favorite.set_tooltip_text(_("Show favorite games"))
        self.tool_filter_multiplayer.set_tooltip_text(
            _("Show multiplayer games"))

        self.entry_filter.set_placeholder_text(_("Filter"))

        # ------------------------------------
        #   Menu
        # ------------------------------------

        self.menu_item_launch = self.get_object("menu_games_launch")
        self.menu_item_favorite = self.get_object("menu_games_favorite")
        self.menu_item_multiplayer = self.get_object("menu_games_multiplayer")
        self.menu_item_screenshots = self.get_object("menu_games_screenshots")
        self.menu_item_output = self.get_object("menu_games_log")
        self.menu_item_notes = self.get_object("menu_games_notes")
        self.menu_item_edit = self.get_object("menu_games_edit")

        self.menu_item_rename = self.get_object("menu_games_rename")
        self.menu_item_parameters = self.get_object("menu_games_parameters")
        self.menu_item_copy = self.get_object("menu_games_copy")
        self.menu_item_open = self.get_object("menu_games_open")
        self.menu_item_desktop = self.get_object("menu_games_desktop")
        self.menu_item_remove = self.get_object("menu_games_remove")
        self.menu_item_database = self.get_object("menu_games_database")

        self.menu_item_preferences = self.get_object("menu_preferences")
        self.menu_item_gem_log = self.get_object("menu_log")
        self.menu_item_dark_theme = self.get_object("menu_dark_theme")
        self.menu_item_about = self.get_object("menu_about")
        self.menu_item_quit = self.get_object("menu_quit")

        # Properties
        self.menu_item_launch.set_label(_("_Launch"))
        self.menu_item_favorite.set_label(_("Mark as _favorite"))
        self.menu_item_multiplayer.set_label(_("Mark as _multiplayer"))
        self.menu_item_screenshots.set_label(_("_Screenshots"))
        self.menu_item_output.set_label(_("Output _log"))
        self.menu_item_notes.set_label(_("_Notes"))
        self.menu_item_edit.set_label(_("_Edit"))

        self.menu_item_rename.set_label(_("_Rename"))
        self.menu_item_parameters.set_label(_("Custom _parameters"))
        self.menu_item_copy.set_label(_("_Copy file path"))
        self.menu_item_open.set_label(_("_Open file path"))
        self.menu_item_desktop.set_label(_("_Generate a menu entry"))
        self.menu_item_database.set_label(_("_Reset game informations"))
        self.menu_item_remove.set_label(_("_Remove game from disk"))

        self.menu_item_preferences.set_label(_("_Preferences"))
        self.menu_item_gem_log.set_label(_("Show main _log"))
        self.menu_item_dark_theme.set_label(_("Use dark theme"))
        self.menu_item_about.set_label(_("_About"))
        self.menu_item_quit.set_label(_("_Quit"))

        # ------------------------------------
        #   Consoles
        # ------------------------------------

        self.model_consoles = self.get_object("store_consoles")
        self.combo_consoles = self.get_object("combo_consoles")

        # Properties
        self.model_consoles.set_sort_column_id(1, Gtk.SortType.ASCENDING)

        # ------------------------------------
        #   Games
        # ------------------------------------

        self.model_games = self.get_object("store_games")
        self.treeview_games = self.get_object("treeview_games")

        self.filter_games = self.model_games.filter_new()

        self.column_game_name = self.get_object("column_games_name")
        self.column_game_play = self.get_object("column_games_played")
        self.column_game_last_play = self.get_object("column_games_last_played")
        self.column_game_play_time = self.get_object("column_games_time_played")
        self.column_game_installed = self.get_object("column_games_installed")
        self.column_game_flags = self.get_object("column_games_flags")

        cell_game_play = self.get_object("cell_games_play")
        self.cell_games_last_date = self.get_object("cell_games_last_date")
        cell_game_play_time = self.get_object("cell_games_play_time")
        cell_game_installed = self.get_object("cell_games_installed")

        # Properties
        self.model_games.set_sort_column_id(2, Gtk.SortType.ASCENDING)

        self.treeview_games.set_model(self.filter_games)
        self.treeview_games.set_has_tooltip(True)

        self.treeview_games.drag_source_set(
            Gdk.ModifierType.BUTTON1_MASK, self.targets, Gdk.DragAction.COPY)

        self.treeview_games.drag_dest_set(
            Gtk.DestDefaults.MOTION | Gtk.DestDefaults.DROP, self.targets,
            Gdk.DragAction.COPY)

        self.column_game_name.set_title(_("Name"))
        self.column_game_play.set_title(_("Launch"))
        self.column_game_last_play.set_title(_("Last launch"))
        self.column_game_play_time.set_title(_("Play time"))
        self.column_game_installed.set_title(_("Installed"))
        self.column_game_flags.set_title(_("Flags"))

        cell_game_play.set_alignment(.5, .5)
        cell_game_play_time.set_alignment(.5, .5)
        cell_game_installed.set_alignment(.5, .5)

        # ------------------------------------
        #   Games - Menu
        # ------------------------------------

        self.menu_games = self.get_object("menu_games")

        # ------------------------------------
        #   Statusbar
        # ------------------------------------

        self.statusbar = self.get_object("statusbar")

        # Properties
        self.statusbar.set_no_show_all(True)


    def __init_signals(self):
        """
        Initialize widgets signals
        """

        # ------------------------------------
        #   Window
        # ------------------------------------

        self.window.connect(
            "delete-event", self.__stop_interface)
        self.window.connect(
            "key-press-event", self.__on_manage_keys)

        # ------------------------------------
        #   Toolbar
        # ------------------------------------

        self.tool_item_launch.connect(
            "clicked", self.__on_game_launch)
        self.tool_item_fullscreen.connect(
            "toggled", self.__on_activate_fullscreen)
        self.tool_item_screenshots.connect(
            "clicked", self.__on_show_viewer)
        self.tool_item_output.connect(
            "clicked", self.__on_show_log)
        self.tool_item_notes.connect(
            "clicked", self.__on_show_notes)
        self.tool_item_parameters.connect(
            "clicked", self.__on_game_parameters)

        self.tool_item_properties.connect(
            "clicked", self.__on_show_emulator_config)

        self.entry_filter.connect(
            "icon-press", on_entry_clear)
        self.entry_filter.connect(
            "changed", self.filters_update)

        self.tool_filter_favorite.connect(
            "clicked", self.filters_update)
        self.tool_filter_multiplayer.connect(
            "clicked", self.filters_update)

        # ------------------------------------
        #   Menu
        # ------------------------------------

        self.menu_item_launch.connect(
            "activate", self.__on_game_launch)
        self.menu_item_favorite.connect(
            "activate", self.__on_game_marked_as_favorite)
        self.menu_item_multiplayer.connect(
            "activate", self.__on_game_marked_as_multiplayer)
        self.menu_item_screenshots.connect(
            "activate", self.__on_show_viewer)
        self.menu_item_output.connect(
            "activate", self.__on_show_log)
        self.menu_item_notes.connect(
            "activate", self.__on_show_notes)

        self.menu_item_rename.connect(
            "activate", self.__on_game_renamed)
        self.menu_item_parameters.connect(
            "activate", self.__on_game_parameters)
        self.menu_item_copy.connect(
            "activate", self.__on_game_copy)
        self.menu_item_open.connect(
            "activate", self.__on_game_open)
        self.menu_item_desktop.connect(
            "activate", self.__on_game_generate_desktop)
        self.menu_item_database.connect(
            "activate", self.__on_game_clean)
        self.menu_item_remove.connect(
            "activate", self.__on_game_removed)

        self.menu_item_preferences.connect(
            "activate", Preferences, self, self.logger)
        self.menu_item_gem_log.connect(
            "activate", self.__on_show_log)
        self.dark_theme_signal = self.menu_item_dark_theme.connect(
            "toggled", self.__on_activate_dark_theme)
        self.menu_item_about.connect(
            "activate", self.__on_show_about)
        self.menu_item_quit.connect(
            "activate", self.__stop_interface)

        # ------------------------------------
        #   Consoles
        # ------------------------------------

        self.combo_consoles.connect(
            "changed", self.__on_selected_console)

        # ------------------------------------
        #   Games
        # ------------------------------------

        self.treeview_games.connect(
            "button-press-event", self.__on_selected_game)
        self.treeview_games.connect(
            "key-release-event", self.__on_selected_game)

        self.treeview_games.connect(
            "button-press-event", self.__on_menu_show)
        self.treeview_games.connect(
            "key-release-event", self.__on_menu_show)

        self.treeview_games.connect(
            "drag-data-get", self.__on_dnd_send_data)
        self.treeview_games.connect(
            "drag-data-received", self.__on_dnd_received_data)


        self.filter_games.set_visible_func(self.filters_match)


    def __start_interface(self):
        """
        Load data and start interface
        """

        self.load_interface()

        if self.config.getboolean("gem", "load_console_startup", fallback=True):
            console = self.config.item("gem", "last_console", str())
            if len(console) > 0:
                for row in self.model_consoles:
                    if row[1] == console:
                        self.treeview_games.set_visible(True)
                        self.combo_consoles.set_active_iter(row.iter)

                        self.selection["console"] = console

                        break

        if self.config.getboolean("gem", "welcome", fallback=True):
            dialog = Message(self, _("Welcome !"), _("Welcome and thanks for "
                "choosing GEM as emulators manager. Start using GEM by "
                "droping some roms into interface.\n\nEnjoy and have fun :D"),
                "face-smile-big", False)

            dialog.set_size_request(500, -1)

            dialog.run()
            dialog.destroy()

            self.config.modify("gem", "welcome", 0)
            self.config.update()


    def __stop_interface(self, widget=None, event=None):
        """
        Save data and stop interface

        :param Gtk.Widget widget:
        :param Gdk.Event event:
        """

        # ------------------------------------
        #   Threads
        # ------------------------------------

        if not self.list_thread == 0:
            source_remove(self.list_thread)

        if len(self.threads.keys()) > 0:
            for thread in self.threads.copy().keys():
                self.threads[thread].terminate()

        # ------------------------------------
        #   Notes
        # ------------------------------------

        if len(self.notes.keys()) > 0:
            for dialog in self.notes.copy().keys():
                self.notes[dialog].response(Gtk.ResponseType.APPLY)

        # ------------------------------------
        #   Last console
        # ------------------------------------

        row = self.combo_consoles.get_active_iter()
        if row is not None:
            console = self.model_consoles.get_value(row, 1)

            last_console = self.config.item("gem", "last_console", None)
            if last_console is None or not last_console == console:
                self.config.modify("gem", "last_console", console)
                self.config.update()

                self.logger.info(_("Save %s for next startup") % console)

        self.logger.info(_("Close interface"))

        # Gtk.main_quit()
        self.main_loop.quit()


    def load_interface(self):
        """
        Load main interface
        """

        # ------------------------------------
        #   Configuration
        # ------------------------------------

        self.config = Configuration(
            expanduser(path_join(Path.User, "gem.conf")))
        self.config.add_missing_data(get_data(Conf.Default))

        self.emulators = Configuration(
            expanduser(path_join(Path.User, "emulators.conf")))

        self.consoles = Configuration(
            expanduser(path_join(Path.User, "consoles.conf")))

        # ------------------------------------
        #   Shortcuts
        # ------------------------------------

        self.__init_shortcuts()

        # ------------------------------------
        #   Theme
        # ------------------------------------

        # Block signal to avoid stack overflow when toggled
        self.menu_item_dark_theme.handler_block(self.dark_theme_signal)

        dark_theme_status = self.config.getboolean(
            "gem", "dark_theme", fallback=False)

        on_change_theme(dark_theme_status)

        self.menu_item_dark_theme.set_active(dark_theme_status)

        # Unblock signal
        self.menu_item_dark_theme.handler_unblock(self.dark_theme_signal)

        # ------------------------------------
        #   Icons
        # ------------------------------------

        icon = self.alternative["save"]

        status = self.config.getboolean(
            "gem", "use_translucent_icons", fallback=False)

        if icon is None or (icon == self.empty and status) or (
            not icon == self.empty and not status):

            for icon in self.icons_data.keys():
                if status:
                    self.alternative[icon] = set_pixbuf_opacity(
                        self.icons[icon], 50)

                else:
                    self.alternative[icon] = self.empty

        # ------------------------------------
        #   Widgets
        # ------------------------------------

        self.window.show_all()
        self.menu_games.show_all()

        self.statusbar.hide()

        self.sensitive_interface()

        # ------------------------------------
        #   Header
        # ------------------------------------

        if not self.config.getboolean("gem", "show_header", fallback=True):
            self.headerbar.set_show_close_button(False)
        else:
            self.headerbar.set_show_close_button(True)

        # ------------------------------------
        #   Consoles
        # ------------------------------------

        current_console = self.append_consoles()

        # ------------------------------------
        #   Variables
        # ------------------------------------

        self.selection = dict(console=None, game=None, name=None)

        # ------------------------------------
        #   Games
        # ------------------------------------

        # Games - Treeview
        lines = {
            "none": Gtk.TreeViewGridLines.NONE,
            "horizontal": Gtk.TreeViewGridLines.HORIZONTAL,
            "vertical": Gtk.TreeViewGridLines.VERTICAL,
            "both": Gtk.TreeViewGridLines.BOTH }

        if self.config.item("gem", "games_treeview_lines", "none") in lines:
            self.treeview_games.set_grid_lines(
                lines[self.config.item("gem", "games_treeview_lines", "none")])

        # Games - Treeview columns
        columns = {
            "play": self.column_game_play,
            "last_play": self.column_game_last_play,
            "play_time": self.column_game_play_time,
            "installed": self.column_game_installed,
            "flags": self.column_game_flags }

        for key, widget in columns.items():
            if not self.config.getboolean("columns", key, fallback=True):
                widget.set_visible(False)
            else:
                widget.set_visible(True)

        if current_console is None:
            self.model_games.clear()

        else:
            self.combo_consoles.set_active_iter(current_console)


    def sensitive_interface(self, status=False):
        """
        Set a sensitive status for specific widgets
        """

        self.menu_item_rename.set_sensitive(status)
        self.menu_item_favorite.set_sensitive(status)
        self.menu_item_multiplayer.set_sensitive(status)
        self.menu_item_screenshots.set_sensitive(status)
        self.menu_item_output.set_sensitive(status)
        self.menu_item_notes.set_sensitive(status)
        self.menu_item_copy.set_sensitive(status)
        self.menu_item_open.set_sensitive(status)
        self.menu_item_desktop.set_sensitive(status)
        self.menu_item_remove.set_sensitive(status)
        self.menu_item_database.set_sensitive(status)

        self.tool_item_launch.set_sensitive(status)
        self.tool_item_output.set_sensitive(status)
        self.tool_item_notes.set_sensitive(status)
        self.tool_item_parameters.set_sensitive(status)
        self.tool_item_screenshots.set_sensitive(status)


    def filters_update(self, widget=None):
        """
        Reload packages filter when user change filters from menu
        """

        self.filter_games.refilter()

        self.check_selection()


    def filters_match(self, model, row, data=None):
        """
        Update treeview filter
        """

        data_favorite = model.get_value(row, Columns.Favorite)
        flag_favorite = self.tool_filter_favorite.get_active()

        data_multiplayer = model.get_value(row, Columns.Multiplayer)
        flag_multiplayer = self.tool_filter_multiplayer.get_active()

        icon = self.alternative["multiplayer"]

        try:
            name = model.get_value(row, Columns.Name)
            if name is not None:
                text = self.entry_filter.get_text()

                found = False
                if len(text) == 0 or match("%s$" % text, name) is not None or \
                    text.lower() in name.lower():
                    found = True

                # No flag
                if not flag_favorite and not flag_multiplayer and found:
                    return True

                # Only favorite flag
                if flag_favorite and data_favorite and not flag_multiplayer and \
                    found:
                    return True

                # Only multiplayer flag
                if flag_multiplayer and not data_multiplayer == icon and \
                    not flag_favorite and found:
                    return True

                # Both favorite and multiplayer flags
                if flag_favorite and data_favorite and flag_multiplayer and \
                    not data_multiplayer == icon and found:
                    return True

        except:
            pass

        return False


    def __init_shortcuts(self):
        """
        Generate shortcuts signals from user configuration
        """

        shortcuts = {
            self.menu_item_open:
                self.config.item("keys", "open", "<Control>O"),
            self.menu_item_copy:
                self.config.item("keys", "copy", "<Control>C"),
            self.menu_item_desktop:
                self.config.item("keys", "desktop", "<Control>G"),
            self.menu_item_launch:
                self.config.item("keys", "start", "Return"),
            self.tool_item_launch:
                self.config.item("keys", "start", "Return"),
            self.menu_item_rename:
                self.config.item("keys", "rename", "F2"),
            self.menu_item_favorite:
                self.config.item("keys", "favorite", "F3"),
            self.menu_item_multiplayer:
                self.config.item("keys", "multiplayer", "F4"),
            self.tool_item_screenshots:
                self.config.item("keys", "snapshots", "F5"),
            self.menu_item_screenshots:
                self.config.item("keys", "snapshots", "F5"),
            self.menu_item_output:
                self.config.item("keys", "log", "F6"),
            self.menu_item_notes:
                self.config.item("keys", "notes", "F7"),
            self.tool_item_parameters:
                self.config.item("keys", "exceptions", "F12"),
            self.menu_item_parameters:
                self.config.item("keys", "exceptions", "F12"),
            self.menu_item_remove:
                self.config.item("keys", "delete", "<Control>Delete"),
            self.menu_item_database:
                self.config.item("keys", "remove", "Delete"),
            self.menu_item_preferences:
                self.config.item("keys", "preferences", "<Control>P"),
            self.menu_item_gem_log:
                self.config.item("keys", "gem", "<Control>L"),
            self.menu_item_quit:
                self.config.item("keys", "quit", "<Control>Q") }

        for widget in shortcuts.keys():
            key, mod = Gtk.accelerator_parse(shortcuts[widget])

            if Gtk.accelerator_valid(key, mod):

                if self.shortcuts_data.get(widget) is not None:
                    old_key, old_mod = self.shortcuts_data.get(widget)

                    widget.remove_accelerator(
                        self.shortcuts_group, old_key, old_mod)

                if type(widget) == Gtk.Entry:
                    widget.add_accelerator("grab_focus",
                        self.shortcuts_group, key, mod, Gtk.AccelFlags.MASK)

                elif type(widget) == Gtk.ToolButton:
                    widget.add_accelerator("clicked",
                        self.shortcuts_group, key, mod, Gtk.AccelFlags.VISIBLE)

                else:
                    widget.add_accelerator("activate",
                        self.shortcuts_group, key, mod, Gtk.AccelFlags.VISIBLE)

                self.shortcuts_data[widget] = [key, mod]


    def __on_manage_keys(self, widget, event):
        """
        Manage widgets for specific keymaps
        """

        if event.keyval == Gdk.KEY_F11:
            self.tool_item_fullscreen.set_active(
                not self.tool_item_fullscreen.get_active())

        # Give me more lifes, powerups or cookies konami code, I need more
        konami_code = [Gdk.KEY_Up, Gdk.KEY_Up, Gdk.KEY_Down, Gdk.KEY_Down,
            Gdk.KEY_Left, Gdk.KEY_Right, Gdk.KEY_Left, Gdk.KEY_Right]

        if event.keyval in konami_code:
            self.keys.append(event.keyval)

            if self.keys == konami_code:
                dialog = Message(self, "Someone wrote the KONAMI CODE !",
                    "Nice catch ! You have discover an easter-egg ! But, this "
                    "kind of code is usefull in a game, not in an emulators "
                    "manager !", "face-monkey")

                dialog.set_size_request(500, -1)

                dialog.run()
                dialog.destroy()

                self.keys = list()

            if not self.keys == konami_code[0:len(self.keys)]:
                self.keys = list()


    def set_informations(self):
        """
        Update text from headerbar
        """

        texts = str()

        if(len(self.model_games) == 1):
            texts = [_("1 game available")]
        elif(len(self.model_games) > 1):
            texts = [_("%s games availables") % len(self.model_games)]

        if self.selection["name"] is not None:
            texts.append(self.selection["name"])
        elif self.selection["game"] is not None:
            texts.append(basename(self.selection["game"]))

        self.headerbar.set_subtitle(" - ".join(texts))


    def set_message(self, title, message, icon="dialog-error"):
        """
        Show a dialog when an error occur.
        """

        if icon == "dialog-error":
            self.logger.error(message)
        elif icon == "dialog-warning":
            self.logger.warning(message)
        else:
            self.logger.info(message)

        dialog = Message(self, title, message, icon)

        dialog.run()
        dialog.destroy()


    def __on_show_about(self, widget=None, event=None):
        """
        Show about window
        """

        about = Gtk.AboutDialog()

        about.set_transient_for(self.window)

        about.set_program_name(Gem.Name)
        about.set_version("%s (%s)" % (Gem.Version, Gem.CodeName))
        about.set_logo_icon_name(Gem.Icon)

        about.set_authors([
            "PacMiam (Lubert Aurélien)" ])
        about.set_artists([
            "Tango projects - GPLv3",
            "Gelide projects - GPLv3",
            "Evan-Amos - CC-by-SA 3.0" ])
        about.set_translator_credits(_("translator-credits"))

        about.set_website(Gem.Website)
        about.set_comments(Gem.Description)
        about.set_copyright(Gem.Copyleft)

        about.set_license_type(Gtk.License.GPL_3_0)

        about.run()
        about.destroy()


    def __on_show_viewer(self, widget):
        """
        Show game's screenshots with native or specified viewer
        """

        viewer = self.config.get("viewer", "binary")
        args = self.config.item("viewer", "options")

        # Get rom name without extension
        gamename, ext = splitext(basename(self.selection["game"]))

        # Get rom data from database
        data = self.database.get("games",
            { "filename": basename(self.selection["game"]) })

        # Get rom specified emulator
        emulator = self.consoles.get(self.selection["console"], "emulator")

        if data is not None and len(data.get("emulator")) > 0:
            if self.emulators.has_section(data.get("emulator")):
                emulator = data.get("emulator")

        # Check if rom has some screenshots
        if self.check_screenshots(emulator, gamename):
            snaps_path = expanduser(self.emulators.get(emulator, "snaps"))

            if "<lname>" in snaps_path:
                path = glob(
                    snaps_path.replace("<lname>", gamename).lower())
            else:
                path = glob(snaps_path.replace("<name>", gamename))

            # ----------------------------
            #   Show screenshots viewer
            # ----------------------------

            title = gamename
            if self.selection["name"] is not None:
                title = self.selection["name"]

            title = "%s (%s)" % (title, self.selection["console"])

            if self.config.getboolean("viewer", "native", fallback=True):
                DialogViewer(self, title, sorted(path))

            elif exists(viewer):
                command = list()

                # Append binaries
                command.extend(shlex_split(viewer))

                # Append arguments
                if args is not None:
                    command.extend(shlex_split(args))

                # Append game file
                command.extend(sorted(path))

                process = Popen(command)
                process.wait()

            else:
                self.set_message(_("Missing binary"),
                    _("Cannot find <b>%s</b> viewer !" % viewer),
                    "dialog-warning")

            # ----------------------------
            #   Check snapshots
            # ----------------------------

            if not self.check_screenshots(emulator, gamename):
                self.set_game_data(
                    Columns.Snapshots, self.alternative["snap"], gamename)


    def __on_show_log(self, widget):
        """
        Show game's log
        """

        if widget == self.menu_item_gem_log:
            path = path_join(Path.Data, "gem.log")

            title = _("GEM")

        else:
            path = self.check_log()

            title = basename(self.selection["game"])
            if self.selection["name"] is not None:
                title = self.selection["name"]

        if path is not None and exists(expanduser(path)):
            dialog = DialogEditor(
                self, title, expanduser(path), False, Icons.Output)

            dialog.run()
            dialog.destroy()


    def __on_show_notes(self, widget):
        """
        Show game's notes
        """

        path = path_join(expanduser(Path.Notes),
            "%s.txt" % basename(self.selection["game"]))

        title = basename(self.selection["game"])
        if self.selection["name"] is not None:
            title = self.selection["name"]

        if path is not None and not expanduser(path) in self.notes.keys():
            dialog = DialogEditor(
                self, title, expanduser(path), icon="emblem-documents")

            # Allow to launch games with open notes
            dialog.set_modal(False)

            dialog.connect("response", self.__on_show_notes_response,
                title, expanduser(path))

            dialog.show()

            # Save dialogs to close it properly when gem terminate and avoid to
            # reopen existing one
            self.notes[expanduser(path)] = dialog

        elif expanduser(path) in self.notes.keys():
            self.notes[expanduser(path)].grab_focus()


    def __on_show_notes_response(self, dialog, response, title, path):
        """
        Close game's note and save buffer to correct file
        """

        if response == Gtk.ResponseType.APPLY:
            text_buffer = dialog.buffer_editor.get_text(
                dialog.buffer_editor.get_start_iter(),
                dialog.buffer_editor.get_end_iter(), True)

            if len(text_buffer) > 0:
                with open(path, 'w') as pipe:
                    pipe.write(text_buffer)

                self.logger.info(_("Update %s notes") % title)

        dialog.destroy()

        if path in self.notes.keys():
            del self.notes[path]


    def __on_show_emulator_config(self, widget):
        """
        Show emulator's configuration file
        """

        if self.selection["console"] is not None:
            emulator = self.consoles.get(self.selection["console"], "emulator")

            if self.selection["game"] is not None:
                data = self.database.get("games",
                    { "filename": basename(self.selection["game"]) })

                if data is not None and len(data.get("emulator")) > 0:
                    if self.emulators.has_section(data.get("emulator")):
                        emulator = data.get("emulator")

            if self.emulators.has_option(emulator, "configuration"):
                path = self.emulators.get(emulator, "configuration")

                if path is not None and exists(expanduser(path)):
                    dialog = DialogEditor(self,
                        _("Configuration for %s") % emulator, expanduser(path))

                    response = dialog.run()

                    if response == Gtk.ResponseType.APPLY:
                        with open(path, 'w') as pipe:
                            pipe.write(dialog.buffer_editor.get_text(
                                dialog.buffer_editor.get_start_iter(),
                                dialog.buffer_editor.get_end_iter(), True))

                        self.logger.info(
                            _("Update %s configuration file") % emulator)

                    dialog.destroy()


    def append_consoles(self):
        """
        Append user's consoles into combobox.

        :return: Selected row
        :rtype: Gtk.TreeIter or None
        """

        item = None

        self.model_consoles.clear()

        for console in self.consoles.sections():

            if self.consoles.has_option(console, "emulator"):
                emulator = self.consoles.get(console, "emulator")

                # Check if console ROM path exist
                path = self.consoles.item(console, "roms")
                if path is not None and exists(expanduser(path)):
                    status = self.empty

                    # Check if current emulator can be launched
                    binary = self.emulators.item(emulator, "binary")
                    if binary is None or len(get_binary_path(binary)) == 0:
                        status = self.icons["warning"]

                        self.logger.warning(
                            _("Cannot find %(binary)s for %(console)s" % dict(
                            binary=binary, console=console)))

                    icon = icon_from_data(self.consoles.item(
                        console, "icon"), self.empty, subfolder="consoles")

                    row = self.model_consoles.append([icon, console, status])

                    if self.selection.get("console") is not None and \
                        self.selection.get("console") == console:
                        item = row

        return item


    def __on_selected_console(self, widget=None):
        """
        Select a console in combobox and append console's games
        """

        self.selection["name"] = None
        self.selection["game"] = None

        self.set_informations()

        error = False

        treeiter = self.combo_consoles.get_active_iter()
        if treeiter is not None:

            console = self.model_consoles.get_value(treeiter, 1)
            if console is not None:

                self.selection["console"] = console

                # ------------------------------------
                #   Check emulator
                # ------------------------------------

                if not self.consoles.has_option(console, "emulator"):
                    message = _("Cannot find emulator for %s") % console
                    error = True

                emulator = self.consoles.get(console, "emulator")

                # Check emulator data
                if not self.emulators.has_section(emulator):
                    message = _("%s emulator not exist !") % (emulator)
                    error = True

                # ------------------------------------
                #   Set sensistive widgets
                # ------------------------------------

                self.sensitive_interface()

                # Check emulator configurator
                configuration = self.emulators.item(emulator, "configuration")

                if configuration is not None and \
                    exists(expanduser(configuration)):
                    self.tool_item_properties.set_sensitive(True)

                else:
                    self.tool_item_properties.set_sensitive(False)

                # ------------------------------------
                #   Load game list
                # ------------------------------------

                if error:
                    self.model_games.clear()
                    self.filter_games.refilter()

                    self.set_message(console, message)

                else:
                    if not self.list_thread == 0:
                        source_remove(self.list_thread)

                    loader = self.append_games(console)
                    self.list_thread = idle_add(loader.__next__)

                    self.selection["game"] = None


    def append_games(self, console):
        """
        Append games from console to treeview

        :param str console: Console key
        """

        iteration = int()

        # Get current thread id
        current_thread_id = self.list_thread

        self.game_path = dict()

        # ------------------------------------
        #   Load data
        # ------------------------------------

        self.model_games.clear()

        games_path = expanduser(self.consoles.get(console, "roms"))

        if exists(games_path) and access(games_path, W_OK):
            games_list = list()

            for root, dirnames, filenames in walk(games_path):
                for path in filenames:
                    games_list.append(path_join(root, path))

            sorted(games_list)

            # ------------------------------------
            #   Refresh treeview
            # ------------------------------------

            self.treeview_games.set_enable_search(False)
            self.treeview_games.freeze_child_notify()

            # ------------------------------------
            #   Load games
            # ------------------------------------

            emulator = self.consoles.get(console, "emulator")

            for game in games_list:

                # Another thread has been called by user, close this one
                if not current_thread_id == self.list_thread:
                    yield False

                if '.' in basename(game):
                    filename, ext = splitext(basename(game))

                    # Remove dot from extension
                    ext = ext.split('.')[-1]

                    # Get extensions list for current console
                    ext_list = self.consoles.get(console, "exts").split(';')

                    # Check lowercase extensions
                    if ext in ext_list or ext.lower() in ext_list:
                        row_data = [
                            False,          # Favorite status
                            self.alternative["favorite"],
                            filename,       # File name
                            str(),          # Play number
                            str(),          # Last play date
                            str(),          # Last play time
                            str(),          # Total play time
                            str(),          # Installed date
                            self.alternative["except"],
                            self.alternative["snap"],
                            self.alternative["multiplayer"],
                            self.alternative["save"],
                            filename ]      # Filename without extension

                        # Get values from database
                        data = self.database.get("games",
                            { "filename": basename(game) })

                        # Get global emulator
                        rom_emulator = emulator

                        # Set specified emulator is available
                        if data is not None and len(data.get("emulator")) > 0:
                            if self.emulators.has_section(data.get("emulator")):
                                rom_emulator = data.get("emulator")

                        if data is not None:

                            # Favorite
                            if bool(data["favorite"]):
                                row_data[Columns.Favorite] = True
                                row_data[Columns.Icon] = self.icons["favorite"]

                            # Custom name
                            if len(data["name"]) > 0:
                                row_data[Columns.Name] = data["name"]

                            # Played
                            if data["play"] > 0:
                                row_data[Columns.Played] = str(data["play"])

                            # Last time
                            if len(data["last_play"]) > 0:
                                row_data[Columns.LastPlay] = str(
                                    string_from_date(data["last_play"]))

                            # Last play time
                            if len(data["last_play_time"]) > 0:
                                row_data[Columns.LastTimePlay] = str(
                                    string_from_time(data["last_play_time"]))

                            # Play time
                            if len(data["play_time"]) > 0:
                                row_data[Columns.TimePlay] = str(
                                    string_from_time(data["play_time"]))

                            # Exception
                            if data["arguments"] is not None and \
                                len(data["arguments"]) > 0:
                                row_data[Columns.Except] = self.icons["except"]

                            elif data["emulator"] is not None and \
                                len(data["emulator"]) > 0 and \
                                not data["emulator"] == emulator:
                                row_data[Columns.Except] = self.icons["except"]

                            # Multiplayer
                            if bool(data["multiplayer"]):
                                row_data[Columns.Multiplayer] = \
                                    self.icons["multiplayer"]

                        # Installed time
                        row_data[Columns.Installed] = string_from_date(
                            datetime.fromtimestamp(
                            getctime(game)).strftime("%d-%m-%Y %H:%M:%S"))

                        # Snap
                        if self.check_screenshots(rom_emulator, filename):
                            row_data[Columns.Snapshots] = self.icons["snap"]

                        # Save state
                        if self.check_save_states(rom_emulator, filename):
                            row_data[Columns.Save] = self.icons["save"]

                        row = self.model_games.append(row_data)

                        self.game_path[filename] = [game, row]

                        iteration += 1
                        if (iteration % 20 == 0):
                            self.set_informations()

                            self.treeview_games.thaw_child_notify()
                            yield True
                            self.treeview_games.freeze_child_notify()

            # Restore options for packages treeviews
            self.treeview_games.set_enable_search(True)
            self.treeview_games.thaw_child_notify()

        self.set_informations()

        # ------------------------------------
        #   Cannot read games path
        # ------------------------------------

        if not access(games_path, W_OK):
            pass

        # ------------------------------------
        #   Close thread
        # ------------------------------------

        self.list_thread = int()

        yield False


    def __on_selected_game(self, treeview, event):
        """
        Select a game in games treeview
        """

        filename, name, snap, run_game = None, None, None, None

        # Keyboard
        if event.type == EventType.KEY_RELEASE:
            model, treeiter = treeview.get_selection().get_selected()

            if treeiter is not None:
                name = model.get_value(treeiter, Columns.Name)
                filename = model.get_value(treeiter, Columns.Filename)

                if event.keyval == Gdk.KEY_Return:
                    run_game = True

        # Mouse
        elif (event.type in [EventType.BUTTON_PRESS, EventType._2BUTTON_PRESS]) \
            and (event.button == 1 or event.button == 3):

            selection = treeview.get_path_at_pos(int(event.x), int(event.y))
            if selection is not None:
                model = treeview.get_model()

                treeiter = model.get_iter(selection[0])
                name = model.get_value(treeiter, Columns.Name)
                filename = model.get_value(treeiter, Columns.Filename)

                if event.button == 1 and event.type == EventType._2BUTTON_PRESS:
                    run_game = True

        # ----------------------------
        #   Game selected
        # ----------------------------

        if filename is not None:
            self.selection["name"] = name
            self.selection["game"] = self.game_path[filename][0]

            self.sensitive_interface(True)

            # ----------------------------
            #   Game data
            # ----------------------------

            if splitext(filename)[0] in self.threads:
                self.tool_item_launch.set_sensitive(False)
                self.tool_item_parameters.set_sensitive(False)
                self.tool_item_output.set_sensitive(False)
                self.menu_item_launch.set_sensitive(False)
                self.menu_item_output.set_sensitive(False)
                self.menu_item_parameters.set_sensitive(False)
                self.menu_item_database.set_sensitive(False)
                self.menu_item_remove.set_sensitive(False)
                self.menu_item_rename.set_sensitive(False)

            iter_snaps = model.get_value(treeiter, Columns.Snapshots)

            # Check snaps icon to avoid to check screenshots again
            if iter_snaps == self.alternative["snap"]:
                self.tool_item_screenshots.set_sensitive(False)
                self.menu_item_screenshots.set_sensitive(False)

            if self.check_log() is None:
                self.tool_item_output.set_sensitive(False)
                self.menu_item_output.set_sensitive(False)

            if run_game:
                self.__on_game_launch()

        self.set_informations()


    def check_selection(self):
        """
        Check if selected game is the good game
        """

        name = None

        if self.selection["name"] is not None:
            name = self.selection["name"]

        elif self.selection["game"] is not None:
            name = splitext(basename(self.selection["game"]))[0]

        if name is not None:
            model, treeiter = self.treeview_games.get_selection().get_selected()

            if treeiter is not None:
                treeview_name = model.get_value(treeiter, Columns.Name)

                if not treeview_name == name:
                    self.treeview_games.get_selection().unselect_iter(treeiter)
                    self.selection["game"] = None
                    self.selection["name"] = None

                    self.sensitive_interface()
                    self.set_informations()

                    return False

        return True


    def __on_game_launch(self, widget=None):
        """
        Start a game
        """

        binary = str()

        if self.selection["game"] is None:
            return

        filename = basename(self.selection["game"])
        game = self.database.get("games", { "filename": filename })

        # ----------------------------
        #   Check selection
        # ----------------------------

        if not self.check_selection():
            return

        if splitext(filename)[0] in self.threads:
            return

        # ----------------------------
        #   Check emulator
        # ----------------------------

        console = self.selection["console"]

        emulator = self.consoles.get(console, "emulator")
        if game is not None and len(game.get("emulator")) > 0:
            if self.emulators.has_section(game.get("emulator")):
                emulator = game.get("emulator")

        if emulator is not None and emulator in self.emulators.sections():
            title = filename
            if self.selection["name"] is not None:
                title = self.selection["name"]

            self.logger.info(_("Initialize %s") % title)

            # ----------------------------
            #   Generate correct command
            # ----------------------------

            command = self.generate_command(emulator, self.selection["game"])

            if command is not None:

                # ----------------------------
                #   Run game
                # ----------------------------

                thread = Thread(target=self.launch_game,
                    args=[emulator, filename, command, title])
                thread.start()

                self.logger.debug("Start %s into %s" % (filename, thread))

                self.sensitive_interface()

                self.tool_item_notes.set_sensitive(True)
                self.menu_item_notes.set_sensitive(True)


    def generate_command(self, emulator, filename):
        """
        Generate a command for a game with a specific emulator
        """

        not_use_filename = False

        if not exists(filename):
            self.set_message(_("Missing file"), _("Cannot found %s" % filename))

            return None

        # ----------------------------
        #   Check emulator binary
        # ----------------------------

        binary = self.emulators.get(emulator, "binary")

        if len(get_binary_path(binary)) == 0:
            self.set_message(_("Missing binary"), _("Cannot found %s" % binary))

            return None

        # ----------------------------
        #   Default arguments
        # ----------------------------

        args = str()

        if self.emulators.has_option(emulator, "default"):
            args = self.emulators.get(emulator, "default")

        exceptions = self.database.select("games", "arguments",
            { "filename": basename(filename) })
        if exceptions is not None and len(exceptions) > 0:
            args = exceptions

        # ----------------------------
        #   Set fullscreen mode
        # ----------------------------

        # Fullscreen
        if self.tool_item_fullscreen.get_active():
            if self.emulators.has_option(emulator, "fullscreen"):
                args += " %s" % self.emulators.get(emulator, "fullscreen")

        # Windowed
        elif self.emulators.has_option(emulator, "windowed"):
            args += " %s" % self.emulators.get(emulator, "windowed")

        # ----------------------------
        #   Replace special parameters
        # ----------------------------

        if "<conf_path>" in args and \
            self.emulators.has_option(emulator, "configuration"):
            args = args.replace("<conf_path>",
                self.emulators.get(emulator, "configuration"))

        if "<rom_path>" in args:
            args = args.replace("<rom_path>", dirname(expanduser(filename)))

            not_use_filename = True

        if "<rom_name>" in args:
            name, extension = splitext(expanduser(filename))

            args = args.replace("<rom_name>", name)

            not_use_filename = True

        if "<rom_file>" in args:
            args = args.replace("<rom_file>", self.selection["game"])

            not_use_filename = True

        # ----------------------------
        #   Generate correct command
        # ----------------------------

        command = list()

        # Append binaries
        command.extend(shlex_split(binary))

        # Append arguments
        if args is not None:
            command.extend(shlex_split(args))

        # Append game file
        if not not_use_filename:
            command.append(self.selection["game"])

        return command


    def launch_game(self, emulator, filename, command, title):
        """
        Launch a game with correct arguments and update game informations
        """

        error = False

        launch_date = datetime.now()

        gamename, extension = splitext(basename(filename))

        try:
            # ----------------------------
            #   Launch game
            # ----------------------------

            self.logger.info(_("Launch %s") % ' '.join(command))

            proc = Popen(command, stdout=PIPE, stdin=PIPE,
                stderr=STDOUT, universal_newlines=True)

            self.threads[gamename] = proc

            output, error_output = proc.communicate()

            self.logger.info(_("Close %s") % title)

            proc.terminate()

            # ----------------------------
            #   Log data
            # ----------------------------

            log_path = path_join(expanduser(Path.Logs), "%s.log" % filename)

            self.logger.info(_("Log to %s") % log_path)

            # Write output into game's log
            with open(log_path, 'w') as pipe:
                pipe.write(str())
                pipe.write("%s\n\n" % " ".join(command))
                pipe.write(output)

        except OSError as error:
            error = True

        except KeyboardInterrupt as error:
            self.logger.info(_("Terminate by keyboard interrupt"))

        self.emit("game_close", error, emulator, filename, launch_date)


    def do_game_close(self, error, emulator, filename, launch_date):
        """
        Close a game which send game_close signal
        """

        gamename, extension = splitext(basename(filename))

        # ----------------------------
        #   Save game data
        # ----------------------------

        if not error:
            # Calc time since game start
            interval = datetime.now() - launch_date

            total = self.get_play_time(filename, interval)
            play_time = self.get_play_time(filename, interval, False)

            # ----------------------------
            #   Update data
            # ----------------------------

            # Play data
            self.database.modify("games", {
                "play_time": total,
                "last_play": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                "last_play_time": play_time,
                }, { "filename": filename })

            # Set new data into games treeview
            value = self.database.get("games", { "filename": filename })
            if value is not None:

                # Played
                play = value.get("play", 0) + 1

                self.database.modify("games",
                    { "play": play }, { "filename": filename })

                self.set_game_data(Columns.Played, str(play), gamename)

                # Last played
                self.set_game_data(Columns.LastPlay,
                    string_from_date(value["last_play"]), gamename)

                # Last time played
                self.set_game_data(Columns.LastTimePlay,
                    string_from_time(value["last_play_time"]), gamename)

                # Play time
                self.set_game_data(Columns.TimePlay,
                    string_from_time(value["play_time"]), gamename)

                # Snaps
                if self.check_screenshots(emulator, gamename):
                    self.set_game_data(
                        Columns.Snapshots, self.icons["snap"], gamename)
                    self.tool_item_screenshots.set_sensitive(True)

                else:
                    self.set_game_data(
                        Columns.Snapshots, self.alternative["snap"], gamename)

                # Save state
                if self.check_save_states(emulator, gamename):
                    self.set_game_data(
                        Columns.Save, self.icons["save"], gamename)

                else:
                    self.set_game_data(
                        Columns.Save, self.alternative["save"], gamename)

        # ----------------------------
        #   Refresh widgets
        # ----------------------------

        name, extension = splitext(basename(self.selection["game"]))

        # Current selected game is the same as launched
        if name == gamename:
            self.tool_item_launch.set_sensitive(True)
            self.tool_item_output.set_sensitive(True)
            self.tool_item_parameters.set_sensitive(True)
            self.menu_item_launch.set_sensitive(True)
            self.menu_item_parameters.set_sensitive(True)
            self.menu_item_output.set_sensitive(True)
            self.menu_item_database.set_sensitive(True)
            self.menu_item_remove.set_sensitive(True)
            self.menu_item_rename.set_sensitive(True)

        # Remove this game from threads list
        if gamename in self.threads:
            self.logger.debug("Remove %s from process cache" % gamename)
            del self.threads[gamename]


    def __on_game_renamed(self, widget):
        """
        Set a custom name for a specific game
        """

        gamefile = basename(self.selection["game"])
        gamename = splitext(gamefile)[0]

        treeiter = self.game_path[gamename][1]

        result = self.database.get("games", { "filename": gamefile })
        if not result is None and len(result["name"]) > 0:
            gamename = result["name"]

        # ----------------------------
        #   Dialog
        # ----------------------------

        dialog = DialogRename(self, _("Rename a game"),
            _("Set a custom name for %s") % gamefile, gamename)

        if dialog.run() == Gtk.ResponseType.APPLY:
            if not dialog.entry.get_text() == result and \
                len(dialog.entry.get_text()) > 0:

                self.model_games[treeiter][Columns.Name] = \
                    dialog.entry.get_text()

                new_name = dialog.entry.get_text()

                self.database.modify("games",
                    { "name": new_name },
                    { "filename": gamefile })

                self.selection["name"] = new_name
                self.set_informations()

                self.logger.info(_("Rename %(old)s to %(new)s") % {
                    "old": gamename, "new": new_name })

        dialog.destroy()


    def __on_game_clean(self, widget):
        """
        Reset game informations from database
        """

        gamefile = basename(self.selection["game"])
        gamename = splitext(gamefile)[0]

        treeiter = self.game_path[gamename][1]

        title = gamename
        if self.selection["name"] is not None:
            title = self.selection["name"]

        dialog = Question(self, title,
            _("Would you really want to clean informations for this game ?"))

        if dialog.run() == Gtk.ResponseType.YES:
            self.model_games[treeiter][Columns.Name] = gamename
            self.model_games[treeiter][Columns.Favorite] = False
            self.model_games[treeiter][Columns.Icon] = \
                self.alternative["favorite"]
            self.model_games[treeiter][Columns.Played] = None
            self.model_games[treeiter][Columns.LastPlay] = None
            self.model_games[treeiter][Columns.TimePlay] = None
            self.model_games[treeiter][Columns.LastTimePlay] = None
            self.model_games[treeiter][Columns.Except] = \
                self.alternative["except"]
            self.model_games[treeiter][Columns.Multiplayer] = \
                self.alternative["multiplayer"]

            self.database.remove("games", { "filename": gamefile })

            self.logger.info(_("Clean %s informations") % gamefile)

        dialog.destroy()


    def __on_game_removed(self, widget):
        """
        Remove a game from harddrive and from database
        """

        file_to_remove = list()

        need_to_reload = False

        emulator = self.consoles.get(self.selection["console"], "emulator")

        gamefile = basename(self.selection["game"])
        gamename = splitext(gamefile)[0]

        treeiter = self.game_path[gamename][1]

        # ----------------------------
        #   Dialog
        # ----------------------------

        title = gamename
        if self.selection["name"] is not None:
            title = self.selection["name"]

        dialog = DialogRemove(self, title)

        if dialog.run() == Gtk.ResponseType.YES:
            file_to_remove.append(self.selection["game"])

            # ----------------------------
            #   Database
            # ----------------------------

            if dialog.check_database.get_active():
                self.database.remove("games", { "filename": gamefile })

            # ----------------------------
            #   Save state
            # ----------------------------

            if dialog.check_save_state.get_active():
                if self.emulators.has_option(emulator, "save"):
                    path = expanduser(self.emulators.get(emulator, "save"))

                    if emulator in self.emulators.sections():
                        file_to_remove.extend(
                            glob(path.replace("<name>", gamename)))

            # ----------------------------
            #   Screenshots
            # ----------------------------

            if dialog.check_screenshots.get_active():
                if self.emulators.has_option(emulator, "snaps"):
                    path = expanduser(self.emulators.get(emulator, "snaps"))

                    if emulator in self.emulators.sections():
                        if "<lname>" in path:
                            pattern = path.replace("<lname>", gamename).lower()
                        else:
                            pattern = path.replace("<name>", gamename)

                        file_to_remove.extend(glob(pattern))

            for element in file_to_remove:
                self.logger.info(_("%s has been deleted from disk") % element)
                remove(element)

            need_to_reload = True

        dialog.destroy()

        if need_to_reload:
            self.load_interface()

            self.set_message(
                _("Remove %s") % self.model_games[treeiter][Columns.Name],
                _("This game was removed successfully"), "dialog-information")


    def __on_game_parameters(self, widget):
        """
        Set some parameters for a specific game
        """

        gamefile = basename(self.selection["game"])
        gamename = splitext(gamefile)[0]

        parameters = None

        emulator = {
            "rom": None,
            "console": None,
            "parameters": None }

        # Current console default emulator
        if self.selection.get("console") is not None:
            emulator["console"] = self.consoles.get(
                self.selection["console"], "emulator")

            if self.emulators.has_option(emulator["console"], "default"):
                parameters = self.emulators.get(emulator["console"], "default")

        # ----------------------------
        #   Generate data
        # ----------------------------

        # Get game data from database
        data = self.database.select("games", ["arguments", "emulator"],
            { "filename": gamefile })

        if data is not None:
            if len(data[0]) > 0 and not data[0] == parameters:
                emulator["parameters"] = data[0]

            if len(data[1]) > 0 and not data[1] == emulator["console"]:
                emulator["rom"] = data[1]

        # ----------------------------
        #   Dialog
        # ----------------------------

        title = gamename
        if self.selection["name"] is not None:
            title = self.selection["name"]

        dialog = DialogParameters(self, title, emulator)

        if dialog.run() == Gtk.ResponseType.OK:
            new_emulator = dialog.combo.get_active_id()
            new_parameters = dialog.entry.get_text()

            # ----------------------------
            #   Check new results
            # ----------------------------

            if new_emulator is None:
                new_emulator = str()

            self.database.modify("games", {
                    "arguments": new_parameters,
                    "emulator": new_emulator
                }, { "filename": gamefile })

            self.logger.info(_("Change custom parameters for %s") % title)

            # ----------------------------
            #   Check diferences
            # ----------------------------

            custom = False

            if len(new_emulator) > 0 and \
                not new_emulator == emulator["console"]:
                custom = True

            elif len(new_parameters) > 0 and \
                not new_parameters == emulator["parameters"]:
                custom = True

            if custom:
                self.set_game_data(
                    Columns.Except, self.icons["except"], gamename)
            else:
                self.set_game_data(
                    Columns.Except, self.alternative["except"], gamename)

            # ----------------------------
            #   Update icons
            # ----------------------------

            if len(new_emulator) == 0:
                new_emulator = emulator["console"]

            # Snap
            if self.check_screenshots(new_emulator, gamename):
                self.set_game_data(
                    Columns.Snapshots, self.icons["snap"], gamename)
                self.tool_item_screenshots.set_sensitive(True)

            else:
                self.set_game_data(
                    Columns.Snapshots, self.alternative["snap"], gamename)
                self.tool_item_screenshots.set_sensitive(False)

            # Save state
            if self.check_save_states(new_emulator, gamename):
                self.set_game_data(Columns.Save, self.icons["save"], gamename)

            else:
                self.set_game_data(
                    Columns.Save, self.alternative["save"], gamename)

        dialog.hide()


    def __on_game_marked_as_favorite(self, widget):
        """
        Mark or unmark a game as favorite
        """

        gamefile = basename(self.selection["game"])
        gamename = splitext(gamefile)[0]

        treeiter = self.game_path[gamename][1]

        if self.model_games[treeiter][Columns.Icon] == \
            self.alternative["favorite"]:
            self.model_games[treeiter][Columns.Favorite] = True
            self.model_games[treeiter][Columns.Icon] = self.icons["favorite"]

            self.database.modify("games",
                { "favorite": 1 }, { "filename": gamefile })

            self.logger.debug("Mark %s as favorite" % gamename)

        else:
            self.model_games[treeiter][Columns.Favorite] = False
            self.model_games[treeiter][Columns.Icon] = \
                self.alternative["favorite"]

            self.database.modify("games",
                { "favorite": 0 }, { "filename": gamefile })

            self.logger.debug("Unmark %s as favorite" % gamename)

        self.check_selection()


    def __on_game_marked_as_multiplayer(self, widget):
        """
        Mark or unmark a game as multiplayer
        """

        gamefile = basename(self.selection["game"])
        gamename = splitext(gamefile)[0]

        treeiter = self.game_path[gamename][1]

        if self.model_games[treeiter][Columns.Multiplayer] == \
            self.alternative["multiplayer"]:
            self.model_games[treeiter][Columns.Multiplayer] = \
                self.icons["multiplayer"]

            self.database.modify("games",
                { "multiplayer": 1 }, { "filename": gamefile })

            self.logger.debug("Mark %s as multiplayers" % gamename)

        else:
            self.model_games[treeiter][Columns.Multiplayer] = \
                self.alternative["multiplayer"]

            self.database.modify("games",
                { "multiplayer": 0 }, { "filename": gamefile })

            self.logger.debug("Unmark %s as multiplayers" % gamename)

        self.check_selection()


    def __on_game_copy(self, widget):
        """
        Copy game directory to clipboard
        """

        self.clipboard.set_text(self.selection["game"], -1)


    def __on_game_open(self, widget):
        """
        Open game directory in default files manager

        http://stackoverflow.com/a/6631329
        """

        path = dirname(self.selection["game"])

        self.logger.debug("Open %s folder in files manager" % path)

        if system() == "Windows":
            from os import startfile
            startfile(path)

        elif system() == "Darwin":
            Popen(["open", path], stdout=PIPE, stdin=PIPE,
                stderr=STDOUT, universal_newlines=True)

        else:
            Popen(["xdg-open", path], stdout=PIPE, stdin=PIPE,
                stderr=STDOUT, universal_newlines=True)


    def __on_game_generate_desktop(self, widget):
        """
        Mark or unmark a game as multiplayer
        """

        model, treeiter = self.treeview_games.get_selection().get_selected()

        if treeiter is not None:
            gamefile = basename(self.selection["game"])
            gamename = splitext(gamefile)[0]

            game = self.database.get("games", { "filename": gamefile })

            # ----------------------------
            #   Check emulator
            # ----------------------------

            console = self.selection["console"]

            emulator = self.consoles.get(console, "emulator")
            if game is not None and len(game.get("emulator")) > 0:
                if self.emulators.has_section(game.get("emulator")):
                    emulator = game.get("emulator")

            if emulator is not None and emulator in self.emulators.sections():
                name = "%s.desktop" % gamename

                # ----------------------------
                #   Fill template
                # ----------------------------

                title = gamename
                if self.selection["name"] is not None:
                    title = self.selection["name"]

                icon = self.consoles.get(console, "icon")
                if not exists(icon):
                    icon = path_join(Path.Consoles, "%s.%s" % (icon, Icons.Ext))

                values = {
                    "%name%": title,
                    "%icon%": icon,
                    "%path%": dirname(self.selection["game"]),
                    "%command%": ' '.join(self.generate_command(
                        emulator, self.selection["game"])) }

                try:
                    with open(get_data(Conf.Desktop), 'r') as pipe:
                        template = pipe.readlines()

                    content = str()

                    for line in template:
                        for key in values.keys():
                            line = line.replace(key, values[key])

                        content += line

                    if not exists(Path.Apps):
                        mkdir(Path.Apps)

                    with open(path_join(Path.Apps, name), 'w') as pipe:
                        pipe.write(content)

                    self.set_message(
                        _("Generate menu entry for %s") % title,
                        _("%s was generated successfully")  % name,
                        "dialog-information")

                except OSError as error:
                    self.set_message(
                        _("Generate menu entry for %s") % title,
                        _("An error occur during generation, consult log for "
                        "futher details."), "dialog-error")


    def __on_menu_show(self, treeview, event):
        """
        Show a menu when user right-click in treeview
        """

        if event.type == EventType.BUTTON_PRESS:
            if event.button == Gdk.BUTTON_SECONDARY:
                treeiter = treeview.get_path_at_pos(int(event.x), int(event.y))

                if treeiter is not None:
                    path, col = treeiter[0:2]

                    treeview.grab_focus()
                    treeview.set_cursor(path, col, 0)

                    self.menu_games.popup(
                        None, None, None, None, event.button, event.time)

                    return True

        elif event.type == EventType.KEY_RELEASE:
            if event.keyval == Gdk.KEY_Menu:
                model, treeiter = treeview.get_selection().get_selected()

                if treeiter is not None:
                    self.menu_games.popup(None, None, None, None, 0, event.time)

                    return True

        return False


    def __on_activate_fullscreen(self, widget):
        """
        Update fullscreen icon
        """

        if self.tool_item_fullscreen.get_active():
            self.logger.debug("Switch to windowed mode")
            self.get_object("image_fullscreen").set_from_icon_name(
                "view-fullscreen", Gtk.IconSize.BUTTON)

        else:
            self.logger.debug("Switch to fullscreen mode")
            self.get_object("image_fullscreen").set_from_icon_name(
                "view-restore", Gtk.IconSize.BUTTON)


    def __on_activate_dark_theme(self, widget):
        """
        Change ui theme between dark and light version
        """

        dark_theme_status = self.config.getboolean(
            "gem", "dark_theme", fallback=False)

        on_change_theme(not dark_theme_status)

        self.config.modify("gem", "dark_theme", int(not dark_theme_status))
        self.config.update()

        self.menu_item_dark_theme.set_active(not dark_theme_status)


    def __on_dnd_send_data(self, widget, context, data, target, time):
        """
        Send rom file path
        """

        data.set_uris(["file://%s" % self.selection["game"]])


    def __on_dnd_received_data(self, widget, context, x, y, data, info, time):
        """
        Install drop files
        """

        self.logger.debug("Received data from drag & drop")
        widget.stop_emission("drag_data_received")

        if not info == Gem.Id:
            return

        previous_console = None
        need_to_reload = False

        for uri in data.get_uris():
            result = urlparse(uri)

            console = None

            if result.scheme == "file":
                path = expanduser(url2pathname(result.path))

                if exists(path):
                    self.logger.debug("Check %s" % path)
                    filename, ext = splitext(basename(path))

                    # ----------------------------
                    #   Get right console for rom
                    # ----------------------------

                    consoles_list = list()
                    for console in self.consoles.keys():
                        exts = self.consoles.item(console, "exts")

                        if exts is not None and ext[1:] in exts.split(';'):
                            consoles_list.append(console)

                    console = None

                    if len(consoles_list) > 0:
                        console = consoles_list[0]

                        if len(consoles_list) > 1:
                            dialog = DialogConsoles(self,
                                basename(path), consoles_list, previous_console)

                            if dialog.run() == Gtk.ResponseType.APPLY:
                                console = dialog.current

                            previous_console = console

                            dialog.destroy()

            # ----------------------------
            #   Check console
            # ----------------------------

            if console is not None and self.consoles.has_section(console):
                rom_path = expanduser(self.consoles.item(console, "roms"))

                # ----------------------------
                #   Install roms
                # ----------------------------

                if rom_path is not None and not dirname(path) == rom_path and \
                    exists(rom_path) and access(rom_path, W_OK):
                    move = True

                    if exists(path_join(rom_path, basename(path))):
                        dialog = Question(self, basename(path),
                            _("This rom already exists in %s. Do you want to "
                            "replace it ?") % rom_path)

                        move = False
                        if dialog.run() == Gtk.ResponseType.YES:
                            move = True

                            self.logger.debug(
                                "Move %s to %s" % (path, rom_path))
                            remove(path_join(rom_path, basename(path)))

                        dialog.destroy()

                    if move:
                        rename(path, rom_path)

                        self.logger.info(_("Drop %(rom)s to %(path)s") % {
                            "rom": basename(path), "path": rom_path })

                        if console == self.selection["console"]:
                            need_to_reload = True

                # ----------------------------
                #   Errors
                # ----------------------------

                if dirname(path) == rom_path:
                    self.set_message(basename(path), _("%s is already in the "
                        "roms folder. Canceling operation.") % basename(path))

                elif not exists(rom_path):
                    self.set_message(basename(path), _("Destination %s not "
                        "exist. Canceling operation.") % rom_path)

                elif not access(rom_path, W_OK):
                    self.set_message(basename(path), _("Cannot write into %s. "
                        "Canceling operation.") % rom_path)

        if need_to_reload:
            self.load_interface()


    def get_play_time(self, gamename, interval, total=True):
        """
        Calc time passed ingame
        """

        result = self.database.get("games", { "filename": gamename })

        if result is not None and total and len(result["play_time"]) > 0:
            play_time = datetime.strptime(result["play_time"], "%H:%M:%S")
            play_time += interval

        else:
            play_time = interval

        return str(play_time).split('.')[0].split()[-1]


    def check_save_states(self, emulator, filename):
        """
        Check if a game has some save states
        """

        if not emulator in self.emulators.sections():
            return False

        if self.emulators.has_option(emulator, "save"):
            save_path = expanduser(self.emulators.get(emulator, "save"))

            if "<rom_path>" in save_path:
                pattern = save_path.replace("<rom_path>",
                    basename(self.selection["game"]))

            if "<lname>" in save_path:
                pattern = save_path.replace("<lname>", filename).lower()
            else:
                pattern = save_path.replace("<name>", filename)

            if len(glob(pattern)) > 0:
                return True

        return False


    def check_screenshots(self, emulator, filename):
        """
        Check if a game has some snaps
        """

        if not emulator in self.emulators.sections():
            return False

        if self.emulators.has_option(emulator, "snaps"):
            snaps_path = expanduser(self.emulators.get(emulator, "snaps"))

            if "<rom_path>" in snaps_path:
                pattern = snaps_path.replace("<rom_path>",
                    basename(self.selection["game"]))

            if "<lname>" in snaps_path:
                pattern = snaps_path.replace("<lname>", filename).lower()
            else:
                pattern = snaps_path.replace("<name>", filename)

            if len(glob(pattern)) > 0:
                return True

        return False


    def check_desktop(self, filename):
        """
        Check if a game has already a desktop entry file
        """

        name, extension = splitext(filename)

        return exists(path_join(Path.Apps, "%s.desktop" % name))


    def check_log(self):
        """
        Check if a game has an output file available
        """

        log_path = path_join(expanduser(Path.Logs),
            "%s.log" % basename(self.selection["game"]))

        if exists(expanduser(log_path)):
            return log_path

        return None


    def set_game_data(self, index, data, gamename):
        """
        Update game informations in games treeview
        """

        model = self.treeview_games.get_model()
        treeiter = self.game_path.get(gamename, None)

        if treeiter is not None:
            self.model_games[treeiter[1]][index] = data


class Splash(object):

    def __init__(self, length):
        """
        Constructor
        """

        # ------------------------------------
        #   Initialize variables
        # ------------------------------------

        self.length = length

        self.index = 1

        # ------------------------------------
        #   Initialize icons
        # ------------------------------------

        # Get user icon theme
        self.icons_theme = Gtk.IconTheme.get_default()

        self.icons_theme.append_search_path(get_data(path_join("ui", "icons")))

        # ------------------------------------
        #   Prepare interface
        # ------------------------------------

        # Init widgets
        self.__init_widgets()

        # Start interface
        self.__start_interface()


    def __init_widgets (self):
        """
        Load widgets into main interface
        """

        # Load glade file
        try:
            builder = Gtk.Builder()

            # Properties
            builder.add_from_file(get_data(path_join("ui", "interface.glade")))

        except OSError as error:
            sys_exit(_("Cannot open interface: %s" % error))

        # ------------------------------------
        #   Main window
        # ------------------------------------

        self.window = builder.get_object("splash")

        # Properties
        self.window.set_title("Graphical Emulators Manager")

        # ------------------------------------
        #   Image
        # ------------------------------------

        self.image_splash = builder.get_object("image_splash")

        # Properties
        self.image_splash.set_from_icon_name("gem", 256)

        # ------------------------------------
        #   Progressbar
        # ------------------------------------

        self.label_splash = builder.get_object("label_splash")

        self.progressbar = builder.get_object("progress_splash")

        # Properties
        self.label_splash.set_text(
            _("Migrating entries from old database"))


    def __start_interface(self):
        """
        Load data and start interface
        """

        self.window.show_all()

        self.refresh()


    def update(self):
        """
        Update splash widgets
        """

        self.refresh()

        if self.index <= self.length:
            self.progressbar.set_text("%d / %d" % (self.index, self.length))
            self.progressbar.set_fraction(float(self.index) / (self.length))

            self.index += 1

            self.refresh()


    def refresh(self):
        """
        Refresh all pendings event in main interface
        """

        while Gtk.events_pending():
            Gtk.main_iteration()
