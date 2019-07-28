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

# Datetime
from datetime import date
from datetime import datetime
from datetime import timedelta

# Filesystem
from os import R_OK
from os import W_OK
from os import X_OK
from os import access
from os import remove

from os.path import getctime

from pathlib import Path

from copy import deepcopy

from shutil import rmtree

# GEM
from gem.engine.utils import copy
from gem.engine.utils import get_data
from gem.engine.utils import get_binary_path
from gem.engine.utils import parse_timedelta
from gem.engine.utils import generate_identifier
from gem.engine.api import GEM
from gem.engine.console import Console
from gem.engine.lib.configuration import Configuration

from gem.ui.data import Icons
from gem.ui.data import Columns
from gem.ui.data import Folders
from gem.ui.data import Metadata
from gem.ui.utils import magic_from_file
from gem.ui.utils import on_change_theme
from gem.ui.utils import string_from_date
from gem.ui.utils import string_from_time
from gem.ui.utils import replace_for_markup
from gem.ui.utils import on_activate_listboxrow
from gem.ui.dialog.cache import CleanCacheDialog
from gem.ui.dialog.cover import CoverDialog
from gem.ui.dialog.editor import EditorDialog
from gem.ui.dialog.delete import DeleteDialog
from gem.ui.dialog.rename import RenameDialog
from gem.ui.dialog.viewer import ViewerDialog
from gem.ui.dialog.message import MessageDialog
from gem.ui.dialog.question import QuestionDialog
from gem.ui.dialog.mednafen import MednafenDialog
from gem.ui.dialog.duplicate import DuplicateDialog
from gem.ui.dialog.parameter import ParametersDialog
from gem.ui.dialog.dndconsole import DNDConsoleDialog
from gem.ui.dialog.maintenance import MaintenanceDialog
from gem.ui.preferences.interface import ConsolePreferences
from gem.ui.preferences.interface import EmulatorPreferences
from gem.ui.preferences.interface import PreferencesWindow
from gem.ui.widgets.game import GameThread
from gem.ui.widgets.script import ScriptThread
from gem.ui.widgets.widgets import ListBoxItem
from gem.ui.widgets.widgets import IconsGenerator

# GObject
try:
    from gi import require_version

    require_version("Gtk", "3.0")

    from gi.repository import Gtk
    from gi.repository import GLib
    from gi.repository import GObject
    from gi.repository import Gio
    from gi.repository import Gdk
    from gi.repository import GdkPixbuf
    from gi.repository import Pango

except ImportError as error:
    from sys import exit

    exit("Cannot found python3-gobject module: %s" % str(error))

# Processus
from subprocess import PIPE
from subprocess import Popen
from subprocess import STDOUT

# Random
from random import shuffle

# Regex
from re import match
from re import IGNORECASE

# System
from sys import version_info

from shlex import split as shlex_split

# Thread
from threading import enumerate as thread_enumerate
from threading import main_thread as thread_main_thread

# Translation
from gettext import gettext as _

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

        self.grid_game_view_mode = Gtk.Box()

        self.grid_consoles = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
        self.grid_consoles_toolbar = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 0)
        self.grid_consoles_menu = Gtk.Box.new(Gtk.Orientation.VERTICAL, 6)

        self.grid_game_toolbar = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 8)
        self.grid_game_launch = Gtk.Box()
        self.grid_game_options = Gtk.Box()
        self.grid_game_filters = Gtk.Box()
        self.grid_game_filters_popover = Gtk.Box.new(
            Gtk.Orientation.VERTICAL, 6)

        self.grid_infobar = Gtk.Box()

        self.grid_games = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
        self.grid_games_views = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
        self.grid_games_placeholder = Gtk.Box.new(Gtk.Orientation.VERTICAL, 12)

        self.grid_sidebar = Gtk.Grid()
        self.grid_sidebar_content = Gtk.Box.new(Gtk.Orientation.VERTICAL, 6)
        self.grid_sidebar_score = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 6)
        self.grid_sidebar_informations = Gtk.Grid()

        # Properties
        Gtk.StyleContext.add_class(
            self.grid_game_view_mode.get_style_context(), "linked")
        self.grid_game_view_mode.set_spacing(-1)

        self.grid_consoles_menu.set_border_width(6)
        self.grid_consoles_menu.set_halign(Gtk.Align.FILL)

        self.grid_consoles_toolbar.set_border_width(4)
        Gtk.StyleContext.add_class(
            self.grid_consoles_toolbar.get_style_context(), "linked")

        self.grid_game_toolbar.set_border_width(4)

        Gtk.StyleContext.add_class(
            self.grid_game_launch.get_style_context(), "linked")
        self.grid_game_launch.set_spacing(-1)

        Gtk.StyleContext.add_class(
            self.grid_game_options.get_style_context(), "linked")
        self.grid_game_options.set_spacing(-1)

        Gtk.StyleContext.add_class(
            self.grid_game_filters.get_style_context(), "linked")
        self.grid_game_filters.set_spacing(-1)

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

        self.headerbar = Gtk.HeaderBar()

        self.image_headerbar_menu = Gtk.Image()
        self.button_headerbar_main = Gtk.MenuButton()

        self.image_headerbar_view = Gtk.Image()
        self.button_headerbar_view = Gtk.MenuButton()

        # Properties
        self.headerbar.set_title(self.title)
        self.headerbar.set_subtitle(str())

        self.button_headerbar_main.set_tooltip_text(_("Main menu"))
        self.button_headerbar_main.set_use_popover(False)

        self.button_headerbar_view.set_tooltip_text(_("Display menu"))
        self.button_headerbar_view.set_use_popover(False)

        # ------------------------------------
        #   Menubar
        # ------------------------------------

        self.menubar = Gtk.MenuBar()

        self.item_menubar_main = Gtk.MenuItem()
        self.item_menubar_view = Gtk.MenuItem()
        self.item_menubar_game = Gtk.MenuItem()
        self.item_menubar_edit = Gtk.MenuItem()
        self.item_menubar_tools = Gtk.MenuItem()
        self.item_menubar_help = Gtk.MenuItem()

        # Properties
        self.item_menubar_main.set_label(_("_GEM"))
        self.item_menubar_main.set_use_underline(True)
        self.item_menubar_view.set_label(_("_Display"))
        self.item_menubar_view.set_use_underline(True)
        self.item_menubar_game.set_label(_("_Game"))
        self.item_menubar_game.set_use_underline(True)
        self.item_menubar_edit.set_label(_("_Edit"))
        self.item_menubar_edit.set_use_underline(True)
        self.item_menubar_help.set_label(_("_Help"))
        self.item_menubar_help.set_use_underline(True)

        # ------------------------------------
        #   Menubar - Main items
        # ------------------------------------

        self.menu_menubar_main = Gtk.Menu()

        self.item_menubar_preferences = Gtk.MenuItem()
        self.item_menubar_log = Gtk.MenuItem()
        self.item_menubar_clean_cache = Gtk.MenuItem()

        self.item_menubar_quit = Gtk.MenuItem()

        # Properties
        self.item_menubar_preferences.set_label(
            "%s…" % _("_Preferences"))
        self.item_menubar_preferences.set_use_underline(True)

        self.item_menubar_log.set_label(
            "%s…" % _("Application _log"))
        self.item_menubar_log.set_use_underline(True)

        self.item_menubar_clean_cache.set_label(
            "%s…" % _("Clean icons _cache"))
        self.item_menubar_clean_cache.set_use_underline(True)

        self.item_menubar_quit.set_label(
            _("_Quit"))
        self.item_menubar_quit.set_use_underline(True)

        # ------------------------------------
        #   Menubar - View items
        # ------------------------------------

        self.menu_menubar_view = Gtk.Menu()

        self.menu_menubar_games_display = Gtk.Menu()
        self.item_menubar_games_display = Gtk.MenuItem()

        self.menu_menubar_sidebar = Gtk.Menu()
        self.item_menubar_sidebar = Gtk.MenuItem()

        self.menu_menubar_statusbar = Gtk.Menu()
        self.item_menubar_statusbar = Gtk.MenuItem()

        self.item_menubar_dark_theme = Gtk.CheckMenuItem()

        self.item_menubar_list = Gtk.RadioMenuItem()
        self.item_menubar_grid = Gtk.RadioMenuItem()

        # Properties
        self.item_menubar_games_display.set_label(
            _("_Games lists"))
        self.item_menubar_games_display.set_use_underline(True)

        self.item_menubar_sidebar.set_label(
            _("_Sidebar"))
        self.item_menubar_sidebar.set_use_underline(True)

        self.item_menubar_statusbar.set_label(
            _("_Statusbar"))
        self.item_menubar_statusbar.set_use_underline(True)

        self.item_menubar_dark_theme.set_label(
            _("Use _dark theme"))
        self.item_menubar_dark_theme.set_use_underline(True)

        # ------------------------------------
        #   Menubar - Game view items
        # ------------------------------------

        self.menu_menubar_columns = Gtk.Menu()
        self.item_menubar_columns = Gtk.MenuItem()

        self.item_menubar_columns_favorite = Gtk.CheckMenuItem()
        self.item_menubar_columns_multiplayer = Gtk.CheckMenuItem()
        self.item_menubar_columns_finish = Gtk.CheckMenuItem()
        self.item_menubar_columns_play = Gtk.CheckMenuItem()
        self.item_menubar_columns_play_time = Gtk.CheckMenuItem()
        self.item_menubar_columns_last_play = Gtk.CheckMenuItem()
        self.item_menubar_columns_score = Gtk.CheckMenuItem()
        self.item_menubar_columns_installed = Gtk.CheckMenuItem()
        self.item_menubar_columns_flags = Gtk.CheckMenuItem()

        # Properties
        self.item_menubar_columns.set_label(
            _("_Columns visibility"))
        self.item_menubar_columns.set_use_underline(True)

        self.item_menubar_columns_favorite.set_label(
            _("Favorite"))
        self.item_menubar_columns_multiplayer.set_label(
            _("Multiplayer"))
        self.item_menubar_columns_finish.set_label(
            _("Finish"))
        self.item_menubar_columns_play.set_label(
            _("Launch number"))
        self.item_menubar_columns_play_time.set_label(
            _("Play time"))
        self.item_menubar_columns_last_play.set_label(
            _("Last launch date"))
        self.item_menubar_columns_score.set_label(
            _("Score"))
        self.item_menubar_columns_installed.set_label(
            _("Installed date"))
        self.item_menubar_columns_flags.set_label(
            _("Emulator flags"))

        self.item_menubar_list.set_label(
            _("List view"))

        self.item_menubar_grid.set_label(
            _("Grid icons"))
        self.item_menubar_grid.join_group(self.item_menubar_list)

        # ------------------------------------
        #   Menubar - Sidebar items
        # ------------------------------------

        self.item_menubar_sidebar_status = Gtk.CheckMenuItem()

        self.item_menubar_sidebar_right = Gtk.RadioMenuItem()
        self.item_menubar_sidebar_bottom = Gtk.RadioMenuItem()

        # Properties
        self.item_menubar_sidebar_status.set_label(
            _("Show _sidebar"))
        self.item_menubar_sidebar_status.set_use_underline(True)

        self.item_menubar_sidebar_right.set_label(
            _("Right"))

        self.item_menubar_sidebar_bottom.set_label(
            _("Bottom"))
        self.item_menubar_sidebar_bottom.join_group(
            self.item_menubar_sidebar_right)

        # ------------------------------------
        #   Menubar - Statusbar items
        # ------------------------------------

        self.item_menubar_statusbar_status = Gtk.CheckMenuItem()

        # Properties
        self.item_menubar_statusbar_status.set_label(
            _("Show _statusbar"))
        self.item_menubar_statusbar_status.set_use_underline(True)

        # ------------------------------------
        #   Menubar - Game items
        # ------------------------------------

        self.menu_menubar_game = Gtk.Menu()

        self.item_menubar_game_launch = Gtk.MenuItem()
        self.item_menubar_game_screenshots = Gtk.MenuItem()
        self.item_menubar_game_output = Gtk.MenuItem()
        self.item_menubar_game_notes = Gtk.MenuItem()
        self.item_menubar_game_properties = Gtk.MenuItem()

        self.item_menubar_game_favorite = Gtk.CheckMenuItem()
        self.item_menubar_game_multiplayer = Gtk.CheckMenuItem()
        self.item_menubar_game_finish = Gtk.CheckMenuItem()
        self.item_menubar_game_fullscreen = Gtk.CheckMenuItem()

        # Properties
        self.item_menubar_game_launch.set_label(
            _("_Launch"))
        self.item_menubar_game_launch.set_use_underline(True)

        self.item_menubar_game_favorite.set_label(
            _("_Favorite"))
        self.item_menubar_game_favorite.set_use_underline(True)

        self.item_menubar_game_multiplayer.set_label(
            _("_Multiplayer"))
        self.item_menubar_game_multiplayer.set_use_underline(True)

        self.item_menubar_game_finish.set_label(
            _("_Finish"))
        self.item_menubar_game_finish.set_use_underline(True)

        self.item_menubar_game_screenshots.set_label(
            "%s…" % _("_Screenshots"))
        self.item_menubar_game_screenshots.set_use_underline(True)

        self.item_menubar_game_output.set_label(
            "%s…" % _("Output _log"))
        self.item_menubar_game_output.set_use_underline(True)

        self.item_menubar_game_notes.set_label(
            "%s…" % _("_Notes"))
        self.item_menubar_game_notes.set_use_underline(True)

        self.item_menubar_game_properties.set_label(
            "%s…" % _("_Properties"))
        self.item_menubar_game_properties.set_use_underline(True)

        self.item_menubar_game_fullscreen.set_label(
            _("Fullscreen mode"))

        # ------------------------------------
        #   Menubar - Edit items
        # ------------------------------------

        self.menu_menubar_edit = Gtk.Menu()

        self.item_menubar_rename = Gtk.MenuItem()
        self.item_menubar_duplicate = Gtk.MenuItem()
        self.item_menubar_edit_file = Gtk.MenuItem()
        self.item_menubar_copy = Gtk.MenuItem()
        self.item_menubar_open = Gtk.MenuItem()
        self.item_menubar_cover = Gtk.MenuItem()
        self.item_menubar_desktop = Gtk.MenuItem()
        self.item_menubar_maintenance = Gtk.MenuItem()
        self.item_menubar_database = Gtk.MenuItem()
        self.item_menubar_delete = Gtk.MenuItem()
        self.item_menubar_mednafen = Gtk.MenuItem()

        # Properties
        self.item_menubar_rename.set_label(
            "%s…" % _("_Rename"))
        self.item_menubar_rename.set_use_underline(True)

        self.item_menubar_duplicate.set_label(
            "%s…" % _("_Duplicate"))
        self.item_menubar_duplicate.set_use_underline(True)

        self.item_menubar_edit_file.set_label(
            _("_Edit game file"))
        self.item_menubar_edit_file.set_use_underline(True)

        self.item_menubar_copy.set_label(
            _("_Copy path to clipboard"))
        self.item_menubar_copy.set_use_underline(True)

        self.item_menubar_open.set_label(
            _("_Open path"))
        self.item_menubar_open.set_use_underline(True)

        self.item_menubar_cover.set_label(
            "%s…" % _("Set game _thumbnail"))
        self.item_menubar_cover.set_use_underline(True)

        self.item_menubar_desktop.set_label(
            _("_Generate a menu entry"))
        self.item_menubar_desktop.set_use_underline(True)

        self.item_menubar_maintenance.set_label(
            "%s…" % _("_Maintenance"))
        self.item_menubar_maintenance.set_use_underline(True)

        self.item_menubar_database.set_label(
            "%s…" % _("_Reset data"))
        self.item_menubar_database.set_use_underline(True)

        self.item_menubar_delete.set_label(
            "%s…" % _("_Remove from disk"))
        self.item_menubar_delete.set_use_underline(True)

        self.item_menubar_mednafen.set_label(
            "%s…" % _("Specify a _memory type"))
        self.item_menubar_mednafen.set_use_underline(True)

        # ------------------------------------
        #   Menubar - Edit - Score items
        # ------------------------------------

        self.menu_menubar_score = Gtk.Menu()
        self.item_menubar_score = Gtk.MenuItem()

        self.item_menubar_score_up = Gtk.MenuItem()
        self.item_menubar_score_down = Gtk.MenuItem()
        self.item_menubar_score_0 = Gtk.MenuItem()
        self.item_menubar_score_1 = Gtk.MenuItem()
        self.item_menubar_score_2 = Gtk.MenuItem()
        self.item_menubar_score_3 = Gtk.MenuItem()
        self.item_menubar_score_4 = Gtk.MenuItem()
        self.item_menubar_score_5 = Gtk.MenuItem()

        # Properties
        self.item_menubar_score.set_label(
            _("Score"))
        self.item_menubar_score.set_use_underline(True)

        self.item_menubar_score_up.set_label(
            _("Increase score"))
        self.item_menubar_score_up.set_use_underline(True)

        self.item_menubar_score_down.set_label(
            _("Decrease score"))
        self.item_menubar_score_down.set_use_underline(True)

        self.item_menubar_score_0.set_label(
            _("Set score as 0"))
        self.item_menubar_score_0.set_use_underline(True)

        self.item_menubar_score_1.set_label(
            _("Set score as 1"))
        self.item_menubar_score_1.set_use_underline(True)

        self.item_menubar_score_2.set_label(
            _("Set score as 2"))
        self.item_menubar_score_2.set_use_underline(True)

        self.item_menubar_score_3.set_label(
            _("Set score as 3"))
        self.item_menubar_score_3.set_use_underline(True)

        self.item_menubar_score_4.set_label(
            _("Set score as 4"))
        self.item_menubar_score_4.set_use_underline(True)

        self.item_menubar_score_5.set_label(
            _("Set score as 5"))
        self.item_menubar_score_5.set_use_underline(True)

        # ------------------------------------
        #   Menubar - Help items
        # ------------------------------------

        self.menu_menubar_help = Gtk.Menu()

        self.item_menubar_website = Gtk.MenuItem()
        self.item_menubar_bug_tracker = Gtk.MenuItem()
        self.item_menubar_about = Gtk.MenuItem()

        # Properties
        self.item_menubar_website.set_label(
            _("_Website"))
        self.item_menubar_website.set_tooltip_text(Metadata.WEBSITE)
        self.item_menubar_website.set_use_underline(True)

        self.item_menubar_bug_tracker.set_label(
            _("_Report problem"))
        self.item_menubar_bug_tracker.set_tooltip_text(Metadata.BUG_TRACKER)
        self.item_menubar_bug_tracker.set_use_underline(True)

        self.item_menubar_about.set_label(
            _("_About"))
        self.item_menubar_about.set_use_underline(True)

        # ------------------------------------
        #   Toolbar - Consoles
        # ------------------------------------

        self.entry_toolbar_consoles_filters = Gtk.SearchEntry()

        self.image_toolbar_consoles_add = Gtk.Image()
        self.button_toolbar_consoles_add = Gtk.MenuButton()

        # Properties
        self.entry_toolbar_consoles_filters.set_hexpand(True)
        self.entry_toolbar_consoles_filters.set_placeholder_text(
            "%s…" % _("Filter"))

        # ------------------------------------
        #   Menu - Consoles toolbar
        # ------------------------------------

        self.menu_toolbar_consoles = Gtk.Menu()

        self.item_toolbar_add_console = Gtk.MenuItem()
        self.item_toolbar_add_emulator = Gtk.MenuItem()

        self.item_toolbar_hide_empty_console = Gtk.CheckMenuItem()

        # Properties
        self.item_toolbar_add_console.set_label(
            _("Add _console"))
        self.item_toolbar_add_console.set_use_underline(True)

        self.item_toolbar_add_emulator.set_label(
            _("Add _emulator"))
        self.item_toolbar_add_emulator.set_use_underline(True)

        self.item_toolbar_hide_empty_console.set_label(
            _("_Hide empty consoles"))
        self.item_toolbar_hide_empty_console.set_use_underline(True)

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
        #   Menu - Consoles
        # ------------------------------------

        self.menu_consoles = Gtk.Menu()

        self.item_consoles_console = Gtk.MenuItem()
        self.item_consoles_remove = Gtk.MenuItem()

        self.item_consoles_emulator = Gtk.MenuItem()
        self.item_consoles_config = Gtk.MenuItem()

        self.item_consoles_copy = Gtk.MenuItem()
        self.item_consoles_open = Gtk.MenuItem()

        self.item_consoles_reload = Gtk.MenuItem()

        self.item_consoles_favorite = Gtk.CheckMenuItem()
        self.item_consoles_recursive = Gtk.CheckMenuItem()

        # Properties
        self.item_consoles_console.set_label(
            _("_Edit console"))
        self.item_consoles_console.set_use_underline(True)

        self.item_consoles_remove.set_label(
            _("_Remove console"))
        self.item_consoles_remove.set_use_underline(True)

        self.item_consoles_emulator.set_label(
            _("_Edit emulator"))
        self.item_consoles_emulator.set_use_underline(True)

        self.item_consoles_config.set_label(
            _("_Edit configuration file"))
        self.item_consoles_config.set_use_underline(True)

        self.item_consoles_copy.set_label(
            _("_Copy games directory path to clipboard"))
        self.item_consoles_copy.set_use_underline(True)

        self.item_consoles_open.set_label(
            _("_Open games directory"))
        self.item_consoles_open.set_use_underline(True)

        self.item_consoles_reload.set_label(
            _("_Reload games list"))
        self.item_consoles_reload.set_use_underline(True)

        self.item_consoles_favorite.set_label(
            _("_Favorite"))
        self.item_consoles_favorite.set_use_underline(True)

        self.item_consoles_recursive.set_label(
            _("_Recursive"))
        self.item_consoles_recursive.set_use_underline(True)
        self.item_consoles_recursive.set_tooltip_text(
            _("You need to reload games list to apply changes"))

        # ------------------------------------
        #   Toolbar - Game
        # ------------------------------------

        self.button_toolbar_launch = Gtk.Button()
        self.button_toolbar_fullscreen = Gtk.ToggleButton()
        self.button_toolbar_parameters = Gtk.Button()
        self.button_toolbar_screenshots = Gtk.Button()
        self.button_toolbar_output = Gtk.Button()
        self.button_toolbar_notes = Gtk.Button()

        self.button_toolbar_grid = Gtk.ToggleButton()
        self.button_toolbar_list = Gtk.ToggleButton()

        self.separator_toolbar = Gtk.SeparatorToolItem()

        self.image_toolbar_fullscreen = Gtk.Image()
        self.image_toolbar_parameters = Gtk.Image()
        self.image_toolbar_screenshots = Gtk.Image()
        self.image_toolbar_output = Gtk.Image()
        self.image_toolbar_notes = Gtk.Image()
        self.image_toolbar_grid = Gtk.Image()
        self.image_toolbar_list = Gtk.Image()

        # Properties
        self.button_toolbar_launch.set_label(_("Play"))
        self.button_toolbar_launch.set_tooltip_text(
            _("Launch selected game"))
        self.button_toolbar_launch.get_style_context().add_class(
            "suggested-action")

        self.button_toolbar_fullscreen.set_tooltip_text(
            _("Alternate game fullscreen mode"))

        self.button_toolbar_parameters.set_tooltip_text(
            _("Set custom parameters"))

        self.button_toolbar_screenshots.set_tooltip_text(
            _("Show selected game screenshots"))
        self.button_toolbar_output.set_tooltip_text(
            _("Show selected game log"))
        self.button_toolbar_notes.set_tooltip_text(
            _("Show selected game notes"))

        self.separator_toolbar.set_expand(True)
        self.separator_toolbar.set_draw(False)

        self.button_toolbar_grid.set_tooltip_text(_("Grid icons"))
        self.button_toolbar_list.set_tooltip_text(_("List view"))

        # ------------------------------------
        #   Toolbar - Game tags
        # ------------------------------------

        self.image_sidebar_tags = Gtk.Image()
        self.button_sidebar_tags = Gtk.MenuButton()

        self.menu_sidebar_tags = Gtk.Menu()

        # Properties
        self.button_sidebar_tags.set_halign(Gtk.Align.END)
        self.button_sidebar_tags.set_valign(Gtk.Align.CENTER)
        self.button_sidebar_tags.set_tooltip_text(
            _("Show selected game tags"))
        self.button_sidebar_tags.set_popup(self.menu_sidebar_tags)

        # ------------------------------------
        #   Toolbar - Game filter
        # ------------------------------------

        self.entry_toolbar_filters = Gtk.SearchEntry()

        self.button_toolbar_filters = Gtk.MenuButton()

        self.popover_toolbar_filters = Gtk.Popover()

        # Properties
        self.entry_toolbar_filters.set_placeholder_text("%s…" % _("Filter"))

        self.button_toolbar_filters.set_tooltip_text(
            _("Advanced filters"))
        self.button_toolbar_filters.set_use_popover(True)

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
            _("Unfinish"))
        self.check_filter_unfinish.set_active(True)

        self.item_filter_reset.set_label(_("Reset filters"))

        # ------------------------------------
        #   Infobar
        # ------------------------------------

        self.infobar = Gtk.InfoBar()

        self.label_infobar = Gtk.Label()

        # Properties
        self.infobar.set_show_close_button(False)

        self.label_infobar.set_use_markup(True)

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
            _("Start to play by drag & drop some ROM files into interface"))
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
        #   Menu - Game
        # ------------------------------------

        self.menu_game = Gtk.Menu()

        self.item_game_launch = Gtk.MenuItem()
        self.item_game_properties = Gtk.MenuItem()

        self.item_game_favorite = Gtk.CheckMenuItem()
        self.item_game_multiplayer = Gtk.CheckMenuItem()
        self.item_game_finish = Gtk.CheckMenuItem()

        # Properties
        self.item_game_launch.set_label(
            _("_Launch"))
        self.item_game_launch.set_use_underline(True)

        self.item_game_favorite.set_label(
            _("_Favorite"))
        self.item_game_favorite.set_use_underline(True)

        self.item_game_multiplayer.set_label(
            _("_Multiplayer"))
        self.item_game_multiplayer.set_use_underline(True)

        self.item_game_finish.set_label(
            _("_Finish"))
        self.item_game_finish.set_use_underline(True)

        self.item_game_properties.set_label(
            "%s…" % _("_Properties"))
        self.item_game_properties.set_use_underline(True)

        # ------------------------------------
        #   Menu - Game edit
        # ------------------------------------

        self.menu_game_edit = Gtk.Menu()
        self.item_game_edit = Gtk.MenuItem()

        self.item_game_rename = Gtk.MenuItem()
        self.item_game_duplicate = Gtk.MenuItem()
        self.item_game_edit_file = Gtk.MenuItem()
        self.item_game_copy = Gtk.MenuItem()
        self.item_game_open = Gtk.MenuItem()
        self.item_game_cover = Gtk.MenuItem()
        self.item_game_maintenance = Gtk.MenuItem()
        self.item_game_remove = Gtk.MenuItem()
        self.item_game_database = Gtk.MenuItem()

        # Properties
        self.item_game_edit.set_label(
            _("_Edit"))
        self.item_game_edit.set_use_underline(True)

        self.item_game_rename.set_label(
            "%s…" % _("_Rename"))
        self.item_game_rename.set_use_underline(True)

        self.item_game_duplicate.set_label(
            "%s…" % _("_Duplicate"))
        self.item_game_duplicate.set_use_underline(True)

        self.item_game_edit_file.set_label(
            _("_Edit game file"))
        self.item_game_edit_file.set_use_underline(True)

        self.item_game_copy.set_label(
            _("_Copy path to clipboard"))
        self.item_game_copy.set_use_underline(True)

        self.item_game_open.set_label(
            _("_Open path"))
        self.item_game_open.set_use_underline(True)

        self.item_game_cover.set_label(
            "%s…" % _("Set game thumbnail"))
        self.item_game_cover.set_use_underline(True)

        self.item_game_maintenance.set_label(
            "%s…" % _("_Maintenance"))
        self.item_game_maintenance.set_use_underline(True)

        self.item_game_database.set_label(
            "%s…" % _("_Reset data"))
        self.item_game_database.set_use_underline(True)

        self.item_game_remove.set_label(
            "%s…" % _("_Remove from disk"))
        self.item_game_remove.set_use_underline(True)

        # ------------------------------------
        #   Menu - Game score
        # ------------------------------------

        self.menu_game_score = Gtk.Menu()
        self.item_game_score = Gtk.MenuItem()

        self.item_game_score_up = Gtk.MenuItem()
        self.item_game_score_down = Gtk.MenuItem()
        self.item_game_score_0 = Gtk.MenuItem()
        self.item_game_score_1 = Gtk.MenuItem()
        self.item_game_score_2 = Gtk.MenuItem()
        self.item_game_score_3 = Gtk.MenuItem()
        self.item_game_score_4 = Gtk.MenuItem()
        self.item_game_score_5 = Gtk.MenuItem()

        # Properties
        self.item_game_score.set_label(
            _("_Score"))
        self.item_game_score.set_use_underline(True)

        self.item_game_score_up.set_label(
            _("_Increase score"))
        self.item_game_score_up.set_use_underline(True)

        self.item_game_score_down.set_label(
            _("_Decrease score"))
        self.item_game_score_down.set_use_underline(True)

        self.item_game_score_0.set_label(
            _("Set score as 0"))
        self.item_game_score_0.set_use_underline(True)

        self.item_game_score_1.set_label(
            _("Set score as 1"))
        self.item_game_score_1.set_use_underline(True)

        self.item_game_score_2.set_label(
            _("Set score as 2"))
        self.item_game_score_2.set_use_underline(True)

        self.item_game_score_3.set_label(
            _("Set score as 3"))
        self.item_game_score_3.set_use_underline(True)

        self.item_game_score_4.set_label(
            _("Set score as 4"))
        self.item_game_score_4.set_use_underline(True)

        self.item_game_score_5.set_label(
            _("Set score as 5"))
        self.item_game_score_5.set_use_underline(True)

        # ------------------------------------
        #   Menu - Game tools
        # ------------------------------------

        self.menu_game_tools = Gtk.Menu()
        self.item_game_tools = Gtk.MenuItem()

        self.item_game_screenshots = Gtk.MenuItem()
        self.item_game_output = Gtk.MenuItem()
        self.item_game_notes = Gtk.MenuItem()
        self.item_game_desktop = Gtk.MenuItem()
        self.item_game_mednafen = Gtk.MenuItem()

        # Properties
        self.item_game_tools.set_label(_("_Tools"))
        self.item_game_tools.set_use_underline(True)

        self.item_game_screenshots.set_label("%s…" % _("_Screenshots"))
        self.item_game_screenshots.set_use_underline(True)

        self.item_game_output.set_label("%s…" % _("Game _log"))
        self.item_game_output.set_use_underline(True)

        self.item_game_notes.set_label("%s…" % _("_Notes"))
        self.item_game_notes.set_use_underline(True)

        self.item_game_desktop.set_label(_("_Generate a menu entry"))
        self.item_game_desktop.set_use_underline(True)

        self.item_game_mednafen.set_label("%s…" % _("Specify a _memory type"))
        self.item_game_mednafen.set_use_underline(True)

        # ------------------------------------
        #   Statusbar
        # ------------------------------------

        self.statusbar = Gtk.Statusbar()

        self.grid_statusbar = self.statusbar.get_message_area()

        self.label_statusbar_console = self.grid_statusbar.get_children()[0]
        self.label_statusbar_emulator = Gtk.Label()
        self.label_statusbar_game = Gtk.Label()

        self.image_statusbar_properties = Gtk.Image()
        self.image_statusbar_screenshots = Gtk.Image()
        self.image_statusbar_savestates = Gtk.Image()

        self.progress_statusbar = Gtk.ProgressBar()

        # Properties
        self.statusbar.set_no_show_all(True)

        self.grid_statusbar.set_spacing(12)
        self.grid_statusbar.set_margin_top(0)
        self.grid_statusbar.set_margin_end(0)
        self.grid_statusbar.set_margin_start(0)
        self.grid_statusbar.set_margin_bottom(0)

        self.label_statusbar_console.set_use_markup(True)
        self.label_statusbar_console.set_halign(Gtk.Align.START)
        self.label_statusbar_console.set_valign(Gtk.Align.CENTER)
        self.label_statusbar_emulator.set_use_markup(True)
        self.label_statusbar_emulator.set_halign(Gtk.Align.START)
        self.label_statusbar_emulator.set_valign(Gtk.Align.CENTER)
        self.label_statusbar_game.set_ellipsize(Pango.EllipsizeMode.END)
        self.label_statusbar_game.set_halign(Gtk.Align.START)
        self.label_statusbar_game.set_valign(Gtk.Align.CENTER)

        self.image_statusbar_properties.set_from_pixbuf(self.icons.blank())
        self.image_statusbar_screenshots.set_from_pixbuf(self.icons.blank())
        self.image_statusbar_savestates.set_from_pixbuf(self.icons.blank())

        self.progress_statusbar.set_no_show_all(True)
        self.progress_statusbar.set_show_text(True)

    def __init_packing(self):
        """ Initialize widgets packing in main window
        """

        # Main widgets
        self.grid.pack_start(self.menubar, False, False, 0)
        self.grid.pack_start(self.hpaned_consoles, True, True, 0)
        self.grid.pack_start(self.statusbar, False, False, 0)

        # ------------------------------------
        #   Headerbar
        # ------------------------------------

        self.headerbar.pack_start(self.button_headerbar_main)
        self.headerbar.pack_start(self.button_headerbar_view)

        # Headerbar main menu
        self.button_headerbar_main.add(self.image_headerbar_menu)
        self.button_headerbar_view.add(self.image_headerbar_view)

        # ------------------------------------
        #   Menubar
        # ------------------------------------

        self.menubar.append(self.item_menubar_main)
        self.menubar.append(self.item_menubar_view)
        self.menubar.append(self.item_menubar_game)
        self.menubar.append(self.item_menubar_edit)
        self.menubar.append(self.item_menubar_help)

        # Menu - Main items
        self.menu_menubar_main.append(self.item_menubar_preferences)
        self.menu_menubar_main.append(self.item_menubar_log)
        self.menu_menubar_main.append(Gtk.SeparatorMenuItem())
        self.menu_menubar_main.append(self.item_menubar_clean_cache)
        self.menu_menubar_main.append(Gtk.SeparatorMenuItem())
        self.menu_menubar_main.append(self.item_menubar_quit)

        # Menu - View items
        self.menu_menubar_view.append(self.item_menubar_games_display)
        self.menu_menubar_view.append(Gtk.SeparatorMenuItem())
        self.menu_menubar_view.append(self.item_menubar_sidebar)
        self.menu_menubar_view.append(self.item_menubar_statusbar)
        self.menu_menubar_view.append(Gtk.SeparatorMenuItem())
        self.menu_menubar_view.append(self.item_menubar_dark_theme)

        self.item_menubar_games_display.set_submenu(
            self.menu_menubar_games_display)

        self.menu_menubar_games_display.append(self.item_menubar_columns)
        self.menu_menubar_games_display.append(Gtk.SeparatorMenuItem())
        self.menu_menubar_games_display.append(self.item_menubar_list)
        self.menu_menubar_games_display.append(self.item_menubar_grid)

        self.item_menubar_columns.set_submenu(self.menu_menubar_columns)

        self.menu_menubar_columns.append(
            self.item_menubar_columns_favorite)
        self.menu_menubar_columns.append(
            self.item_menubar_columns_multiplayer)
        self.menu_menubar_columns.append(
            self.item_menubar_columns_finish)
        self.menu_menubar_columns.append(
            self.item_menubar_columns_play)
        self.menu_menubar_columns.append(
            self.item_menubar_columns_play_time)
        self.menu_menubar_columns.append(
            self.item_menubar_columns_last_play)
        self.menu_menubar_columns.append(
            self.item_menubar_columns_score)
        self.menu_menubar_columns.append(
            self.item_menubar_columns_installed)
        self.menu_menubar_columns.append(
            self.item_menubar_columns_flags)

        self.item_menubar_sidebar.set_submenu(self.menu_menubar_sidebar)

        self.menu_menubar_sidebar.append(self.item_menubar_sidebar_status)
        self.menu_menubar_sidebar.append(Gtk.SeparatorMenuItem())
        self.menu_menubar_sidebar.append(self.item_menubar_sidebar_right)
        self.menu_menubar_sidebar.append(self.item_menubar_sidebar_bottom)

        self.item_menubar_statusbar.set_submenu(self.menu_menubar_statusbar)

        self.menu_menubar_statusbar.append(self.item_menubar_statusbar_status)

        # Menu - Game items
        self.item_menubar_game.set_submenu(self.menu_menubar_game)

        self.menu_menubar_game.append(self.item_menubar_game_launch)
        self.menu_menubar_game.append(Gtk.SeparatorMenuItem())
        self.menu_menubar_game.append(self.item_menubar_game_favorite)
        self.menu_menubar_game.append(self.item_menubar_game_multiplayer)
        self.menu_menubar_game.append(self.item_menubar_game_finish)
        self.menu_menubar_game.append(Gtk.SeparatorMenuItem())
        self.menu_menubar_game.append(self.item_menubar_game_properties)
        self.menu_menubar_game.append(Gtk.SeparatorMenuItem())
        self.menu_menubar_game.append(self.item_menubar_game_screenshots)
        self.menu_menubar_game.append(self.item_menubar_game_output)
        self.menu_menubar_game.append(self.item_menubar_game_notes)
        self.menu_menubar_game.append(Gtk.SeparatorMenuItem())
        self.menu_menubar_game.append(self.item_menubar_game_fullscreen)

        # Menu - Edit items
        self.item_menubar_edit.set_submenu(self.menu_menubar_edit)

        self.item_menubar_score.set_submenu(self.menu_menubar_score)

        self.menu_menubar_edit.append(self.item_menubar_score)
        self.menu_menubar_edit.append(Gtk.SeparatorMenuItem())
        self.menu_menubar_edit.append(self.item_menubar_rename)
        self.menu_menubar_edit.append(Gtk.SeparatorMenuItem())
        self.menu_menubar_edit.append(self.item_menubar_duplicate)
        self.menu_menubar_edit.append(Gtk.SeparatorMenuItem())
        self.menu_menubar_edit.append(self.item_menubar_mednafen)
        self.menu_menubar_edit.append(Gtk.SeparatorMenuItem())
        self.menu_menubar_edit.append(self.item_menubar_edit_file)
        self.menu_menubar_edit.append(Gtk.SeparatorMenuItem())
        self.menu_menubar_edit.append(self.item_menubar_copy)
        self.menu_menubar_edit.append(self.item_menubar_open)
        self.menu_menubar_edit.append(self.item_menubar_desktop)
        self.menu_menubar_edit.append(Gtk.SeparatorMenuItem())
        self.menu_menubar_edit.append(self.item_menubar_cover)
        self.menu_menubar_edit.append(Gtk.SeparatorMenuItem())
        self.menu_menubar_edit.append(self.item_menubar_maintenance)
        self.menu_menubar_edit.append(Gtk.SeparatorMenuItem())
        self.menu_menubar_edit.append(self.item_menubar_delete)

        self.menu_menubar_score.append(self.item_menubar_score_up)
        self.menu_menubar_score.append(self.item_menubar_score_down)
        self.menu_menubar_score.append(Gtk.SeparatorMenuItem())
        self.menu_menubar_score.append(self.item_menubar_score_0)
        self.menu_menubar_score.append(self.item_menubar_score_1)
        self.menu_menubar_score.append(self.item_menubar_score_2)
        self.menu_menubar_score.append(self.item_menubar_score_3)
        self.menu_menubar_score.append(self.item_menubar_score_4)
        self.menu_menubar_score.append(self.item_menubar_score_5)

        # Menu - Help items
        self.item_menubar_help.set_submenu(self.menu_menubar_help)

        # ------------------------------------
        #   Toolbar - Consoles
        # ------------------------------------

        self.grid_consoles_toolbar.pack_start(
            self.entry_toolbar_consoles_filters, True, True, 0)
        self.grid_consoles_toolbar.pack_start(
            self.button_toolbar_consoles_add, False, False, 0)

        self.button_toolbar_consoles_add.add(self.image_toolbar_consoles_add)

        self.button_toolbar_consoles_add.set_popup(self.menu_toolbar_consoles)

        self.menu_toolbar_consoles.append(self.item_toolbar_add_console)
        self.menu_toolbar_consoles.append(self.item_toolbar_add_emulator)
        self.menu_toolbar_consoles.append(Gtk.SeparatorMenuItem())
        self.menu_toolbar_consoles.append(self.item_toolbar_hide_empty_console)

        self.grid_consoles.pack_start(
            self.grid_consoles_toolbar, False, False, 0)

        # ------------------------------------
        #   Sidebar - Consoles
        # ------------------------------------

        self.grid_consoles.pack_start(
            self.scroll_consoles, True, True, 0)

        self.scroll_consoles.add(self.listbox_consoles)

        self.hpaned_consoles.pack1(self.grid_consoles, False, False)
        self.hpaned_consoles.pack2(self.vpaned_games, True, True)

        # ------------------------------------
        #   Menu - Consoles
        # ------------------------------------

        self.menu_consoles.append(self.item_consoles_console)
        self.menu_consoles.append(self.item_consoles_remove)
        self.menu_consoles.append(Gtk.SeparatorMenuItem())
        self.menu_consoles.append(self.item_consoles_emulator)
        self.menu_consoles.append(self.item_consoles_config)
        self.menu_consoles.append(Gtk.SeparatorMenuItem())
        self.menu_consoles.append(self.item_consoles_copy)
        self.menu_consoles.append(self.item_consoles_open)
        self.menu_consoles.append(Gtk.SeparatorMenuItem())
        self.menu_consoles.append(self.item_consoles_reload)
        self.menu_consoles.append(Gtk.SeparatorMenuItem())
        self.menu_consoles.append(self.item_consoles_favorite)
        self.menu_consoles.append(self.item_consoles_recursive)

        # ------------------------------------
        #   Toolbar - Games
        # ------------------------------------

        self.grid_game_toolbar.pack_start(
            self.grid_game_launch, False, False, 0)
        self.grid_game_toolbar.pack_start(
            self.button_toolbar_parameters, False, False, 0)
        self.grid_game_toolbar.pack_start(
            self.grid_game_options, False, False, 0)
        self.grid_game_toolbar.pack_start(
            self.button_sidebar_tags, False, False, 0)
        self.grid_game_toolbar.pack_start(
            self.separator_toolbar, True, True, 0)
        self.grid_game_toolbar.pack_start(
            self.grid_game_view_mode, False, False, 0)
        self.grid_game_toolbar.pack_start(
            self.grid_game_filters, False, False, 0)

        self.button_toolbar_parameters.add(self.image_toolbar_parameters)
        self.button_toolbar_screenshots.add(self.image_toolbar_screenshots)
        self.button_toolbar_output.add(self.image_toolbar_output)
        self.button_toolbar_notes.add(self.image_toolbar_notes)

        self.grid_game_options.pack_start(
            self.button_toolbar_screenshots, False, False, 0)
        self.grid_game_options.pack_start(
            self.button_toolbar_output, False, False, 0)
        self.grid_game_options.pack_start(
            self.button_toolbar_notes, False, False, 0)

        # Toolbar - Game launch
        self.grid_game_launch.pack_start(
            self.button_toolbar_launch, True, True, 0)
        self.grid_game_launch.pack_start(
            self.button_toolbar_fullscreen, True, True, 0)

        self.button_toolbar_fullscreen.add(self.image_toolbar_fullscreen)

        # Toolbar - Tags
        self.button_sidebar_tags.add(self.image_sidebar_tags)

        # Toolbar - Games view modes
        self.grid_game_view_mode.pack_start(
            self.button_toolbar_list, True, True, 0)
        self.grid_game_view_mode.pack_start(
            self.button_toolbar_grid, True, True, 0)

        self.button_toolbar_grid.add(self.image_toolbar_grid)
        self.button_toolbar_list.add(self.image_toolbar_list)

        # Toolbar - Filters menu
        self.button_toolbar_filters.set_popover(self.popover_toolbar_filters)

        self.grid_game_filters.pack_start(
            self.entry_toolbar_filters, False, False, 0)
        self.grid_game_filters.pack_start(
            self.button_toolbar_filters, False, False, 0)

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

        # Infobar
        self.infobar.get_content_area().pack_start(
            self.label_infobar, True, True, 4)

        # ------------------------------------
        #   Games
        # ------------------------------------

        self.grid_games.pack_start(self.grid_game_toolbar, False, False, 0)
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

        # Games menu
        self.menu_game.append(self.item_game_launch)
        self.menu_game.append(Gtk.SeparatorMenuItem())
        self.menu_game.append(self.item_game_favorite)
        self.menu_game.append(self.item_game_multiplayer)
        self.menu_game.append(self.item_game_finish)
        self.menu_game.append(Gtk.SeparatorMenuItem())
        self.menu_game.append(self.item_game_properties)
        self.menu_game.append(Gtk.SeparatorMenuItem())
        self.menu_game.append(self.item_game_edit)
        self.menu_game.append(self.item_game_score)
        self.menu_game.append(self.item_game_tools)

        self.item_game_edit.set_submenu(self.menu_game_edit)
        self.item_game_score.set_submenu(self.menu_game_score)
        self.item_game_tools.set_submenu(self.menu_game_tools)

        self.menu_game_edit.append(self.item_game_rename)
        self.menu_game_edit.append(Gtk.SeparatorMenuItem())
        self.menu_game_edit.append(self.item_game_duplicate)
        self.menu_game_edit.append(Gtk.SeparatorMenuItem())
        self.menu_game_edit.append(self.item_game_edit_file)
        self.menu_game_edit.append(Gtk.SeparatorMenuItem())
        self.menu_game_edit.append(self.item_game_copy)
        self.menu_game_edit.append(self.item_game_open)
        self.menu_game_edit.append(Gtk.SeparatorMenuItem())
        self.menu_game_edit.append(self.item_game_cover)
        self.menu_game_edit.append(Gtk.SeparatorMenuItem())
        self.menu_game_edit.append(self.item_game_maintenance)
        self.menu_game_edit.append(Gtk.SeparatorMenuItem())
        self.menu_game_edit.append(self.item_game_remove)

        self.menu_game_score.append(self.item_game_score_up)
        self.menu_game_score.append(self.item_game_score_down)
        self.menu_game_score.append(Gtk.SeparatorMenuItem())
        self.menu_game_score.append(self.item_game_score_0)
        self.menu_game_score.append(self.item_game_score_1)
        self.menu_game_score.append(self.item_game_score_2)
        self.menu_game_score.append(self.item_game_score_3)
        self.menu_game_score.append(self.item_game_score_4)
        self.menu_game_score.append(self.item_game_score_5)

        self.menu_game_tools.append(self.item_game_screenshots)
        self.menu_game_tools.append(self.item_game_output)
        self.menu_game_tools.append(self.item_game_notes)
        self.menu_game_tools.append(Gtk.SeparatorMenuItem())
        self.menu_game_tools.append(self.item_game_desktop)
        self.menu_game_tools.append(Gtk.SeparatorMenuItem())
        self.menu_game_tools.append(self.item_game_mednafen)

        # ------------------------------------
        #   Statusbar
        # ------------------------------------

        self.grid_statusbar.pack_start(
            self.label_statusbar_emulator, False, False, 0)
        self.grid_statusbar.pack_start(
            self.label_statusbar_game, True, True, 0)

        self.grid_statusbar.pack_end(
            self.progress_statusbar, False, False, 0)
        self.grid_statusbar.pack_end(
            self.image_statusbar_savestates, False, False, 0)
        self.grid_statusbar.pack_end(
            self.image_statusbar_screenshots, False, False, 0)
        self.grid_statusbar.pack_end(
            self.image_statusbar_properties, False, False, 0)

        self.add(self.grid)

    def __init_signals(self):
        """ Initialize widgets signals
        """

        self.connect("game-started", self.__on_game_started)
        self.connect("game-terminate", self.__on_game_terminate)
        self.connect("script-terminate", self.__on_script_terminate)

        # ------------------------------------
        #   Window
        # ------------------------------------

        self.connect(
            "delete-event", self.__stop_interface)
        self.connect(
            "key-press-event", self.__on_manage_keys)

        # ------------------------------------
        #   Menubar
        # ------------------------------------

        self.item_menubar_preferences.connect(
            "activate", self.__on_show_preferences)
        self.item_menubar_log.connect(
            "activate", self.__on_show_log)
        self.item_menubar_clean_cache.connect(
            "activate", self.__on_show_clean_cache)
        self.item_menubar_quit.connect(
            "activate", self.__stop_interface)

        self.signal_menu_sidebar = self.item_menubar_sidebar_status.connect(
            "toggled", self.__on_activate_sidebar)
        self.item_menubar_sidebar_right.connect(
            "toggled", self.__on_move_sidebar)
        self.item_menubar_sidebar_bottom.connect(
            "toggled", self.__on_move_sidebar)

        self.signal_menu_dark_theme = self.item_menubar_dark_theme.connect(
            "toggled", self.__on_activate_dark_theme)
        self.signal_menu_statusbar = \
            self.item_menubar_statusbar_status.connect(
                "toggled", self.__on_activate_statusbar)

        self.signal_menu_favorite = self.item_menubar_columns_favorite.connect(
            "activate", self.__on_switch_column_visibility, "favorite")
        self.signal_menu_multiplayer = \
            self.item_menubar_columns_multiplayer.connect(
                "activate", self.__on_switch_column_visibility, "multiplayer")
        self.signal_menu_finish = self.item_menubar_columns_finish.connect(
            "activate", self.__on_switch_column_visibility, "finish")
        self.signal_menu_play = self.item_menubar_columns_play.connect(
            "activate", self.__on_switch_column_visibility, "play")
        self.signal_menu_play_time = \
            self.item_menubar_columns_play_time.connect(
                "activate", self.__on_switch_column_visibility, "play_time")
        self.signal_menu_last_play = \
            self.item_menubar_columns_last_play.connect(
                "activate", self.__on_switch_column_visibility, "last_play")
        self.signal_menu_score = self.item_menubar_columns_score.connect(
            "activate", self.__on_switch_column_visibility, "score")
        self.signal_menu_installed = \
            self.item_menubar_columns_installed.connect(
                "activate", self.__on_switch_column_visibility, "installed")
        self.signal_menu_flags = self.item_menubar_columns_flags.connect(
            "activate", self.__on_switch_column_visibility, "flags")

        self.signal_menu_list = self.item_menubar_list.connect(
            "toggled", self.__on_switch_games_view)
        self.signal_menu_grid = self.item_menubar_grid.connect(
            "toggled", self.__on_switch_games_view)

        self.item_menubar_game_launch.connect(
            "activate", self.__on_game_launch)
        self.item_menubar_game_properties.connect(
            "activate", self.__on_game_parameters)
        self.item_menubar_game_screenshots.connect(
            "activate", self.__on_show_viewer)
        self.item_menubar_game_output.connect(
            "activate", self.__on_show_log)
        self.item_menubar_game_notes.connect(
            "activate", self.__on_show_notes)

        self.signal_menu_game_favorite = \
            self.item_menubar_game_favorite.connect(
                "activate", self.__on_game_marked_as_favorite)
        self.signal_menu_game_multiplayer = \
            self.item_menubar_game_multiplayer.connect(
                "activate", self.__on_game_marked_as_multiplayer)
        self.signal_menu_game_finish = self.item_menubar_game_finish.connect(
            "activate", self.__on_game_marked_as_finish)

        self.signal_menu_fullscreen = \
            self.item_menubar_game_fullscreen.connect(
                "toggled", self.__on_activate_fullscreen)

        self.item_menubar_rename.connect(
            "activate", self.__on_game_renamed)
        self.item_menubar_duplicate.connect(
            "activate", self.__on_game_duplicate)
        self.item_menubar_edit_file.connect(
            "activate", self.__on_game_edit_file)
        self.item_menubar_copy.connect(
            "activate", self.__on_copy_path_to_clipboard)
        self.item_menubar_open.connect(
            "activate", self.__on_open_directory)
        self.item_menubar_desktop.connect(
            "activate", self.__on_game_generate_desktop)
        self.item_menubar_cover.connect(
            "activate", self.__on_game_cover)
        self.item_menubar_maintenance.connect(
            "activate", self.__on_game_maintenance)
        self.item_menubar_delete.connect(
            "activate", self.__on_game_removed)
        self.item_menubar_mednafen.connect(
            "activate", self.__on_game_backup_memory)
        self.item_menubar_score_up.connect(
            "activate", self.__on_game_score)
        self.item_menubar_score_down.connect(
            "activate", self.__on_game_score)
        self.item_menubar_score_0.connect(
            "activate", self.__on_game_score, 0)
        self.item_menubar_score_1.connect(
            "activate", self.__on_game_score, 1)
        self.item_menubar_score_2.connect(
            "activate", self.__on_game_score, 2)
        self.item_menubar_score_3.connect(
            "activate", self.__on_game_score, 3)
        self.item_menubar_score_4.connect(
            "activate", self.__on_game_score, 4)
        self.item_menubar_score_5.connect(
            "activate", self.__on_game_score, 5)

        self.item_menubar_website.connect(
            "activate", self.__on_show_external_link)
        self.item_menubar_bug_tracker.connect(
            "activate", self.__on_show_external_link)
        self.item_menubar_about.connect(
            "activate", self.__on_show_about)

        # ------------------------------------
        #   Toolbar - Consoles
        # ------------------------------------

        self.listbox_consoles.connect(
            "row-activated", self.__on_selected_console)
        self.entry_toolbar_consoles_filters.connect(
            "changed", self.__on_update_consoles)

        self.item_toolbar_add_console.connect(
            "activate", self.__on_show_console_editor)
        self.item_toolbar_add_emulator.connect(
            "activate", self.__on_show_emulator_editor)

        self.signal_console_hide_empty = \
            self.item_toolbar_hide_empty_console.connect(
                "activate", self.__on_change_console_option)

        # ------------------------------------
        #   Sidebar - Consoles
        # ------------------------------------

        self.listbox_consoles.connect(
            "button-press-event", self.__on_console_menu_show)
        self.listbox_consoles.connect(
            "key-release-event", self.__on_console_menu_show)

        # ------------------------------------
        #   Menu - Consoles
        # ------------------------------------

        self.item_consoles_console.connect(
            "activate", self.__on_show_console_editor)
        self.item_consoles_remove.connect(
            "activate", self.__on_remove_console)

        self.item_consoles_emulator.connect(
            "activate", self.__on_show_emulator_editor)
        self.item_consoles_config.connect(
            "activate", self.__on_show_emulator_config)

        self.item_consoles_copy.connect(
            "activate", self.__on_copy_path_to_clipboard)
        self.item_consoles_open.connect(
            "activate", self.__on_open_directory)

        self.item_consoles_reload.connect(
            "activate", self.__on_reload_games)

        self.signal_console_favorite = \
            self.item_consoles_favorite.connect(
                "activate", self.__on_change_console_option)
        self.signal_console_recursive = \
            self.item_consoles_recursive.connect(
                "activate", self.__on_change_console_option)

        # ------------------------------------
        #   Toolbar - Game
        # ------------------------------------

        self.button_toolbar_launch.connect(
            "clicked", self.__on_game_launch)
        self.signal_toolbar_fullscreen = \
            self.button_toolbar_fullscreen.connect(
                "toggled", self.__on_activate_fullscreen)
        self.button_toolbar_screenshots.connect(
            "clicked", self.__on_show_viewer)
        self.button_toolbar_output.connect(
            "clicked", self.__on_game_log)
        self.button_toolbar_notes.connect(
            "clicked", self.__on_show_notes)
        self.button_toolbar_parameters.connect(
            "clicked", self.__on_game_parameters)

        self.signal_headerbar_list = self.button_toolbar_list.connect(
            "toggled", self.__on_switch_games_view)
        self.signal_headerbar_grid = self.button_toolbar_grid.connect(
            "toggled", self.__on_switch_games_view)

        self.entry_toolbar_filters.connect(
            "changed", self.filters_update)

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
        #   Menu - Game
        # ------------------------------------

        self.item_game_launch.connect(
            "activate", self.__on_game_launch)
        self.signal_game_favorite = self.item_game_favorite.connect(
            "activate", self.__on_game_marked_as_favorite)
        self.signal_game_multiplayer = self.item_game_multiplayer.connect(
            "activate", self.__on_game_marked_as_multiplayer)
        self.signal_game_finish = self.item_game_finish.connect(
            "activate", self.__on_game_marked_as_finish)
        self.item_game_screenshots.connect(
            "activate", self.__on_show_viewer)
        self.item_game_output.connect(
            "activate", self.__on_game_log)
        self.item_game_notes.connect(
            "activate", self.__on_show_notes)

        self.item_game_rename.connect(
            "activate", self.__on_game_renamed)
        self.item_game_duplicate.connect(
            "activate", self.__on_game_duplicate)
        self.item_game_properties.connect(
            "activate", self.__on_game_parameters)
        self.item_game_edit_file.connect(
            "activate", self.__on_game_edit_file)
        self.item_game_copy.connect(
            "activate", self.__on_copy_path_to_clipboard)
        self.item_game_open.connect(
            "activate", self.__on_open_directory)
        self.item_game_cover.connect(
            "activate", self.__on_game_cover)
        self.item_game_desktop.connect(
            "activate", self.__on_game_generate_desktop)
        self.item_game_maintenance.connect(
            "activate", self.__on_game_maintenance)
        self.item_game_remove.connect(
            "activate", self.__on_game_removed)
        self.item_game_mednafen.connect(
            "activate", self.__on_game_backup_memory)
        self.item_game_score_up.connect(
            "activate", self.__on_game_score)
        self.item_game_score_down.connect(
            "activate", self.__on_game_score)
        self.item_game_score_0.connect(
            "activate", self.__on_game_score, 0)
        self.item_game_score_1.connect(
            "activate", self.__on_game_score, 1)
        self.item_game_score_2.connect(
            "activate", self.__on_game_score, 2)
        self.item_game_score_3.connect(
            "activate", self.__on_game_score, 3)
        self.item_game_score_4.connect(
            "activate", self.__on_game_score, 4)
        self.item_game_score_5.connect(
            "activate", self.__on_game_score, 5)

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
        #   Treeview - Games
        # ------------------------------------

        self.treeview_games.connect(
            "button-press-event", self.__on_selected_game)
        self.treeview_games.connect(
            "key-release-event", self.__on_selected_game)

        self.treeview_games.connect(
            "button-press-event", self.__on_game_menu_show)
        self.treeview_games.connect(
            "key-release-event", self.__on_game_menu_show)

        self.treeview_games.connect(
            "drag-data-get", self.__on_dnd_send_data)

        self.treeview_games.connect(
            "query-tooltip", self.__on_selected_game_tooltip)

        self.filter_games_list.set_visible_func(self.filters_match)

        # ------------------------------------
        #   Iconview - Games
        # ------------------------------------

        self.iconview_games.connect(
            "button-press-event", self.__on_selected_game)
        self.iconview_games.connect(
            "key-release-event", self.__on_selected_game)

        self.iconview_games.connect(
            "button-press-event", self.__on_game_menu_show)
        self.iconview_games.connect(
            "key-release-event", self.__on_game_menu_show)

        self.iconview_games.connect(
            "drag-data-get", self.__on_dnd_send_data)

        self.iconview_games.connect(
            "query-tooltip", self.__on_selected_game_tooltip)

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

        # Define signals per toggle buttons
        self.__signals_storage = {
            # Headerbar
            self.button_toolbar_grid: self.signal_headerbar_grid,
            self.button_toolbar_list: self.signal_headerbar_list,
            # Menubar
            self.item_menubar_columns_favorite: self.signal_menu_favorite,
            self.item_menubar_columns_finish: self.signal_menu_finish,
            self.item_menubar_columns_flags: self.signal_menu_flags,
            self.item_menubar_columns_installed: self.signal_menu_installed,
            self.item_menubar_columns_last_play: self.signal_menu_last_play,
            self.item_menubar_columns_multiplayer:
                self.signal_menu_multiplayer,
            self.item_menubar_columns_play: self.signal_menu_play,
            self.item_menubar_columns_play_time: self.signal_menu_play_time,
            self.item_menubar_columns_score: self.signal_menu_score,
            self.item_menubar_dark_theme: self.signal_menu_dark_theme,
            self.item_menubar_game_favorite: self.signal_menu_game_favorite,
            self.item_menubar_game_finish: self.signal_menu_game_finish,
            self.item_menubar_game_fullscreen: self.signal_menu_fullscreen,
            self.item_menubar_game_multiplayer:
                self.signal_menu_game_multiplayer,
            self.item_menubar_grid: self.signal_menu_grid,
            self.item_menubar_list: self.signal_menu_list,
            self.item_menubar_sidebar_status: self.signal_menu_sidebar,
            self.item_menubar_statusbar_status: self.signal_menu_statusbar,
            # Toolbar
            self.button_toolbar_fullscreen: self.signal_toolbar_fullscreen,
            self.item_toolbar_hide_empty_console:
                self.signal_console_hide_empty,
            # Console menu
            self.item_consoles_favorite: self.signal_console_favorite,
            self.item_consoles_recursive: self.signal_console_recursive,
            # Game menu
            self.item_game_favorite: self.signal_game_favorite,
            self.item_game_finish: self.signal_game_finish,
            self.item_game_multiplayer: self.signal_game_multiplayer
        }

        # Store image references with associate icons
        self.__images_storage = {
            self.image_headerbar_menu: Icons.Symbolic.MENU,
            self.image_headerbar_view: Icons.Symbolic.VIDEO,
            self.image_sidebar_tags: Icons.Symbolic.PAPERCLIP,
            self.image_toolbar_consoles_add: Icons.Symbolic.VIEW_MORE,
            self.image_toolbar_fullscreen: Icons.Symbolic.RESTORE,
            self.image_toolbar_grid: Icons.Symbolic.GRID,
            self.image_toolbar_list: Icons.Symbolic.LIST,
            self.image_toolbar_notes: Icons.Symbolic.EDITOR,
            self.image_toolbar_output: Icons.Symbolic.TERMINAL,
            self.image_toolbar_parameters: Icons.Symbolic.PROPERTIES,
            self.image_toolbar_screenshots: Icons.Symbolic.CAMERA
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
            self.button_toolbar_launch,
            # Menubar
            self.item_menubar_copy,
            self.item_menubar_cover,
            self.item_menubar_database,
            self.item_menubar_delete,
            self.item_menubar_desktop,
            self.item_menubar_duplicate,
            self.item_menubar_edit_file,
            self.item_menubar_game_favorite,
            self.item_menubar_game_finish,
            self.item_menubar_game_launch,
            self.item_menubar_game_multiplayer,
            self.item_menubar_game_notes,
            self.item_menubar_game_output,
            self.item_menubar_game_properties,
            self.item_menubar_game_screenshots,
            self.item_menubar_maintenance,
            self.item_menubar_mednafen,
            self.item_menubar_open,
            self.item_menubar_rename,
            self.item_menubar_score,
            # Toolbar
            self.button_sidebar_tags,
            self.button_toolbar_notes,
            self.button_toolbar_output,
            self.button_toolbar_parameters,
            self.button_toolbar_screenshots,
            # Game menu
            self.item_game_copy,
            self.item_game_cover,
            self.item_game_database,
            self.item_game_desktop,
            self.item_game_duplicate,
            self.item_game_edit_file,
            self.item_game_favorite,
            self.item_game_finish,
            self.item_game_maintenance,
            self.item_game_mednafen,
            self.item_game_multiplayer,
            self.item_game_notes,
            self.item_game_open,
            self.item_game_output,
            self.item_game_remove,
            self.item_game_rename,
            self.item_game_screenshots
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

        shortcuts = [
            {
                "path": "<GEM>/game/edit",
                "widgets": [
                    self.item_game_edit_file,
                    self.item_menubar_edit_file
                ],
                "keys": self.config.item("keys", "edit-file", "<Control>M")
            },
            {
                "path": "<GEM>/game/open",
                "widgets": [
                    self.item_game_open,
                    self.item_menubar_open
                ],
                "keys": self.config.item("keys", "open", "<Control>O")
            },
            {
                "path": "<GEM>/game/copy",
                "widgets": [
                    self.item_game_copy,
                    self.item_menubar_copy
                ],
                "keys": self.config.item("keys", "copy", "<Control>C")
            },
            {
                "path": "<GEM>/game/desktop",
                "widgets": [
                    self.item_game_desktop,
                    self.item_menubar_desktop
                ],
                "keys": self.config.item("keys", "desktop", "<Control>G")
            },
            {
                "path": "<GEM>/game/start",
                "widgets": [
                    self.item_game_launch,
                    self.item_menubar_game_launch
                ],
                "keys": self.config.item("keys", "start", "<Control>Return")
            },
            {
                "path": "<GEM>/game/rename",
                "widgets": [
                    self.item_game_rename,
                    self.item_menubar_rename
                ],
                "keys": self.config.item("keys", "rename", "F2")
            },
            {
                "path": "<GEM>/game/duplicate",
                "widgets": [
                    self.item_game_duplicate,
                    self.item_menubar_duplicate
                ],
                "keys": self.config.item("keys", "duplicate", "<Control>U")
            },
            {
                "path": "<GEM>/game/favorite",
                "widgets": [
                    self.item_game_favorite,
                    self.item_menubar_game_favorite
                ],
                "keys": self.config.item("keys", "favorite", "F3")
            },
            {
                "path": "<GEM>/game/multiplayer",
                "widgets": [
                    self.item_game_multiplayer,
                    self.item_menubar_game_multiplayer
                ],
                "keys": self.config.item("keys", "multiplayer", "F4")
            },
            {
                "path": "<GEM>/game/finish",
                "widgets": [
                    self.item_game_finish,
                    self.item_menubar_game_finish
                ],
                "keys": self.config.item("keys", "finish", "<Control>F3")
            },
            {
                "path": "<GEM>/game/score/up",
                "widgets": [
                    self.item_game_score_up,
                    self.item_menubar_score_up
                ],
                "keys": self.config.item(
                    "keys", "score-up", "<Control>Page_Up")
            },
            {
                "path": "<GEM>/game/score/down",
                "widgets": [
                    self.item_game_score_down,
                    self.item_menubar_score_down
                ],
                "keys": self.config.item(
                    "keys", "score-down", "<Control>Page_Down")
            },
            {
                "path": "<GEM>/game/score/0",
                "widgets": [
                    self.item_game_score_0,
                    self.item_menubar_score_0
                ],
                "keys": self.config.item(
                    "keys", "score-0", "<Primary>0")
            },
            {
                "path": "<GEM>/game/score/1",
                "widgets": [
                    self.item_game_score_1,
                    self.item_menubar_score_1
                ],
                "keys": self.config.item(
                    "keys", "score-1", "<Primary>1")
            },
            {
                "path": "<GEM>/game/score/2",
                "widgets": [
                    self.item_game_score_2,
                    self.item_menubar_score_2
                ],
                "keys": self.config.item(
                    "keys", "score-2", "<Primary>2")
            },
            {
                "path": "<GEM>/game/score/3",
                "widgets": [
                    self.item_game_score_3,
                    self.item_menubar_score_3
                ],
                "keys": self.config.item(
                    "keys", "score-3", "<Primary>3")
            },
            {
                "path": "<GEM>/game/score/4",
                "widgets": [
                    self.item_game_score_4,
                    self.item_menubar_score_4
                ],
                "keys": self.config.item(
                    "keys", "score-4", "<Primary>4")
            },
            {
                "path": "<GEM>/game/score/5",
                "widgets": [
                    self.item_game_score_5,
                    self.item_menubar_score_5
                ],
                "keys": self.config.item(
                    "keys", "score-5", "<Primary>5")
            },
            {
                "path": "<GEM>/game/cover",
                "widgets": [
                    self.item_game_cover,
                    self.item_menubar_cover
                ],
                "keys": self.config.item("keys", "cover", "<Control>I")
            },
            {
                "path": "<GEM>/game/screenshots",
                "widgets": [
                    self.item_game_screenshots,
                    self.item_menubar_game_screenshots,
                    self.button_toolbar_screenshots
                ],
                "keys": self.config.item("keys", "snapshots", "F5")
            },
            {
                "path": "<GEM>/game/log",
                "widgets": [
                    self.item_game_output,
                    self.item_menubar_game_output
                ],
                "keys": self.config.item("keys", "log", "F6")
            },
            {
                "path": "<GEM>/game/notes",
                "widgets": [
                    self.item_game_notes,
                    self.item_menubar_game_notes
                ],
                "keys": self.config.item("keys", "notes", "F7")
            },
            {
                "path": "<GEM>/game/memory",
                "widgets": [
                    self.item_game_mednafen,
                    self.item_menubar_mednafen
                ],
                "keys": self.config.item("keys", "memory", "F8")
            },
            {
                "path": "<GEM>/fullscreen",
                "widgets": [
                    self.item_menubar_game_fullscreen
                ],
                "keys": self.config.item("keys", "fullscreen", "F11"),
                "function": self.__on_activate_fullscreen
            },
            {
                "path": "<GEM>/sidebar",
                "widgets": [
                    self.item_menubar_sidebar_status
                ],
                "keys": self.config.item("keys", "sidebar", "F9"),
                "function": self.__on_activate_sidebar
            },
            {
                "path": "<GEM>/statusbar",
                "widgets": [
                    self.item_menubar_statusbar_status
                ],
                "keys": self.config.item("keys", "statusbar", "<Control>F9"),
                "function": self.__on_activate_statusbar
            },
            {
                "path": "<GEM>/game/exceptions",
                "widgets": [
                    self.item_game_properties,
                    self.item_menubar_game_properties
                ],
                "keys": self.config.item("keys", "exceptions", "F12")
            },
            {
                "path": "<GEM>/game/delete",
                "widgets": [
                    self.item_game_remove,
                    self.item_menubar_delete
                ],
                "keys": self.config.item("keys", "delete", "<Control>Delete")
            },
            {
                "path": "<GEM>/game/maintenance",
                "widgets": [
                    self.item_game_maintenance,
                    self.item_menubar_maintenance
                ],
                "keys": self.config.item("keys", "maintenance", "<Control>D")
            },
            {
                "path": "<GEM>/preferences",
                "widgets": [
                    self.item_menubar_preferences
                ],
                "keys": self.config.item("keys", "preferences", "<Control>P"),
                "function": self.__on_show_preferences
            },
            {
                "path": "<GEM>/log",
                "widgets": [
                    self.item_menubar_log
                ],
                "keys": self.config.item("keys", "gem", "<Control>L"),
                "function": self.__on_show_log
            },
            {
                "path": "<GEM>/quit",
                "widgets": [
                    self.item_menubar_quit
                ],
                "keys": self.config.item("keys", "quit", "<Control>Q"),
                "function": self.__stop_interface
            }
        ]

        # Disconnect previous shortcut to avoid multiple allocation
        for key, mod in self.shortcuts:
            self.shortcuts_group.disconnect_key(key, mod)

        for data in shortcuts:
            key, mod = Gtk.accelerator_parse(data["keys"])

            if Gtk.accelerator_valid(key, mod):

                self.shortcuts_map.change_entry(data["path"], key, mod, True)

                for widget in data["widgets"]:

                    # Global signals
                    if type(widget) is MainWindow:

                        # Avoid to have multiple shortcuts with classic theme
                        if not self.use_classic_theme:
                            self.shortcuts_group.connect(
                                key,
                                mod,
                                Gtk.AccelFlags.VISIBLE,
                                data["function"])

                    # Local signals
                    else:
                        widget.add_accelerator("activate",
                                               self.shortcuts_group,
                                               key,
                                               mod,
                                               Gtk.AccelFlags.VISIBLE)

                    # Store current shortcut to remove it properly later
                    self.shortcuts.append((key, mod))

    def __init_interface(self):
        """ Init main interface
        """

        self.selection = dict(console=None, game=None)

        # ------------------------------------
        #   Menus
        # ------------------------------------

        if self.use_classic_theme:
            self.item_menubar_main.set_submenu(self.menu_menubar_main)
            self.item_menubar_view.set_submenu(self.menu_menubar_view)

            self.menu_menubar_help.append(self.item_menubar_website)
            self.menu_menubar_help.append(self.item_menubar_bug_tracker)
            self.menu_menubar_help.append(Gtk.SeparatorMenuItem())
            self.menu_menubar_help.append(self.item_menubar_about)

        else:
            self.button_headerbar_main.set_popup(self.menu_menubar_main)
            self.button_headerbar_view.set_popup(self.menu_menubar_view)

            self.menu_menubar_main.insert(self.item_menubar_website, 5)
            self.menu_menubar_main.insert(self.item_menubar_bug_tracker, 6)
            self.menu_menubar_main.insert(Gtk.SeparatorMenuItem(), 7)
            self.menu_menubar_main.insert(self.item_menubar_about, 8)
            self.menu_menubar_main.insert(Gtk.SeparatorMenuItem(), 9)

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
            self.button_toolbar_grid.set_active(True)
            self.item_menubar_grid.set_active(True)

        else:
            self.button_toolbar_list.set_active(True)
            self.item_menubar_list.set_active(True)

        # ------------------------------------
        #   Toolbar design
        # ------------------------------------

        # Update design colorscheme
        on_change_theme(self.use_dark_theme)

        self.item_menubar_dark_theme.set_active(self.use_dark_theme)

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

        self.grid_consoles_menu.show_all()
        self.grid_game_filters_popover.show_all()

        self.infobar.show_all()
        self.grid_infobar.show_all()
        self.label_infobar.show_all()

        self.grid_sidebar.show_all()
        self.scroll_sidebar.show_all()
        self.scroll_sidebar_informations.show_all()

        self.grid_games_placeholder.show_all()
        self.label_consoles.show_all()

        # Manage window template
        if self.use_classic_theme:
            self.menubar.show_all()

        else:
            self.menubar.hide()

        self.menu_menubar_main.show_all()
        self.menu_menubar_view.show_all()
        self.menu_menubar_edit.show_all()
        self.menu_menubar_help.show_all()
        self.menu_toolbar_consoles.show_all()
        self.menu_consoles.show_all()
        self.menu_game.show_all()

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
            self.grid_statusbar.show_all()

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

            dialog = MessageDialog(
                self,
                _("Welcome !"),
                _("Welcome and thanks for choosing GEM as emulators manager. "
                  "Start using GEM by droping some roms into interface.\n\n"
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

        # Remove games listing thread
        if not self.list_thread == 0:
            GLib.source_remove(self.list_thread)

        # Remove game and script threads
        for thread in thread_enumerate().copy():

            # Avoid to remove the main thread
            if thread is not thread_main_thread():
                thread.proc.terminate()
                thread.join()

                self.__on_game_terminate(None, thread)

        # ------------------------------------
        #   Notes
        # ------------------------------------

        # Close open notes dialog
        if len(self.notes.keys()) > 0:
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
                    "Save %s console for next startup" % row.console.id)

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

        if self.button_toolbar_list.get_active():
            self.config.modify("gem", "games_view_mode", Columns.Key.List)

        elif self.button_toolbar_grid.get_active():
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

        self.main_loop.quit()

    def load_configuration(self):
        """ Load main configuration file and store values
        """

        if getattr(self, "config", None) is None:
            self.config = Configuration(Folders.CONFIG.joinpath("gem.conf"))

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
        self.item_menubar_sidebar_status.set_active(self.show_sidebar)

        # Show statusbar visibility buttons
        self.item_menubar_statusbar_status.set_active(self.show_statusbar)

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

        if self.__current_orientation == Gtk.Orientation.VERTICAL:
            self.item_menubar_sidebar_bottom.set_active(True)

        else:
            self.item_menubar_sidebar_right.set_active(True)

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

            # Retrieve menubar item
            menu_item = getattr(self, "item_menubar_columns_%s" % key, None)
            if menu_item is not None:
                menu_item.set_active(visibility)

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

        self.item_toolbar_hide_empty_console.set_active(
            self.hide_empty_console)

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
            self.button_toolbar_filters.get_style_context().add_class(
                "suggested-action")
        else:
            self.button_toolbar_filters.get_style_context().remove_class(
                "suggested-action")

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

        self.button_toolbar_filters.get_style_context().remove_class(
            "suggested-action")

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
            text = self.entry_toolbar_filters.get_text()

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

        text = str()
        if not self.entry_toolbar_filters.get_text() == widget.get_label():
            text = widget.get_label()

        self.entry_toolbar_filters.set_text(text)

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
                dialog = MessageDialog(
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

        self.image_statusbar_properties.set_from_pixbuf(self.icons.blank(24))
        self.image_statusbar_savestates.set_from_pixbuf(self.icons.blank(24))
        self.image_statusbar_screenshots.set_from_pixbuf(self.icons.blank(24))
        self.image_statusbar_properties.set_tooltip_text(str())
        self.image_statusbar_savestates.set_tooltip_text(str())
        self.image_statusbar_screenshots.set_tooltip_text(str())

        # ----------------------------------------
        #   Update informations
        # ----------------------------------------

        if game is not None:

            # ----------------------------------------
            #   Widgets
            # ----------------------------------------

            self.__on_game_launch_button_update(game.id not in self.threads)

            self.button_toolbar_launch.set_sensitive(True)

            # This game is not running
            if game.id not in self.threads:
                self.item_menubar_game_launch.set_sensitive(True)
                self.item_menubar_database.set_sensitive(True)

                self.item_game_launch.set_sensitive(True)
                self.item_game_database.set_sensitive(True)

                if game.path.exists() and access(game.path, W_OK):
                    self.item_menubar_delete.set_sensitive(True)
                    self.item_game_remove.set_sensitive(True)

            # Menus
            self.item_menubar_copy.set_sensitive(True)
            self.item_menubar_cover.set_sensitive(True)
            self.item_menubar_desktop.set_sensitive(True)
            self.item_menubar_duplicate.set_sensitive(True)
            self.item_menubar_game_favorite.set_sensitive(True)
            self.item_menubar_game_finish.set_sensitive(True)
            self.item_menubar_game_multiplayer.set_sensitive(True)
            self.item_menubar_game_notes.set_sensitive(True)
            self.item_menubar_game_properties.set_sensitive(True)
            self.item_menubar_maintenance.set_sensitive(True)
            self.item_menubar_open.set_sensitive(True)
            self.item_menubar_rename.set_sensitive(True)
            self.item_menubar_score.set_sensitive(True)

            # Game menu
            self.item_game_copy.set_sensitive(True)
            self.item_game_cover.set_sensitive(True)
            self.item_game_desktop.set_sensitive(True)
            self.item_game_duplicate.set_sensitive(True)
            self.item_game_favorite.set_sensitive(True)
            self.item_game_finish.set_sensitive(True)
            self.item_game_maintenance.set_sensitive(True)
            self.item_game_multiplayer.set_sensitive(True)
            self.item_game_notes.set_sensitive(True)
            self.item_game_open.set_sensitive(True)
            self.item_game_rename.set_sensitive(True)

            # Toolbar
            self.button_toolbar_notes.set_sensitive(True)
            self.button_toolbar_parameters.set_sensitive(True)

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
                    self.item_game_edit_file.set_sensitive(True)
                    self.item_menubar_edit_file.set_sensitive(True)

            if game.emulator is not None:

                # Check extension and emulator for GBA game on mednafen
                if self.__mednafen_status and game.extension == ".gba":

                    if "mednafen" in str(game.emulator.binary):
                        self.item_game_mednafen.set_sensitive(True)
                        self.item_menubar_mednafen.set_sensitive(True)

            # ----------------------------------------
            #   Game flags
            # ----------------------------------------

            self.item_menubar_game_favorite.set_active(game.favorite)
            self.item_menubar_game_multiplayer.set_active(game.multiplayer)
            self.item_menubar_game_finish.set_active(game.finish)

            self.item_game_favorite.set_active(game.favorite)
            self.item_game_multiplayer.set_active(game.multiplayer)
            self.item_game_finish.set_active(game.finish)

            # ----------------------------------------
            #   Game screenshots
            # ----------------------------------------

            pixbuf = self.icons.get_translucent("screenshot")

            # Check screenshots
            if len(game.screenshots) > 0:
                pixbuf = self.icons.get("screenshot")

                self.button_toolbar_screenshots.set_sensitive(True)
                self.item_game_screenshots.set_sensitive(True)
                self.item_menubar_game_screenshots.set_sensitive(True)

                text = _("1 screenshot")
                if len(game.screenshots) > 1:
                    text = _("%d screenshots") % len(game.screenshots)

                self.image_statusbar_screenshots.set_tooltip_text(text)

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

            else:
                self.image_statusbar_screenshots.set_tooltip_text(
                    _("No screenshot"))

            # Set statusbar icon for screenshot status
            self.image_statusbar_screenshots.set_from_pixbuf(pixbuf)

            # ----------------------------------------
            #   Game log
            # ----------------------------------------

            # Check game log file
            if self.check_log() is not None:
                self.button_toolbar_output.set_sensitive(True)
                self.item_game_output.set_sensitive(True)
                self.item_menubar_game_output.set_sensitive(True)

            # ----------------------------------------
            #   Game tags
            # ----------------------------------------

            if len(game.tags) > 0:
                self.button_sidebar_tags.set_sensitive(True)

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

            if len(game.savestates) > 0:
                pixbuf = self.icons.get("savestate")

                text = _("1 savestate")
                if len(game.savestates) > 1:
                    text = _("%d savestates") % len(game.savestates)

                self.image_statusbar_savestates.set_tooltip_text(text)

            else:
                self.image_statusbar_savestates.set_tooltip_text(
                    _("No savestate"))

            self.image_statusbar_savestates.set_from_pixbuf(pixbuf)

            # ----------------------------------------
            #   Game custom parameters
            # ----------------------------------------

            # Game custom parameters
            pixbuf = self.icons.get_translucent("parameter")

            if len(game.default) > 0 or not game.emulator == console.emulator:
                pixbuf = self.icons.get("parameter")

                if len(game.default) > 0:
                    self.image_statusbar_properties.set_tooltip_text(
                        _("Use alternative arguments"))

                elif game.emulator == console.emulator:
                    self.image_statusbar_properties.set_tooltip_text(
                        _("Use alternative emulator"))

            self.image_statusbar_properties.set_from_pixbuf(pixbuf)

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

        self.label_statusbar_console.set_visible(console is not None)
        self.label_statusbar_emulator.set_visible(emulator is not None)
        self.label_statusbar_game.set_visible(game is not None)

        texts = list()

        # ----------------------------------------
        #   Console
        # ----------------------------------------

        if console is not None:
            text = _("N/A")

            if len(self.filter_games_list) == 1:
                text = _("1 game available")

                texts.append(text)

            elif len(self.filter_games_list) > 1:
                text = _("%d games available") % len(self.filter_games_list)

                texts.append(text)

            self.label_statusbar_console.set_markup(
                "<b>%s</b> : %s" % (_("Console"), text))

        # ----------------------------------------
        #   Emulator
        # ----------------------------------------

        if emulator is not None:
            self.label_statusbar_emulator.set_markup(
                "<b>%s</b> : %s" % (_("Emulator"), emulator.name))

        # ----------------------------------------
        #   Game
        # ----------------------------------------

        if game is not None:
            self.label_statusbar_game.set_text(game.name)

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
            dialog = MessageDialog(self, title, message, icon)

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
            if widget == self.item_menubar_website:
                link = Metadata.WEBSITE

            elif widget == self.item_menubar_bug_tracker:
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
            "Lubert Aurélien (PacMiam)"
        ])
        about.set_artists([
            "Evan-Amos %s - Public Domain" % Metadata.EVAN_AMOS
        ])
        about.set_translator_credits(_("translator-credits"))
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

                    dialog = ViewerDialog(
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

        dialog = PreferencesWindow(self.api, self)

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

        path = Folders.LOCAL.joinpath("gem.log")

        if path.exists():
            try:
                size = self.config.get(
                    "windows", "log", fallback="800x600").split('x')

            except ValueError:
                size = (800, 600)

            self.set_sensitive(False)

            dialog = EditorDialog(
                self,
                _("Application log"),
                path,
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

            dialog = CleanCacheDialog(self)

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
            path = Folders.LOCAL.joinpath("notes", game.id + ".txt")

            if path is not None and not str(path) in self.notes.keys():
                try:
                    size = self.config.get(
                        "windows", "notes", fallback="800x600").split('x')

                except ValueError:
                    size = (800, 600)

                dialog = EditorDialog(
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
        dialog : gem.windows.EditorDialog
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

        if widget == self.item_toolbar_add_console:
            console = None

        elif self.__current_menu_row is not None:
            console = self.__current_menu_row.console

            previous_id = console.id

        dialog = ConsolePreferences(
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

                if widget == self.item_toolbar_add_console:

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
                    if len(console.get_games()) == 1:
                        text = _("1 game")
                    elif len(console.get_games()) > 1:
                        text = _("%d games") % len(console.get_games())

                    self.__current_menu_row.set_tooltip_text(text)

                    # Console flag selectors
                    self.item_consoles_favorite.set_active(console.favorite)
                    self.item_consoles_recursive.set_active(console.recursive)

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

        if widget == self.item_toolbar_add_emulator:
            emulator = None

        elif self.__current_menu_row is not None:
            emulator = self.__current_menu_row.console.emulator

            previous_id = emulator.id

            # Retrieve the correct emulator instance from api
            emulator = self.api.get_emulator(previous_id)

        dialog = EmulatorPreferences(self, emulator, self.api.emulators)

        if dialog.run() == Gtk.ResponseType.APPLY:

            if emulator is not None:
                self.logger.debug("Save %s modifications" % emulator.name)

            data = dialog.save()

            if data is not None:

                if emulator is not None:
                    self.api.delete_emulator(previous_id)

                emulator = self.api.add_emulator(data["name"], data.items())

                if not widget == self.item_toolbar_add_emulator:

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

                if widget == self.item_toolbar_add_emulator:

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

                    self.item_consoles_config.set_sensitive(status)

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

                    dialog = EditorDialog(
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

            dialog = QuestionDialog(
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
        self.model_games_list.clear()
        self.model_games_grid.clear()

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
        if len(console.get_games()) == 1:
            text = _("1 game")
        elif len(console.get_games()) > 1:
            text = _("%d games") % len(console.get_games())

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
            filter_text = \
                self.entry_toolbar_consoles_filters.get_text().strip().lower()

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

        if widget == self.item_toolbar_hide_empty_console:

            self.hide_empty_console = not self.config.getboolean(
                "gem", "hide_empty_console", fallback=False)

            self.config.modify(
                "gem", "hide_empty_console", self.hide_empty_console)
            self.config.update()

            self.item_toolbar_hide_empty_console.set_active(
                self.hide_empty_console)

            self.__on_update_consoles()

        elif self.__current_menu_row is not None:

            if widget == self.item_consoles_recursive:
                self.__current_menu_row.console.recursive = \
                    not self.__current_menu_row.console.recursive

                self.api.write_object(self.__current_menu_row.console)

            elif widget == self.item_consoles_favorite:
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

                    self.item_consoles_config.set_sensitive(False)

                    # Check console emulator
                    if row.console.emulator is not None:
                        configuration = row.console.emulator.configuration

                        # Check emulator configurator
                        self.item_consoles_config.set_sensitive(
                            configuration is not None
                            and configuration.exists())

                    # Check console paths
                    if row.console.path is not None:
                        self.item_consoles_copy.set_sensitive(
                            row.console.path.exists())
                        self.item_consoles_open.set_sensitive(
                            row.console.path.exists())

                    self.item_consoles_reload.set_sensitive(
                        selected_row == row)

                    self.item_consoles_favorite.set_active(
                        row.console.favorite)
                    self.item_consoles_recursive.set_active(
                        row.console.recursive)

                    self.menu_consoles.popup_at_pointer(event)

                    status = True

        # Gdk.EventKey - Keyboard
        elif event.type == Gdk.EventType.KEY_RELEASE:
            if event.keyval == Gdk.KEY_Menu:
                row = widget.get_selected_row()

                if row is not None:
                    self.__current_menu_row = row

                    self.item_consoles_config.set_sensitive(False)

                    # Check console emulator
                    if row.console.emulator is not None:
                        configuration = row.console.emulator.configuration

                        # Check emulator configurator
                        self.item_consoles_config.set_sensitive(
                            configuration is not None
                            and configuration.exists())

                    self.item_consoles_reload.set_sensitive(
                        selected_row == row)

                    self.item_consoles_favorite.set_active(
                        row.console.favorite)
                    self.item_consoles_recursive.set_active(
                        row.console.recursive)

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

        # Get current thread id
        current_thread_id = self.list_thread

        self.game_path = dict()

        # ------------------------------------
        #   Check errors
        # ------------------------------------

        self.infobar.set_visible(False)

        if console.emulator is None:
            self.logger.warning(
                "Cannot find emulator for %s" % console.name)

            self.infobar.set_visible(True)

            self.infobar.set_message_type(Gtk.MessageType.WARNING)
            self.label_infobar.set_markup(
                _("There is no default emulator set for this console"))

        elif not console.emulator.exists:
            self.logger.warning(
                "%s emulator not exist" % console.emulator.name)

            self.infobar.set_visible(True)

            self.infobar.set_message_type(Gtk.MessageType.ERROR)
            self.label_infobar.set_markup(
                _("<b>%s</b> cannot been found on your system") % (
                    console.emulator.name))

        # ------------------------------------
        #   Load data
        # ------------------------------------

        self.scroll_games_list.set_visible(False)
        self.scroll_games_grid.set_visible(False)

        self.scroll_games_placeholder.set_visible(True)

        self.model_games_list.clear()
        self.model_games_grid.clear()

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

            if self.button_toolbar_list.get_active():
                self.scroll_games_list.set_visible(True)
                self.treeview_games.show_all()

            if self.button_toolbar_grid.get_active():
                self.scroll_games_grid.set_visible(True)
                self.iconview_games.show_all()

            self.scroll_games_placeholder.set_visible(False)

            self.progress_statusbar.show()

        else:
            self.scroll_sidebar.set_visible(False)

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

                self.progress_statusbar.set_text("%d/%d" % (index, len(games)))
                self.progress_statusbar.set_fraction(index / len(games))

                self.treeview_games.thaw_child_notify()
                yield True
                self.treeview_games.freeze_child_notify()

        # Restore options for packages treeviews
        self.treeview_games.thaw_child_notify()

        self.progress_statusbar.hide()

        self.set_informations_headerbar()

        # ------------------------------------
        #   Timer - Debug
        # ------------------------------------

        delta = (datetime.now() - started).total_seconds()

        if len(console.get_games()) == 0:
            text = "No game available for %s" % console.name

        elif len(console.get_games()) == 1:
            text = "Append 1 game for %s in %s second(s)" % (
                console.name, delta)

        elif len(console.get_games()) >= 2:
            text = "Append %d games for %s in %s second(s)" % (
                len(console.get_games()), console.name, delta)

        self.logger.debug(text)

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

    def __on_selected_game(self, treeview, event):
        """ Select a game

        This function occurs when the user select a game in the games treeview

        Parameters
        ----------
        treeview : Gtk.Treeview
            Object which receive signal
        event : Gdk.EventButton or Gdk.EventKey
            Event which triggered this signal
        """

        # ----------------------------------------
        #   Mouse events
        # ----------------------------------------

        run_game = False

        # Set selection from cursor position
        if event.type == Gdk.EventType.BUTTON_PRESS:
            selection = treeview.get_path_at_pos(int(event.x), int(event.y))

            if selection is not None:

                if treeview == self.iconview_games:
                    self.iconview_games.select_path(selection)

                # Avoid to click on treeview header
                elif event.window == treeview.get_bin_window():
                    self.treeview_games.set_cursor(selection[0], None, False)

            # Remove view selections
            else:
                self.iconview_games.unselect_all()
                self.treeview_games.get_selection().unselect_all()

        # Mouse - Double click with left mouse button
        if event.type == Gdk.EventType._2BUTTON_PRESS and event.button == 1:

            if treeview == self.iconview_games:
                run_game = True

            # Avoid to click on treeview header
            elif event.window == treeview.get_bin_window():
                run_game = True

        # ----------------------------------------
        #   Game selected
        # ----------------------------------------

        # Current selected game
        game = self.__on_retrieve_selected_game()

        # No game has been choosen (when the user click in the empty view area)
        if game is None:
            # Unselect both games views
            self.treeview_games.get_selection().unselect_all()
            self.iconview_games.unselect_all()

            # Reset sidebar widgets and menus entries
            self.sensitive_interface()
            self.set_informations()

        # A new game has been selected
        elif not self.selection["game"] == game:
            # Synchronize selection between both games views
            self.__on_synchronize_game_selection(treeview, game)

            # Update game informations and widgets
            self.sensitive_interface()
            self.set_informations()

        # Store game instance
        self.selection["game"] = game

        # The user has do a specific action to launch current game
        if run_game:
            self.__on_game_launch()

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

        # Show a tooltip when the main window is sentitive only
        if self.get_sensitive():

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
        if self.button_toolbar_grid.get_active():
            model = self.iconview_games.get_model()
            items = self.iconview_games.get_selected_items()

            if len(items) >= 1:
                treeiter = model.get_iter(items[0])

                if treeiter is not None:
                    return model.get_value(treeiter, Columns.Grid.OBJECT)

        # List view
        elif self.button_toolbar_list.get_active():
            selection = self.treeview_games.get_selection()

            if selection is not None:
                model, treeiter = selection.get_selected()

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
                    self.treeview_games.get_selection().unselect_all()

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

        status = widget.get_active()

        if widget == self.button_toolbar_list:
            self.button_toolbar_grid.set_active(not status)

            self.item_menubar_list.set_active(status)

        elif widget == self.button_toolbar_grid:
            self.button_toolbar_list.set_active(not status)

            self.item_menubar_grid.set_active(status)

        elif widget == self.item_menubar_list:
            self.button_toolbar_list.set_active(status)

        elif widget == self.item_menubar_grid:
            self.button_toolbar_grid.set_active(status)

        if not self.scroll_games_placeholder.get_visible():
            self.scroll_games_list.set_visible(
                self.button_toolbar_list.get_active())
            self.scroll_games_grid.set_visible(
                self.button_toolbar_grid.get_active())

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
            model, treeiter = \
                self.treeview_games.get_selection().get_selected()

            if treeiter is not None:
                treeview_name = model.get_value(treeiter, Columns.List.NAME)

                if not treeview_name == name:
                    self.treeview_games.get_selection().unselect_iter(treeiter)
                    self.selection["game"] = None

                    self.sensitive_interface()
                    self.set_informations()

                    return False

        return True

    def __on_game_launch_button_update(self, status):
        """ Update game launch button

        Parameters
        ----------
        status : bool
            The game status
        """

        label = self.button_toolbar_launch.get_label()

        if status and not label == _("Play"):
            self.button_toolbar_launch.set_label(
                _("Play"))
            self.button_toolbar_launch.set_tooltip_text(
                _("Launch selected game"))
            self.button_toolbar_launch.get_style_context().remove_class(
                "destructive-action")
            self.button_toolbar_launch.get_style_context().add_class(
                "suggested-action")

        elif not status and not label == _("Stop"):
            self.button_toolbar_launch.set_label(
                _("Stop"))
            self.button_toolbar_launch.set_tooltip_text(
                _("Stop selected game"))
            self.button_toolbar_launch.get_style_context().remove_class(
                "suggested-action")
            self.button_toolbar_launch.get_style_context().add_class(
                "destructive-action")

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
                        fullscreen=self.button_toolbar_fullscreen.get_active())

                    # Save thread references
                    self.threads[game.id] = thread

                    # Launch thread
                    thread.start()

                    self.__on_game_launch_button_update(False)
                    self.button_toolbar_launch.set_sensitive(True)

                    self.item_game_output.set_sensitive(True)
                    self.button_toolbar_output.set_sensitive(True)
                    self.item_menubar_game_output.set_sensitive(True)

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

        path = Folders.LOCAL.joinpath("ongamestarted")

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
                self.button_toolbar_screenshots.set_sensitive(True)
                self.item_menubar_game_screenshots.set_sensitive(True)

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
            self.button_toolbar_launch.set_sensitive(True)

            self.item_game_launch.set_sensitive(True)
            self.item_game_database.set_sensitive(True)
            self.item_game_remove.set_sensitive(True)

            self.item_menubar_game_launch.set_sensitive(True)
            self.item_menubar_database.set_sensitive(True)
            self.item_menubar_delete.set_sensitive(True)

            self.__current_tooltip = None

            if game.emulator is not None:

                # Check extension and emulator for GBA game on mednafen
                if self.__mednafen_status and game.extension == ".gba":

                    if "mednafen" in str(game.emulator.binary):
                        self.item_game_mednafen.set_sensitive(True)
                        self.item_menubar_mednafen.set_sensitive(True)

            # Avoid to launch the game again when use Enter in game terminate
            # self.treeview_games.get_selection().unselect_all()

        # ----------------------------------------
        #   Manage thread
        # ----------------------------------------

        # Remove this game from threads list
        if game.id in self.threads:
            self.logger.debug("Remove %s from process cache" % game.name)

            del self.threads[game.id]

        if len(self.threads) == 0:
            self.item_menubar_preferences.set_sensitive(True)

        # ----------------------------------------
        #   Manage script
        # ----------------------------------------

        # Remove this script from threads list
        if game.id in self.scripts:
            self.logger.debug("Remove %s from scripts cache" % game.name)

            del self.scripts[game.id]

        path = Folders.LOCAL.joinpath("ongamestopped")

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

            dialog = RenameDialog(self, game)

            if dialog.run() == Gtk.ResponseType.APPLY:

                new_name = dialog.get_name()

                # Check if game name has been changed
                if not new_name == game.name:
                    self.logger.info("Rename %(old)s to %(new)s" % {
                        "old": game.name,
                        "new": dialog.get_name()
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
                    if self.button_toolbar_grid.get_active():
                        self.iconview_games.grab_focus()

                    elif self.button_toolbar_list.get_active():
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

                dialog = MaintenanceDialog(self, game)

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
                            self.button_toolbar_output.set_sensitive(False)
                            self.item_game_output.set_sensitive(False)
                            self.item_menubar_game_output.set_sensitive(False)

                        self.item_game_favorite.set_active(False)
                        self.item_menubar_game_favorite.set_active(False)

                        self.item_game_multiplayer.set_active(False)
                        self.item_menubar_game_multiplayer.set_active(False)

                        self.item_game_finish.set_active(False)
                        self.item_menubar_game_finish.set_active(False)

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

                dialog = DeleteDialog(self, game)

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
                            if len(console.get_games()) == 1:
                                text = _("1 game")
                            elif len(console.get_games()) > 1:
                                text = _("%d games") % len(console.get_games())

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
                    self.iconview_games.unselect_all()
                    self.treeview_games.get_selection().unselect_all()

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

            dialog = DuplicateDialog(self, game)

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

            dialog = ParametersDialog(self, game)

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

                    self.button_toolbar_screenshots.set_sensitive(True)
                    self.item_menubar_game_screenshots.set_sensitive(True)

                else:
                    self.set_game_data(
                        Columns.List.SCREENSHOT,
                        self.icons.get_translucent("screenshot"),
                        game.id)

                    self.button_toolbar_screenshots.set_sensitive(False)
                    self.item_menubar_game_screenshots.set_sensitive(False)

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

            dialog = EditorDialog(
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

        if self.item_game_mednafen.get_sensitive():

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

                dialog = MednafenDialog(self, game.name, content)

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

    def __on_game_marked_as_favorite(self, *args):
        """ Mark or unmark a game as favorite

        This function update the database when user change the game favorite
        status
        """

        self.__block_signals()

        game = self.__on_retrieve_selected_game()

        if game is not None:
            row, treepath, gridpath = self.game_path[game.id]

            if not game.favorite:
                self.logger.debug("Mark %s as favorite" % game.name)

                icon = self.icons.get("favorite")

                game.favorite = True

            else:
                self.logger.debug("Unmark %s as favorite" % game.name)

                icon = self.icons.get_translucent("favorite")

                game.favorite = False

            self.model_games_list.set_value(
                treepath, Columns.List.FAVORITE, icon)
            self.model_games_list.set_value(
                treepath, Columns.List.OBJECT, game)

            self.model_games_grid.set_value(
                gridpath, Columns.Grid.OBJECT, game)

            # Update game from database
            self.api.update_game(game)

            self.item_menubar_game_favorite.set_active(game.favorite)
            self.item_game_favorite.set_active(game.favorite)

            self.check_selection()

        else:
            self.item_menubar_game_favorite.set_active(False)
            self.item_game_favorite.set_active(False)

        self.filters_update(None)

        self.__unblock_signals()

    def __on_game_marked_as_multiplayer(self, *args):
        """ Mark or unmark a game as multiplayer

        This function update the database when user change the game
        multiplayers status
        """

        self.__block_signals()

        game = self.__on_retrieve_selected_game()

        if game is not None:
            row, treepath, gridpath = self.game_path[game.id]

            if not game.multiplayer:
                self.logger.debug("Mark %s as multiplayers" % game.name)

                icon = self.icons.get("multiplayer")

                game.multiplayer = True

            else:
                self.logger.debug("Unmark %s as multiplayers" % game.name)

                icon = self.icons.get_translucent("multiplayer")

                game.multiplayer = False

            self.model_games_list.set_value(
                treepath, Columns.List.MULTIPLAYER, icon)
            self.model_games_list.set_value(
                treepath, Columns.List.OBJECT, game)

            self.model_games_grid.set_value(
                gridpath, Columns.Grid.OBJECT, game)

            # Update game from database
            self.api.update_game(game)

            self.item_menubar_game_multiplayer.set_active(game.multiplayer)
            self.item_game_multiplayer.set_active(game.multiplayer)

            self.check_selection()

        else:
            self.item_menubar_game_multiplayer.set_active(False)
            self.item_game_multiplayer.set_active(False)

        self.filters_update(None)

        self.__unblock_signals()

    def __on_game_marked_as_finish(self, *args):
        """ Mark or unmark a game as finish

        This function update the database when user change the game finish
        status
        """

        self.__block_signals()

        game = self.__on_retrieve_selected_game()

        if game is not None:
            row, treepath, gridpath = self.game_path[game.id]

            if not game.finish:
                self.logger.debug("Mark %s as finish" % game.name)

                icon = self.icons.get("finish")

                game.finish = True

            else:
                self.logger.debug("Unmark %s as finish" % game.name)

                icon = self.icons.get_translucent("finish")

                game.finish = False

            self.model_games_list.set_value(
                treepath, Columns.List.FINISH, icon)
            self.model_games_list.set_value(
                treepath, Columns.List.OBJECT, game)

            self.model_games_grid.set_value(
                gridpath, Columns.Grid.OBJECT, game)

            # Update game from database
            self.api.update_game(game)

            self.item_menubar_game_finish.set_active(game.finish)
            self.item_game_finish.set_active(game.finish)

            self.check_selection()

        else:
            self.item_menubar_game_finish.set_active(False)
            self.item_game_finish.set_active(False)

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

            if widget in [self.item_menubar_score_up,
                          self.item_game_score_up]:

                if game.score < 5:
                    game.score += 1

                    modification = True

            elif widget in [self.item_menubar_score_down,
                            self.item_game_score_down]:

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

                dialog = EditorDialog(
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

            dialog = CoverDialog(self, game)

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

        model, treeiter = self.treeview_games.get_selection().get_selected()

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
                    icon = Folders.LOCAL.joinpath(
                        "icons", '%s.png' % str(icon))

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
                          "futher details."), Icons.ERROR)

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

                if widget == self.treeview_games:
                    model, treeiter = widget.get_selection().get_selected()

                elif widget == self.iconview_games:
                    model = widget.get_model()
                    items = widget.get_selected_items()

                    if len(items) >= 1:
                        treeiter = model.get_iter(items[0])

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

        if not self.__fullscreen_status:
            self.logger.debug("Switch game launch to windowed mode")

            self.image_toolbar_fullscreen.set_from_icon_name(
                Icons.Symbolic.RESTORE, Gtk.IconSize.SMALL_TOOLBAR)
            self.button_toolbar_fullscreen.get_style_context().remove_class(
                "suggested-action")

        else:
            self.logger.debug("Switch game launch to fullscreen mode")

            self.image_toolbar_fullscreen.set_from_icon_name(
                Icons.Symbolic.FULLSCREEN, Gtk.IconSize.SMALL_TOOLBAR)
            self.button_toolbar_fullscreen.get_style_context().add_class(
                "suggested-action")

        self.button_toolbar_fullscreen.set_active(self.__fullscreen_status)
        self.item_menubar_game_fullscreen.set_active(self.__fullscreen_status)

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

        self.item_menubar_dark_theme.set_active(dark_theme_status)

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

        self.item_menubar_sidebar_status.set_active(sidebar_status)

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

        self.sidebar_image = None

        if widget is not None:
            status = self.item_menubar_sidebar_right.get_active()

            self.sidebar_orientation = "vertical"
            if status:
                self.sidebar_orientation = "horizontal"

            self.config.modify(
                "gem", "sidebar_orientation", self.sidebar_orientation)
            self.config.update()

        # Right-side sidebar
        if self.sidebar_orientation == "horizontal" \
           and not self.__current_orientation == Gtk.Orientation.HORIZONTAL:

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
        elif self.sidebar_orientation == "vertical" \
           and not self.__current_orientation == Gtk.Orientation.VERTICAL:

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

        self.item_menubar_statusbar_status.set_active(statusbar_status)

        self.__unblock_signals()

    def __on_copy_path_to_clipboard(self, widget):
        """ Copy path to clipboard

        Parameters
        ----------
        widget : Gtk.Widget
            object which received the signal
        """

        path = None

        if widget in (self.item_menubar_copy, self.item_game_copy):
            game = self.__on_retrieve_selected_game()

            if game is not None and game.path.parent.exists():
                path = game.path

        elif widget == self.item_consoles_copy:

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

        if widget in (self.item_menubar_open, self.item_game_open):
            game = self.__on_retrieve_selected_game()

            if game is not None and game.path.parent.exists():
                path = game.path.parent

        elif widget == self.item_consoles_open:

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

            dialog = DNDConsoleDialog(self, filepaths)

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

        self.progress_statusbar.set_text(None)
        self.progress_statusbar.show()

        yield True

        validate_index = int()
        progress_index = int()

        # Manage files
        for path, console in data.items():
            progress_index += 1

            self.progress_statusbar.set_fraction(progress_index / len(data))

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
                    if len(console.get_games()) == 1:
                        text = _("1 game")
                    elif len(console.get_games()) > 1:
                        text = _("%d games") % len(console.get_games())

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
                        if self.button_toolbar_grid.get_active():
                            self.scroll_games_grid.set_visible(True)
                            self.iconview_games.show_all()

                        # List view
                        elif self.button_toolbar_list.get_active():
                            self.scroll_games_list.set_visible(True)
                            self.treeview_games.show_all()

                        self.scroll_games_placeholder.set_visible(False)

        # Reset mouse cursor
        self.get_window().set_cursor(
            Gdk.Cursor.new_from_name(self.window_display, "default"))

        # Show an informative dialog
        text = _("No game has been added")

        if validate_index == 1:
            text = _("1 game has been added")

        elif validate_index > 1:
            text = _("%d games has been added") % validate_index

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

        for widget, signal in self.__signals_storage.items():
            widget.handler_block(signal)

    def __unblock_signals(self):
        """ Unblock check button signals
        """

        for widget, signal in self.__signals_storage.items():
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
            log_path = Folders.LOCAL.joinpath("logs", game.id + ".log")

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
                    collection_path = Folders.LOCAL.joinpath(
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
