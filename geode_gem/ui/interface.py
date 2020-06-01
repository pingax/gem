# ------------------------------------------------------------------------------
#  Copyleft 2015-2020 PacMiam
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
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

# Datetime
from datetime import date, datetime, timedelta

# Filesystem
from os import R_OK, W_OK, X_OK, access, remove
from os.path import getctime
from pathlib import Path
from copy import deepcopy
from shutil import rmtree

# GEM
from geode_gem.engine.utils import (copy,
                                    get_data,
                                    get_binary_path,
                                    parse_timedelta,
                                    generate_identifier)
from geode_gem.engine.api import GEM
from geode_gem.engine.console import Console
from geode_gem.engine.lib.configuration import Configuration

from geode_gem.ui.data import Icons, Columns, Folders, Metadata
from geode_gem.ui.utils import (magic_from_file,
                                on_change_theme,
                                string_from_date,
                                string_from_time,
                                replace_for_markup,
                                on_activate_listboxrow)
from geode_gem.ui.dialog import GeodeDialog
from geode_gem.ui.widgets.game import GameThread
from geode_gem.ui.widgets.script import ScriptThread
from geode_gem.ui.widgets import GeodeGtk
from geode_gem.ui.widgets.widgets import ListBoxItem, IconsGenerator

# GObject
try:
    from gi import require_version
    require_version("Gtk", "3.0")

    from gi.repository import Gtk, GLib, GObject, Gio, Gdk, GdkPixbuf, Pango

except ImportError as error:
    from sys import exit
    exit("Cannot found python3-gobject module: %s" % str(error))

# Processus
from subprocess import PIPE, Popen, STDOUT

# Random
from random import shuffle

# Regex
from re import match, IGNORECASE

# System
from sys import version_info
from shlex import split as shlex_split

# Thread
from threading import enumerate as thread_enumerate
from threading import main_thread as thread_main_thread

# Translation
from gettext import gettext as _
from gettext import ngettext

# URL
from urllib.parse import urlparse
from urllib.request import url2pathname


# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class MainWindow(Gtk.ApplicationWindow):

    __gsignals__ = {
        "game-started": (GObject.SignalFlags.RUN_FIRST, None, [object]),
        "game-terminate": (GObject.SignalFlags.RUN_LAST, None, [object]),
        "script-terminate": (GObject.SignalFlags.RUN_LAST, None, [object]),
    }

    def __init__(self, api, cache):
        """ Constructor

        Parameters
        ----------
        api : gem.engine.api.GEM
            GEM API instance
        cache : pathlib.Path
            Cache folder path

        Raises
        ------
        TypeError
            if api type is not gem.engine.api.GEM
            if metadata type is not gem.engine.lib.configuration.Configuration
            if cache type is not pathlib.Path
        """

        if not type(api) is GEM:
            raise TypeError("Wrong type for api, expected gem.engine.api.GEM")

        if not isinstance(cache, Path):
            raise TypeError("Wrong type for cache, expected pathlib.Path")

        Gtk.ApplicationWindow.__init__(self)

        # ------------------------------------
        #   Initialize API
        # ------------------------------------

        # GEM API
        self.api = api

        # Quick access to API logger
        self.logger = api.logger

        # Cache folder
        self.__cache = cache

        # Check development version
        self.__version = self.check_version()

        # ------------------------------------
        #   Initialize variables
        # ------------------------------------

        # Generate a title from GEM informations
        self.title = "%s - %s (%s)" % (
            Metadata.NAME, self.__version, Metadata.CODE_NAME)

        # Store thread id for game listing
        self.list_thread = int()

        # Store started notes with note file path as key
        self.notes = dict()
        # Store script threads with basename game file without extension as key
        self.scripts = dict()
        # Store threads with basename game file without extension as key
        self.threads = dict()
        # Store selected game informations with console, game and name as keys
        self.selection = dict()
        # Store shortcut with Gtk.Widget as key
        self.shortcuts_data = dict()
        # Store consoles iters
        self.consoles_iter = dict()
        # Define signals per toggle buttons
        self.signals_storage = dict()

        # Store user keys input
        self.keys = list()
        # Store available shortcuts
        self.shortcuts = list()
        # Store sidebar latest image path
        self.sidebar_image = None

        # Avoid to reload interface when switch between default & classic theme
        self.use_classic_theme = False

        # Manage fullscreen from boolean variable
        self.__fullscreen_status = False

        # Avoid to reload game tooltip every time the user move in line
        self.__current_tooltip = None
        self.__current_tooltip_data = list()
        self.__current_tooltip_pixbuf = None

        # Store previous toolbar icon size
        self.__current_toolbar_size = None

        # Store previous sidebar orientation
        self.__current_orientation = None

        # Store selected row for console menu
        self.__current_menu_row = None

        # Check mednafen status
        self.__mednafen_status = self.check_mednafen()

        # Manage game flags
        self.__flags_labels = ("favorite", "multiplayer", "finish")
        # Manage treeview columns
        self.__columns_labels = self.__flags_labels + (
            "play", "play_time", "last_play", "score", "installed", "flags")

        # ------------------------------------
        #   Initialize icons
        # ------------------------------------

        self.icons = IconsGenerator(
            savestate=Icons.FLOPPY,
            screenshot=Icons.PHOTOS,
            parameter=Icons.PROPERTIES,
            warning=Icons.WARNING,
            favorite=Icons.FAVORITE,
            multiplayer=Icons.USERS,
            finish=Icons.SMILE,
            unfinish=Icons.UNCERTAIN,
            nostarred=Icons.NO_STARRED,
            starred=Icons.STARRED)

        # ------------------------------------
        #   Shortcuts
        # ------------------------------------

        self.shortcuts_group = Gtk.AccelGroup()

        self.shortcuts_map = Gtk.AccelMap()

        # ------------------------------------
        #   Targets
        # ------------------------------------

        self.targets = [Gtk.TargetEntry.new("text/uri-list", 0, 1337)]

        # ------------------------------------
        #   Prepare interface
        # ------------------------------------

        # Init widgets
        self.__init_widgets()

        # Init packing
        self.__init_packing()

        # Init signals
        self.__init_signals()

        # Init storage
        self.__init_storage()

        # Start interface
        self.__start_interface()

        # ------------------------------------
        #   Main loop
        # ------------------------------------

        try:
            self.main_loop = GLib.MainLoop()
            self.main_loop.run()

        except KeyboardInterrupt:
            self.logger.warning("Terminate by keyboard interrupt")

            self.__stop_interface()

    def __init_widgets(self):
        """ Initialize interface widgets
        """

        # ------------------------------------
        #   Main window
        # ------------------------------------

        self.window_size = Gdk.Geometry()

        self.window_display = Gdk.Display.get_default()

        # Properties
        self.window_size.min_width = 800
        self.window_size.min_height = 600
        self.window_size.base_width = 1024
        self.window_size.base_height = 768

        self.set_title(self.title)

        self.set_default_icon_from_file(
            str(get_data("data", "desktop", "gem.svg")))

        self.set_position(Gtk.WindowPosition.CENTER)

        self.add_accel_group(self.shortcuts_group)

        # ------------------------------------
        #   Clipboard
        # ------------------------------------

        self.clipboard = Gtk.Clipboard.get(Gdk.Atom.intern("CLIPBOARD", False))

        # ------------------------------------
        #   External applications
        # ------------------------------------

        try:
            self.__xdg_open_instance = Gio.AppInfo.create_from_commandline(
                "xdg-open", None, Gio.AppInfoCreateFlags.SUPPORTS_URIS)

        except GLib.Error:
            self.logger.exception("Cannot generate xdg-open instance")

        # ------------------------------------
        #   Grid
        # ------------------------------------

        self.grid = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)

        self.grid_consoles = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)

        self.grid_game_filters_popover = Gtk.Box.new(
            Gtk.Orientation.VERTICAL, 6)

        self.grid_games = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
        self.grid_games_views = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
        self.grid_games_placeholder = Gtk.Box.new(Gtk.Orientation.VERTICAL, 12)

        self.grid_sidebar = Gtk.Grid()
        self.grid_sidebar_content = Gtk.Box.new(Gtk.Orientation.VERTICAL, 6)
        self.grid_sidebar_score = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 6)
        self.grid_sidebar_informations = Gtk.Grid()

        # Properties
        self.grid_game_filters_popover.set_border_width(6)
        self.grid_game_filters_popover.set_orientation(
            Gtk.Orientation.VERTICAL)

        self.grid_games_views.drag_dest_set(
            Gtk.DestDefaults.MOTION | Gtk.DestDefaults.DROP, self.targets,
            Gdk.DragAction.COPY)

        self.grid_games_placeholder.set_border_width(18)

        self.grid_sidebar.set_border_width(12)
        self.grid_sidebar.set_hexpand(True)
        self.grid_sidebar.set_vexpand(True)
        self.grid_sidebar.set_column_homogeneous(False)

        self.grid_sidebar_content.set_valign(Gtk.Align.START)
        self.grid_sidebar_content.set_halign(Gtk.Align.FILL)
        self.grid_sidebar_content.set_hexpand(False)
        self.grid_sidebar_content.set_vexpand(False)

        self.grid_sidebar_informations.set_column_homogeneous(True)
        self.grid_sidebar_informations.set_halign(Gtk.Align.FILL)
        self.grid_sidebar_informations.set_column_spacing(12)
        self.grid_sidebar_informations.set_border_width(6)
        self.grid_sidebar_informations.set_row_spacing(6)
        self.grid_sidebar_informations.set_hexpand(True)
        self.grid_sidebar_informations.set_vexpand(True)

        self.grid_sidebar_score.set_halign(Gtk.Align.CENTER)
        self.grid_sidebar_score.set_valign(Gtk.Align.CENTER)
        self.grid_sidebar_score.set_hexpand(True)

        # ------------------------------------
        #   Headerbar
        # ------------------------------------

        self.headerbar = GeodeGtk.HeaderBar(
            "headerbar",
            GeodeGtk.MenuButton(
                "main",
                _("Main menu"),
                GeodeGtk.MenuItem("preferences", _("_Preferences…")),
                GeodeGtk.MenuItem("log", _("Application _log…")),
                None,
                GeodeGtk.MenuItem("clean_cache", _("Clean icons _cache…")),
                None,
                GeodeGtk.MenuItem("website", _("_Website")),
                GeodeGtk.MenuItem("report", _("_Report problem")),
                None,
                GeodeGtk.MenuItem("about", _("_About")),
                None,
                GeodeGtk.MenuItem("quit", _("_Quit")),
                icon_name=Icons.Symbolic.MENU,
            ),
            GeodeGtk.MenuButton(
                "display",
                _("Display menu"),
                GeodeGtk.MenuItem(
                    "games_list",
                    _("_Games lists"),
                    GeodeGtk.MenuItem(
                        "columns",
                        _("_Columns visibility"),
                        GeodeGtk.CheckMenuItem("favorite", _("Favorite")),
                        GeodeGtk.CheckMenuItem("multiplayer",
                                               _("Multiplayer")),
                        GeodeGtk.CheckMenuItem("finish", _("Finish")),
                        GeodeGtk.CheckMenuItem("play", _("Launch number")),
                        GeodeGtk.CheckMenuItem("play_time", _("Play time")),
                        GeodeGtk.CheckMenuItem("last_play",
                                               _("Last launch date")),
                        GeodeGtk.CheckMenuItem("score", _("Score")),
                        GeodeGtk.CheckMenuItem("installed",
                                               _("Installed date")),
                        GeodeGtk.CheckMenuItem("flags", _("Emulator flags")),
                    ),
                    None,
                    GeodeGtk.RadioMenuItem("list", _("List view")),
                    GeodeGtk.RadioMenuItem(
                        "grid",
                        _("Grid icons"),
                        group="list",
                    ),
                ),
                None,
                GeodeGtk.MenuItem(
                    "sidebar",
                    _("_Sidebar"),
                    GeodeGtk.CheckMenuItem("show_sidebar", _("Show _sidebar")),
                    None,
                    GeodeGtk.RadioMenuItem("right", _("Right")),
                    GeodeGtk.RadioMenuItem(
                        "bottom",
                        _("Bottom"),
                        group="right",
                    ),
                ),
                GeodeGtk.MenuItem(
                    "statusbar",
                    _("_Statusbar"),
                    GeodeGtk.CheckMenuItem("show_statusbar",
                                           _("Show _statusbar")),
                ),
                None,
                GeodeGtk.CheckMenuItem("dark_theme", _("Use _dark theme")),
                icon_name=Icons.Symbolic.VIDEO,
            ),
            title=self.title,
        )

        # ------------------------------------
        #   Menubar
        # ------------------------------------

        self.menubar = Gtk.MenuBar()

        self.menubar_main = GeodeGtk.MenuItem(
            "menubar_main",
            _("_GEM"),
            GeodeGtk.MenuItem("preferences", _("_Preferences…")),
            GeodeGtk.MenuItem("log", _("Application _log…")),
            None,
            GeodeGtk.MenuItem("clean_cache", _("Clean icons _cache…")),
            None,
            GeodeGtk.MenuItem("quit", _("_Quit"))
        )

        self.menubar_view = GeodeGtk.MenuItem(
            "menubar_view",
            _("_Display"),
            GeodeGtk.MenuItem(
                "games_list",
                _("_Games lists"),
                GeodeGtk.MenuItem(
                    "columns",
                    _("_Columns visibility"),
                    GeodeGtk.CheckMenuItem("favorite", _("Favorite")),
                    GeodeGtk.CheckMenuItem("multiplayer", _("Multiplayer")),
                    GeodeGtk.CheckMenuItem("finish", _("Finish")),
                    GeodeGtk.CheckMenuItem("play", _("Launch number")),
                    GeodeGtk.CheckMenuItem("play_time", _("Play time")),
                    GeodeGtk.CheckMenuItem("last_play", _("Last launch date")),
                    GeodeGtk.CheckMenuItem("score", _("Score")),
                    GeodeGtk.CheckMenuItem("installed", _("Installed date")),
                    GeodeGtk.CheckMenuItem("flags", _("Emulator flags")),
                ),
                None,
                GeodeGtk.RadioMenuItem("list", _("List view")),
                GeodeGtk.RadioMenuItem(
                    "grid",
                    _("Grid icons"),
                    group="list",
                )
            ),
            None,
            GeodeGtk.MenuItem(
                "sidebar",
                _("_Sidebar"),
                GeodeGtk.CheckMenuItem("show_sidebar", _("Show _sidebar")),
                None,
                GeodeGtk.RadioMenuItem("right", _("Right")),
                GeodeGtk.RadioMenuItem(
                    "bottom",
                    _("Bottom"),
                    group="right",
                )
            ),
            GeodeGtk.MenuItem(
                "statusbar",
                _("_Statusbar"),
                GeodeGtk.CheckMenuItem("show_statusbar", _("Show _statusbar")),
            ),
            None,
            GeodeGtk.CheckMenuItem("dark_theme", _("Use _dark theme"))
        )

        self.menubar_game = GeodeGtk.MenuItem(
            "menubar_game",
            _("_Game"),
            GeodeGtk.MenuItem("launch", _("_Launch")),
            None,
            GeodeGtk.CheckMenuItem("favorite", _("_Favorite")),
            GeodeGtk.CheckMenuItem("multiplayer", _("_Multiplayer")),
            GeodeGtk.CheckMenuItem("finish", _("_Finished")),
            None,
            GeodeGtk.MenuItem("properties", _("_Properties…")),
            None,
            GeodeGtk.MenuItem("screenshots", _("_Screenshots…")),
            GeodeGtk.MenuItem("game_log", _("Output _log…")),
            GeodeGtk.MenuItem("notes", _("_Notes…")),
            None,
            GeodeGtk.CheckMenuItem("fullscreen", _("Fullscreen mode")),
        )

        self.menubar_edit = GeodeGtk.MenuItem(
            "menubar_edit",
            _("_Edit"),
            GeodeGtk.MenuItem(
                "score",
                _("_Score"),
                GeodeGtk.MenuItem("increase", _("_Increase score")),
                GeodeGtk.MenuItem("decrease", _("_Decrease score")),
                None,
                GeodeGtk.MenuItem("score_0", _("Set score as 0")),
                GeodeGtk.MenuItem("score_1", _("Set score as 1")),
                GeodeGtk.MenuItem("score_2", _("Set score as 2")),
                GeodeGtk.MenuItem("score_3", _("Set score as 3")),
                GeodeGtk.MenuItem("score_4", _("Set score as 4")),
                GeodeGtk.MenuItem("score_5", _("Set score as 5")),
            ),
            None,
            GeodeGtk.MenuItem("rename", _("_Rename…")),
            None,
            GeodeGtk.MenuItem("duplicate", _("_Duplicate…")),
            None,
            GeodeGtk.MenuItem("memory_type", _("Specify a _memory type…")),
            None,
            GeodeGtk.MenuItem("game_file", _("_Edit game file")),
            None,
            GeodeGtk.MenuItem("copy_path", _("_Copy path to clipboard")),
            GeodeGtk.MenuItem("open_path", _("_Open path")),
            GeodeGtk.MenuItem("menu_entry", _("_Generate a menu entry")),
            None,
            GeodeGtk.MenuItem("thumbnail", _("Set game _thumbnail…")),
            None,
            GeodeGtk.MenuItem("maintenance", _("_Maintenance…")),
            None,
            GeodeGtk.MenuItem("remove", _("_Remove from disk…")),
        )

        self.menubar_help = GeodeGtk.MenuItem(
            "menubar_help",
            _("_Help"),
            GeodeGtk.MenuItem("website", _("_Website")),
            GeodeGtk.MenuItem("report", _("_Report problem")),
            None,
            GeodeGtk.MenuItem("about", _("_About")),
        )

        # ------------------------------------
        #   Submenu
        # ------------------------------------

        self.menu_consoles = GeodeGtk.Menu(
            "menu_consoles",
            GeodeGtk.MenuItem("edit_console", _("_Edit console")),
            GeodeGtk.MenuItem("remove_console", _("_Remove console")),
            None,
            GeodeGtk.MenuItem("edit_emulator", _("_Edit emulator")),
            GeodeGtk.MenuItem("edit_file", _("_Edit configuration file")),
            None,
            GeodeGtk.MenuItem(
                "copy_path", _("_Copy games directory path to clipboard")),
            GeodeGtk.MenuItem("open_path", _("_Open games directory")),
            None,
            GeodeGtk.MenuItem("reload", _("_Reload games list")),
            None,
            GeodeGtk.CheckMenuItem("favorite", _("_Favorite")),
            GeodeGtk.CheckMenuItem(
                "recursive",
                _("_Recursive"),
                tooltip=_("You need to reload games list to apply changes"),
            ),
        )

        self.menu_game = GeodeGtk.Menu(
            "menu_game",
            GeodeGtk.MenuItem("launch", _("_Launch")),
            None,
            GeodeGtk.CheckMenuItem("favorite", _("_Favorite")),
            GeodeGtk.CheckMenuItem("multiplayer", _("_Multiplayer")),
            GeodeGtk.CheckMenuItem("finish", _("_Finished")),
            None,
            GeodeGtk.MenuItem("properties", _("_Properties…")),
            None,
            GeodeGtk.MenuItem(
                "edit",
                _("_Edit"),
                GeodeGtk.MenuItem("rename", _("_Rename…")),
                None,
                GeodeGtk.MenuItem("duplicate", _("_Duplicate…")),
                None,
                GeodeGtk.MenuItem("game_file", _("_Edit game file")),
                None,
                GeodeGtk.MenuItem("copy_path", _("_Copy path to clipboard")),
                GeodeGtk.MenuItem("open_path", _("_Open path")),
                None,
                GeodeGtk.MenuItem("thumbnail", _("Set game thumbnail…")),
                None,
                GeodeGtk.MenuItem("maintenance", _("_Maintenance…")),
                None,
                GeodeGtk.MenuItem("remove", _("_Remove from disk…")),
            ),
            GeodeGtk.MenuItem(
                "score",
                _("_Score"),
                GeodeGtk.MenuItem("increase", _("_Increase score")),
                GeodeGtk.MenuItem("decrease", _("_Decrease score")),
                None,
                GeodeGtk.MenuItem("score_0", _("Set score as 0")),
                GeodeGtk.MenuItem("score_1", _("Set score as 1")),
                GeodeGtk.MenuItem("score_2", _("Set score as 2")),
                GeodeGtk.MenuItem("score_3", _("Set score as 3")),
                GeodeGtk.MenuItem("score_4", _("Set score as 4")),
                GeodeGtk.MenuItem("score_5", _("Set score as 5")),
            ),
            GeodeGtk.MenuItem(
                "tools",
                _("_Tools"),
                GeodeGtk.MenuItem("screenshots", _("_Screenshots…")),
                GeodeGtk.MenuItem("game_log", _("Game _log…")),
                GeodeGtk.MenuItem("notes", _("_Notes…")),
                None,
                GeodeGtk.MenuItem("menu_entry", _("_Generate a menu entry")),
                None,
                GeodeGtk.MenuItem("memory_type", _("Specify a _memory type…")),
            )
        )

        # ------------------------------------
        #   Toolbar
        # ------------------------------------

        self.toolbar_consoles = GeodeGtk.Toolbar(
            "toolbar",
            GeodeGtk.ToolbarBox(
                "filter_box",
                GeodeGtk.SearchEntry(
                    "entry",
                    expand=True,
                    placeholder=_("Filter…"),
                ),
                GeodeGtk.MenuButton(
                    "consoles",
                    _("Manage console and emulator"),
                    GeodeGtk.MenuItem("add_console", _("Add _console")),
                    GeodeGtk.MenuItem("add_emulator", _("Add _emulator")),
                    None,
                    GeodeGtk.CheckMenuItem("hide_empty",
                                           _("_Hide empty consoles")),
                    icon_name=Icons.Symbolic.VIEW_MORE,
                ),
                merge=True,
            ),
            border_width=4,
        )

        self.toolbar_games = GeodeGtk.Toolbar(
            "toolbar",
            GeodeGtk.ToolbarBox(
                "launch_box",
                GeodeGtk.Button(
                    "launch",
                    _("Play"),
                    style="suggested-action",
                    tooltip=_("Launch selected game"),
                ),
                GeodeGtk.ToggleButton(
                    "fullscreen",
                    _("Alternate game fullscreen mode"),
                    icon_name=Icons.Symbolic.RESTORE,
                ),
                merge=True,
            ),
            GeodeGtk.Button(
                "parameters",
                _("Set custom parameters"),
                icon_name=Icons.Symbolic.PROPERTIES,
            ),
            GeodeGtk.ToolbarBox(
                "tools_box",
                GeodeGtk.Button(
                    "screenshots",
                    _("Show selected game screenshots"),
                    icon_name=Icons.Symbolic.PROPERTIES,
                ),
                GeodeGtk.Button(
                    "game_log",
                    _("Show selected game log"),
                    icon_name=Icons.Symbolic.PROPERTIES,
                ),
                GeodeGtk.Button(
                    "notes",
                    _("Show selected game notes"),
                    icon_name=Icons.Symbolic.PROPERTIES,
                ),
                merge=True,
            ),
            GeodeGtk.MenuButton(
                "tags",
                _("Show selected game tags"),
                icon_name=Icons.Symbolic.PAPERCLIP,
            ),
            None,
            GeodeGtk.ToolbarSwitch(
                "views",
                GeodeGtk.ToggleButton(
                    "list",
                    _("List view"),
                    icon_name=Icons.Symbolic.LIST,
                ),
                GeodeGtk.ToggleButton(
                    "grid",
                    _("Grid icons"),
                    icon_name=Icons.Symbolic.GRID,
                ),
                default="list",
                merge=True,
            ),
            GeodeGtk.ToolbarBox(
                "filters_box",
                GeodeGtk.SearchEntry(
                    "entry",
                    placeholder=_("Filter…"),
                ),
                GeodeGtk.MenuButton(
                    "filters",
                    _("Advanced filters"),
                    icon_name=Icons.Symbolic.VIEW_MORE,
                    use_popover=True,
                ),
                merge=True,
            ),
            border_width=4,
            spacing=8,
        )

        self.menu_sidebar_tags = Gtk.Menu()

        # ------------------------------------
        #   Toolbar - Game filter
        # ------------------------------------

        self.popover_toolbar_filters = Gtk.Popover()

        # Properties
        self.popover_toolbar_filters.set_modal(True)

        # ------------------------------------
        #   Toolbar - Game filter menu
        # ------------------------------------

        self.frame_filters_favorite = Gtk.Frame()
        self.listbox_filters_favorite = Gtk.ListBox()

        self.widget_filters_favorite = ListBoxItem()
        self.check_filter_favorite = Gtk.Switch()

        self.widget_filters_unfavorite = ListBoxItem()
        self.check_filter_unfavorite = Gtk.Switch()

        self.frame_filters_multiplayer = Gtk.Frame()
        self.listbox_filters_multiplayer = Gtk.ListBox()

        self.widget_filters_multiplayer = ListBoxItem()
        self.check_filter_multiplayer = Gtk.Switch()

        self.widget_filters_singleplayer = ListBoxItem()
        self.check_filter_singleplayer = Gtk.Switch()

        self.frame_filters_finish = Gtk.Frame()
        self.listbox_filters_finish = Gtk.ListBox()

        self.widget_filters_finish = ListBoxItem()
        self.check_filter_finish = Gtk.Switch()

        self.widget_filters_unfinish = ListBoxItem()
        self.check_filter_unfinish = Gtk.Switch()

        self.item_filter_reset = Gtk.Button()

        # Properties
        self.listbox_filters_favorite.set_activate_on_single_click(True)
        self.listbox_filters_favorite.set_selection_mode(
            Gtk.SelectionMode.NONE)

        self.widget_filters_favorite.set_widget(
            self.check_filter_favorite)
        self.widget_filters_favorite.set_option_label(
            _("Favorite"))
        self.check_filter_favorite.set_active(True)

        self.widget_filters_unfavorite.set_widget(
            self.check_filter_unfavorite)
        self.widget_filters_unfavorite.set_option_label(
            _("Unfavorite"))
        self.check_filter_unfavorite.set_active(True)

        self.listbox_filters_multiplayer.set_activate_on_single_click(True)
        self.listbox_filters_multiplayer.set_selection_mode(
            Gtk.SelectionMode.NONE)

        self.widget_filters_multiplayer.set_widget(
            self.check_filter_multiplayer)
        self.widget_filters_multiplayer.set_option_label(
            _("Multiplayer"))
        self.check_filter_multiplayer.set_active(True)

        self.widget_filters_singleplayer.set_widget(
            self.check_filter_singleplayer)
        self.widget_filters_singleplayer.set_option_label(
            _("Singleplayer"))
        self.check_filter_singleplayer.set_active(True)

        self.listbox_filters_finish.set_activate_on_single_click(True)
        self.listbox_filters_finish.set_selection_mode(
            Gtk.SelectionMode.NONE)

        self.widget_filters_finish.set_widget(
            self.check_filter_finish)
        self.widget_filters_finish.set_option_label(
            _("Finish"))
        self.check_filter_finish.set_active(True)

        self.widget_filters_unfinish.set_widget(
            self.check_filter_unfinish)
        self.widget_filters_unfinish.set_option_label(
            _("Unfinished"))
        self.check_filter_unfinish.set_active(True)

        self.item_filter_reset.set_label(_("Reset filters"))

        # ------------------------------------
        #   Infobar
        # ------------------------------------

        self.infobar = GeodeGtk.InfoBar()

        # ------------------------------------
        #   Sidebar - Consoles
        # ------------------------------------

        self.hpaned_consoles = Gtk.Paned()

        self.scroll_consoles = Gtk.ScrolledWindow()
        self.listbox_consoles = Gtk.ListBox()

        self.label_consoles = Gtk.Label()

        # Properties
        self.hpaned_consoles.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.hpaned_consoles.set_position(280)

        self.scroll_consoles.set_min_content_width(200)

        self.listbox_consoles.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.listbox_consoles.set_filter_func(self.__on_filter_consoles)
        self.listbox_consoles.set_sort_func(self.__on_sort_consoles)
        self.listbox_consoles.set_placeholder(self.label_consoles)

        self.label_consoles.set_text(_("No console available"))
        self.label_consoles.set_single_line_mode(False)
        self.label_consoles.set_line_wrap(True)
        self.label_consoles.set_justify(Gtk.Justification.CENTER)
        self.label_consoles.get_style_context().add_class("dim-label")

        # ------------------------------------
        #   Sidebar - Game
        # ------------------------------------

        self.scroll_sidebar = Gtk.ScrolledWindow()

        self.vpaned_games = Gtk.Paned()
        self.hpaned_games = Gtk.Paned()

        # Properties
        self.vpaned_games.set_orientation(Gtk.Orientation.VERTICAL)
        self.hpaned_games.set_orientation(Gtk.Orientation.HORIZONTAL)

        # ------------------------------------
        #   Sidebar - Game title
        # ------------------------------------

        self.label_sidebar_title = Gtk.Label()

        # Properties
        self.label_sidebar_title.set_xalign(0.0)
        self.label_sidebar_title.set_hexpand(True)
        self.label_sidebar_title.set_use_markup(True)
        self.label_sidebar_title.set_margin_bottom(12)
        self.label_sidebar_title.set_halign(Gtk.Align.CENTER)
        self.label_sidebar_title.set_valign(Gtk.Align.CENTER)

        # ------------------------------------
        #   Sidebar - Game screenshot
        # ------------------------------------

        self.view_sidebar_screenshot = Gtk.Viewport()

        self.frame_sidebar_screenshot = Gtk.Frame()
        self.image_sidebar_screenshot = Gtk.Image()

        # Properties
        self.view_sidebar_screenshot.drag_source_set(
            Gdk.ModifierType.BUTTON1_MASK, self.targets, Gdk.DragAction.COPY)

        self.frame_sidebar_screenshot.set_valign(Gtk.Align.CENTER)
        self.frame_sidebar_screenshot.set_halign(Gtk.Align.CENTER)

        self.image_sidebar_screenshot.set_halign(Gtk.Align.CENTER)
        self.image_sidebar_screenshot.set_valign(Gtk.Align.CENTER)

        # ------------------------------------
        #   Sidebar - Game content
        # ------------------------------------

        self.scroll_sidebar_informations = Gtk.ScrolledWindow()

        # Properties
        self.scroll_sidebar_informations.set_propagate_natural_width(True)
        self.scroll_sidebar_informations.set_propagate_natural_height(True)
        self.scroll_sidebar_informations.set_policy(
            Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        # ------------------------------------
        #   Sidebar - Game description
        # ------------------------------------

        self.label_sidebar_played = Gtk.Label()
        self.label_sidebar_played_value = Gtk.Label()

        self.label_sidebar_play_time = Gtk.Label()
        self.label_sidebar_play_time_value = Gtk.Label()

        self.label_sidebar_last_play = Gtk.Label()
        self.label_sidebar_last_play_value = Gtk.Label()

        self.label_sidebar_last_time = Gtk.Label()
        self.label_sidebar_last_time_value = Gtk.Label()

        self.label_sidebar_installed = Gtk.Label()
        self.label_sidebar_installed_value = Gtk.Label()

        self.label_sidebar_emulator = Gtk.Label()
        self.label_sidebar_emulator_value = Gtk.Label()

        self.label_sidebar_score = Gtk.Label()
        self.image_sidebar_score_0 = Gtk.Image()
        self.image_sidebar_score_1 = Gtk.Image()
        self.image_sidebar_score_2 = Gtk.Image()
        self.image_sidebar_score_3 = Gtk.Image()
        self.image_sidebar_score_4 = Gtk.Image()

        # Properties
        self.label_sidebar_played.set_text(_("Launch"))
        self.label_sidebar_played.set_halign(Gtk.Align.END)
        self.label_sidebar_played.set_valign(Gtk.Align.CENTER)
        self.label_sidebar_played.get_style_context().add_class("dim-label")
        self.label_sidebar_played.set_margin_bottom(12)

        self.label_sidebar_played_value.set_use_markup(True)
        self.label_sidebar_played_value.set_halign(Gtk.Align.START)
        self.label_sidebar_played_value.set_valign(Gtk.Align.CENTER)
        self.label_sidebar_played_value.set_margin_bottom(12)

        self.label_sidebar_play_time.set_text(_("Play time"))
        self.label_sidebar_play_time.set_halign(Gtk.Align.END)
        self.label_sidebar_play_time.set_valign(Gtk.Align.CENTER)
        self.label_sidebar_play_time.get_style_context().add_class("dim-label")
        self.label_sidebar_play_time.set_margin_bottom(12)

        self.label_sidebar_play_time_value.set_use_markup(True)
        self.label_sidebar_play_time_value.set_halign(Gtk.Align.START)
        self.label_sidebar_play_time_value.set_valign(Gtk.Align.CENTER)
        self.label_sidebar_play_time_value.set_margin_bottom(12)

        self.label_sidebar_last_play.set_text(_("Last launch"))
        self.label_sidebar_last_play.set_halign(Gtk.Align.END)
        self.label_sidebar_last_play.set_valign(Gtk.Align.CENTER)
        self.label_sidebar_last_play.get_style_context().add_class("dim-label")

        self.label_sidebar_last_play_value.set_use_markup(True)
        self.label_sidebar_last_play_value.set_halign(Gtk.Align.START)
        self.label_sidebar_last_play_value.set_valign(Gtk.Align.CENTER)

        self.label_sidebar_last_time.set_text(_("Last play time"))
        self.label_sidebar_last_time.set_halign(Gtk.Align.END)
        self.label_sidebar_last_time.set_valign(Gtk.Align.CENTER)
        self.label_sidebar_last_time.get_style_context().add_class("dim-label")

        self.label_sidebar_last_time_value.set_use_markup(True)
        self.label_sidebar_last_time_value.set_halign(Gtk.Align.START)
        self.label_sidebar_last_time_value.set_valign(Gtk.Align.CENTER)

        self.label_sidebar_installed.set_text(_("Installed"))
        self.label_sidebar_installed.set_halign(Gtk.Align.END)
        self.label_sidebar_installed.set_valign(Gtk.Align.CENTER)
        self.label_sidebar_installed.get_style_context().add_class("dim-label")
        self.label_sidebar_installed.set_margin_bottom(12)

        self.label_sidebar_installed_value.set_use_markup(True)
        self.label_sidebar_installed_value.set_halign(Gtk.Align.START)
        self.label_sidebar_installed_value.set_valign(Gtk.Align.CENTER)
        self.label_sidebar_installed_value.set_margin_bottom(12)

        self.label_sidebar_emulator.set_text(_("Emulator"))
        self.label_sidebar_emulator.set_halign(Gtk.Align.END)
        self.label_sidebar_emulator.set_valign(Gtk.Align.CENTER)
        self.label_sidebar_emulator.get_style_context().add_class("dim-label")

        self.label_sidebar_emulator_value.set_use_markup(True)
        self.label_sidebar_emulator_value.set_halign(Gtk.Align.START)
        self.label_sidebar_emulator_value.set_valign(Gtk.Align.CENTER)

        self.label_sidebar_score.set_text(_("Score"))
        self.label_sidebar_score.set_halign(Gtk.Align.END)
        self.label_sidebar_score.set_valign(Gtk.Align.CENTER)
        self.label_sidebar_score.get_style_context().add_class("dim-label")

        # ------------------------------------
        #   Games - Placeholder
        # ------------------------------------

        self.scroll_games_placeholder = Gtk.ScrolledWindow()

        self.image_game_placeholder = Gtk.Image()
        self.label_game_placeholder = Gtk.Label()

        # Properties
        self.scroll_games_placeholder.set_no_show_all(True)

        self.image_game_placeholder.set_from_icon_name(
            Icons.Symbolic.GAMING, Gtk.IconSize.DIALOG)
        self.image_game_placeholder.set_pixel_size(256)
        self.image_game_placeholder.set_halign(Gtk.Align.CENTER)
        self.image_game_placeholder.set_valign(Gtk.Align.END)
        self.image_game_placeholder.get_style_context().add_class("dim-label")

        self.label_game_placeholder.set_label(
            _("Start to play by drag & drop some files into interface"))
        self.label_game_placeholder.set_halign(Gtk.Align.CENTER)
        self.label_game_placeholder.set_valign(Gtk.Align.START)

        # ------------------------------------
        #   Games - Treeview / Grid mode
        # ------------------------------------

        self.scroll_games_grid = Gtk.ScrolledWindow()

        self.model_games_grid = Gtk.ListStore(
            GdkPixbuf.Pixbuf,   # Cover icon
            str,                # Name
            object              # Game object
        )
        self.iconview_games = Gtk.IconView()

        self.filter_games_grid = self.model_games_grid.filter_new()
        self.sorted_games_grid = Gtk.TreeModelSort(
            model=self.filter_games_grid)

        # Properties
        self.scroll_games_grid.set_no_show_all(True)

        self.sorted_games_grid.set_sort_column_id(
            Columns.Grid.NAME, Gtk.SortType.ASCENDING)

        self.iconview_games.set_model(self.sorted_games_grid)
        self.iconview_games.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.iconview_games.set_has_tooltip(True)
        self.iconview_games.set_column_spacing(0)
        self.iconview_games.set_row_spacing(0)
        self.iconview_games.set_item_width(96)
        self.iconview_games.set_pixbuf_column(0)
        self.iconview_games.set_text_column(1)
        self.iconview_games.set_spacing(6)

        self.iconview_games.drag_source_set(
            Gdk.ModifierType.BUTTON1_MASK, self.targets, Gdk.DragAction.COPY)

        # ------------------------------------
        #   Games - Treeview / List mode
        # ------------------------------------

        self.scroll_games_list = Gtk.ScrolledWindow()

        self.model_games_list = Gtk.ListStore(
            GdkPixbuf.Pixbuf,   # Favorite icon
            GdkPixbuf.Pixbuf,   # Multiplayer icon
            GdkPixbuf.Pixbuf,   # Finish icon
            str,                # Name
            int,                # Played
            str,                # Last play
            str,                # Last time play
            str,                # Time play
            int,                # Score
            str,                # Installed
            GdkPixbuf.Pixbuf,   # Custom parameters
            GdkPixbuf.Pixbuf,   # Screenshots
            GdkPixbuf.Pixbuf,   # Save states
            object,             # Game object
            GdkPixbuf.Pixbuf    # Thumbnail
        )
        self.treeview_games = Gtk.TreeView()

        self.filter_games_list = self.model_games_list.filter_new()
        self.sorted_games_list = Gtk.TreeModelSort(
            model=self.filter_games_list)

        self.column_game_favorite = Gtk.TreeViewColumn()
        self.column_game_multiplayer = Gtk.TreeViewColumn()
        self.column_game_finish = Gtk.TreeViewColumn()
        self.column_game_name = Gtk.TreeViewColumn()
        self.column_game_play = Gtk.TreeViewColumn()
        self.column_game_last_play = Gtk.TreeViewColumn()
        self.column_game_play_time = Gtk.TreeViewColumn()
        self.column_game_score = Gtk.TreeViewColumn()
        self.column_game_installed = Gtk.TreeViewColumn()
        self.column_game_flags = Gtk.TreeViewColumn()

        self.cell_game_favorite = Gtk.CellRendererPixbuf()
        self.cell_game_multiplayer = Gtk.CellRendererPixbuf()
        self.cell_game_finish = Gtk.CellRendererPixbuf()
        self.cell_game_name = Gtk.CellRendererText()
        self.cell_game_play = Gtk.CellRendererText()
        self.cell_game_last_play = Gtk.CellRendererText()
        self.cell_game_last_play_time = Gtk.CellRendererText()
        self.cell_game_play_time = Gtk.CellRendererText()
        self.cell_game_score_first = Gtk.CellRendererPixbuf()
        self.cell_game_score_second = Gtk.CellRendererPixbuf()
        self.cell_game_score_third = Gtk.CellRendererPixbuf()
        self.cell_game_score_fourth = Gtk.CellRendererPixbuf()
        self.cell_game_score_fifth = Gtk.CellRendererPixbuf()
        self.cell_game_installed = Gtk.CellRendererText()
        self.cell_game_except = Gtk.CellRendererPixbuf()
        self.cell_game_snapshots = Gtk.CellRendererPixbuf()
        self.cell_game_save = Gtk.CellRendererPixbuf()
        self.cell_game_thumbnail = Gtk.CellRendererPixbuf()

        # Properties
        self.scroll_games_list.set_no_show_all(True)

        self.sorted_games_list.set_sort_func(Columns.List.FAVORITE,
                                             self.__on_sort_games,
                                             Columns.List.FAVORITE)
        self.sorted_games_list.set_sort_func(Columns.List.MULTIPLAYER,
                                             self.__on_sort_games,
                                             Columns.List.MULTIPLAYER)
        self.sorted_games_list.set_sort_func(Columns.List.FINISH,
                                             self.__on_sort_games,
                                             Columns.List.FINISH)
        self.sorted_games_list.set_sort_func(Columns.List.LAST_PLAY,
                                             self.__on_sort_games,
                                             Columns.List.LAST_PLAY)
        self.sorted_games_list.set_sort_func(Columns.List.TIME_PLAY,
                                             self.__on_sort_games,
                                             Columns.List.TIME_PLAY)
        self.sorted_games_list.set_sort_func(Columns.List.SCORE,
                                             self.__on_sort_games,
                                             Columns.List.SCORE)
        self.sorted_games_list.set_sort_func(Columns.List.INSTALLED,
                                             self.__on_sort_games,
                                             Columns.List.INSTALLED)

        self.treeview_games.set_model(self.sorted_games_list)
        self.treeview_games.set_search_column(Columns.List.NAME)
        self.treeview_games.set_headers_clickable(True)
        self.treeview_games.set_headers_visible(True)
        self.treeview_games.set_show_expanders(False)
        self.treeview_games.set_enable_search(False)
        self.treeview_games.set_has_tooltip(True)

        self.treeview_games.drag_source_set(
            Gdk.ModifierType.BUTTON1_MASK, self.targets, Gdk.DragAction.COPY)

        self.column_game_name.set_title(_("Name"))
        self.column_game_play.set_title(_("Launch"))
        self.column_game_last_play.set_title(_("Last launch"))
        self.column_game_play_time.set_title(_("Play time"))
        self.column_game_score.set_title(_("Score"))
        self.column_game_installed.set_title(_("Installed"))
        self.column_game_flags.set_title(_("Flags"))

        self.column_game_favorite.set_resizable(False)
        self.column_game_favorite.set_reorderable(True)
        self.column_game_favorite.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        self.column_game_favorite.pack_start(
            self.cell_game_favorite, False)
        self.column_game_favorite.set_sort_column_id(Columns.List.FAVORITE)

        self.column_game_multiplayer.set_resizable(False)
        self.column_game_multiplayer.set_reorderable(True)
        self.column_game_multiplayer.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        self.column_game_multiplayer.pack_start(
            self.cell_game_multiplayer, False)
        self.column_game_multiplayer.set_sort_column_id(
            Columns.List.MULTIPLAYER)

        self.column_game_finish.set_resizable(False)
        self.column_game_finish.set_reorderable(True)
        self.column_game_finish.set_sizing(Gtk.TreeViewColumnSizing.FIXED)
        self.column_game_finish.pack_start(
            self.cell_game_finish, False)
        self.column_game_finish.set_sort_column_id(Columns.List.FINISH)

        self.column_game_name.set_expand(True)
        self.column_game_name.set_resizable(True)
        self.column_game_name.set_reorderable(True)
        self.column_game_name.set_min_width(100)
        self.column_game_name.set_fixed_width(300)
        self.column_game_name.set_sort_column_id(Columns.List.NAME)
        self.column_game_name.pack_start(
            self.cell_game_thumbnail, False)
        self.column_game_name.pack_start(
            self.cell_game_name, True)

        self.column_game_play.set_reorderable(True)
        self.column_game_play.set_sort_column_id(Columns.List.PLAYED)
        self.column_game_play.set_alignment(.5)
        self.column_game_play.pack_start(
            self.cell_game_play, False)

        self.column_game_last_play.set_reorderable(True)
        self.column_game_last_play.set_sort_column_id(Columns.List.LAST_PLAY)
        self.column_game_last_play.set_alignment(.5)
        self.column_game_last_play.pack_start(
            self.cell_game_last_play, False)
        self.column_game_last_play.pack_start(
            self.cell_game_last_play_time, False)

        self.column_game_play_time.set_reorderable(True)
        self.column_game_play_time.set_sort_column_id(Columns.List.TIME_PLAY)
        self.column_game_play_time.set_alignment(.5)
        self.column_game_play_time.pack_start(
            self.cell_game_play_time, False)

        self.column_game_score.set_reorderable(True)
        self.column_game_score.set_sort_column_id(Columns.List.SCORE)
        self.column_game_score.set_alignment(.5)
        self.column_game_score.pack_start(
            self.cell_game_score_first, False)
        self.column_game_score.pack_start(
            self.cell_game_score_second, False)
        self.column_game_score.pack_start(
            self.cell_game_score_third, False)
        self.column_game_score.pack_start(
            self.cell_game_score_fourth, False)
        self.column_game_score.pack_start(
            self.cell_game_score_fifth, False)

        self.column_game_installed.set_reorderable(True)
        self.column_game_installed.set_sort_column_id(Columns.List.INSTALLED)
        self.column_game_installed.set_alignment(.5)
        self.column_game_installed.pack_start(
            self.cell_game_installed, False)

        self.column_game_flags.set_reorderable(True)
        self.column_game_flags.set_alignment(.5)
        self.column_game_flags.pack_start(
            self.cell_game_except, False)
        self.column_game_flags.pack_start(
            self.cell_game_snapshots, False)
        self.column_game_flags.pack_start(
            self.cell_game_save, False)

        self.column_game_favorite.add_attribute(
            self.cell_game_favorite, "pixbuf", Columns.List.FAVORITE)
        self.column_game_multiplayer.add_attribute(
            self.cell_game_multiplayer, "pixbuf", Columns.List.MULTIPLAYER)
        self.column_game_finish.add_attribute(
            self.cell_game_finish, "pixbuf", Columns.List.FINISH)
        self.column_game_name.add_attribute(
            self.cell_game_name, "text", Columns.List.NAME)
        self.column_game_name.add_attribute(
            self.cell_game_thumbnail, "pixbuf", Columns.List.THUMBNAIL)
        self.column_game_play.add_attribute(
            self.cell_game_play, "text", Columns.List.PLAYED)
        self.column_game_last_play.add_attribute(
            self.cell_game_last_play, "text", Columns.List.LAST_PLAY)
        self.column_game_last_play.add_attribute(
            self.cell_game_last_play_time, "text", Columns.List.LAST_TIME_PLAY)
        self.column_game_play_time.add_attribute(
            self.cell_game_play_time, "text", Columns.List.TIME_PLAY)
        self.column_game_installed.add_attribute(
            self.cell_game_installed, "text", Columns.List.INSTALLED)
        self.column_game_flags.add_attribute(
            self.cell_game_except, "pixbuf", Columns.List.PARAMETER)
        self.column_game_flags.add_attribute(
            self.cell_game_snapshots, "pixbuf", Columns.List.SCREENSHOT)
        self.column_game_flags.add_attribute(
            self.cell_game_save, "pixbuf", Columns.List.SAVESTATE)

        self.column_game_score.set_cell_data_func(
            self.cell_game_score_first, self.__on_update_game_columns)

        self.cell_game_favorite.set_alignment(.5, .5)
        self.cell_game_multiplayer.set_alignment(.5, .5)
        self.cell_game_finish.set_alignment(.5, .5)
        self.cell_game_name.set_alignment(0, .5)
        self.cell_game_thumbnail.set_alignment(.5, .5)
        self.cell_game_play.set_alignment(.5, .5)
        self.cell_game_last_play.set_alignment(0, .5)
        self.cell_game_last_play_time.set_alignment(1, .5)
        self.cell_game_play_time.set_alignment(.5, .5)
        self.cell_game_score_first.set_alignment(.5, .5)
        self.cell_game_score_second.set_alignment(.5, .5)
        self.cell_game_score_third.set_alignment(.5, .5)
        self.cell_game_score_fourth.set_alignment(.5, .5)
        self.cell_game_score_fifth.set_alignment(.5, .5)
        self.cell_game_installed.set_alignment(.5, .5)

        # self.cell_game_name.set_property("editable", True)
        self.cell_game_name.set_property("ellipsize", Pango.EllipsizeMode.END)

        self.cell_game_name.set_padding(4, 4)
        self.cell_game_thumbnail.set_padding(2, 0)
        self.cell_game_play.set_padding(4, 0)
        self.cell_game_last_play.set_padding(4, 0)
        self.cell_game_last_play_time.set_padding(4, 0)
        self.cell_game_score_first.set_padding(2, 0)
        self.cell_game_score_second.set_padding(2, 0)
        self.cell_game_score_third.set_padding(2, 0)
        self.cell_game_score_fourth.set_padding(2, 0)
        self.cell_game_score_fifth.set_padding(2, 0)
        self.cell_game_installed.set_padding(4, 0)
        self.cell_game_except.set_padding(2, 0)
        self.cell_game_snapshots.set_padding(2, 0)
        self.cell_game_save.set_padding(2, 0)

        # ------------------------------------
        #   Statusbar
        # ------------------------------------

        self.statusbar = GeodeGtk.Statusbar()

    def __init_packing(self):
        """ Initialize widgets packing in main window
        """

        # Main widgets
        self.grid.pack_start(self.menubar, False, False, 0)
        self.grid.pack_start(self.hpaned_consoles, True, True, 0)
        self.grid.pack_start(self.statusbar, False, False, 0)

        # ------------------------------------
        #   Menubar
        # ------------------------------------

        self.menubar.append(self.menubar_main)
        self.menubar.append(self.menubar_view)
        self.menubar.append(self.menubar_game)
        self.menubar.append(self.menubar_edit)
        self.menubar.append(self.menubar_help)

        # ------------------------------------
        #   Toolbar - Consoles
        # ------------------------------------

        self.grid_consoles.pack_start(
            self.toolbar_consoles, False, False, 0)

        # ------------------------------------
        #   Sidebar - Consoles
        # ------------------------------------

        self.grid_consoles.pack_start(
            self.scroll_consoles, True, True, 0)

        self.scroll_consoles.add(self.listbox_consoles)

        self.hpaned_consoles.pack1(self.grid_consoles, False, False)
        self.hpaned_consoles.pack2(self.vpaned_games, True, True)

        # ------------------------------------
        #   Toolbar - Games
        # ------------------------------------

        # Toolbar - Tags menu
        self.toolbar_games.get_widget("tags").set_popup(self.menu_sidebar_tags)

        # Toolbar - Filters menu
        self.toolbar_games.get_widget("filters").set_popover(
            self.popover_toolbar_filters)

        self.popover_toolbar_filters.add(self.grid_game_filters_popover)

        self.grid_game_filters_popover.pack_start(
            self.frame_filters_favorite, False, False, 0)
        self.grid_game_filters_popover.pack_start(
            self.frame_filters_multiplayer, False, False, 0)
        self.grid_game_filters_popover.pack_start(
            self.frame_filters_finish, False, False, 0)
        self.grid_game_filters_popover.pack_start(
            self.item_filter_reset, False, False, 0)

        self.frame_filters_favorite.add(self.listbox_filters_favorite)

        self.listbox_filters_favorite.add(
            self.widget_filters_favorite)
        self.listbox_filters_favorite.add(
            self.widget_filters_unfavorite)

        self.frame_filters_multiplayer.add(self.listbox_filters_multiplayer)

        self.listbox_filters_multiplayer.add(
            self.widget_filters_multiplayer)
        self.listbox_filters_multiplayer.add(
            self.widget_filters_singleplayer)

        self.frame_filters_finish.add(self.listbox_filters_finish)

        self.listbox_filters_finish.add(
            self.widget_filters_finish)
        self.listbox_filters_finish.add(
            self.widget_filters_unfinish)

        # ------------------------------------
        #   Games
        # ------------------------------------

        self.grid_games.pack_start(self.toolbar_games, False, False, 0)
        self.grid_games.pack_start(self.infobar, False, False, 0)
        self.grid_games.pack_start(self.grid_games_views, True, True, 0)

        self.vpaned_games.pack1(self.hpaned_games, True, True)

        self.hpaned_games.pack1(self.grid_games, True, True)

        # Sidebar
        self.scroll_sidebar.add(self.grid_sidebar)

        self.frame_sidebar_screenshot.add(self.view_sidebar_screenshot)
        self.view_sidebar_screenshot.add(self.image_sidebar_screenshot)

        self.grid_sidebar.attach(
            self.label_sidebar_title, 0, 0, 1, 1)
        self.grid_sidebar.attach(
            self.grid_sidebar_content, 0, 1, 1, 1)
        self.grid_sidebar.attach(
            self.grid_sidebar_informations, 0, 2, 1, 1)

        self.grid_sidebar_content.pack_start(
            self.frame_sidebar_screenshot, True, True, 0)
        self.grid_sidebar_content.pack_start(
            self.grid_sidebar_score, False, False, 0)

        # Sidebar - Informations
        self.grid_sidebar_informations.attach(
            self.label_sidebar_played, 0, 0, 1, 1)
        self.grid_sidebar_informations.attach(
            self.label_sidebar_played_value, 1, 0, 1, 1)
        self.grid_sidebar_informations.attach(
            self.label_sidebar_play_time, 0, 1, 1, 1)
        self.grid_sidebar_informations.attach(
            self.label_sidebar_play_time_value, 1, 1, 1, 1)
        self.grid_sidebar_informations.attach(
            self.label_sidebar_last_play, 0, 2, 1, 1)
        self.grid_sidebar_informations.attach(
            self.label_sidebar_last_play_value, 1, 2, 1, 1)
        self.grid_sidebar_informations.attach(
            self.label_sidebar_last_time, 0, 3, 1, 1)
        self.grid_sidebar_informations.attach(
            self.label_sidebar_last_time_value, 1, 3, 1, 1)
        self.grid_sidebar_informations.attach(
            self.label_sidebar_installed, 0, 4, 1, 1)
        self.grid_sidebar_informations.attach(
            self.label_sidebar_installed_value, 1, 4, 1, 1)
        self.grid_sidebar_informations.attach(
            self.label_sidebar_emulator, 0, 5, 1, 1)
        self.grid_sidebar_informations.attach(
            self.label_sidebar_emulator_value, 1, 5, 1, 1)

        self.grid_sidebar_score.pack_start(
            self.image_sidebar_score_0, False, False, 0)
        self.grid_sidebar_score.pack_start(
            self.image_sidebar_score_1, False, False, 0)
        self.grid_sidebar_score.pack_start(
            self.image_sidebar_score_2, False, False, 0)
        self.grid_sidebar_score.pack_start(
            self.image_sidebar_score_3, False, False, 0)
        self.grid_sidebar_score.pack_start(
            self.image_sidebar_score_4, False, False, 0)

        # Games views
        self.grid_games_views.pack_start(
            self.scroll_games_placeholder, True, True, 0)
        self.grid_games_views.pack_start(
            self.scroll_games_list, True, True, 0)
        self.grid_games_views.pack_start(
            self.scroll_games_grid, True, True, 0)

        # Games placeholder
        self.scroll_games_placeholder.add(self.grid_games_placeholder)

        self.grid_games_placeholder.pack_start(
            self.image_game_placeholder, True, True, 0)
        self.grid_games_placeholder.pack_start(
            self.label_game_placeholder, True, True, 0)

        # Games treeview / grid
        self.scroll_games_grid.add(self.iconview_games)

        # Games treeview / list
        self.scroll_games_list.add(self.treeview_games)

        self.add(self.grid)

    def __init_signals(self):
        """ Initialize widgets signals
        """

        self.logger.info("Associate signals to main interface")

        signals = {
            self: {
                "game-started": [
                    {"method": self.__on_game_started},
                ],
                "game-terminate": [
                    {"method": self.__on_game_terminate},
                ],
                "script-terminate": [
                    {"method": self.__on_script_terminate},
                ],
                "delete-event": [
                    {"method": self.__stop_interface},
                ],
                "key-press-event": [
                    {"method": self.__on_manage_keys},
                ],
            },
            self.headerbar: {
                "activate": [
                    {
                        "method": self.__on_show_preferences,
                        "widget": "preferences",
                    },
                    {
                        "method": self.__on_show_log,
                        "widget": "log",
                    },
                    {
                        "method": self.__on_show_clean_cache,
                        "widget": "clean_cache",
                    },
                    {
                        "method": self.__on_show_external_link,
                        "widget": "website",
                    },
                    {
                        "method": self.__on_show_external_link,
                        "widget": "report",
                    },
                    {
                        "method": self.__on_show_about,
                        "widget": "about",
                    },
                    {
                        "method": self.__stop_interface,
                        "widget": "quit",
                    },
                ] + [
                    {
                        "method": self.__on_switch_column_visibility,
                        "args": (widget,),
                        "widget": widget,
                        "allow_block_signal": True,
                    } for widget in self.__columns_labels
                ],
                "toggled": [
                    {
                        "method": self.__on_activate_sidebar,
                        "widget": "show_sidebar",
                        "allow_block_signal": True,
                    },
                    {
                        "method": self.__on_move_sidebar,
                        "widget": "right",
                        "allow_block_signal": True,
                    },
                    {
                        "method": self.__on_move_sidebar,
                        "widget": "bottom",
                        "allow_block_signal": True,
                    },
                    {
                        "method": self.__on_activate_dark_theme,
                        "widget": "dark_theme",
                        "allow_block_signal": True,
                    },
                    {
                        "method": self.__on_activate_statusbar,
                        "widget": "show_statusbar",
                        "allow_block_signal": True,
                    },
                    {
                        "method": self.__on_switch_games_view,
                        "widget": "list",
                        "allow_block_signal": True,
                    },
                    {
                        "method": self.__on_switch_games_view,
                        "widget": "grid",
                        "allow_block_signal": True,
                    },
                ],
            },
            self.menubar_main: {
                "activate": [
                    {
                        "method": self.__on_show_preferences,
                        "widget": "preferences",
                    },
                    {
                        "method": self.__on_show_log,
                        "widget": "log",
                    },
                    {
                        "method": self.__on_show_clean_cache,
                        "widget": "clean_cache",
                    },
                    {
                        "method": self.__stop_interface,
                        "widget": "quit",
                    },
                ],
            },
            self.menubar_view: {
                "activate": [
                    {
                        "method": self.__on_switch_column_visibility,
                        "args": (widget,),
                        "widget": widget,
                        "allow_block_signal": True,
                    } for widget in self.__columns_labels
                ],
                "toggled": [
                    {
                        "method": self.__on_activate_sidebar,
                        "widget": "show_sidebar",
                        "allow_block_signal": True,
                    },
                    {
                        "method": self.__on_move_sidebar,
                        "widget": "right",
                        "allow_block_signal": True,
                    },
                    {
                        "method": self.__on_move_sidebar,
                        "widget": "bottom",
                        "allow_block_signal": True,
                    },
                    {
                        "method": self.__on_activate_dark_theme,
                        "widget": "dark_theme",
                        "allow_block_signal": True,
                    },
                    {
                        "method": self.__on_activate_statusbar,
                        "widget": "show_statusbar",
                        "allow_block_signal": True,
                    },
                    {
                        "method": self.__on_switch_games_view,
                        "widget": "list",
                        "allow_block_signal": True,
                    },
                    {
                        "method": self.__on_switch_games_view,
                        "widget": "grid",
                        "allow_block_signal": True,
                    },
                ],
            },
            self.menubar_game: {
                "activate": [
                    {
                        "method": self.__on_game_launch,
                        "widget": "launch",
                    },
                    {
                        "method": self.__on_game_parameters,
                        "widget": "properties",
                    },
                    {
                        "method": self.__on_show_viewer,
                        "widget": "screenshots",
                    },
                    {
                        "method": self.__on_show_log,
                        "widget": "game_log",
                    },
                    {
                        "method": self.__on_show_notes,
                        "widget": "notes",
                    },
                ] + [
                    {
                        "method": self.update_game_flag,
                        "widget": widget,
                        "allow_block_signal": True,
                    } for widget in self.__flags_labels
                ],
                "toggled": [
                    {
                        "method": self.__on_activate_fullscreen,
                        "widget": "fullscreen",
                        "allow_block_signal": True,
                    },
                ],
            },
            self.menubar_edit: {
                "activate": [
                    {
                        "method": self.__on_game_renamed,
                        "widget": "rename",
                    },
                    {
                        "method": self.__on_game_duplicate,
                        "widget": "duplicate",
                    },
                    {
                        "method": self.__on_game_edit_file,
                        "widget": "game_file",
                    },
                    {
                        "method": self.__on_copy_path_to_clipboard,
                        "widget": "copy_path",
                    },
                    {
                        "method": self.__on_open_directory,
                        "widget": "open_path",
                    },
                    {
                        "method": self.__on_game_generate_desktop,
                        "widget": "menu_entry",
                    },
                    {
                        "method": self.__on_game_cover,
                        "widget": "thumbnail",
                    },
                    {
                        "method": self.__on_game_maintenance,
                        "widget": "maintenance",
                    },
                    {
                        "method": self.__on_game_removed,
                        "widget": "remove",
                    },
                    {
                        "method": self.__on_game_backup_memory,
                        "widget": "memory_type",
                    },
                    {
                        "method": self.__on_game_score,
                        "widget": "increase",
                    },
                    {
                        "method": self.__on_game_score,
                        "widget": "decrease",
                    },
                ] + [
                    {
                        "method": self.__on_game_score,
                        "args": (index,),
                        "widget": f"score_{index}",
                    } for index in range(0, 6)
                ],
            },
            self.menubar_help: {
                "activate": [
                    {
                        "method": self.__on_show_external_link,
                        "widget": "website",
                    },
                    {
                        "method": self.__on_show_external_link,
                        "widget": "report",
                    },
                    {
                        "method": self.__on_show_about,
                        "widget": "about",
                    },
                ],
            },
            self.menu_game: {
                "activate": [
                    {
                        "method": self.__on_game_launch,
                        "widget": "launch",
                    },
                    {
                        "method": self.__on_game_parameters,
                        "widget": "properties",
                    },
                    {
                        "method": self.__on_game_renamed,
                        "widget": "rename",
                    },
                    {
                        "method": self.__on_game_duplicate,
                        "widget": "duplicate",
                    },
                    {
                        "method": self.__on_game_edit_file,
                        "widget": "game_file",
                    },
                    {
                        "method": self.__on_copy_path_to_clipboard,
                        "widget": "copy_path",
                    },
                    {
                        "method": self.__on_open_directory,
                        "widget": "open_path",
                    },
                    {
                        "method": self.__on_game_cover,
                        "widget": "thumbnail",
                    },
                    {
                        "method": self.__on_game_maintenance,
                        "widget": "maintenance",
                    },
                    {
                        "method": self.__on_game_removed,
                        "widget": "remove",
                    },
                    {
                        "method": self.__on_game_score,
                        "widget": "increase",
                    },
                    {
                        "method": self.__on_game_score,
                        "widget": "decrease",
                    },
                    {
                        "method": self.__on_show_viewer,
                        "widget": "screenshots",
                    },
                    {
                        "method": self.__on_game_log,
                        "widget": "game_log",
                    },
                    {
                        "method": self.__on_show_notes,
                        "widget": "notes",
                    },
                    {
                        "method": self.__on_game_generate_desktop,
                        "widget": "menu_entry",
                    },
                    {
                        "method": self.__on_game_backup_memory,
                        "widget": "memory_type",
                    },
                ] + [
                    {
                        "method": self.update_game_flag,
                        "args": (widget,),
                        "widget": widget,
                        "allow_block_signal": True,
                    } for widget in self.__flags_labels
                ] + [
                    {
                        "method": self.__on_game_score,
                        "args": (index,),
                        "widget": f"score_{index}",
                    } for index in range(0, 6)
                ],
            },
            self.menu_consoles: {
                "activate": [
                    {
                        "method": self.__on_show_console_editor,
                        "widget": "edit_console",
                    },
                    {
                        "method": self.__on_remove_console,
                        "widget": "remove_console",
                    },
                    {
                        "method": self.__on_show_emulator_editor,
                        "widget": "edit_emulator",
                    },
                    {
                        "method": self.__on_show_emulator_config,
                        "widget": "edit_file",
                    },
                    {
                        "method": self.__on_copy_path_to_clipboard,
                        "widget": "copy_path",
                    },
                    {
                        "method": self.__on_open_directory,
                        "widget": "open_path",
                    },
                    {
                        "method": self.__on_reload_games,
                        "widget": "reload",
                    },
                    {
                        "method": self.__on_change_console_option,
                        "widget": "favorite",
                        "allow_block_signal": True,
                    },
                    {
                        "method": self.__on_change_console_option,
                        "widget": "recursive",
                        "allow_block_signal": True,
                    },
                ],
            },
            self.treeview_games: {
                "cursor-changed": [
                    {
                        "method": self.__on_selected_game,
                        "allow_block_signal": True,
                    },
                ],
                "row-activated": [
                    {"method": self.__on_game_launch},
                ],
                "button-press-event": [
                    {"method": self.__on_game_menu_show},
                ],
                "key-release-event": [
                    {"method": self.__on_game_menu_show},
                ],
                "drag-data-get": [
                    {"method": self.__on_dnd_send_data},
                ],
                "query-tooltip": [
                    {"method": self.__on_selected_game_tooltip},
                ],
            },
            self.iconview_games: {
                "selection-changed": [
                    {
                        "method": self.__on_selected_game,
                        "allow_block_signal": True,
                    },
                ],
                "item-activated": [
                    {"method": self.__on_game_launch},
                ],
                "button-press-event": [
                    {"method": self.__on_game_menu_show},
                ],
                "key-release-event": [
                    {"method": self.__on_game_menu_show},
                ],
                "drag-data-get": [
                    {"method": self.__on_dnd_send_data},
                ],
                "query-tooltip": [
                    {"method": self.__on_selected_game_tooltip},
                ],
            },
            self.listbox_consoles: {
                "row-activated": [
                    {"method": self.__on_selected_console},
                ],
                "button-press-event": [
                    {"method": self.__on_console_menu_show},
                ],
                "key-release-event": [
                    {"method": self.__on_console_menu_show},
                ],
            },
            self.toolbar_consoles: {
                "activate": [
                    {
                        "method": self.__on_show_console_editor,
                        "widget": "add_console",
                    },
                    {
                        "method": self.__on_show_emulator_editor,
                        "widget": "add_emulator",
                    },
                    {
                        "method": self.__on_change_console_option,
                        "widget": "hide_empty",
                        "allow_block_signal": True,
                    },
                ],
                "changed": [
                    {
                        "method": self.__on_update_consoles,
                        "widget": "entry",
                    },
                ],
            },
            self.toolbar_games: {
                "clicked": [
                    {
                        "method": self.__on_game_launch,
                        "widget": "launch",
                    },
                    {
                        "method": self.__on_show_viewer,
                        "widget": "screenshots",
                    },
                    {
                        "method": self.__on_game_log,
                        "widget": "game_log",
                    },
                    {
                        "method": self.__on_show_notes,
                        "widget": "notes",
                    },
                    {
                        "method": self.__on_game_parameters,
                        "widget": "parameters",
                    },
                ],
                "changed": [
                    {
                        "method": self.filters_update,
                        "widget": "entry",
                    },
                ],
                "toggled": [
                    {
                        "method": self.__on_activate_fullscreen,
                        "widget": "fullscreen",
                        "allow_block_signal": True,
                    },
                    {
                        "method": self.__on_switch_games_view,
                        "widget": "list",
                        "allow_block_signal": True,
                    },
                    {
                        "method": self.__on_switch_games_view,
                        "widget": "grid",
                        "allow_block_signal": True,
                    },
                ],
            }
        }

        # ------------------------------------
        #   Connect widget and store signals
        # ------------------------------------

        for instance, actions_dict in signals.items():
            for action, storage in actions_dict.items():
                for metadata in storage:
                    try:
                        # Use standard widget from Gtk
                        widget = instance
                        # Retrieve subwidget from GeodeGtk objects
                        if "widget" in metadata:
                            widget = instance.get_widget(metadata["widget"])

                        signal = widget.connect(
                            action,
                            metadata.get("method"),
                            *metadata.get("args", list()))

                        if metadata.get("allow_block_signal", False):
                            self.signals_storage[signal] = widget

                            if not hasattr(widget, 'identifier'):
                                continue

                            self.logger.debug(
                                f"Associate signal identifier '{signal}' to "
                                f"{instance.identifier}/{widget.identifier}")

                    except:
                        self.logger.exception(
                            f"Cannot connect signal for {widget}: "
                            f"{list(metadata.values())}")

        del signals

        # ------------------------------------
        #   Toolbar - Game
        # ------------------------------------

        self.listbox_filters_favorite.connect(
            "row-activated", on_activate_listboxrow)
        self.listbox_filters_multiplayer.connect(
            "row-activated", on_activate_listboxrow)
        self.listbox_filters_finish.connect(
            "row-activated", on_activate_listboxrow)

        self.check_filter_favorite.connect(
            "state-set", self.filters_update)
        self.check_filter_unfavorite.connect(
            "state-set", self.filters_update)
        self.check_filter_multiplayer.connect(
            "state-set", self.filters_update)
        self.check_filter_singleplayer.connect(
            "state-set", self.filters_update)
        self.check_filter_finish.connect(
            "state-set", self.filters_update)
        self.check_filter_unfinish.connect(
            "state-set", self.filters_update)
        self.item_filter_reset.connect(
            "clicked", self.filters_reset)

        # ------------------------------------
        #   Sidebar - Games
        # ------------------------------------

        self.view_sidebar_screenshot.connect(
            "drag-data-get", self.__on_dnd_send_data)

        # ------------------------------------
        #   Placeholder - Games
        # ------------------------------------

        self.grid_games_views.connect(
            "drag-data-received", self.__on_dnd_received_data)

        # ------------------------------------
        #   Games views
        # ------------------------------------

        self.filter_games_list.set_visible_func(self.filters_match)
        self.filter_games_grid.set_visible_func(self.filters_match)

    def __init_storage(self):
        """ Initialize reference and constant storages
        """

        # ------------------------------------
        #   Constants
        # ------------------------------------

        self.__toolbar_sizes = {
            "menu": Gtk.IconSize.MENU,
            "small-toolbar": Gtk.IconSize.SMALL_TOOLBAR,
            "large-toolbar": Gtk.IconSize.LARGE_TOOLBAR,
            "button": Gtk.IconSize.BUTTON,
            "dnd": Gtk.IconSize.DND,
            "dialog": Gtk.IconSize.DIALOG
        }

        self.__treeview_lines = {
            "none": Gtk.TreeViewGridLines.NONE,
            "horizontal": Gtk.TreeViewGridLines.HORIZONTAL,
            "vertical": Gtk.TreeViewGridLines.VERTICAL,
            "both": Gtk.TreeViewGridLines.BOTH
        }

        # ------------------------------------
        #   References
        # ------------------------------------

        # Store image references with associate icons
        self.__images_storage = {
            self.headerbar.get_widget("main_image"):
                Icons.Symbolic.MENU,
            self.headerbar.get_widget("display_image"):
                Icons.Symbolic.VIDEO,
            self.toolbar_consoles.get_widget("consoles_image"):
                Icons.Symbolic.VIEW_MORE,
            self.toolbar_games.get_widget("fullscreen_image"):
                Icons.Symbolic.RESTORE,
            self.toolbar_games.get_widget("grid_image"):
                Icons.Symbolic.GRID,
            self.toolbar_games.get_widget("list_image"):
                Icons.Symbolic.LIST,
            self.toolbar_games.get_widget("notes_image"):
                Icons.Symbolic.EDITOR,
            self.toolbar_games.get_widget("game_log_image"):
                Icons.Symbolic.TERMINAL,
            self.toolbar_games.get_widget("parameters_image"):
                Icons.Symbolic.PROPERTIES,
            self.toolbar_games.get_widget("screenshots_image"):
                Icons.Symbolic.CAMERA,
            self.toolbar_games.get_widget("tags_image"):
                Icons.Symbolic.PAPERCLIP,
        }

        # Store treeview columns references
        self.__columns_storage = {
            "favorite": self.column_game_favorite,
            "multiplayer": self.column_game_multiplayer,
            "finish": self.column_game_finish,
            "name": self.column_game_name,
            "play": self.column_game_play,
            "last_play": self.column_game_last_play,
            "play_time": self.column_game_play_time,
            "score": self.column_game_score,
            "installed": self.column_game_installed,
            "flags": self.column_game_flags
        }

        # Store widgets references which can change sensitive state
        self.__widgets_storage = (
            # Menubar - Game
            self.menubar_game.get_widget("favorite"),
            self.menubar_game.get_widget("finish"),
            self.menubar_game.get_widget("game_log"),
            self.menubar_game.get_widget("launch"),
            self.menubar_game.get_widget("multiplayer"),
            self.menubar_game.get_widget("notes"),
            self.menubar_game.get_widget("properties"),
            self.menubar_game.get_widget("screenshots"),
            # Menubar - Edit
            self.menubar_edit.get_widget("copy_path"),
            self.menubar_edit.get_widget("duplicate"),
            self.menubar_edit.get_widget("game_file"),
            self.menubar_edit.get_widget("maintenance"),
            self.menubar_edit.get_widget("memory_type"),
            self.menubar_edit.get_widget("menu_entry"),
            self.menubar_edit.get_widget("open_path"),
            self.menubar_edit.get_widget("remove"),
            self.menubar_edit.get_widget("rename"),
            self.menubar_edit.get_widget("thumbnail"),
            self.menubar_edit.get_widget("score"),
            # Toolbar
            self.toolbar_games.get_widget("launch"),
            self.toolbar_games.get_widget("tags"),
            self.toolbar_games.get_widget("notes"),
            self.toolbar_games.get_widget("game_log"),
            self.toolbar_games.get_widget("parameters"),
            self.toolbar_games.get_widget("screenshots"),
            # Game menu
            self.menu_game.get_widget("copy_path"),
            self.menu_game.get_widget("duplicate"),
            self.menu_game.get_widget("favorite"),
            self.menu_game.get_widget("finish"),
            self.menu_game.get_widget("game_file"),
            self.menu_game.get_widget("game_log"),
            self.menu_game.get_widget("maintenance"),
            self.menu_game.get_widget("memory_type"),
            self.menu_game.get_widget("menu_entry"),
            self.menu_game.get_widget("multiplayer"),
            self.menu_game.get_widget("notes"),
            self.menu_game.get_widget("open_path"),
            self.menu_game.get_widget("remove"),
            self.menu_game.get_widget("rename"),
            self.menu_game.get_widget("screenshots"),
            self.menu_game.get_widget("thumbnail")
        )

        # Store filter widget references
        self.__filters_storage = (
            self.check_filter_favorite,
            self.check_filter_unfavorite,
            self.check_filter_multiplayer,
            self.check_filter_singleplayer,
            self.check_filter_finish,
            self.check_filter_unfinish
        )

    def __init_shortcuts(self):
        """ Generate shortcuts signals from user configuration
        """

        self.logger.info("Associate shortcuts to main interface")

        # Disconnect previous shortcut to avoid multiple allocation
        for key, mod in self.shortcuts:
            self.shortcuts_group.disconnect_key(key, mod)

        # Retrieve shortcuts metadata from GeodeGEM project
        shortcuts = Configuration(get_data("data", "config", "shortcuts.conf"))

        for section in shortcuts.sections():
            shortcut = self.config.item(
                "keys", *shortcuts.get(section, "shortcut").split(" | "))

            # Parse shortcut to Gtk specific format
            accelerator = Gtk.accelerator_parse(shortcut)
            if not Gtk.accelerator_valid(*accelerator):
                self.logger.warning(f"Invalid accelerator for {section}")
                continue

            self.shortcuts_map.change_entry(section, *accelerator, True)

            # Associate shortcut to each widgets
            for widget in shortcuts.get(section, "widgets").split(" | "):
                internal_widget = getattr(self, widget, None)

                # Specified widget must be declared into main interface
                if internal_widget is None:
                    self.logger.warning(
                        f"Cannot retrieve widget '{widget}' from interface")
                    continue

                # Retrieve internal widget for GeodeGtkCommon objects
                if hasattr(internal_widget, "has_widget"):
                    widget_key = shortcuts.get(section, "key")

                    if not internal_widget.has_widget(widget_key):
                        self.logger.warning(
                            f"Cannot retrieve internal widget '{widget_key}'")
                        continue

                    internal_widget = internal_widget.get_widget(widget_key)

                self.logger.debug(f"Associate shortcut '{shortcut}' to "
                                  f"{widget}/{widget_key}")
                internal_widget.add_accelerator("activate",
                                                self.shortcuts_group,
                                                *accelerator,
                                                Gtk.AccelFlags.VISIBLE)

                # Store current shortcut to remove it properly later
                self.shortcuts.append(accelerator)

        del shortcuts

    def __init_interface(self):
        """ Init main interface
        """

        self.selection = dict(console=None, game=None)

        # ------------------------------------
        #   Toolbar icons
        # ------------------------------------

        if self.toolbar_icons_size in self.__toolbar_sizes:
            size = self.__toolbar_sizes[self.toolbar_icons_size]

            # Avoid to change icon size if there is no change
            if not size == self.__current_toolbar_size:
                self.__current_toolbar_size = size

                for widget, icon in self.__images_storage.items():
                    widget.set_from_icon_name(icon, size)

        # ------------------------------------
        #   Toolbar view switcher
        # ------------------------------------

        if self.view_mode == Columns.Key.Grid:
            self.headerbar.set_active(True, widget="grid")
            self.menubar_view.set_active(True, widget="grid")
            self.toolbar_games.get_widget("views").switch_to("grid")

        else:
            self.headerbar.set_active(True, widget="list")
            self.menubar_view.set_active(True, widget="list")
            self.toolbar_games.get_widget("views").switch_to("list")

        # ------------------------------------
        #   Toolbar design
        # ------------------------------------

        # Update design colorscheme
        on_change_theme(self.use_dark_theme)

        self.headerbar.set_active(self.use_dark_theme, widget="dark_theme")
        self.menubar_view.set_active(self.use_dark_theme, widget="dark_theme")

        if self.use_dark_theme:
            self.logger.debug("Use dark variant for GTK+ theme")

        else:
            self.logger.debug("Use light variant for GTK+ theme")

        # Update design template
        if not self.use_classic_theme:
            self.logger.debug("Use default theme for GTK+ interface")
            self.set_titlebar(self.headerbar)

        else:
            self.logger.debug("Use classic theme for GTK+ interface")

        # ------------------------------------
        #   Treeview columns order
        # ------------------------------------

        custom_order = deepcopy(self.columns_order)
        original_order = Columns.ORDER.split(':')

        # Avoid to check custom_order
        if not custom_order == original_order:

            # Append missing column from columns_order string
            for key in original_order:
                if key not in custom_order:
                    custom_order.append(key)

        # Append column in games treeview
        for column in custom_order:

            # Store identifier for __stop_interface function
            setattr(self.__columns_storage[column], "identifier", column)

            self.treeview_games.append_column(self.__columns_storage[column])

        # ------------------------------------
        #   Treeview columns sorting
        # ------------------------------------

        column, order = (Columns.List.NAME, Gtk.SortType.ASCENDING)

        if self.load_sort_column_at_startup:
            column = getattr(Columns.List, self.load_last_column.upper(), None)

            # Cannot found a column, use the default one
            if column is None:
                column = Columns.List.NAME

            if self.load_sort_column_order == "desc":
                order = Gtk.SortType.DESCENDING

        self.sorted_games_list.set_sort_column_id(column, order)

        # ------------------------------------
        #   Window size
        # ------------------------------------

        try:
            width, height = self.main_window_size

            self.window_size.base_width = int(width)
            self.window_size.base_height = int(height)

            self.resize(int(width), int(height))

        except ValueError as error:
            self.logger.error("Cannot resize main window: %s" % str(error))

        self.set_geometry_hints(
            self,
            self.window_size,
            Gdk.WindowHints.MIN_SIZE | Gdk.WindowHints.BASE_SIZE)

        self.set_position(Gtk.WindowPosition.CENTER)

        # ------------------------------------
        #   Sidebars position
        # ------------------------------------

        if self.sidebar_console_position is not None \
           and self.sidebar_console_position > -1:
            self.hpaned_consoles.set_position(self.sidebar_console_position)

        if self.sidebar_game_position is not None \
           and self.sidebar_game_position > -1:

            if self.sidebar_orientation == "horizontal":
                self.hpaned_games.set_position(self.sidebar_game_position)

            else:
                self.vpaned_games.set_position(self.sidebar_game_position)

    def __show_interface(self):
        """ Show main interface widgets
        """

        self.hide()
        self.unrealize()

        self.show_all()

        self.grid_game_filters_popover.show_all()

        self.infobar.show()

        self.grid_sidebar.show_all()
        self.scroll_sidebar.show_all()
        self.scroll_sidebar_informations.show_all()

        self.grid_games_placeholder.show_all()
        self.label_consoles.show_all()

        # Manage window template
        if self.use_classic_theme:
            self.menubar.show_all()
            self.headerbar.hide()

        else:
            self.headerbar.show_all()
            self.menubar.hide()

        self.menubar_main.show_all()
        self.menubar_view.show_all()
        self.menubar_game.show_all()
        self.menubar_edit.show_all()
        self.menubar_help.show_all()
        self.menu_consoles.show_all()
        self.menu_game.show_all()
        self.toolbar_consoles.show_all()

        # Manage sidebar visibility
        self.scroll_sidebar.set_visible(self.show_sidebar)

        self.grid_sidebar_score.set_visible(False)
        self.grid_sidebar_informations.set_visible(False)
        self.frame_sidebar_screenshot.set_visible(False)

        if self.show_sidebar:
            self.frame_sidebar_screenshot.set_visible(False)

            self.grid_sidebar_informations.show_all()

        # Manage statusbar visibility
        if self.show_statusbar:
            self.statusbar.show()
        else:
            self.statusbar.hide()

        # Manage games views
        self.scroll_games_list.set_visible(False)
        self.scroll_games_grid.set_visible(False)
        self.scroll_games_placeholder.set_visible(True)

    def __start_interface(self):
        """ Load data and start interface
        """

        self.logger.info("Use Python interpreter version %d.%d.%d" % (
            version_info.major,
            version_info.minor,
            version_info.micro))

        self.logger.info("Use GTK+ library version %d.%d.%d" % (
            Gtk.get_major_version(),
            Gtk.get_minor_version(),
            Gtk.get_micro_version()))

        self.logger.info("Use GEM version %s (%s)" % (
            self.__version, Metadata.CODE_NAME))

        # ------------------------------------
        #   Load informations
        # ------------------------------------

        self.load_interface(True)

        load_console_startup = self.config.getboolean(
            "gem", "load_console_startup", fallback=True)

        # Check last loaded console in gem.conf
        if load_console_startup:
            console = self.config.item("gem", "last_console", str())

            # A console has been saved
            if len(console) > 0:

                # Check if this console use the old console name value (< 0.8)
                if console not in self.api.consoles.keys():
                    console = generate_identifier(console)

                # Check if current identifier exists
                if console in self.api.consoles.keys() \
                   and console in self.consoles_iter.keys():
                    self.treeview_games.set_visible(True)

                    row = self.consoles_iter[console]

                    # Set console combobox active iter
                    self.listbox_consoles.select_row(row)

                    self.__on_selected_console(self.listbox_consoles, row)

                    # Set Console object as selected
                    self.selection["console"] = row.console

        # Check welcome message status in gem.conf
        if self.config.getboolean("gem", "welcome", fallback=True):

            # Load the first console to avoid mini combobox
            if load_console_startup and self.selection["console"] is None:
                consoles = list(self.consoles_iter.values())

                if len(consoles) > 0:
                    self.listbox_consoles.select_row(consoles[0])

            dialog = GeodeDialog.Message(
                self,
                _("Welcome!"),
                _("Welcome and thanks for choosing GEM as emulators manager. "
                  "Start using GEM by dropping some files into interface.\n\n"
                  "Enjoy and have fun :D"),
                Icons.Symbolic.SMILE_BIG,
                False)

            dialog.set_size_request(500, -1)

            dialog.run()
            dialog.destroy()

            # Disable welcome message for next launch
            self.config.modify("gem", "welcome", False)
            self.config.update()

        # Set default filters flag
        self.filters_reset()

    def __stop_interface(self, *args):
        """ Save data and stop interface
        """

        self.logger.info("Close interface")

        # ------------------------------------
        #   Threads
        # ------------------------------------

        self.logger.debug("Terminate remaining threaded processus")

        # Remove games listing thread
        if not self.list_thread == 0:
            self.logger.debug(f"Remove thread ID {self.list_thread}")
            GLib.source_remove(self.list_thread)

        # Remove game and script threads
        for thread in thread_enumerate().copy():

            # Avoid to remove the main thread
            if thread is not thread_main_thread():
                self.logger.debug(f"Remove thread {thread.name}")
                thread.proc.terminate()
                thread.join()

                self.__on_game_terminate(None, thread)

        # ------------------------------------
        #   Notes
        # ------------------------------------

        # Close open notes dialog
        if len(self.notes.keys()) > 0:
            self.logger.debug("Terminate openning notes")

            for dialog in self.notes.copy().keys():
                self.notes[dialog].emit_response(None, Gtk.ResponseType.APPLY)

        # ------------------------------------
        #   Last console
        # ------------------------------------

        # Save current console as last_console in gem.conf
        row = self.listbox_consoles.get_selected_row()
        if row is not None:
            last_console = self.config.item("gem", "last_console", None)

            # Avoid to modify gem.conf if console is already in conf
            if last_console is None or not last_console == row.console.id:
                self.config.modify("gem", "last_console", row.console.id)

                self.logger.info(
                    f"Save {row.console.name} console for next startup")

        # ------------------------------------
        #   Last sorted column
        # ------------------------------------

        column, order = self.sorted_games_list.get_sort_column_id()

        if column is not None and order is not None:

            for key, value in Columns.List.__dict__.items():
                if not key.startswith("__") and not key.endswith("__"):

                    if column == value:
                        self.config.modify("gem", "last_sort_column", key)

            if order == Gtk.SortType.ASCENDING:
                self.config.modify("gem", "last_sort_column_order", "asc")

            elif order == Gtk.SortType.DESCENDING:
                self.config.modify("gem", "last_sort_column_order", "desc")

        # ------------------------------------
        #   Columns order
        # ------------------------------------

        columns = list()

        for column in self.treeview_games.get_columns():
            columns.append(column.identifier)

        self.config.modify("columns", "order", ':'.join(columns))

        # ------------------------------------
        #   Games view mode
        # ------------------------------------

        if self.toolbar_games.get_active("list"):
            self.config.modify("gem", "games_view_mode", Columns.Key.List)

        elif self.toolbar_games.get_active("grid"):
            self.config.modify("gem", "games_view_mode", Columns.Key.Grid)

        # ------------------------------------
        #   Windows size
        # ------------------------------------

        self.config.modify("windows", "main", "%dx%d" % self.get_size())

        # ------------------------------------
        #   Sidebars position
        # ------------------------------------

        self.config.modify("gem",
                           "sidebar_console_position",
                           self.hpaned_consoles.get_position())

        if self.sidebar_orientation == "horizontal":
            position = self.hpaned_games.get_position()

        else:
            position = self.vpaned_games.get_position()

        self.config.modify("gem", "sidebar_game_position", position)

        self.config.update()

        if self.main_loop.is_running():
            self.logger.debug("Close main loop")
            self.__block_signals()
            self.main_loop.quit()

    def load_configuration(self):
        """ Load main configuration file and store values
        """

        if getattr(self, "config", None) is None:
            self.config = Configuration(
                self.api.get_config("gem.conf"), strict=False)

            # Get missing keys from config/gem.conf
            self.config.add_missing_data(
                get_data("data", "config", "gem.conf"))

        else:
            self.logger.debug("Reload configuration file")

            self.config.reload()

        # ------------------------------------
        #   Configuration values
        # ------------------------------------

        self.toolbar_icons_size = self.config.get(
            "gem", "toolbar_icons_size", fallback="small-toolbar")

        self.icon_translucent = self.config.getboolean(
            "gem", "use_translucent_icons", fallback=False)

        self.view_mode = self.config.get(
            "gem", "games_view_mode", fallback=Columns.Key.List)

        self.columns_order = self.config.get(
            "columns", "order", fallback=Columns.ORDER).split(':')

        self.load_last_column = self.config.get(
            "gem", "last_sort_column", fallback="Name")

        self.load_sort_column_at_startup = self.config.getboolean(
            "gem", "load_sort_column_startup", fallback=True)

        self.load_sort_column_order = self.config.get(
            "gem", "last_sort_column_order", fallback="asc")

        self.load_console_at_startup = self.config.getboolean(
            "gem", "load_console_startup", fallback=True)

        self.load_last_console = self.config.get(
            "gem", "last_console", fallback=None)

        self.hide_empty_console = self.config.getboolean(
            "gem", "hide_empty_console", fallback=False)

        self.use_dark_theme = self.config.getboolean(
            "gem", "dark_theme", fallback=False)

        self.use_classic_theme = self.config.getboolean(
            "gem", "use_classic_theme", fallback=False)

        self.use_ellipsize_title = self.config.getboolean(
            "gem", "sidebar_title_ellipsize", fallback=True)

        self.use_random_screenshot = self.config.getboolean(
            "gem", "show_random_screenshot", fallback=True)

        self.show_headerbar_buttons = self.config.getboolean(
            "gem", "show_header", fallback=True)

        self.show_sidebar = self.config.getboolean(
            "gem", "show_sidebar", fallback=True)

        self.show_statusbar = self.config.getboolean(
            "gem", "show_statusbar", fallback=True)

        self.sidebar_orientation = self.config.get(
            "gem", "sidebar_orientation", fallback="vertical")

        self.sidebar_console_position = self.config.getint(
            "gem", "sidebar_console_position", fallback=None)

        self.sidebar_game_position = self.config.getint(
            "gem", "sidebar_game_position", fallback=None)

        self.treeview_lines = self.config.item(
            "gem", "games_treeview_lines", "none")

        self.main_window_size = self.config.get(
            "windows", "main", fallback="1024x768").split('x')

        # ------------------------------------
        #   Configuration operations
        # ------------------------------------

        # Avoid to have an empty string for last console value
        if type(self.load_last_console) == 0 \
           and len(self.load_last_console) == 0:
            self.load_last_console = None

    def load_interface(self, init_interface=False):
        """ Load main interface

        Parameters
        ----------
        init_interface : bool, optional
            Interface first initialization (Default: False)
        """

        self.logger.debug(
            "%s main interface" % ("Load" if init_interface else "Reload"))

        self.__block_signals()

        self.api.init()

        # Retrieve user configuration
        self.load_configuration()

        # Retrieve user shortcuts
        self.__init_shortcuts()

        # Initialize main widgets
        if init_interface:
            self.__init_interface()

            self.__show_interface()

        # ------------------------------------
        #   Widgets
        # ------------------------------------

        self.infobar.set_visible(False)

        self.sensitive_interface()

        # Show window buttons into headerbar
        self.headerbar.set_show_close_button(self.show_headerbar_buttons)

        # Show sidebar visibility buttons
        self.headerbar.set_active(self.show_sidebar, widget="show_sidebar")
        self.menubar_view.set_active(self.show_sidebar, widget="show_sidebar")

        # Show statusbar visibility buttons
        self.headerbar.set_active(self.show_statusbar, widget="show_statusbar")
        self.menubar_view.set_active(
            self.show_statusbar, widget="show_statusbar")

        # Use translucent icons in games views
        self.icons.set_translucent_status(self.icon_translucent)

        # ------------------------------------
        #   Sidebar
        # ------------------------------------

        if self.use_ellipsize_title:
            self.label_sidebar_title.set_line_wrap(False)
            self.label_sidebar_title.set_single_line_mode(True)
            self.label_sidebar_title.set_ellipsize(Pango.EllipsizeMode.END)
            self.label_sidebar_title.set_line_wrap_mode(Pango.WrapMode.WORD)

        else:
            self.label_sidebar_title.set_line_wrap(True)
            self.label_sidebar_title.set_single_line_mode(False)
            self.label_sidebar_title.set_ellipsize(Pango.EllipsizeMode.NONE)
            self.label_sidebar_title.set_line_wrap_mode(
                Pango.WrapMode.WORD_CHAR)

        self.__on_move_sidebar(init_interface=init_interface)

        # ------------------------------------
        #   Treeview
        # ------------------------------------

        # Games - Treeview lines
        if self.treeview_lines in self.__treeview_lines:
            self.treeview_games.set_grid_lines(
                self.__treeview_lines[self.treeview_lines])

        # Games - Treeview columns
        for key, widget in self.__columns_storage.items():
            visibility = self.config.getboolean("columns", key, fallback=True)

            widget.set_visible(visibility)

            if key in self.menubar_view.inner_widgets.keys():
                self.headerbar.set_active(visibility, widget=key)
                self.menubar_view.set_active(visibility, widget=key)

        if self.column_game_score.get_visible():
            self.__rating_score = [
                self.cell_game_score_first,
                self.cell_game_score_second,
                self.cell_game_score_third,
                self.cell_game_score_fourth,
                self.cell_game_score_fifth
            ]

        # ------------------------------------
        #   Console
        # ------------------------------------

        self.toolbar_consoles.set_active(
            self.hide_empty_console, widget="hide_empty")

        self.append_consoles()

        selected_row = None

        # A console already has been selected
        if self.selection["console"] is not None:

            if self.selection["console"].id in self.consoles_iter.keys():
                selected_row = self.consoles_iter[self.selection["console"].id]

        # Check last loaded console in gem.conf
        elif self.load_console_at_startup:

            # Load first available console in consoles list
            if len(self.listbox_consoles) > 0:
                selected_row = self.listbox_consoles.get_row_at_index(0)

            # Load latest selected console
            if init_interface and self.load_last_console is not None:

                # Avoid to load an unexisting console
                if self.load_last_console in self.consoles_iter.keys():
                    selected_row = self.consoles_iter[self.load_last_console]

        # Load console games
        if selected_row is not None:
            self.scroll_sidebar.set_visible(self.show_sidebar)

            self.__on_selected_console(None, selected_row, True)

        # Manage default widgets visibility when no console selected
        else:
            self.scroll_sidebar.set_visible(False)

            self.set_informations()

        self.__unblock_signals()

    def sensitive_interface(self, status=False):
        """ Update sensitive status for main widgets

        Parameters
        ----------
        status : bool, optional
            Sensitive status (Default: False)
        """

        self.logger.debug(f"Reset widgets sensitivity status to {status}")

        self.__on_game_launch_button_update(True)

        for widget in self.__widgets_storage:
            widget.set_sensitive(status)

    def filters_update(self, widget, status=None):
        """ Reload packages filter when user change filters from menu

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        status : bool or None, optional
            New status for current widget (Default: None)

        Notes
        -----
        Check widget utility in this function
        """

        if status is not None and type(status) is bool:
            widget.set_active(status)

        widgets = (
            self.check_filter_favorite,
            self.check_filter_unfavorite,
            self.check_filter_multiplayer,
            self.check_filter_singleplayer,
            self.check_filter_finish,
            self.check_filter_unfinish
        )

        active_filter = False
        for switch in widgets:
            active_filter = active_filter or not switch.get_active()

        if active_filter:
            self.toolbar_games.get_widget("filters").set_style(
                "suggested-action")
        else:
            self.toolbar_games.get_widget("filters").set_style()

        self.filter_games_list.refilter()
        self.filter_games_grid.refilter()

        self.check_selection()

        self.set_informations_headerbar(self.__on_retrieve_selected_game(),
                                        self.__on_retrieve_selected_console())

    def filters_reset(self, widget=None, events=None):
        """ Reset game filters

        Parameters
        ----------
        widget : Gtk.Widget, optional
            Object which receive signal (Default: None)
        event : Gdk.EventButton or Gdk.EventKey, optional
            Event which triggered this signal (Default: None)
        """

        for switch in self.__filters_storage:
            switch.set_active(True)

        self.toolbar_games.get_widget("filters").set_style()

    def filters_match(self, model, row, *args):
        """ Update treeview rows

        This function update games treeview with filter entry content. A row is
        visible if the content match the filter.

        Parameters
        ----------
        model : Gtk.TreeModel
            Treeview model which receive signal
        row : Gtk.TreeModelRow
            Treeview current row
        """

        found = False

        # Get game object from treeview
        if model == self.model_games_list:
            game = model.get_value(row, Columns.List.OBJECT)

        elif model == self.model_games_grid:
            game = model.get_value(row, Columns.Grid.OBJECT)

        try:
            text = self.toolbar_games.get_widget("entry").get_text()

            # No filter
            if len(text) == 0:
                found = True

            # ------------------------------------
            #   Check filter
            # ------------------------------------

            # Check game name first
            if game.name is not None:

                # Regex match game.name
                if match("%s$" % text, game.name) is not None:
                    found = True

                # Lowercase filter match lowercase game.name
                if text.lower() in game.name.lower():
                    found = True

            # Check game tags second
            if len(game.tags) > 0:

                for tag in game.tags:

                    # Regex match one of game tag
                    if match("%s$" % text, tag) is not None:
                        found = True

                    # Lowercase filter match lowercase game.name
                    if text.lower() in tag.lower():
                        found = True

            # ------------------------------------
            #   Set status
            # ------------------------------------

            flags = [
                (
                    self.check_filter_favorite.get_active(),
                    self.check_filter_unfavorite.get_active(),
                    game.favorite
                ),
                (
                    self.check_filter_multiplayer.get_active(),
                    self.check_filter_singleplayer.get_active(),
                    game.multiplayer
                ),
                (
                    self.check_filter_finish.get_active(),
                    self.check_filter_unfinish.get_active(),
                    game.finish
                )
            ]

            for first, second, status in flags:

                # Check if one of the two checkbox is not active
                if not (first and second):
                    found = found and (
                        (status and first) or (not status and second))

        except Exception:
            pass

        return found

    def __on_filter_tag(self, widget):
        """ Refilter games list with a new tag

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        row : Gtk.ListBoxRow
            Activated ListBox row which contain a specific tag
        """

        entry_widget = self.toolbar_games.get_widget("entry")

        text = str()
        if not entry_widget.get_text() == widget.get_label():
            text = widget.get_label()

        entry_widget.set_text(text)

    def __on_manage_keys(self, widget, event):
        """ Manage widgets for specific keymaps

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        event : Gdk.EventButton or Gdk.EventKey
            Event which triggered this signal
        """

        # Give me more lifes, powerups or cookies konami code, I need more
        konami_code = [Gdk.KEY_Up, Gdk.KEY_Up,
                       Gdk.KEY_Down, Gdk.KEY_Down,
                       Gdk.KEY_Left, Gdk.KEY_Right,
                       Gdk.KEY_Left, Gdk.KEY_Right]

        if event.keyval in konami_code:
            self.keys.append(event.keyval)

            if self.keys == konami_code:
                dialog = GeodeDialog.Message(
                    self,
                    "Someone wrote the KONAMI CODE !",
                    "Nice catch ! You have discover an easter-egg ! But, this "
                    "kind of code is usefull in a game, not in an emulators "
                    "manager !",
                    Icons.Symbolic.MONKEY)

                dialog.set_size_request(500, -1)

                dialog.run()
                dialog.destroy()

                self.keys = list()

            if not self.keys == konami_code[0:len(self.keys)]:
                self.keys = list()

    def set_informations(self):
        """ Update headerbar title and subtitle
        """

        self.__block_signals()

        self.sidebar_image = None

        game = self.__on_retrieve_selected_game()
        console = self.__on_retrieve_selected_console()

        # Update headerbar and statusbar informations
        self.set_informations_headerbar(game, console)

        # ----------------------------------------
        #   Toolbar
        # ----------------------------------------

        # Remove tags list
        for widget in self.menu_sidebar_tags.get_children():
            self.menu_sidebar_tags.remove(widget)

        # ----------------------------------------
        #   Sidebar
        # ----------------------------------------

        # Hide sidebar widgets
        self.grid_sidebar_score.set_visible(False)
        self.grid_sidebar_informations.set_visible(False)
        self.frame_sidebar_screenshot.set_visible(False)

        # Reset sidebar informations
        self.label_sidebar_title.set_text(str())
        self.image_sidebar_screenshot.set_from_pixbuf(None)

        # ----------------------------------------
        #   Statusbar
        # ----------------------------------------

        for widget_key in self.statusbar.pixbuf_widgets:
            self.statusbar.set_widget_value(
                widget_key, image=self.icons.blank(), tooltip=str())

        # ----------------------------------------
        #   Update informations
        # ----------------------------------------

        if game is not None:
            self.logger.debug(
                f"Update informations on main interface for '{game.id}'")

            # ----------------------------------------
            #   Widgets
            # ----------------------------------------

            self.__on_game_launch_button_update(game.id not in self.threads)

            self.toolbar_games.set_sensitive(True, widget="launch")

            # This game is not running
            if game.id not in self.threads:
                self.menu_game.set_sensitive(True, widget="launch")
                self.menubar_game.set_sensitive(True, widget="launch")

                if game.path.exists() and access(game.path, W_OK):
                    self.menu_game.set_sensitive(True, widget="remove")
                    self.menubar_edit.set_sensitive(True, widget="remove")

            # Menubar
            for widget in ("favorite", "finish", "multiplayer", "notes",
                           "properties"):
                self.headerbar.set_sensitive(True, widget=widget)
                self.menubar_game.set_sensitive(True, widget=widget)

            for widget in ("copy_path", "open_path", "duplicate", "menu_entry",
                           "maintenance", "rename", "thumbnail", "score"):
                self.headerbar.set_sensitive(True, widget=widget)
                self.menubar_edit.set_sensitive(True, widget=widget)

            # Game menu
            for widget in ("copy_path", "open_path", "duplicate", "menu_entry",
                           "maintenance", "rename", "thumbnail", "notes",
                           "favorite", "finish", "multiplayer"):
                self.menu_game.set_sensitive(True, widget=widget)

            # Toolbar
            self.toolbar_games.set_sensitive(True, widget="notes")
            self.toolbar_games.set_sensitive(True, widget="parameters")

            # ----------------------------------------
            #   Sidebar
            # ----------------------------------------

            self.grid_sidebar_score.set_visible(True)
            self.grid_sidebar_informations.set_visible(True)

            self.label_sidebar_title.set_markup(
                "<span weight='bold' size='large'>%s</span>" % (
                    replace_for_markup(game.name)))

            # ----------------------------------------
            #   Game special menu entries
            # ----------------------------------------

            # Game editable file
            if magic_from_file(game.path, mime=True).startswith("text/"):
                if access(game.path, R_OK) and access(game.path, W_OK):
                    self.menu_game.set_sensitive(True, widget="game_file")
                    self.menubar_edit.set_sensitive(True, widget="game_file")

            if game.emulator is not None:

                # Check extension and emulator for GBA game on mednafen
                if self.__mednafen_status and game.extension == ".gba":

                    if "mednafen" in str(game.emulator.binary):
                        self.menu_game.set_sensitive(
                            True, widget="memory_type")
                        self.menubar_edit.set_sensitive(
                            True, widget="memory_type")

            # ----------------------------------------
            #   Game flags
            # ----------------------------------------

            for name in ("favorite", "multiplayer", "finish"):
                self.menu_game.set_active(getattr(game, name), widget=name)
                self.menubar_game.set_active(getattr(game, name), widget=name)

            # ----------------------------------------
            #   Game screenshots
            # ----------------------------------------

            pixbuf = self.icons.get_translucent("screenshot")
            tooltip = _("No screenshot")

            # Check screenshots
            if game.screenshots:
                pixbuf = self.icons.get("screenshot")

                self.menu_game.set_sensitive(True, widget="screenshots")
                self.menubar_game.set_sensitive(True, widget="screenshots")
                self.toolbar_games.set_sensitive(True, widget="screenshots")

                tooltip = ngettext(_("1 screenshot"),
                                   _("%d screenshots") % len(game.screenshots),
                                   len(game.screenshots))

                # Ordered game screenshots
                if not self.use_random_screenshot:
                    screenshots = sorted(game.screenshots)

                # Get a random file from game screenshots
                else:
                    screenshots = game.screenshots

                    shuffle(screenshots)

                self.sidebar_image = Path(screenshots[-1])

                # Update sidebar screenshot
                if self.sidebar_image.exists() \
                   and self.sidebar_image.is_file():

                    height = 200
                    if self.__current_orientation == \
                       Gtk.Orientation.HORIZONTAL:
                        height = 250

                    try:
                        # Set sidebar screenshot
                        self.image_sidebar_screenshot.set_from_pixbuf(
                            GdkPixbuf.Pixbuf.new_from_file_at_scale(
                                str(self.sidebar_image),
                                300,
                                height,
                                True))

                        self.frame_sidebar_screenshot.set_visible(True)
                        self.frame_sidebar_screenshot.show_all()

                    except GLib.Error:
                        self.sidebar_image = None

            self.statusbar.set_widget_value(
                "screenshots", image=pixbuf, tooltip=tooltip)

            # ----------------------------------------
            #   Game log
            # ----------------------------------------

            # Check game log file
            if self.check_log() is not None:
                self.menu_game.set_sensitive(True, widget="game_log")
                self.menubar_game.set_sensitive(True, widget="game_log")
                self.toolbar_games.set_sensitive(True, widget="game_log")

            # ----------------------------------------
            #   Game tags
            # ----------------------------------------

            if len(game.tags) > 0:
                self.toolbar_games.get_widget("tags").set_sensitive(True)

                # Append game tags
                for tag in sorted(game.tags):
                    item = Gtk.MenuItem.new_with_label(tag)
                    item.connect("activate", self.__on_filter_tag)

                    self.menu_sidebar_tags.append(item)

                self.menu_sidebar_tags.show_all()

            # ----------------------------------------
            #   Game savestates
            # ----------------------------------------

            pixbuf = self.icons.get_translucent("savestate")
            tooltip = _("No savestate")

            if game.savestates:
                pixbuf = self.icons.get("savestate")

                tooltip = ngettext(_("1 savestate"),
                                   _("%d savestates") % len(game.savestates),
                                   len(game.savestates))

            self.statusbar.set_widget_value(
                "savestates", image=pixbuf, tooltip=tooltip)

            # ----------------------------------------
            #   Game custom parameters
            # ----------------------------------------

            # Game custom parameters
            pixbuf = self.icons.get_translucent("parameter")
            tooltip = str()

            if len(game.default) > 0 or not game.emulator == console.emulator:
                pixbuf = self.icons.get("parameter")

                if len(game.default) > 0:
                    tooltip = _("Use alternative arguments")

                elif game.emulator == console.emulator:
                    tooltip = _("Use alternative emulator")

            self.statusbar.set_widget_value(
                "properties", image=pixbuf, tooltip=tooltip)

            # ----------------------------------------
            #   Sidebar informations
            # ----------------------------------------

            widgets = [
                {
                    "widget": self.label_sidebar_played_value,
                    "condition": game.played > 0,
                    "markup": str(game.played)
                },
                {
                    "widget": self.label_sidebar_play_time_value,
                    "condition": not game.play_time == timedelta(),
                    "markup": string_from_time(game.play_time),
                    "tooltip": parse_timedelta(game.play_time)
                },
                {
                    "widget": self.label_sidebar_last_play_value,
                    "condition": not game.last_launch_date.strftime(
                        "%d%m%y") == "010101",
                    "markup": string_from_date(game.last_launch_date),
                    "tooltip": str(game.last_launch_date)
                },
                {
                    "widget": self.label_sidebar_last_time_value,
                    "condition": not game.last_launch_time == timedelta(),
                    "markup": string_from_time(game.last_launch_time),
                    "tooltip": parse_timedelta(game.last_launch_time)
                },
                {
                    "widget": self.label_sidebar_installed_value,
                    "condition": game.installed is not None,
                    "markup": string_from_date(game.installed),
                    "tooltip": str(game.installed)
                },
                {
                    "widget": self.grid_sidebar_score,
                    "markup": str(game.score)
                },
                {
                    "widget": self.label_sidebar_emulator_value,
                    "condition": game.emulator is not None,
                    "markup": getattr(game.emulator, "name", None)
                }
            ]

            for data in widgets:

                # Default label value widget
                if "condition" in data:
                    data["widget"].set_markup(str())
                    data["widget"].set_tooltip_text(str())

                    if data["condition"]:

                        if data["markup"] is not None:
                            data["widget"].set_markup(data["markup"])

                        # Set tooltip for current widget
                        if "tooltip" in data:
                            data["widget"].set_tooltip_text(data["tooltip"])

                # Score case
                elif data["widget"] == self.grid_sidebar_score:
                    children = data["widget"].get_children()

                    # Append star icons to sidebar
                    for child in children:
                        icon = Icons.Symbolic.NO_STARRED
                        if game.score >= children.index(child) + 1:
                            icon = Icons.Symbolic.STARRED

                        child.set_from_icon_name(
                            icon, Gtk.IconSize.LARGE_TOOLBAR)

                    # Show game score as tooltip
                    data["widget"].set_tooltip_text("%d/5" % game.score)

        self.__unblock_signals()

    def set_informations_headerbar(self, game=None, console=None):
        """ Update headerbar and statusbar informations from games list

        Parameters
        ----------
        game : gem.engine.game.Game
            Game object
        console : gem.api.Console
            Console object
        """

        if game is None:
            game = self.__on_retrieve_selected_game()

        if console is None:
            console = self.__on_retrieve_selected_console()

        emulator = None
        if console is not None:
            emulator = console.emulator

        self.statusbar.console.set_visible(console is not None)
        self.statusbar.emulator.set_visible(emulator is not None)
        self.statusbar.game.set_visible(game is not None)

        texts = list()

        # ----------------------------------------
        #   Console
        # ----------------------------------------

        if console is not None:
            text = _("N/A")

            if self.filter_games_list:
                text = ngettext(
                    _("1 game available"),
                    _("%d games available") % len(self.filter_games_list),
                    len(self.filter_games_list))

                texts.append(text)

            name = replace_for_markup(text)
            self.statusbar.set_widget_value(
                "console", markup=f"<b>{_('Console')}</b>: {name}")

        # ----------------------------------------
        #   Emulator
        # ----------------------------------------

        if emulator is not None:
            name = replace_for_markup(emulator.name)
            self.statusbar.set_widget_value(
                "emulator", markup=f"<b>{_('Emulator')}</b>: {name}")

        # ----------------------------------------
        #   Game
        # ----------------------------------------

        if game is not None:
            self.statusbar.set_widget_value("game", text=game.name)

            texts.append(game.name)

        # ----------------------------------------
        #   Headerbar
        # ----------------------------------------

        if not self.use_classic_theme:
            self.headerbar.set_subtitle(" - ".join(texts))

    def set_message(self, title, message, icon="dialog-error", popup=True):
        """ Open a message dialog

        This function open a dialog to inform user and write message to logger
        output.

        Parameters
        ----------
        title : str
            Dialog title
        message : str
            Dialog message
        icon : str, optional
            Dialog icon, set also the logging mode (Default: dialog-error)
        popup : bool, optional
            Show a popup dialog with specified message (Default: True)
        """

        if icon == Icons.ERROR:
            self.logger.error(message)
        elif icon == Icons.WARNING:
            self.logger.warning(message)
        else:
            self.logger.info(message)

        if popup:
            dialog = GeodeDialog.Message(self, title, message, icon)

            dialog.run()
            dialog.destroy()

    def __on_show_external_link(self, widget, *args):
        """ Open an external link

        Parameters
        ----------
        widget : Gtk.MenuItem
            object which received the signal
        """

        try:
            if widget in (self.headerbar.get_widget("website"),
                          self.menubar_help.get_widget("website")):
                link = Metadata.WEBSITE

            elif widget in (self.headerbar.get_widget("report"),
                            self.menubar_help.get_widget("report")):
                link = Metadata.BUG_TRACKER

            self.logger.debug("Open %s in web navigator" % link)

            self.__xdg_open_instance.launch_uris([link], None)

        except GLib.Error:
            self.logger.exception("Cannot open external link")

    def __on_show_about(self, *args):
        """ Show about dialog
        """

        self.set_sensitive(False)

        about = Gtk.AboutDialog(use_header_bar=not self.use_classic_theme)

        about.set_transient_for(self)

        about.set_program_name(Metadata.NAME)
        about.set_version("%s (%s)" % (self.__version, Metadata.CODE_NAME))
        about.set_comments(Metadata.DESCRIPTION)
        about.set_copyright(Metadata.COPYLEFT)
        about.set_website(Metadata.WEBSITE)

        about.set_authors([
            "Aurélien Lubert (PacMiam)"
        ])
        about.set_artists([
            "Evan-Amos %s - Public Domain" % Metadata.EVAN_AMOS
        ])
        about.set_translator_credits('\n'.join([
            "Anthony Jorion (Pingax)",
            "Aurélien Lubert (PacMiam)",
            "José Luis Lopez Castillo (DarkNekros)",
        ]))
        about.add_credit_section(_("Tested by"), [
            "Bruno Visse (atralfalgar)",
            "Herlief",
        ])
        about.set_license_type(Gtk.License.GPL_3_0)

        # Strange case... With an headerbar, the AboutDialog got some useless
        # buttons whitout any reasons. To avoid this, I remove any widget from
        # headerbar which is not a Gtk.StackSwitcher.
        if not self.use_classic_theme:
            children = about.get_header_bar().get_children()

            for child in children:
                if type(child) is not Gtk.StackSwitcher:
                    about.get_header_bar().remove(child)

        about.run()

        self.set_sensitive(True)
        about.destroy()

    def __on_show_viewer(self, *args):
        """ Show game screenshots

        This function open game screenshots in a viewer. This viewer can be a
        custom one or the gem native viewer. This choice can be do in gem
        configuration file
        """

        game = self.__on_retrieve_selected_game()
        console = self.__on_retrieve_selected_console()

        if game is not None and console is not None:

            # ----------------------------------------
            #   Show screenshots viewer
            # ----------------------------------------

            if len(game.screenshots) > 0:
                title = "%s (%s)" % (game.name, console.name)

                self.set_sensitive(False)

                # Get external viewer
                viewer = Path(self.config.get("viewer", "binary"))

                # ----------------------------------------
                #   Native viewer
                # ----------------------------------------

                if self.config.getboolean("viewer", "native", fallback=True):
                    try:
                        size = self.config.get(
                            "windows", "viewer", fallback="800x600").split('x')

                    except ValueError:
                        size = (800, 600)

                    dialog = GeodeDialog.Viewer(
                        self, title, size, sorted(game.screenshots))
                    dialog.run()

                    self.config.modify(
                        "windows", "viewer", "%dx%d" % dialog.get_size())
                    self.config.update()

                    dialog.destroy()

                # ----------------------------------------
                #   External viewer
                # ----------------------------------------

                elif viewer.exists():

                    # Retrieve viewer binary
                    command = shlex_split(str(viewer))

                    # Add arguments if available
                    parameters = self.config.item("viewer", "options")
                    if parameters is not None:
                        command.append(parameters)

                    # Add game screenshot files
                    for path in sorted(game.screenshots):
                        command.append(str(path))

                    # Launch external viewer
                    try:
                        instance = Gio.AppInfo.create_from_commandline(
                            ' '.join(command), None,
                            Gio.AppInfoCreateFlags.SUPPORTS_URIS)

                        instance.launch(None, None)

                    except GLib.Error:
                        self.logger.exception(
                            "Cannot generate %s instance" % str(viewer))

                # ----------------------------------------
                #   No available viewer
                # ----------------------------------------

                else:
                    self.set_message(_("Cannot open screenshots viewer"),
                                     _("Cannot find <b>%s</b>") % viewer.name,
                                     Icons.WARNING)

                self.set_sensitive(True)

                # ----------------------------------------
                #   Check screenshots
                # ----------------------------------------

                if len(game.screenshots) == 0:
                    self.set_game_data(
                        Columns.List.SCREENSHOT,
                        self.icons.get_translucent("screenshot"),
                        game.id)

    def __on_show_preferences(self, *args):
        """ Show preferences window

        This function show the gem preferences manager
        """

        self.set_sensitive(False)

        dialog = GeodeDialog.Preferences(self.api, self)

        if dialog.run() == Gtk.ResponseType.APPLY:
            dialog.save_configuration()

            self.logger.debug("Main interface need to be reload")
            self.load_interface()

        dialog.destroy()

        self.set_sensitive(True)

    def __on_show_log(self, *args):
        """ Show gem log

        This function show the gem log content in a non-editable dialog
        """

        if self.api.log.exists():
            try:
                size = self.config.get(
                    "windows", "log", fallback="800x600").split('x')

            except ValueError:
                size = (800, 600)

            self.set_sensitive(False)

            dialog = GeodeDialog.Editor(
                self,
                _("Application log"),
                self.api.log,
                size,
                Icons.Symbolic.TERMINAL,
                editable=False)

            dialog.run()

            self.config.modify("windows", "log", "%dx%d" % dialog.get_size())
            self.config.update()

            self.set_sensitive(True)

            dialog.destroy()

    def __on_show_clean_cache(self, *args):
        """ Clean icons cache directory

        This function show a dialog to ask if the icons cache directory need to
        be cleaned
        """

        if Folders.CACHE.exists():
            self.set_sensitive(False)

            success = False

            dialog = GeodeDialog.CleanCache(self)

            if dialog.run() == Gtk.ResponseType.YES:

                # Remove cache directory
                rmtree(str(Folders.CACHE))

                # Generate directories
                Folders.CACHE.mkdir(mode=0o755, parents=True)

                for name in ("consoles", "emulators", "games"):
                    sizes = getattr(Icons.Size, name.upper(), list())

                    for size in sizes:
                        path = Folders.CACHE.joinpath(
                            name, "%sx%s" % (size, size))

                        if not path.exists():
                            self.logger.debug("Generate %s" % path)

                            path.mkdir(mode=0o755, parents=True)

                success = True

            dialog.destroy()

            if success:
                self.set_message(
                    _("Clean icons cache"),
                    _("Icons cache directory has been succesfully cleaned."),
                    Icons.INFORMATION)

            self.set_sensitive(True)

    def __on_show_notes(self, *args):
        """ Edit game notes

        This function allow user to write some notes for a specific game. The
        user can open as many notes he wants but cannot open a note already
        open
        """

        game = self.__on_retrieve_selected_game()

        if game is not None:
            path = self.api.get_local("notes", game.id + ".txt")

            if path is not None and not str(path) in self.notes.keys():
                try:
                    size = self.config.get(
                        "windows", "notes", fallback="800x600").split('x')

                except ValueError:
                    size = (800, 600)

                dialog = GeodeDialog.Editor(
                    self,
                    game.name,
                    path,
                    size,
                    Icons.Symbolic.DOCUMENT)

                # Allow to launch games with open notes
                dialog.set_modal(False)

                dialog.window.connect(
                    "response",
                    self.__on_show_notes_response,
                    dialog,
                    game.name,
                    path)

                dialog.show_all()

                # Save dialogs to close it properly when gem terminate and
                # avoid to reopen existing one
                self.notes[str(path)] = dialog

            elif str(path) in self.notes.keys():
                self.notes[str(path)].grab_focus()

    def __on_show_notes_response(self, widget, response, dialog, title, path):
        """ Close notes dialog

        This function close current notes dialog and save his textview buffer
        to the game notes file

        Parameters
        ----------
        widget : Gtk.Dialog
            Dialog object
        response : Gtk.ResponseType
            Dialog object user response
        dialog : Gtk.Dialog
            Dialog editor object
        title : str
            Dialog title, it's game name by default
        path : pathlib.Path
            Notes path
        """

        if response == Gtk.ResponseType.APPLY:
            text_buffer = dialog.buffer_editor.get_text(
                dialog.buffer_editor.get_start_iter(),
                dialog.buffer_editor.get_end_iter(), True)

            if len(text_buffer) > 0:

                with path.open('w') as pipe:
                    pipe.write(text_buffer)

                self.logger.info("Update note for %s" % title)

            elif path.exists():
                path.unlink()

                self.logger.debug("Remove note for %s" % title)

        self.config.modify("windows", "notes", "%dx%d" % dialog.get_size())
        self.config.update()

        dialog.destroy()

        if str(path) in self.notes.keys():
            del self.notes[str(path)]

    def __on_show_console_editor(self, widget, *args):
        """ Open console editor dialog

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        self.__block_signals()

        selected_row = self.listbox_consoles.get_selected_row()

        if widget == self.toolbar_consoles.get_widget("add_console"):
            console = None

        elif self.__current_menu_row is not None:
            console = self.__current_menu_row.console

            previous_id = console.id

        dialog = GeodeDialog.Console(
            self, console, self.api.consoles, self.api.emulators)

        if dialog.run() == Gtk.ResponseType.APPLY:

            if console is not None:
                self.logger.debug("Save %s modifications" % console.name)

            data = dialog.save()

            if data is not None:

                if console is not None:
                    self.api.delete_console(previous_id)

                    # Remove previous console storage
                    del self.consoles_iter[previous_id]

                    # Store row with the new identifier
                    self.consoles_iter[data["id"]] = self.__current_menu_row

                console = self.api.add_console(data["name"], data.items())

                # Write console data
                self.api.write_data(GEM.Consoles)

                # Load games list if the game directory exists
                if console.path.exists():

                    try:
                        console.init_games()

                    except OSError as error:
                        self.logger.warning(error)

                # Remove thumbnails from cache
                for size in ("22x22", "24x24", "48x48", "64x64", "96x96"):
                    cache_path = self.get_icon_from_cache(
                        "consoles", size, console.id + ".png")

                    if cache_path.exists():
                        remove(cache_path)

                # ----------------------------------------
                #   Update console row
                # ----------------------------------------

                if widget == self.toolbar_consoles.get_widget("add_console"):
                    console_data = self.__on_generate_console_row(console)

                    if console_data is not None:
                        row = self.__on_append_console_row(*console_data)

                        # Store console iter
                        self.consoles_iter[row.console.id] = row

                    self.set_message(
                        _("New console"),
                        _("%s has been correctly added to your "
                          "configuration.") % console.name,
                        Icons.Symbolic.INFORMATION)

                else:

                    self.__current_menu_row.console = console

                    # Console name
                    self.__current_menu_row.label.set_text(console.name)

                    # Console icon
                    icon = self.get_pixbuf_from_cache(
                        "consoles", 24, console.id, console.icon)

                    if icon is None:
                        icon = self.icons.blank(24)

                    self.__current_menu_row.image_icon.set_from_pixbuf(icon)

                    # Console favorite status icon
                    icon = None
                    if console.favorite:
                        icon = Icons.Symbolic.FAVORITE

                    self.__current_menu_row.image_status.set_from_icon_name(
                        icon, Gtk.IconSize.MENU)

                    text = _("No game")
                    if console.get_games():
                        text = ngettext(
                            _("1 game"),
                            _("%d games") % len(console.get_games()),
                            len(console.get_games()))

                    self.__current_menu_row.set_tooltip_text(text)

                    # Console flag selectors
                    self.menu_consoles.set_active(
                        console.favorite, widget="favorite")
                    self.menu_consoles.set_active(
                        console.recursive, widget="recursive")

                # ----------------------------------------
                #   Refilter consoles list
                # ----------------------------------------

                self.__on_update_consoles()

                # ----------------------------------------
                #   Reload games list
                # ----------------------------------------

                if selected_row == self.__current_menu_row:
                    self.selection["console"] = self.__current_menu_row.console

                    self.__on_reload_games()

        dialog.destroy()

        self.__unblock_signals()

    def __on_show_emulator_editor(self, widget, *args):
        """ Open console editor dialog

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        self.__block_signals()

        selected_row = self.listbox_consoles.get_selected_row()

        if widget == self.toolbar_consoles.get_widget("add_emulator"):
            emulator = None

        elif self.__current_menu_row is not None:
            emulator = self.__current_menu_row.console.emulator

            previous_id = emulator.id

            # Retrieve the correct emulator instance from api
            emulator = self.api.get_emulator(previous_id)

        dialog = GeodeDialog.Emulator(self, emulator, self.api.emulators)

        if dialog.run() == Gtk.ResponseType.APPLY:

            if emulator is not None:
                self.logger.debug("Save %s modifications" % emulator.name)

            data = dialog.save()

            if data is not None:

                if emulator is not None:
                    self.api.delete_emulator(previous_id)

                emulator = self.api.add_emulator(data["name"], data.items())

                if not widget == self.toolbar_consoles.get_widget(
                   "add_emulator"):

                    # Rename emulator identifier in consoles and games
                    if not emulator.id == previous_id:
                        self.api.rename_emulator(previous_id, emulator.id)

                # Write console data
                self.api.write_data(GEM.Emulators)

                # Remove thumbnails from cache
                for size in ("22x22", "48x48", "64x64"):
                    cache_path = self.get_icon_from_cache(
                        "emulators", size, emulator.id + ".png")

                    if cache_path.exists():
                        remove(cache_path)

                # ----------------------------------------
                #   Update console row
                # ----------------------------------------

                if widget == self.toolbar_consoles.get_widget("add_emulator"):
                    self.set_message(
                        _("New emulator"),
                        _("%s has been correctly added to your "
                          "configuration.") % emulator.name,
                        Icons.Symbolic.INFORMATION)

                else:
                    status = False

                    self.__current_menu_row.console.emulator = emulator

                    if emulator is not None \
                       and emulator.configuration is not None:
                        status = emulator.configuration.exists()

                    self.menu_consoles.set_sensitive(
                        status, widget="edit_file")

                    # ----------------------------------------
                    #   Reload games list
                    # ----------------------------------------

                    same_emulator = False

                    if selected_row is not None:
                        identifier = selected_row.console.emulator.id

                        # Reload games list if selected console has the same
                        # emulator to avoid missing references
                        same_emulator = identifier == emulator.id

                    if selected_row == self.__current_menu_row:
                        self.selection["console"] = \
                            self.__current_menu_row.console

                        self.__on_reload_games()

                    elif same_emulator:
                        self.__on_reload_games()

        dialog.destroy()

        self.__unblock_signals()

    def __on_show_emulator_config(self, *args):
        """ Edit emulator configuration file
        """

        console = None
        if self.__current_menu_row is not None:
            console = self.__current_menu_row.console

        if console is not None:
            emulator = console.emulator

            if emulator.configuration is not None:
                path = emulator.configuration

                if path.exists():
                    try:
                        size = self.config.get(
                            "windows", "editor", fallback="800x600").split('x')

                    except ValueError:
                        size = (800, 600)

                    self.set_sensitive(False)

                    dialog = GeodeDialog.Editor(
                        self,
                        _("Edit %s configuration") % emulator.name,
                        path,
                        size,
                        Icons.Symbolic.DOCUMENT)

                    if dialog.run() == Gtk.ResponseType.APPLY:

                        with path.open('w') as pipe:
                            pipe.write(dialog.buffer_editor.get_text(
                                dialog.buffer_editor.get_start_iter(),
                                dialog.buffer_editor.get_end_iter(), True))

                        self.logger.info(
                            "Update %s configuration file" % emulator.name)

                    self.config.modify(
                        "windows", "editor", "%dx%d" % dialog.get_size())
                    self.config.update()

                    self.set_sensitive(True)

                    dialog.destroy()

    def __on_remove_console(self, *args):
        """ Remove a console from user configuration
        """

        self.__block_signals()

        selected_row = self.listbox_consoles.get_selected_row()

        if self.__current_menu_row is not None:
            console = self.__current_menu_row.console

            dialog = GeodeDialog.Question(
                self,
                _("Remove a console"),
                _("Are you sure you want to remove <b>%s</b> ?") % (
                    console.name))

            if dialog.run() == Gtk.ResponseType.YES:

                # Remove console
                self.api.delete_console(console.id)

                # Write consoles data
                self.api.write_data(GEM.Consoles)

                # Remove row from listbox
                self.listbox_consoles.remove(self.__current_menu_row)

                # Remove the current selected console
                if selected_row == self.__current_menu_row:
                    self.selection["console"] = None

                    self.infobar.set_visible(False)
                    self.scroll_sidebar.set_visible(False)
                    self.scroll_games_list.set_visible(False)
                    self.scroll_games_grid.set_visible(False)

                    self.scroll_games_placeholder.set_visible(True)

                    self.model_games_list.clear()
                    self.model_games_grid.clear()

                    self.set_informations()

            dialog.destroy()

        self.__unblock_signals()

    def __on_clear_games_views(self):
        """ Remove games from both list and icon views
        """

        if len(self.model_games_list):
            self.logger.debug("Clear games treeview content")
            self.model_games_list.clear()

        if len(self.model_games_grid):
            self.logger.debug("Clear games iconview content")
            self.model_games_grid.clear()

    def append_consoles(self):
        """ Append to consoles combobox all available consoles

        This function add every consoles into consoles combobox and inform user
        when an emulator binary is missing
        """

        # Reset consoles caches
        self.consoles_iter.clear()

        # Remove previous consoles objects
        for child in self.listbox_consoles.get_children():
            self.listbox_consoles.remove(child)

        # Reset games view content
        self.__on_clear_games_views()

        # Retrieve available consoles
        for console in self.api.consoles:
            console_data = self.__on_generate_console_row(console)

            if console_data is not None:
                row = self.__on_append_console_row(*console_data)

                # Store console iter
                self.consoles_iter[row.console.id] = row

        self.__on_update_consoles()

        if len(self.listbox_consoles) > 0:
            self.scroll_sidebar.set_visible(self.show_sidebar)

            self.logger.debug(
                "%d console(s) has been added" % len(self.listbox_consoles))

        # Show games placeholder when no console available
        else:
            self.scroll_games_placeholder.set_visible(True)
            self.scroll_sidebar.set_visible(False)

    def __on_generate_console_row(self, console):
        """ Generate console row data from a specific console

        Parameters
        ----------
        console : gem.engine.console.Console or str
            Console instance or identifier

        Returns
        -------
        tuple or None
            Generation results
        """

        if not isinstance(console, Console):
            console = self.api.get_console(console)

        # Load games list if the game directory exists
        if console.path.exists():

            try:
                console.init_games()

            except OSError as error:
                self.logger.warning(error)

        else:
            self.logger.warning(
                "Cannot found games directory for %s" % console.name)

        icon = self.get_pixbuf_from_cache(
            "consoles", 24, console.id, console.icon)

        if icon is None:
            icon = self.icons.blank(24)

        return (console, icon)

    def __on_append_console_row(self, console, icon):
        """ Append console row in consoles list

        Parameters
        ----------
        console : gem.engine.console.Console
            Console instance
        icon : GdkPixbuf.Pixbuf
            Console icon

        Returns
        -------
        Gtk.ListBoxRow
            New console row
        """

        grid_console = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 8)
        grid_console.set_border_width(6)

        row_console = Gtk.ListBoxRow()
        row_console.add(grid_console)

        image_console = Gtk.Image.new_from_pixbuf(icon)

        label_console = Gtk.Label.new(console.name)
        label_console.set_ellipsize(Pango.EllipsizeMode.END)
        label_console.set_halign(Gtk.Align.START)

        if console.favorite:
            image_console_status = Gtk.Image.new_from_icon_name(
                Icons.Symbolic.FAVORITE, Gtk.IconSize.MENU)

        else:
            image_console_status = Gtk.Image.new_from_pixbuf(
                self.icons.blank(22))

        text = _("No game")
        if console.get_games():
            text = ngettext(
                _("1 game"),
                _("%d games") % len(console.get_games()),
                len(console.get_games()))

        row_console.set_tooltip_text(text)

        grid_console.pack_start(image_console, False, False, 0)
        grid_console.pack_start(label_console, True, True, 0)
        grid_console.pack_start(image_console_status, False, False, 0)

        row_console.show_all()

        setattr(row_console, "label", label_console)
        setattr(row_console, "console", console)
        setattr(row_console, "image_icon", image_console)
        setattr(row_console, "image_status", image_console_status)

        self.listbox_consoles.add(row_console)

        return row_console

    def __on_selected_console(self, widget, row, force=False):
        """ Select a console

        This function occurs when the user select a console in the consoles
        listbox

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        row : gem.gtk.widgets.ListBoxSelectorItem
            Activated row
        force : bool
            Force console selection even if this is the same console
        """

        # Avoid to reload the same console
        if force or not self.selection["console"] == row.console:
            self.__block_signals()

            self.selection["name"] = None
            self.selection["game"] = None
            self.selection["console"] = row.console

            self.infobar.set_visible(False)

            self.set_informations_headerbar()

            self.logger.debug("Select %s console" % row.console.name)

            self.__console_icon = self.get_pixbuf_from_cache(
                "consoles", 96, row.console.id, row.console.icon)

            if self.__console_icon is None:
                self.__console_icon = self.icons.blank(96)

            self.__console_thumbnail = self.get_pixbuf_from_cache(
                "consoles", 22, row.console.id, row.console.icon)

            if self.__console_thumbnail is None:
                self.__console_thumbnail = self.icons.blank(22)

            # ------------------------------------
            #   Check data
            # ------------------------------------

            self.sensitive_interface()

            # Set console informations into button grid widgets
            self.listbox_consoles.select_row(row)

            self.__unblock_signals()

            # ------------------------------------
            #   Load game list
            # ------------------------------------

            if not self.list_thread == 0:
                GLib.source_remove(self.list_thread)

            loader = self.append_games(row.console)
            self.list_thread = GLib.idle_add(loader.__next__)

    def __on_retrieve_selected_console(self):
        """ Retrieve console object instance from current selection

        Returns
        -------
        gem.engine.console.Console or None
            Console instance when a selection exists, None otherwise
        """

        if "console" in self.selection:
            return self.selection["console"]

        return None

    def __on_sort_consoles(self, first_row, second_row, *args):
        """ Sort consoles to reorganize them

        Parameters
        ----------
        first_row : gem.gtk.widgets.ListBoxSelectorItem
            First row to compare
        second_row : gem.gtk.widgets.ListBoxSelectorItem
            Second row to compare
        """

        # Sort by name when favorite status are identical
        if first_row.console.favorite == second_row.console.favorite:
            return first_row.console.name.lower() > \
                second_row.console.name.lower()

        return first_row.console.favorite < second_row.console.favorite

    def __on_filter_consoles(self, row, *args):
        """ Filter list with consoles searchentry text

        Parameters
        ----------
        row : gem.gtk.widgets.ListBoxSelectorItem
            Activated row
        """

        try:
            widget = self.toolbar_consoles.get_widget("entry")
            if widget is None:
                return False

            filter_text = widget.get_text().strip().lower()

            if self.hide_empty_console and len(row.console.get_games()) == 0:
                return False

            if len(filter_text) == 0:
                return True

            return filter_text in row.console.name.lower()

        except Exception:
            return False

    def __on_update_consoles(self, *args):
        """ Reload consoles list when user set a filter
        """

        self.listbox_consoles.invalidate_sort()
        self.listbox_consoles.invalidate_filter()

    def __on_change_console_option(self, widget, *args):
        """ Change a console option switch

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        self.__block_signals()

        if widget == self.toolbar_consoles.get_widget("hide_empty"):

            self.hide_empty_console = not self.config.getboolean(
                "gem", "hide_empty_console", fallback=False)

            self.config.modify(
                "gem", "hide_empty_console", self.hide_empty_console)
            self.config.update()

            self.toolbar_consoles.set_active(
                self.hide_empty_console, widget="hide_empty")

            self.__on_update_consoles()

        elif self.__current_menu_row is not None:

            if widget == self.menu_consoles.get_widget("recursive"):
                self.__current_menu_row.console.recursive = \
                    not self.__current_menu_row.console.recursive

                self.api.write_object(self.__current_menu_row.console)

            elif widget == self.menu_consoles.get_widget("favorite"):
                self.__current_menu_row.console.favorite = \
                    not self.__current_menu_row.console.favorite

                if self.__current_menu_row.console.favorite:
                    self.__current_menu_row.image_status.set_from_icon_name(
                        Icons.Symbolic.FAVORITE, Gtk.IconSize.MENU)

                else:
                    self.__current_menu_row.image_status.set_from_icon_name(
                        None, Gtk.IconSize.MENU)

                self.api.write_object(self.__current_menu_row.console)

                self.__on_update_consoles()

        self.__unblock_signals()

    def __on_console_menu_show(self, widget, event):
        """ Open context menu

        This function open context-menu when user right-click or use context
        key on games treeview

        Parameters
        ----------
        widget : Gtk.ListBox
            Object which receive signal
        event : Gdk.EventButton or Gdk.EventKey
            Event which triggered this signal

        Returns
        -------
        bool
            Context menu popup status
        """

        self.__block_signals()

        status = False

        selected_row = self.listbox_consoles.get_selected_row()

        self.__current_menu_row = None

        # Gdk.EventButton - Mouse
        if event.type == Gdk.EventType.BUTTON_PRESS:
            if event.button == Gdk.BUTTON_SECONDARY:
                row = widget.get_row_at_y(int(event.y))

                if row is not None:
                    self.__current_menu_row = row

                    self.menu_consoles.set_sensitive(False, widget="edit_file")

                    # Check console emulator
                    if row.console.emulator is not None:
                        configuration = row.console.emulator.configuration

                        # Check emulator configurator
                        self.menu_consoles.set_sensitive(
                            configuration is not None and
                            configuration.exists(),
                            widget="edit_file")

                    # Check console paths
                    if row.console.path is not None:
                        self.menu_consoles.set_sensitive(
                            row.console.path.exists(), widget="copy_path")
                        self.menu_consoles.set_sensitive(
                            row.console.path.exists(), widget="open_path")

                    self.menu_consoles.set_sensitive(
                        selected_row == row, widget="reload")

                    self.menu_consoles.set_active(
                        row.console.favorite, widget="favorite")
                    self.menu_consoles.set_active(
                        row.console.recursive, widget="recursive")

                    self.menu_consoles.popup_at_pointer(event)

                    status = True

        # Gdk.EventKey - Keyboard
        elif event.type == Gdk.EventType.KEY_RELEASE:
            if event.keyval == Gdk.KEY_Menu:
                row = widget.get_selected_row()

                if row is not None:
                    self.__current_menu_row = row

                    self.menu_consoles.set_sensitive(False, widget="edit_file")

                    # Check console emulator
                    if row.console.emulator is not None:
                        configuration = row.console.emulator.configuration

                        # Check emulator configurator
                        self.menu_consoles.set_sensitive(
                            configuration is not None and
                            configuration.exists(),
                            widget="edit_file")

                    self.menu_consoles.set_sensitive(
                        selected_row == row, widget="reload")

                    self.menu_consoles.set_active(
                        row.console.favorite, widget="favorite")
                    self.menu_consoles.set_active(
                        row.console.recursive, widget="recursive")

                    self.menu_consoles.popup_at_widget(
                        row, Gdk.Gravity.CENTER, Gdk.Gravity.NORTH, event)

                    status = True

        self.__unblock_signals()

        return status

    def append_games(self, console):
        """ Append to games treeview all games from console

        This function add every games which match console extensions to games
        treeview

        Parameters
        ----------
        console : gem.engine.console.Console
            Console object

        Raises
        ------
        TypeError
            if console type is not gem.engine.console.Console

        Notes
        -----
        Using yield avoid an UI freeze when append a lot of games
        """

        if type(console) is not Console:
            raise TypeError(
                "Wrong type for console, expected gem.engine.console.Console")

        self.logger.debug(f"Start to append games for console {console.name}")

        # Get current thread id
        current_thread_id = self.list_thread

        self.game_path = dict()

        # ------------------------------------
        #   Check errors
        # ------------------------------------

        self.__block_signals()

        self.infobar.set_visible(False)

        if console.emulator is None:
            self.logger.warning(
                "Cannot find emulator for %s" % console.name)

            self.infobar.set_message(
                Gtk.MessageType.WARNING,
                _("There is no default emulator set for this console"))

        elif not console.emulator.exists:
            self.logger.warning(
                "%s emulator not exist" % console.emulator.name)

            self.infobar.set_message(
                Gtk.MessageType.ERROR,
                _("<b>%s</b> cannot been found on your system") % (
                    console.emulator.name))

        # ------------------------------------
        #   Load data
        # ------------------------------------

        self.unselect_all()

        self.scroll_games_list.set_visible(False)
        self.scroll_games_grid.set_visible(False)

        self.scroll_games_placeholder.set_visible(True)

        self.__on_clear_games_views()

        self.set_informations()

        # ------------------------------------
        #   Refresh treeview
        # ------------------------------------

        self.treeview_games.freeze_child_notify()

        # ------------------------------------
        #   Prepare games
        # ------------------------------------

        self.selection["console"] = console

        # Load games list if the game directory exists
        if console.path.exists():

            try:
                console.init_games()

            except OSError as error:
                self.logger.warning(error)

        games = console.get_games()
        if len(games):
            self.logger.info(f"Found {len(games)} game(s) for {console.name}")
        else:
            self.logger.info(f"No game available for {console.name}")

        column, order = self.sorted_games_list.get_sort_column_id()

        # Retrieve reverse value from column order
        reverse = order == Gtk.SortType.DESCENDING

        # Name
        if column == Columns.List.NAME:
            games.sort(key=lambda game: game.name.lower().replace(' ', ''),
                       reverse=reverse)

        # Favorite
        elif column == Columns.List.FAVORITE:
            games.sort(key=lambda game: game.favorite, reverse=reverse)

        # Multiplayer
        elif column == Columns.List.MULTIPLAYER:
            games.sort(key=lambda game: game.multiplayer, reverse=reverse)

        # Finish
        elif column == Columns.List.FINISH:
            games.sort(key=lambda game: game.finish, reverse=reverse)

        # Played
        elif column == Columns.List.PLAYED:
            games.sort(key=lambda game: game.played, reverse=reverse)

        # Last play
        elif column == Columns.List.LAST_PLAY:
            games.sort(
                key=lambda game: game.last_launch_date, reverse=reverse)

        # Play time
        elif column == Columns.List.TIME_PLAY:
            games.sort(key=lambda game: game.play_time, reverse=reverse)

        # Score
        elif column == Columns.List.SCORE:
            games.sort(key=lambda game: game.score, reverse=reverse)

        # Installed
        elif column == Columns.List.INSTALLED:
            games.sort(key=lambda game: game.installed, reverse=reverse)

        # ------------------------------------
        #   Load games
        # ------------------------------------

        if len(games) > 0:
            self.scroll_sidebar.set_visible(self.config.getboolean(
                "gem", "show_sidebar", fallback=True))

            if self.toolbar_games.get_active("list"):
                self.scroll_games_list.set_visible(True)
                self.treeview_games.show_all()

            if self.toolbar_games.get_active("grid"):
                self.scroll_games_grid.set_visible(True)
                self.iconview_games.show_all()

            self.scroll_games_placeholder.set_visible(False)

            self.statusbar.progressbar.show()

        else:
            self.scroll_sidebar.set_visible(False)

        self.__unblock_signals()

        yield True

        # Start a timer for debug purpose
        started = datetime.now()

        index = int()
        for game in games:
            index += 1

            # Another thread has been called by user, close this one
            if not current_thread_id == self.list_thread:
                yield False

            if self.__on_append_game(console, game):
                self.set_informations_headerbar()

                self.statusbar.set_widget_value(
                    "progressbar", index=index, length=len(games))

                self.treeview_games.thaw_child_notify()
                yield True
                self.treeview_games.freeze_child_notify()

        # Restore options for packages treeviews
        self.treeview_games.thaw_child_notify()

        self.statusbar.progressbar.hide()

        self.set_informations_headerbar()

        # ------------------------------------
        #   Timer - Debug
        # ------------------------------------

        delta = (datetime.now() - started).total_seconds()

        if len(console.get_games()):
            self.logger.debug(
                f"Append game(s) for {console.name} in {delta} second(s)")

        # ------------------------------------
        #   Close thread
        # ------------------------------------

        self.list_thread = int()

        yield False

    def __on_append_game(self, console, game):
        """ Append a new game to current views

        Parameters
        ----------
        console : gem.engine.console.Console
            Console instance
        game : gem.engine.game.Game
            Game instance
        """

        # Hide games which match ignores regex
        show = True
        for element in console.ignores:
            try:
                if match(element, game.name, IGNORECASE) is not None:
                    show = False
                    break

            except Exception:
                pass

        # Check if rom file exists
        if game.path.exists() and show:

            # ------------------------------------
            #   Grid mode
            # ------------------------------------

            row_data = [
                self.__console_icon,
                game.name,
                game
            ]

            # Large icon
            icon = self.get_pixbuf_from_cache(
                "games", 96, game.id, game.cover)

            if icon is not None:
                row_data[Columns.Grid.THUMBNAIL] = icon

            row_grid = self.model_games_grid.append(row_data)

            # ------------------------------------
            #   List mode
            # ------------------------------------

            row_data = [
                self.icons.get_translucent("favorite"),
                self.icons.get_translucent("multiplayer"),
                self.icons.get_translucent("unfinish"),
                game.name,
                game.played,
                str(),          # Last launch date
                str(),          # Last launch time
                str(),          # Total play time
                game.score,
                str(),          # Installed date
                self.icons.get_translucent("parameter"),
                self.icons.get_translucent("screenshot"),
                self.icons.get_translucent("savestate"),
                game,
                self.__console_thumbnail
            ]

            # Favorite
            if game.favorite:
                row_data[Columns.List.FAVORITE] = \
                    self.icons.get("favorite")

            # Multiplayer
            if game.multiplayer:
                row_data[Columns.List.MULTIPLAYER] = \
                    self.icons.get("multiplayer")

            # Finish
            if game.finish:
                row_data[Columns.List.FINISH] = \
                    self.icons.get("finish")

            # Last launch date
            if not game.last_launch_date.strftime("%d%m%y") == "010101":
                row_data[Columns.List.LAST_PLAY] = \
                    string_from_date(game.last_launch_date)

            # Last launch time
            if not game.last_launch_time == timedelta():
                row_data[Columns.List.LAST_TIME_PLAY] = \
                    string_from_time(game.last_launch_time)

            # Play time
            if not game.play_time == timedelta():
                row_data[Columns.List.TIME_PLAY] = \
                    string_from_time(game.play_time)

            # Parameters
            if len(game.default) > 0:
                row_data[Columns.List.PARAMETER] = \
                    self.icons.get("parameter")

            elif not game.emulator == console.emulator:
                row_data[Columns.List.PARAMETER] = \
                    self.icons.get("parameter")

            # Installed time
            if game.installed is not None:
                row_data[Columns.List.INSTALLED] = \
                    string_from_date(game.installed)

            # Snap
            if len(game.screenshots) > 0:
                row_data[Columns.List.SCREENSHOT] = \
                    self.icons.get("screenshot")

            # Save state
            if len(game.savestates) > 0:
                row_data[Columns.List.SAVESTATE] = \
                    self.icons.get("savestate")

            # Thumbnail icon
            icon = self.get_pixbuf_from_cache(
                "games", 22, game.id, game.cover)

            if icon is not None:
                row_data[Columns.List.THUMBNAIL] = icon

            row_list = self.model_games_list.append(row_data)

            # ------------------------------------
            #   Refesh view
            # ------------------------------------

            # Store both Gtk.TreeIter under game filename key
            self.game_path[game.id] = [game, row_list, row_grid]

            return True

        return False

    def __on_update_game_columns(self, column, cell, model, treeiter, *args):
        """ Manage specific columns behavior during games adding

        Parameters
        ----------
        column : Gtk.TreeViewColumn
            Treeview column which contains cell
        cell : Gtk.CellRenderer
            Cell that is being rendered by column
        model : Gtk.TreeModel
            Rendered model
        treeiter : Gtk.TreeIter
            Rendered row
        """

        if column.get_visible():
            score = model.get_value(treeiter, Columns.List.SCORE)

            for widget in self.__rating_score:

                if score >= self.__rating_score.index(widget) + 1:
                    widget.set_property(
                        "pixbuf", self.icons.get("starred"))
                else:
                    widget.set_property(
                        "pixbuf", self.icons.get_translucent("nostarred"))

    def __on_selected_game(self, widget):
        """ Select a game

        This function occurs when the user select a game in the games treeview

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        self.__block_signals()

        # Current selected game
        game = self.__on_retrieve_selected_game()

        # No game has been choosen (when the user click in the empty view area)
        if game is None:
            # Unselect both games views
            self.unselect_all()

            # Reset sidebar widgets and menus entries
            self.sensitive_interface()
            self.set_informations()

        # A new game has been selected
        elif not self.selection["game"] == game:
            self.logger.debug(f"Select game '{game.id}'")

            # Synchronize selection between both games views
            self.__on_synchronize_game_selection(widget, game)

            # Update game informations and widgets
            self.sensitive_interface()
            self.set_informations()

        # Store game instance
        self.selection["game"] = game

        self.__unblock_signals()

    def __on_selected_game_tooltip(self, treeview, x, y, keyboard, tooltip):
        """ Show game informations tooltip

        Parameters
        ----------
        treeview : Gtk.TreeView
            Widget which received the signal
        x : int
            X coordinate for mouse cursor position
        y : int
            Y coordinate for mouse cursor position
        keyboard : bool
            Set as True if the tooltip has been trigged by keyboard
        tooltip : Gtk.Tooltip
            Tooltip widget

        Returns
        -------
        bool
            Tooltip visible status
        """

        # Show a tooltip when the show_tooltip option is activate
        if not self.config.getboolean("gem", "show_tooltip", fallback=True):
            return False

        # Show a tooltip when the main window is sentitive only
        if not self.get_sensitive():
            return False

        # Get relative treerow position based on absolute cursor
        # coordinates
        x, y = treeview.convert_widget_to_bin_window_coords(x, y)

        selection = treeview.get_path_at_pos(x, y)
        # Using a tuple to mimic Gtk.TreeView behavior
        if treeview == self.iconview_games and selection is not None:
            selection = (selection)

        if selection is not None:
            model = treeview.get_model()
            treeiter = model.get_iter(selection[0])

            column_id = Columns.Grid.OBJECT
            if treeview == self.treeview_games:
                column_id = Columns.List.OBJECT

            game = model.get_value(treeiter, column_id)

            # Reload tooltip when another game is hovered
            if not self.__current_tooltip == game:
                self.__current_tooltip = game
                self.__current_tooltip_data = list()
                self.__current_tooltip_pixbuf = None

                return False

            # Get new data from hovered game
            if len(self.__current_tooltip_data) == 0:
                data = list()

                data.append(
                    "<big><b>%s</b></big>" % replace_for_markup(game.name))

                if not game.play_time == timedelta():
                    data.append(
                        ": ".join(
                            [
                                "<b>%s</b>" % _("Play time"),
                                parse_timedelta(game.play_time)
                            ]
                        )
                    )

                if not game.last_launch_time == timedelta():
                    data.append(
                        ": ".join(
                            [
                                "<b>%s</b>" % _("Last launch"),
                                parse_timedelta(game.last_launch_time)
                            ]
                        )
                    )

                # Fancy new line
                if len(data) > 1:
                    data.insert(1, str())

                self.__current_tooltip_data = data

            console = self.selection["console"]

            # Get new screenshots from hovered game
            if console is not None \
               and self.__current_tooltip_pixbuf is None:

                image = None

                # Retrieve user choice for tooltip image
                tooltip_image = self.config.get(
                    "gem", "tooltip_image_type", fallback="screenshot")

                if not tooltip_image == "none":

                    if tooltip_image in ["both", "cover"]:

                        if game.cover is not None and game.cover.exists():
                            image = game.cover

                    if tooltip_image in ["both", "screenshot"]:

                        # Ordered game screenshots
                        if not self.use_random_screenshot:
                            screenshots = sorted(game.screenshots)

                        # Get a random file from game screenshots
                        else:
                            screenshots = game.screenshots

                            shuffle(screenshots)

                        if len(game.screenshots) > 0:
                            image = Path(screenshots[-1])

                    # Check if image exists and is not a directory
                    if image is not None \
                       and image.exists() and image.is_file():

                        try:
                            # Resize pixbuf to have a 96 pixels height
                            pixbuf = \
                                GdkPixbuf.Pixbuf.new_from_file_at_scale(
                                    str(image), -1, 96, True)

                            self.__current_tooltip_pixbuf = pixbuf

                        except GLib.Error:
                            self.__current_tooltip_pixbuf = None

                else:
                    self.__current_tooltip_pixbuf = None

            # Only show tooltip when data are available
            if len(self.__current_tooltip_data) > 0:
                tooltip.set_markup('\n'.join(self.__current_tooltip_data))

                if self.__current_tooltip_pixbuf is not None:
                    tooltip.set_icon(self.__current_tooltip_pixbuf)

                self.__current_tooltip = game

                return True

        return False

    def __on_retrieve_selected_game(self):
        """ Retrieve game object instance from current selection

        Returns
        -------
        gem.engine.game.Game or None
            Game instance when a selection exists, None otherwise
        """

        # Grid view
        if self.toolbar_games.get_active("grid"):
            model = self.iconview_games.get_model()
            items = self.iconview_games.get_selected_items()

            if len(items) >= 1:
                treeiter = model.get_iter(items[0])

                if treeiter is not None:
                    return model.get_value(treeiter, Columns.Grid.OBJECT)

        # List view
        elif self.toolbar_games.get_active("list"):
            model, treeiter = self.get_selected_treeiter_from_container(
                self.treeview_games)

            if treeiter is not None:
                return model.get_value(treeiter, Columns.List.OBJECT)

        return None

    def __on_synchronize_game_selection(self, view, game):
        """ Synchronize grid and list views selection

        Parameters
        ----------
        view : Gtk.Widget
            Games view currently selected
        game : gem.engine.game.Game
            Game instance
        """

        if game is not None and game.id in self.game_path:
            self.logger.debug(f"Synchronize selection for game '{game.id}'")

            if view == self.treeview_games:
                viewiter = self.sorted_games_grid.convert_child_iter_to_iter(
                    self.filter_games_grid.convert_child_iter_to_iter(
                        self.game_path[game.id][2])[1])[1]

                path = self.sorted_games_grid.get_path(viewiter)

                if path is not None:
                    self.iconview_games.select_path(path)
                    self.iconview_games.scroll_to_path(path, True, 0.5, 0.5)

                else:
                    self.iconview_games.unselect_all()

            elif view == self.iconview_games:
                viewiter = self.sorted_games_list.convert_child_iter_to_iter(
                    self.filter_games_list.convert_child_iter_to_iter(
                        self.game_path[game.id][1])[1])[1]

                path = self.sorted_games_list.get_path(viewiter)

                if path is not None:
                    self.treeview_games.set_cursor(path, None, False)
                    self.treeview_games.scroll_to_cell(
                        path, None, True, 0.5, 0.5)

                else:
                    selection = self.treeview_games.get_selection()
                    if selection is not None:
                        selection.unselect_all()

    def __on_reload_games(self, *args):
        """ Reload games list from selected console
        """

        row = self.listbox_consoles.get_selected_row()

        if row is not None:
            self.__on_selected_console(None, row, force=True)

    def __on_sort_games(self, model, row1, row2, column):
        """ Sort games list for specific columns

        Parameters
        ----------
        model : Gtk.TreeModel
            Treeview model which receive signal
        row1 : Gtk.TreeIter
            First treeiter to compare with second one
        row2 : Gtk.TreeIter
            Second treeiter to compare with first one
        column : int
            Sorting column index

        Returns
        -------
        int
            Sorting comparaison result
        """

        order = Gtk.SortType.ASCENDING

        data1 = model.get_value(row1, Columns.List.OBJECT)
        data2 = model.get_value(row2, Columns.List.OBJECT)

        # Favorite
        if column == Columns.List.FAVORITE:
            first = data1.favorite
            second = data2.favorite

            order = self.column_game_favorite.get_sort_order()

        # Multiplayer
        elif column == Columns.List.MULTIPLAYER:
            first = data1.multiplayer
            second = data2.multiplayer

            order = self.column_game_multiplayer.get_sort_order()

        # Finish
        elif column == Columns.List.FINISH:
            first = data1.finish
            second = data2.finish

            order = self.column_game_finish.get_sort_order()

        # Last play
        elif column == Columns.List.LAST_PLAY:
            first = data1.last_launch_date
            second = data2.last_launch_date

        # Play time
        elif column == Columns.List.TIME_PLAY:
            first = data1.play_time
            second = data2.play_time

        # Score
        elif column == Columns.List.SCORE:
            first = data1.score
            second = data2.score

            order = self.column_game_score.get_sort_order()

        # Installed
        elif column == Columns.List.INSTALLED:
            first = data1.installed
            second = data2.installed

        # ----------------------------------------
        #   Compare
        # ----------------------------------------

        # Sort by name in the case where this games are never been launched
        if first is None and second is None:

            if data1.name.lower() < data2.name.lower():
                return -1

            elif data1.name.lower() == data2.name.lower():
                return 0

        # The second has been launched instead of first one
        elif first is None:
            return -1

        # The first has been launched instead of second one
        elif second is None:
            return 1

        elif first < second:
            return -1

        elif first == second:

            if data1.name.lower() < data2.name.lower():

                if order == Gtk.SortType.ASCENDING:
                    return -1

                elif order == Gtk.SortType.DESCENDING:
                    return 1

            elif data1.name.lower() == data2.name.lower():
                return 0

        return 1

    def __on_switch_games_view(self, widget):
        """ Switch between the available games list view mode

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        self.__block_signals()

        games_view = "grid"
        if widget in (self.headerbar.get_widget("list"),
                      self.menubar_view.get_widget("list"),
                      self.toolbar_games.get_widget("list")):
            games_view = "list"

        # Update widgets status based on selected games view
        self.headerbar.set_active(True, widget=games_view)
        self.menubar_view.set_active(True, widget=games_view)
        self.toolbar_games.get_widget("views").switch_to(games_view)

        # Show activated games view when there are games available
        if not self.scroll_games_placeholder.get_visible():
            self.scroll_games_list.set_visible(games_view == "list")
            self.scroll_games_grid.set_visible(games_view == "grid")

            if self.scroll_games_list.get_visible():
                self.treeview_games.show_all()

            elif self.scroll_games_grid.get_visible():
                self.iconview_games.show_all()

        self.__unblock_signals()

    def __on_switch_column_visibility(self, widget, key):
        """ Manage games treeview columns visibility

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        key : str
            Column key
        """

        self.__block_signals()

        if self.config.has_option("columns", key):
            self.config.modify("columns", key, widget.get_active())

            column = getattr(self, "column_game_%s" % key, None)
            if column is not None:
                column.set_visible(widget.get_active())

                self.logger.debug(f"Switch visibility for '{key}' column to "
                                  f"{column.get_visible()}")

        self.__unblock_signals()

    def check_selection(self):
        """ Check selected game

        This function check if the selected game in the games treeview is the
        same as the one stock in self.selection["game"]. If this is not the
        case, the self.selection is reset

        Returns
        -------
        bool
            Check status
        """

        name = None

        if self.selection["game"] is not None:
            name = self.selection["game"].name

        if name is not None:
            model, treeiter = self.get_selected_treeiter_from_container(
                self.treeview_games)

            if treeiter is not None:
                treeview_name = model.get_value(treeiter, Columns.List.NAME)

                if not treeview_name == name:
                    selection = self.treeview_games.get_selection()
                    if selection is not None:
                        selection.unselect_iter(treeiter)

                    self.selection["game"] = None

                    self.sensitive_interface()
                    self.set_informations()

                    return False

        return True

    def unselect_all(self):
        """ Unselect selections from both games views
        """

        self.logger.debug("Unselect games on both views")

        self.iconview_games.unselect_all()

        selection = self.treeview_games.get_selection()
        if selection is not None:
            selection.unselect_all()

    def get_selected_treeiter_from_container(self, widget):
        """ Retrieve treeiter from container widget

        Parameters
        ----------
        widget : Gtk.Container
            Container widget

        Returns
        -------
        Gtk.TreeStore, Gtk.TreeIter
            Selected treeiter
        """

        model, treeiter = None, None

        if widget == self.treeview_games:
            selection = widget.get_selection()

            if selection is not None:
                model, treeiter = selection.get_selected()

        elif widget == self.iconview_games:
            model = widget.get_model()
            items = widget.get_selected_items()

            if len(items):
                treeiter = model.get_iter(items[0])

        return model, treeiter

    def __on_game_launch_button_update(self, status):
        """ Update game launch button

        Parameters
        ----------
        status : bool
            The game status
        """

        launch_button = self.toolbar_games.get_widget("launch")
        launch_style = launch_button.current_style

        if status and not launch_style == "suggested-action":
            launch_button.set_label(_("Play"))
            launch_button.set_style("suggested-action")
            launch_button.set_tooltip_text(_("Launch selected game"))

        elif not status and not launch_style == "destructive-action":
            launch_button.set_label(_("Stop"))
            launch_button.set_style("destructive-action")
            launch_button.set_tooltip_text(_("Stop selected game"))

    def __on_game_launch(self, widget=None, *args):
        """ Prepare the game launch

        This function prepare the game launch and start a thread when
        everything are done

        Parameters
        ----------
        widget : Gtk.Widget, optional
            Object which receive signal (Default: None)
        """

        # ----------------------------------------
        #   Check selection
        # ----------------------------------------

        game = self.__on_retrieve_selected_game()

        if game is None or game.emulator is None:
            return False

        if not self.check_selection():
            return False

        if game.id in self.threads:
            if widget is not None and type(widget) is Gtk.Button:
                self.threads[game.id].proc.terminate()

            return False

        # ----------------------------------------
        #   Check emulator
        # ----------------------------------------

        console = self.__on_retrieve_selected_console()

        if console is not None and game.emulator is not None:

            if game.emulator.id in self.api.emulators:
                self.logger.info("Initialize %s" % game.name)

                # ----------------------------------------
                #   Run game
                # ----------------------------------------

                try:
                    thread = GameThread(
                        self,
                        game,
                        fullscreen=self.toolbar_games.get_active("fullscreen"))

                    # Save thread references
                    self.threads[game.id] = thread

                    # Launch thread
                    thread.start()

                    self.__on_game_launch_button_update(False)
                    self.toolbar_games.set_sensitive(True, widget="launch")

                    self.menu_game.set_sensitive(True, widget="game_log")
                    self.menubar_game.set_sensitive(True, widget="game_log")
                    self.toolbar_games.set_sensitive(True, widget="game_log")

                    return True

                except FileNotFoundError:
                    self.set_message(
                        _("Cannot launch game"),
                        _("%s binary cannot be found") % game.emulator.name)

                    return False

        return False

    def __on_game_started(self, widget, game):
        """ The game processus has been started

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        game : gem.engine.game.Game
            Game object
        """

        path = self.api.get_local("ongamestarted")

        if path.exists() and access(path, X_OK):
            thread = ScriptThread(self, path, game)

            # Save thread references
            self.scripts[game.id] = thread

            # Launch thread
            thread.start()

    def __on_script_terminate(self, widget, thread):
        """ Terminate the script processus

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        thread : gem.widgets.script.ScriptThread
            Game thread
        """

        # Remove this script from threads list
        if thread.game.id in self.scripts:
            self.logger.debug(
                "Remove %s from scripts cache" % thread.game.name)

            del self.scripts[thread.game.id]

    def __on_game_terminate(self, widget, thread):
        """ Terminate the game processus and update data

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        thread : gem.widgets.game.GameThread
            Game thread
        """

        # ----------------------------------------
        #   Save game data
        # ----------------------------------------

        # Get the last occurence from database
        game = thread.game

        if not thread.error:

            # ----------------------------------------
            #   Update data
            # ----------------------------------------

            # Play data
            game.played += 1
            game.play_time = thread.game.play_time + thread.delta
            game.last_launch_time = thread.delta
            game.last_launch_date = date.today()

            # Update game from database
            self.api.update_game(game)

            # Played
            self.set_game_data(Columns.List.PLAYED, game.played, game.id)

            # Last played
            self.set_game_data(Columns.List.LAST_PLAY,
                               string_from_date(game.last_launch_date),
                               game.id)

            # Last time played
            self.set_game_data(Columns.List.LAST_TIME_PLAY,
                               string_from_time(game.last_launch_time),
                               game.id)

            # Play time
            self.set_game_data(Columns.List.TIME_PLAY,
                               string_from_time(game.play_time),
                               game.id)

            # Snaps
            if len(game.screenshots) > 0:
                self.set_game_data(Columns.List.SCREENSHOT,
                                   self.icons.get("screenshot"),
                                   game.id)
                self.menubar_game.set_sensitive(True, widget="screenshots")
                self.toolbar_games.set_sensitive(True, widget="screenshots")

            else:
                self.set_game_data(Columns.List.SCREENSHOT,
                                   self.icons.get_translucent("screenshot"),
                                   game.id)

            # Save state
            if len(game.savestates) > 0:
                self.set_game_data(Columns.List.SAVESTATE,
                                   self.icons.get("savestate"),
                                   game.id)

            else:
                self.set_game_data(Columns.List.SAVESTATE,
                                   self.icons.get_translucent("savestate"),
                                   game.id)

            self.set_informations()

        # ----------------------------------------
        #   Refresh widgets
        # ----------------------------------------

        # Get current selected file
        select_game = self.__on_retrieve_selected_game()
        # Get current selected console
        select_console = self.__on_retrieve_selected_console()

        if select_console is None:
            self.logger.debug("Restore widgets status for %s" % game.name)

            self.sensitive_interface()

        # Check if current selected file is the same as thread file
        elif select_game is not None and select_game.id == game.id:
            self.logger.debug("Restore widgets status for %s" % game.name)

            self.__on_game_launch_button_update(True)
            self.toolbar_games.set_sensitive(True, widget="launch")

            self.menu_game.set_sensitive(True, widget="launch")
            self.menu_game.set_sensitive(True, widget="remove")

            self.menubar_game.set_sensitive(True, widget="launch")
            self.menubar_edit.set_sensitive(True, widget="remove")

            self.__current_tooltip = None

            if game.emulator is not None:

                # Check extension and emulator for GBA game on mednafen
                if self.__mednafen_status and game.extension == ".gba":

                    if "mednafen" in str(game.emulator.binary):
                        self.menu_game.set_sensitive(
                            True, widget="memory_type")
                        self.menubar_edit.set_sensitive(
                            True, widget="memory_type")

        # ----------------------------------------
        #   Manage thread
        # ----------------------------------------

        # Remove this game from threads list
        if game.id in self.threads:
            self.logger.debug("Remove %s from process cache" % game.name)

            del self.threads[game.id]

        if len(self.threads) == 0:
            self.headerbar.set_sensitive(True, widget="quit")
            self.menubar_main.set_sensitive(True, widget="quit")

        # ----------------------------------------
        #   Manage script
        # ----------------------------------------

        # Remove this script from threads list
        if game.id in self.scripts:
            self.logger.debug("Remove %s from scripts cache" % game.name)

            del self.scripts[game.id]

        path = self.api.get_local("ongamestopped")

        if path.exists() and access(path, X_OK):
            thread = ScriptThread(self, path, game)

            # Save thread references
            self.scripts[game.id] = thread

            # Launch thread
            thread.start()

    def __on_game_renamed(self, *args):
        """ Set a custom name for a specific game

        Parameters
        ----------
        widget : Gtk.CellRendererText
            object which received the signal
        path : str
            path identifying the edited cell
        new_name : str
            new name
        """

        game = self.__on_retrieve_selected_game()

        if game is not None:
            self.set_sensitive(False)

            dialog = GeodeDialog.Rename(self, game)

            if dialog.run() == Gtk.ResponseType.APPLY:

                new_name = dialog.get_name().strip()

                # Check if game name has been changed
                if not new_name == game.name:
                    self.logger.info("Rename \"%(old)s\" to \"%(new)s\"" % {
                        "old": game.name,
                        "new": new_name
                    })

                    game.name = new_name

                    row, treepath, gridpath = self.game_path[game.id]

                    treepath = self.model_games_list.get_path(treepath)

                    # Update game name
                    self.model_games_list[treepath][Columns.List.NAME] = str(
                        new_name)
                    self.model_games_list[treepath][Columns.List.OBJECT] = game

                    self.model_games_grid[gridpath][Columns.Grid.NAME] = str(
                        new_name)
                    self.model_games_grid[gridpath][Columns.Grid.OBJECT] = game

                    # Update game from database
                    self.api.update_game(game)

                    # Store modified game
                    self.selection["game"] = game

                    # Restore focus to current game view
                    if self.toolbar_games.get_active("grid"):
                        self.iconview_games.grab_focus()

                    elif self.toolbar_games.get_active("list"):
                        self.treeview_games.grab_focus()

                    self.__current_tooltip = None

                    self.set_informations()

            self.set_sensitive(True)

            dialog.destroy()

    def __on_game_maintenance(self, *args):
        """ Set some maintenance for selected game
        """

        game = self.__on_retrieve_selected_game()
        console = self.__on_retrieve_selected_console()

        if game is not None and console is not None:

            # Avoid trying to remove an executed game
            if game.id not in self.threads:
                treeiter = self.game_path[game.id][1]

                need_to_reload = False

                # ----------------------------------------
                #   Dialog
                # ----------------------------------------

                self.set_sensitive(False)

                dialog = GeodeDialog.Maintenance(self, game)

                if dialog.run() == Gtk.ResponseType.APPLY:
                    try:
                        self.logger.info("%s maintenance" % game.name)

                        data = dialog.get_data()

                        # Reload the games list
                        if len(data["paths"]) > 0:

                            # Duplicate game files
                            for element in data["paths"]:
                                self.logger.debug("Remove %s" % element)

                                remove(element)

                            need_to_reload = True

                        # Clean game from database
                        if data["database"]:
                            game_data = {
                                Columns.List.FAVORITE:
                                    self.icons.get_translucent("favorite"),
                                Columns.List.NAME: game.path.stem,
                                Columns.List.PLAYED: None,
                                Columns.List.LAST_PLAY: None,
                                Columns.List.TIME_PLAY: None,
                                Columns.List.LAST_TIME_PLAY: None,
                                Columns.List.SCORE: 0,
                                Columns.List.PARAMETER:
                                    self.icons.get_translucent("parameter"),
                                Columns.List.MULTIPLAYER:
                                    self.icons.get_translucent("multiplayer"),
                            }

                            for key, value in game_data.items():
                                self.model_games_list[treeiter][key] = value

                            game.reset()

                            # Update game from database
                            self.api.update_game(game)

                            need_to_reload = True

                        # Remove environment variables from game
                        elif data["environment"]:
                            game.environment = dict()

                            # Update game from database
                            self.api.update_game(game)

                            need_to_reload = True

                        # Set game output buttons as unsensitive
                        if data["log"]:
                            self.toolbar_games.set_sensitive(
                                False, widget="game_log")
                            self.menu_game.set_sensitive(
                                False, widget="game_log")
                            self.menubar_game.set_sensitive(
                                False, widget="game_log")

                        for widget in ("favorite", "multiplayer", "finish"):
                            self.menu_game.set_active(False, widget=widget)
                            self.menubar_game.set_active(False, widget=widget)

                    except Exception:
                        self.logger.exception("An error occur during removing")

                dialog.destroy()

                if need_to_reload:
                    self.set_informations()

                self.set_sensitive(True)

    def __on_game_removed(self, *args):
        """ Remove a game

        This function also remove files from user disk as screenshots,
        savestates and game file.
        """

        game = self.__on_retrieve_selected_game()
        console = self.__on_retrieve_selected_console()

        if game is not None and console is not None:

            # Avoid trying to remove an executed game
            if game.id not in self.threads:
                identifier = game.id

                need_to_reload = False

                # ----------------------------------------
                #   Dialog
                # ----------------------------------------

                self.set_sensitive(False)

                dialog = GeodeDialog.Delete(self, game)

                if dialog.run() == Gtk.ResponseType.YES:
                    self.logger.info("Remove %s" % game.name)

                    try:
                        data = dialog.get_data()

                        # Reload the games list
                        if len(data["paths"]) > 0:

                            # Remove specified game files
                            for element in data["paths"]:

                                if access(element, W_OK):
                                    self.logger.debug("Remove %s" % element)

                                    remove(element)

                                else:
                                    self.logger.error(
                                        "Cannot remove %s, "
                                        "operation not permitted" % element)

                            need_to_reload = True

                        # Remove game from database
                        if data["database"]:
                            self.api.delete_game(game)

                            need_to_reload = True

                        # Remove game from console storage
                        console.delete_game(game)

                        # Update console tooltip
                        if console.id in self.consoles_iter:
                            row = self.consoles_iter[console.id]

                            text = _("No game")
                            if console.get_games():
                                text = ngettext(
                                    _("1 game"),
                                    _("%d games") % len(console.get_games()),
                                    len(console.get_games()))

                            row.set_tooltip_text(text)

                    except Exception:
                        self.logger.exception("An error occur during removing")

                dialog.destroy()

                if need_to_reload:

                    # Remove an old entry in views
                    if identifier in self.game_path:
                        self.model_games_list.remove(
                            self.game_path[identifier][1])
                        self.model_games_grid.remove(
                            self.game_path[identifier][2])

                        del self.game_path[identifier]

                    # Remove view selections
                    self.unselect_all()

                    self.sensitive_interface()

                    self.set_informations()

                    self.set_message(
                        _("Remove a game"),
                        _("This game was removed successfully"),
                        Icons.INFORMATION)

                self.set_sensitive(True)

    def __on_game_duplicate(self, *args):
        """ Duplicate a game

        This function allow the user to duplicate a game and his associate
        data
        """

        game = self.__on_retrieve_selected_game()

        if game is not None:
            need_to_reload = False

            # ----------------------------------------
            #   Dialog
            # ----------------------------------------

            self.set_sensitive(False)

            dialog = GeodeDialog.Duplicate(self, game)

            if dialog.run() == Gtk.ResponseType.APPLY:
                self.logger.info("Duplicate %s" % game.name)

                try:
                    data = dialog.get_data()

                    if data is not None:

                        # Duplicate game files
                        for original, path in data["paths"]:
                            self.logger.debug("Copy %s" % original)

                            copy(original, path)

                            need_to_reload = True

                        # Update game from database
                        if data["database"]:
                            self.api.update_game(game.copy(data["filepath"]))

                            need_to_reload = True

                except Exception:
                    self.logger.exception("An error occur during duplication")

            dialog.destroy()

            if need_to_reload:
                self.__on_reload_games()

                self.set_message(
                    _("Duplicate a game"),
                    _("This game was duplicated successfully"),
                    Icons.INFORMATION)

            self.set_sensitive(True)

    def __on_game_parameters(self, *args):
        """ Manage game default parameters

        This function allow the user to specify default emulator and default
        emulator arguments for the selected game
        """

        game = self.__on_retrieve_selected_game()
        console = self.__on_retrieve_selected_console()

        if game is not None and console is not None:

            # ----------------------------------------
            #   Dialog
            # ----------------------------------------

            self.set_sensitive(False)

            dialog = GeodeDialog.Parameters(self, game)

            if dialog.run() == Gtk.ResponseType.APPLY:
                self.logger.info("Update %s parameters" % game.name)

                game.emulator = self.api.get_emulator(
                    dialog.combo.get_active_id())

                game.default = dialog.entry_arguments.get_text().strip()

                game.key = dialog.entry_key.get_text().strip()

                game.tags.clear()
                for tag in dialog.entry_tags.get_text().split(","):
                    game.tags.append(tag.strip())

                game.environment.clear()
                for row in dialog.store_environment:
                    key = dialog.store_environment.get_value(row.iter, 0)

                    if key is not None and len(key) > 0:
                        value = dialog.store_environment.get_value(row.iter, 1)

                        if value is not None and len(value) > 0:
                            game.environment[key] = value

                # Update game from database
                self.api.update_game(game)

                # ----------------------------------------
                #   Check diferences
                # ----------------------------------------

                custom = False

                if not game.emulator == console.emulator:
                    custom = True

                elif len(game.default) > 0:
                    custom = True

                if custom:
                    self.set_game_data(Columns.List.PARAMETER,
                                       self.icons.get("parameter"),
                                       game.id)
                else:
                    self.set_game_data(Columns.List.PARAMETER,
                                       self.icons.get_translucent("parameter"),
                                       game.id)

                # ----------------------------------------
                #   Update views
                # ----------------------------------------

                # Screenshots
                if len(game.screenshots) > 0:
                    self.set_game_data(Columns.List.SCREENSHOT,
                                       self.icons.get("screenshot"),
                                       game.id)

                    self.menubar_game.set_sensitive(True, widget="screenshots")
                    self.toolbar_games.set_sensitive(
                        True, widget="screenshots")

                else:
                    self.set_game_data(
                        Columns.List.SCREENSHOT,
                        self.icons.get_translucent("screenshot"),
                        game.id)

                    self.menubar_game.set_sensitive(True, widget="screenshots")
                    self.toolbar_games.set_sensitive(
                        False, widget="screenshots")

                # Savestates
                if len(game.savestates) > 0:
                    self.set_game_data(Columns.List.SAVESTATE,
                                       self.icons.get("savestate"),
                                       game.id)

                else:
                    self.set_game_data(Columns.List.SAVESTATE,
                                       self.icons.get_translucent("savestate"),
                                       game.id)

                # Objects
                row, treepath, gridpath = self.game_path[game.id]

                treepath = self.model_games_list.get_path(treepath)

                self.model_games_list[treepath][Columns.List.OBJECT] = game
                self.model_games_grid[gridpath][Columns.Grid.OBJECT] = game

                self.set_informations()

            self.set_sensitive(True)

            dialog.destroy()

    def __on_game_log(self, *args):
        """ Show game log

        This function show the gem log content in a non-editable dialog
        """

        path = self.check_log()

        if path is not None and path.exists():
            game = self.__on_retrieve_selected_game()

            try:
                size = self.config.get(
                    "windows", "log", fallback="800x600").split('x')

            except ValueError:
                size = (800, 600)

            self.set_sensitive(False)

            dialog = GeodeDialog.Editor(
                self,
                game.name,
                path,
                size,
                Icons.Symbolic.TERMINAL,
                editable=False)

            dialog.run()

            self.config.modify("windows", "log", "%dx%d" % dialog.get_size())
            self.config.update()

            self.set_sensitive(True)

            dialog.destroy()

    def __on_game_backup_memory(self, *args):
        """ Manage game backup memory

        This function can only be used with a GBA game and Mednafen emulator.
        """

        if self.menu_game.get_sensitive(widget="memory_type"):

            game = self.__on_retrieve_selected_game()
            console = self.__on_retrieve_selected_console()

            if game is not None and console is not None:
                content = dict()

                filepath = self.get_mednafen_memory_type(game)

                # Check if a type file already exist in mednafen sav folder
                if filepath.exists():

                    with filepath.open('r') as pipe:

                        for line in pipe.readlines():
                            data = line.split()

                            if len(data) == 2:
                                content[data[0]] = int(data[1])

                # ----------------------------------------
                #   Dialog
                # ----------------------------------------

                self.set_sensitive(False)

                dialog = GeodeDialog.Mednafen(self, game.name, content)

                if dialog.run() == Gtk.ResponseType.APPLY:
                    data = list()
                    for key, value in dialog.model:
                        data.append(' '.join([key, str(value)]))

                    # Write data into type file
                    if len(data) > 0:

                        with filepath.open('w') as pipe:
                            pipe.write('\n'.join(data))

                    # Remove type file when no data are available
                    elif filepath.exists():
                        filepath.unlink()

                self.set_sensitive(True)

                dialog.destroy()

    def update_game_flag(self, widget, flag_name):
        """ Update a specific flag for the selected game

        Parameters
        ----------
        widget : Gtk.Widget
            object which received the signal
        flag_name : str
            flag label name used to retrieve current status from game object
        """

        self.__block_signals()

        game, status = self.__on_retrieve_selected_game(), False

        if game is not None:
            row, treepath, gridpath = self.game_path[game.id]

            # Reverse current game status
            status = not getattr(game, flag_name, False)

            # Update treeview icon
            flag_column = getattr(Columns.List, flag_name.upper(), None)
            if flag_column is not None:

                icon = self.icons.get_translucent(flag_name)
                if status:
                    icon = self.icons.get(flag_name)

                self.model_games_list.set_value(treepath, flag_column, icon)

            # Update game object in both games views storages
            self.model_games_list.set_value(
                treepath, Columns.List.OBJECT, game)
            self.model_games_grid.set_value(
                gridpath, Columns.Grid.OBJECT, game)

            self.logger.debug(
                f"Set {flag_name} status for '{game.id}' to {status}")

            # Update game from database
            setattr(game, flag_name, status)
            self.api.update_game(game)

            self.check_selection()

        self.menubar_game.set_active(status, widget=flag_name)
        self.menu_game.set_active(status, widget=flag_name)

        self.filters_update(None)

        self.__unblock_signals()

    def __on_game_score(self, widget, score=None):
        """ Manage selected game score

        Parameters
        ----------
        widget : Gtk.MenuItem
            object which received the signal
        """

        modification = False

        game = self.__on_retrieve_selected_game()

        if game is not None:

            if widget in [self.menubar_edit.get_widget("increase"),
                          self.menu_game.get_widget("increase")]:

                if game.score < 5:
                    game.score += 1

                    modification = True

            elif widget in [self.menubar_edit.get_widget("decrease"),
                            self.menu_game.get_widget("decrease")]:

                if game.score > 0:
                    game.score -= 1

                    modification = True

            elif score is not None:
                game.score = score

                modification = True

        if modification:
            row, treepath, gridpath = self.game_path[game.id]

            self.model_games_list.set_value(
                treepath, Columns.List.SCORE, game.score)
            self.model_games_list.set_value(
                treepath, Columns.List.OBJECT, game)

            self.model_games_grid.set_value(
                gridpath, Columns.Grid.OBJECT, game)

            self.api.update_game(game)

            self.set_informations()

    def __on_game_edit_file(self, *args):
        """ Edit game file

        This function check if the game file mime type is text/
        """

        game = self.__on_retrieve_selected_game()

        if game is not None:

            if magic_from_file(game.path, mime=True).startswith("text/"):

                try:
                    size = self.config.get(
                        "windows", "game", fallback="800x600").split('x')

                except ValueError:
                    size = (800, 600)

                self.set_sensitive(False)

                dialog = GeodeDialog.Editor(
                    self,
                    game.name,
                    game.path,
                    size,
                    Icons.Symbolic.EDIT)

                if dialog.run() == Gtk.ResponseType.APPLY:
                    game.path.write_text(dialog.buffer_editor.get_text(
                        dialog.buffer_editor.get_start_iter(),
                        dialog.buffer_editor.get_end_iter(), True))

                    game.update_installation_date()

                    self.set_game_data(Columns.List.INSTALLED,
                                       string_from_date(game.installed),
                                       game.id)

                self.config.modify(
                    "windows", "game", "%dx%d" % dialog.get_size())
                self.config.update()

                self.set_sensitive(True)

                dialog.destroy()

    def __on_game_copy(self, *args):
        """ Copy path folder which contains selected game to clipboard
        """

        game = self.__on_retrieve_selected_game()

        if game is not None:
            self.clipboard.set_text(str(game.path), -1)

    def __on_game_cover(self, *args):
        """ Set a new cover for selected game
        """

        game = self.__on_retrieve_selected_game()

        if game is not None:
            self.set_sensitive(False)

            dialog = GeodeDialog.Cover(self, game)

            response = dialog.run()

            if response == Gtk.ResponseType.APPLY:
                path = dialog.file_image_selector.get_filename()

                # Avoid to update the database with same contents
                if not path == str(game.cover):

                    # Reset cover for current game
                    game.cover = None

                    if path is not None:
                        game.cover = Path(path).expanduser()

                    # Update game from database
                    self.api.update_game(game)

                    treeiter = self.game_path[game.id]

                    large_cache_path = self.get_icon_from_cache(
                        "games", "96x96", game.id + ".png")

                    thumbnail_cache_path = self.get_icon_from_cache(
                        "games", "22x22", game.id + ".png")

                    # A new icon is available so we regenerate icon cache
                    if game.cover is not None and game.cover.exists():

                        # ----------------------------------------
                        #   Large grid icon
                        # ----------------------------------------

                        try:
                            large = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                                str(game.cover), 96, 96, True)

                            large.savev(str(large_cache_path),
                                        "png",
                                        list(),
                                        list())

                        except GLib.Error:
                            self.logger.exception(
                                "An error occur during cover generation")

                        # ----------------------------------------
                        #   Thumbnail icon
                        # ----------------------------------------

                        try:
                            thumbnail = \
                                GdkPixbuf.Pixbuf.new_from_file_at_scale(
                                    str(game.cover), 22, 22, True)

                            thumbnail.savev(str(thumbnail_cache_path),
                                            "png",
                                            list(),
                                            list())

                        except GLib.Error:
                            self.logger.exception(
                                "An error occur during cover generation")

                    # Remove previous cache icons
                    else:
                        large = self.__console_icon

                        thumbnail = self.__console_thumbnail

                        if large_cache_path.exists():
                            remove(large_cache_path)

                        if thumbnail_cache_path.exists():
                            remove(thumbnail_cache_path)

                    self.model_games_grid.set_value(
                        treeiter[2], Columns.Grid.THUMBNAIL, large)

                    self.model_games_list.set_value(
                        treeiter[1], Columns.List.THUMBNAIL, thumbnail)

                    # Reset tooltip pixbuf
                    self.__current_tooltip_pixbuf = None

            self.set_sensitive(True)

            dialog.destroy()

    def __on_game_generate_desktop(self, *args):
        """ Generate application desktop file

        This function generate a .desktop file to allow user to launch the game
        from his favorite applications launcher
        """

        model, treeiter = self.get_selected_treeiter_from_container(
            self.treeview_games)

        game = self.__on_retrieve_selected_game()
        console = self.__on_retrieve_selected_console()

        if treeiter is not None and game is not None and console is not None:

            if game.emulator is not None \
               and game.emulator.id in self.api.emulators:
                name = "%s.desktop" % game.path.stem

                # ----------------------------------------
                #   Fill template
                # ----------------------------------------

                icon = console.icon
                if not icon.exists():
                    icon = self.api.get_local("icons", '%s.png' % str(icon))

                values = {
                    "%name%": game.name,
                    "%icon%": icon,
                    "%path%": str(game.path.parent),
                    "%command%": ' '.join(game.command())
                }

                # Put game path between quotes
                values["%command%"] = values["%command%"].replace(
                    str(game.path), "\"%s\"" % str(game.path))

                self.set_sensitive(False)

                try:
                    # Read default template
                    template = get_data(
                        "data", "config", "template.desktop").read_text()

                    # Replace custom variables
                    for key, value in values.items():
                        template = template.replace(key, str(value))

                    # Check ~/.local/share/applications
                    if not Folders.APPLICATIONS.exists():
                        Folders.APPLICATIONS.mkdir(mode=0o755, parents=True)

                    # Write the new desktop file
                    Folders.APPLICATIONS.joinpath(name).write_text(template)

                    self.set_message(
                        _("Generate menu entry"),
                        _("%s was generated successfully") % name,
                        Icons.INFORMATION)

                except OSError:
                    self.set_message(
                        _("Generate menu entry for %s") % game.name,
                        _("An error occur during generation, consult log for "
                          "further details."), Icons.ERROR)

                self.set_sensitive(True)

    def __on_game_menu_show(self, widget, event):
        """ Open context menu

        This function open context-menu when user right-click or use context
        key on games views

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        event : Gdk.EventButton or Gdk.EventKey
            Event which triggered this signal

        Returns
        -------
        bool
            Context menu popup status
        """

        treeiter = None

        # Gdk.EventButton - Mouse
        if event.type == Gdk.EventType.BUTTON_PRESS:
            if event.button == Gdk.BUTTON_SECONDARY:
                selection = False

                x, y = int(event.x), int(event.y)

                # List view
                if widget == self.treeview_games:

                    # Avoid to click on treeview header
                    if event.window == widget.get_bin_window():
                        treeiter = widget.get_path_at_pos(x, y)

                        if treeiter is not None:
                            widget.set_cursor(treeiter[0], treeiter[1], False)

                            selection = True

                # Grid icons view
                if widget == self.iconview_games:
                    treeiter = widget.get_path_at_pos(x, y)

                    if treeiter is not None:
                        widget.select_path(treeiter)

                        selection = True

                if selection:
                    widget.grab_focus()

                    self.menu_game.popup_at_pointer(event)

                    return True

        # Gdk.EventKey - Keyboard
        elif event.type == Gdk.EventType.KEY_RELEASE:
            if event.keyval == Gdk.KEY_Menu:
                model, treeiter = self.get_selected_treeiter_from_container(
                    widget)

                if treeiter is not None:
                    self.menu_game.popup_at_pointer(event)

                    return True

        return False

    def __on_activate_fullscreen(self, widget, *args):
        """ Update fullscreen button

        This function alternate fullscreen status between active and inactive
        state when user use fullscreen button in toolbar

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        self.__block_signals()

        # Switch fullscreen status
        self.__fullscreen_status = not self.__fullscreen_status

        fullscreen_button = self.toolbar_games.get_widget("fullscreen")
        fullscreen_image = self.toolbar_games.get_widget("fullscreen_image")

        if not self.__fullscreen_status:
            self.logger.debug("Switch game launch to windowed mode")

            fullscreen_image.set_from_icon_name(Icons.Symbolic.RESTORE,
                                                Gtk.IconSize.SMALL_TOOLBAR)
            fullscreen_button.set_style()

        else:
            self.logger.debug("Switch game launch to fullscreen mode")

            fullscreen_image.set_from_icon_name(Icons.Symbolic.FULLSCREEN,
                                                Gtk.IconSize.SMALL_TOOLBAR)
            fullscreen_button.set_style("suggested-action")

        fullscreen_button.set_active(self.__fullscreen_status)
        self.menubar_game.set_active(
            self.__fullscreen_status, widget="fullscreen")

        self.__unblock_signals()

    def __on_activate_dark_theme(self, widget, status=False, *args):
        """ Update dark theme status

        This function alternate between dark and light theme when user use
        dark theme entry in main menu

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        status : bool, optional
            New switch status (Default: False)
        """

        self.__block_signals()

        dark_theme_status = not self.config.getboolean(
            "gem", "dark_theme", fallback=False)

        on_change_theme(dark_theme_status)

        self.config.modify("gem", "dark_theme", dark_theme_status)
        self.config.update()

        self.menubar_view.set_active(
            dark_theme_status, widget="dark_theme")

        self.__unblock_signals()

    def __on_activate_sidebar(self, widget, status=False, *args):
        """ Update sidebar status

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        status : bool, optional
            New switch status (Default: False)
        """

        self.__block_signals()

        sidebar_status = not self.config.getboolean(
            "gem", "show_sidebar", fallback=True)

        if sidebar_status and not self.scroll_games_placeholder.get_visible():
            self.scroll_sidebar.show()

        else:
            self.scroll_sidebar.hide()

        self.config.modify("gem", "show_sidebar", sidebar_status)
        self.config.update()

        self.menubar_view.set_active(
            sidebar_status, widget="show_sidebar")

        self.__unblock_signals()

    def __on_move_sidebar(self, widget=None, init_interface=False):
        """ Move sidebar based on user configuration value

        Parameters
        ----------
        widget : Gtk.Widget, optional
            Object which receive signal
        init_interface : bool, optional
            Interface first initialization (Default: False)
        """

        self.__block_signals()

        self.sidebar_image = None

        # Retrieve current position and update configuration file
        if widget is not None:
            self.sidebar_orientation = "vertical"
            if widget in (self.headerbar.get_widget("right"),
                          self.menubar_view.get_widget("right")):
                self.sidebar_orientation = "horizontal"

            self.config.modify(
                "gem", "sidebar_orientation", self.sidebar_orientation)
            self.config.update()

        # Right-side sidebar
        if self.sidebar_orientation == "horizontal" and \
           not self.__current_orientation == Gtk.Orientation.HORIZONTAL:

            self.label_sidebar_title.set_justify(Gtk.Justification.CENTER)
            self.label_sidebar_title.set_halign(Gtk.Align.CENTER)
            self.label_sidebar_title.set_xalign(0.5)

            # Change game screenshot and score placement
            self.grid_sidebar.remove(self.grid_sidebar_content)
            self.grid_sidebar.attach(self.grid_sidebar_content, 0, 1, 1, 1)

            self.grid_sidebar_content.set_orientation(Gtk.Orientation.VERTICAL)
            self.grid_sidebar_content.set_margin_bottom(12)

            self.grid_sidebar_informations.set_halign(Gtk.Align.FILL)
            self.grid_sidebar_informations.set_column_homogeneous(True)
            self.grid_sidebar_informations.set_orientation(
                Gtk.Orientation.VERTICAL)

            if not init_interface:
                self.vpaned_games.remove(self.scroll_sidebar)

            self.hpaned_games.pack2(self.scroll_sidebar, False, True)

            self.scroll_sidebar.set_min_content_width(350)
            self.scroll_sidebar.set_min_content_height(-1)

            self.__current_orientation = Gtk.Orientation.HORIZONTAL

        # Bottom-side sidebar
        elif (self.sidebar_orientation == "vertical" and
              not self.__current_orientation == Gtk.Orientation.VERTICAL):

            self.label_sidebar_title.set_justify(Gtk.Justification.LEFT)
            self.label_sidebar_title.set_halign(Gtk.Align.START)
            self.label_sidebar_title.set_xalign(0.0)

            # Change game screenshot and score placement
            self.grid_sidebar.remove(self.grid_sidebar_content)
            self.grid_sidebar.attach(self.grid_sidebar_content, 1, 0, 1, 3)

            self.grid_sidebar_content.set_margin_bottom(0)

            self.grid_sidebar_informations.set_halign(Gtk.Align.START)
            self.grid_sidebar_informations.set_column_homogeneous(False)
            self.grid_sidebar_informations.set_orientation(
                Gtk.Orientation.HORIZONTAL)

            if not init_interface:
                self.hpaned_games.remove(self.scroll_sidebar)

            self.vpaned_games.pack2(self.scroll_sidebar, False, True)

            self.scroll_sidebar.set_min_content_width(-1)
            self.scroll_sidebar.set_min_content_height(260)

            self.__current_orientation = Gtk.Orientation.VERTICAL

        # Update menu radio widgets
        position = "right"
        if self.__current_orientation == Gtk.Orientation.VERTICAL:
            position = "bottom"

        self.headerbar.set_active(True, widget=position)
        self.menubar_view.set_active(True, widget=position)

        self.logger.debug(f"Mode sidebar to {position} side")

        self.__unblock_signals()

        if widget is not None:
            self.set_informations()

    def __on_activate_statusbar(self, widget, status=False, *args):
        """ Update statusbar status

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        status : bool, optional
            New switch status (Default: False)
        """

        self.__block_signals()

        statusbar_status = not self.config.getboolean(
            "gem", "show_statusbar", fallback=True)

        if statusbar_status:
            self.statusbar.show()
        else:
            self.statusbar.hide()

        self.config.modify("gem", "show_statusbar", statusbar_status)
        self.config.update()

        self.menubar_view.set_active(statusbar_status, widget="show_statusbar")

        self.__unblock_signals()

    def __on_copy_path_to_clipboard(self, widget):
        """ Copy path to clipboard

        Parameters
        ----------
        widget : Gtk.Widget
            object which received the signal
        """

        path = None

        if widget in (self.menubar_edit.get_widget("copy_path"),
                      self.menu_game.get_widget("copy_path")):
            game = self.__on_retrieve_selected_game()

            if game is not None and game.path.parent.exists():
                path = game.path

        elif widget == self.menu_consoles.get_widget("copy_path"):

            if self.__current_menu_row is not None:
                path = self.__current_menu_row.console.path

        if path is not None:
            self.clipboard.set_text(str(path), -1)

    def __on_open_directory(self, widget):
        """ Open directory into files manager

        Parameters
        ----------
        widget : Gtk.Widget
            object which received the signal
        """

        path = None

        if widget in (self.menubar_edit.get_widget("open_path"),
                      self.menu_game.get_widget("open_path")):
            game = self.__on_retrieve_selected_game()

            if game is not None and game.path.parent.exists():
                path = game.path.parent

        elif widget == self.menu_consoles.get_widget("open_path"):

            if self.__current_menu_row is not None:
                path = self.__current_menu_row.console.path

        if path is not None and path.exists():
            self.logger.debug("Open '%s' directory in files manager" % path)

            try:
                self.__xdg_open_instance.launch_uris(
                    ["file://%s" % path], None)

            except GLib.Error:
                self.logger.exception("Cannot open files manager")

    def __on_dnd_send_data(self, widget, context, data, info, time):
        """ Set rom file path uri

        This function send rom file path uri when user drag a game from gem and
        drop it to extern application

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        context : Gdk.DragContext
            Drag context
        data : Gtk.SelectionData
            Received data
        info : int
            Info that has been registered with the target in the Gtk.TargetList
        time : int
            Timestamp at which the data was received
        """

        if type(widget) is Gtk.TreeView or type(widget) is Gtk.IconView:
            game = self.__on_retrieve_selected_game()

            if game is not None:
                data.set_uris(["file://%s" % game.path])

        elif type(widget) is Gtk.Viewport:

            if self.sidebar_image is not None:
                data.set_uris(["file://%s" % self.sidebar_image])

    def __on_dnd_received_data(self, widget, context, x, y, data, info, delta):
        """ Manage drag & drop acquisition

        This function receive drag files and install them into the correct
        games folder. If a file extension can be find in multiple consoles,
        a dialog appear to ask user where he want to put it.

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        context : Gdk.DragContext
            Drag context
        x : int
            X coordinate where the drop happened
        y : int
            Y coordinate where the drop happened
        data : Gtk.SelectionData
            Received data
        info : int
            Info that has been registered with the target in the Gtk.TargetList
        delta : int
            Timestamp at which the data was received
        """

        GObject.signal_stop_emission_by_name(widget, "drag_data_received")

        # Current acquisition not respect text/uri-list
        if not info == 1337:
            return

        # Avoid to read data dropped from main interface
        if Gtk.drag_get_source_widget(context) is not None:
            return

        self.logger.debug("Received data from drag & drop")

        # ----------------------------------------
        #   Check received URIs
        # ----------------------------------------

        filepaths = dict()

        for uri in data.get_uris():
            result = urlparse(uri)

            if result.scheme == "file":
                path = Path(url2pathname(result.path)).expanduser()

                if path is not None and path.exists():
                    filepaths[path] = list()

        # ----------------------------------------
        #   Retrieve consoles for every file
        # ----------------------------------------

        consoles = self.api.get_consoles()

        for path in filepaths:
            self.logger.debug("Receive %s" % path.name)

            # Lowercase extension
            extension = str()
            # Only retrieve extensions and not part of the name
            for subextension in path.suffixes:
                if subextension not in path.stem:
                    extension += subextension.lower()

            # Remove the first dot to match console extensions system
            if len(extension) > 0 and extension[0] == '.':
                extension = extension[1:]

            # Check consoles which
            for console in consoles:
                if extension in console.extensions:
                    filepaths[path].append(console)

            # Move favorite console on first position
            filepaths[path].sort(key=lambda console: console.favorite)

        # ----------------------------------------
        #   Drag and drop dialog
        # ----------------------------------------

        if len(filepaths) > 0:
            self.set_sensitive(False)

            data = None
            options = None

            dialog = GeodeDialog.DNDConsole(self, filepaths)

            if dialog.run() == Gtk.ResponseType.APPLY:
                # Retrieve validate files
                data = dialog.get_data()

                # Retrieve user options
                options = dialog.get_options()

            dialog.destroy()

            # Manage validate files
            if data is not None and options is not None:
                GLib.idle_add(
                    self.__on_dnd_install_data(data, options).__next__)

            else:
                self.set_sensitive(True)

    def __on_dnd_install_data(self, data, options):
        """ Install received file in user system

        Parameters
        ----------
        data : dict
            Received files
        option : dict
            User options from DND dialog

        Notes
        -----
        Using yield to show a progressbar whitout freeze
        """

        # Update mouse cursor
        self.get_window().set_cursor(
            Gdk.Cursor.new_from_name(self.window_display, "wait"))

        self.statusbar.set_widget_value("progressbar")
        self.statusbar.progressbar.show()

        yield True

        validate_index = int()
        progress_index = int()

        # Manage files
        for path, console in data.items():
            progress_index += 1

            self.statusbar.set_widget_value(
                "progressbar", index=progress_index, length=len(data))

            yield True

            # Lowercase extension
            extension = str()
            # Only retrieve extensions and not part of the name
            for subextension in path.suffixes:
                if subextension not in path.stem:
                    extension += subextension.lower()

            # Destination path
            new_path = console.path.joinpath(
                ''.join([path.stem, extension])).expanduser()

            # Check consoles games subdirectory
            if not new_path.parent.exists():

                if options["create"]:
                    new_path.parent.mkdir(mode=0o755, parents=True)

                else:
                    self.logger.warning(
                        "%s directory not exists" % new_path.parent)

            # Replace an existing file
            if new_path.exists():
                if new_path.is_file() and options["replace"]:
                    new_path.unlink()

            # Move or copy file to the correct location
            if new_path.parent.exists() \
               and new_path.parent.is_dir() \
               and not new_path.exists():
                validate_index += 1

                copy(path, new_path)

                if not options["copy"]:
                    path.unlink()

                game = console.get_game(generate_identifier(new_path))

                # Add a new game to console storage if not exists
                if game is None:
                    game = console.add_game(new_path)

                # Update installed time
                else:
                    game.installed = datetime.fromtimestamp(
                        getctime(new_path)).date()

                # Update console tooltip
                if console.id in self.consoles_iter:
                    row = self.consoles_iter[console.id]

                    text = _("No game")
                    if console.get_games():
                        text = ngettext(
                            _("1 game"),
                            _("%d games") % len(console.get_games()),
                            len(console.get_games()))

                    row.set_tooltip_text(text)

                # This file is owned by current selected console
                if self.selection["console"] is not None \
                   and console.id == self.selection["console"].id:

                    # Remove an old entry in views
                    if game.id in self.game_path:
                        self.model_games_list.remove(
                            self.game_path[game.id][1])
                        self.model_games_grid.remove(
                            self.game_path[game.id][2])

                        del self.game_path[game.id]

                    # Add a new item to views
                    if self.__on_append_game(console, game):
                        self.set_informations_headerbar()

                        self.scroll_sidebar.set_visible(self.config.getboolean(
                            "gem", "show_sidebar", fallback=True))

                        # Grid view
                        if self.toolbar_games.get_active("grid"):
                            self.scroll_games_grid.set_visible(True)
                            self.iconview_games.show_all()

                        # List view
                        elif self.toolbar_games.get_active("list"):
                            self.scroll_games_list.set_visible(True)
                            self.treeview_games.show_all()

                        self.scroll_games_placeholder.set_visible(False)

        # Reset mouse cursor
        self.get_window().set_cursor(
            Gdk.Cursor.new_from_name(self.window_display, "default"))

        # Show an informative dialog
        text = _("No game has been added")
        if validate_index > 0:
            text = ngettext(
                _("1 game has been added"),
                _("%d games have been added") % validate_index,
                validate_index)

        self.set_message(_("Games installation"),
                         text,
                         Icons.Symbolic.INFORMATION)

        # Update consoles filters
        self.__on_update_consoles()

        self.set_sensitive(True)

        self.progress_statusbar.hide()

        yield False

    def __block_signals(self):
        """ Block check button signals to avoid stack overflow when toggled
        """

        for signal, widget in self.signals_storage.items():
            widget.handler_block(signal)

    def __unblock_signals(self):
        """ Unblock check button signals
        """

        for signal, widget in self.signals_storage.items():
            widget.handler_unblock(signal)

    def check_desktop(self, path):
        """ Check user applications folder for specific desktop file

        Parameters
        ----------
        path : pathlib.Path
            Application path

        Returns
        -------
        bool
            Desktop file status

        Examples
        --------
        >>> check_desktop("unavailable_file")
        False

        Notes
        -----
        In GNU/Linux desktop, the default folder for user applications is:

            ~/.local/share/applications/
        """

        return Folders.APPLICATIONS.joinpath("%s.desktop" % path.stem).exists()

    def check_log(self):
        """ Check if a game has an output file available

        Returns
        -------
        str or None
            Output file path
        """

        game = self.__on_retrieve_selected_game()

        if game is not None:
            log_path = self.api.get_local("logs", game.id + ".log")

            if log_path.exists():
                return log_path

        return None

    def check_mednafen(self):
        """ Check if Mednafen exists on user system

        This function read the first line of mednafen default output and check
        if this one match "Starting Mednafen [0-9+.?]+".

        Returns
        -------
        bool
            Mednafen exists status

        Notes
        -----
        Still possible to troll this function with a script call mednafen which
        send the match string as output. But, this problem only appear if a
        user want to do that, so ...
        """

        if len(get_binary_path("mednafen")) > 0:
            proc = Popen(
                ["mednafen"],
                stdin=PIPE,
                stdout=PIPE,
                stderr=STDOUT,
                universal_newlines=True)

            output, error_output = proc.communicate()

            if output is not None:
                result = match(
                    r'Starting Mednafen [\d+\.?]+', output.split('\n')[0])

                if result is not None:
                    return True

        return False

    def check_version(self):
        """ Check development version when debug mode is activate

        This function allow the developper to know which hash version is
        currently using

        Returns
        -------
        str
            Application version
        """

        version = Metadata.VERSION

        if self.api.debug:

            if len(get_binary_path("git")) > 0:
                path = Path(".git")

                if path.exists():
                    proc = Popen(
                        ["git", "rev-parse", "--short", "HEAD"],
                        stdin=PIPE,
                        stdout=PIPE,
                        stderr=STDOUT,
                        universal_newlines=True)

                    output, error_output = proc.communicate()

                    if output is not None:
                        output = output.split('\n')[0]

                        if match(r'^[\d\w]+$', output) is not None:
                            return "%s-%s" % (version, output)

        return version

    def set_game_data(self, index, data, identifier):
        """ Update game informations in games treeview

        Parameters
        ----------
        index : int
            Column index
        data : object
            Value to set
        identifier : str
            Game identifier
        """

        treeiter = self.game_path.get(identifier, None)

        if treeiter is not None:
            self.model_games_list[treeiter[1]][index] = data

    def get_icon_from_cache(self, *args):
        """ Retrieve icon from cache folder

        Returns
        -------
        str
            Cached icon path
        """

        return self.__cache.joinpath(*args)

    def get_pixbuf_from_cache(self,
                              key, size, identifier, path, use_cache=True):
        """ Retrieve an icon from cache or generate it

        Parameters
        ----------
        key : str
            Cache category folder
        size : int
            Pixbuf size in pixels
        identifier : str
            Icon identifier
        path : pathlib.Path
            Icon path
        use_cache : bool, optional
            Use cache directory and save new generated icons into cache

        Returns
        -------
        Gdk.Pixbuf or None
            New cached icon or None if no icon has been generated
        """

        icon = None
        need_save = False

        cache_path = self.get_icon_from_cache(
            key, "%dx%d" % (size, size), identifier + ".png")

        # Retrieve icon from cache folder
        if use_cache and cache_path.exists() and cache_path.is_file():
            return GdkPixbuf.Pixbuf.new_from_file(str(cache_path))

        # Generate a new cache icon
        elif path is not None:

            # Retrieve icon from specific collection
            if not path.exists():

                if key == "consoles":
                    collection_path = self.api.get_local(
                        "icons", "%s.png" % path)

                    # Generate a new cache icon
                    if collection_path.exists() and collection_path.is_file():

                        # Check the file mime-type to avoid non-image file
                        if magic_from_file(collection_path,
                                           mime=True).startswith("image/"):

                            icon = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                                str(collection_path), size, size, True)

                            need_save = True

                elif key == "emulators":

                    if self.icons.theme.has_icon(str(path)):
                        icon = self.icons.theme.load_icon(
                            str(path), size, Gtk.IconLookupFlags.FORCE_SIZE)

                        need_save = True

            # Generate a new cache icon
            elif path.exists() and path.is_file():

                # Check the file mime-type to avoid non-image file
                if magic_from_file(path, mime=True).startswith("image/"):
                    icon = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                        str(path), size, size, True)

                    need_save = True

            # Save generated icon to cache
            if use_cache and need_save:
                try:
                    self.logger.debug(
                        "Save generated icon to %s" % cache_path)

                    if not cache_path.parent.exists():
                        cache_path.parent.mkdir(mode=0o755, parents=True)

                    icon.savev(str(cache_path), "png", list(), list())

                except GLib.Error:
                    self.logger.exception(
                        "An error occur during cache generation")

            return icon

        return None

    def get_mednafen_status(self):
        """ Retrieve mednafen status

        Returns
        -------
        bool
            Mednafen status
        """

        return self.__mednafen_status

    def get_mednafen_memory_type(self, game):
        """ Retrieve a memory type file for a specific game

        Parameters
        ----------
        game : gem.engine.game.Game
            Game object

        Returns
        -------
        pathlib.Path
            Memory type file path
        """

        # FIXME: Maybe a better way to determine type file
        return Path.home().joinpath(
            ".mednafen", "sav", game.path.stem + ".type")

    def emit(self, *args):
        """ Override emit function

        This override allow to use Interface function from another thread in
        MainThread
        """

        GLib.idle_add(GObject.GObject.emit, self, *args)
