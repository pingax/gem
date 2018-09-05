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
from gem.engine.api import *
from gem.engine.utils import *
from gem.engine.lib.configuration import Configuration

from gem.ui import *
from gem.ui.data import *
from gem.ui.utils import *

from gem.ui.widgets.game import GameThread
from gem.ui.widgets.addon import AddonThread
from gem.ui.widgets.widgets import ListBoxPopover
from gem.ui.widgets.widgets import ListBoxSelector

from gem.ui.dialog import *

from gem.ui.preferences.interface import PreferencesWindow

# Random
from random import randint

# Regex
from re import match
from re import IGNORECASE

# System
from shlex import split as shlex_split
from shutil import move as rename
from platform import system

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
        "game-started": (SIGNAL_RUN_FIRST, None, [object]),
        "game-terminate": (SIGNAL_RUN_LAST, None, [object]),
    }

    def __init__(self, api):
        """ Constructor

        Parameters
        ----------
        api : gem.engine.api.GEM
            GEM API instance

        Raises
        ------
        TypeError
            if api type is not gem.engine.api.GEM
        """

        if not type(api) is GEM:
            raise TypeError("Wrong type for api, expected gem.engine.api.GEM")

        Gtk.ApplicationWindow.__init__(self)

        # ------------------------------------
        #   Initialize variables
        # ------------------------------------

        # Generate a title from GEM informations
        self.title = "%s - %s (%s)" % (GEM.Name, GEM.Version, GEM.CodeName)

        # Store thread id for game listing
        self.list_thread = int()

        # Store normal icons with icon name as key
        self.icons = dict()
        # Store alternative icons with icon name as key
        self.alternative = dict()
        # Store started notes with note file path as key
        self.notes = dict()
        # Store started threads with basename game file without extension as key
        self.threads = dict()
        # Store modules functions
        self.modules = dict()
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
        # Store sidebar description ordre
        self.sidebar_keys = [
            ("played", _("Launch")),
            ("play_time", _("Play time")),
            ("last_play", _("Last launch")),
            ("last_time", _("Last play time"))
        ]
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

        # Check mednafen status
        self.__mednafen_status = self.check_mednafen()

        # ------------------------------------
        #   Initialize API
        # ------------------------------------

        # GEM API
        self.api = api

        # Quick access to API logger
        self.logger = api.logger

        # ------------------------------------
        #   Initialize icons
        # ------------------------------------

        # Get user icon theme
        self.icons_theme = Gtk.IconTheme.get_default()

        self.icons_theme.append_search_path(get_data(path_join("icons", "ui")))

        # Generate symbolic icons class
        for key, value in Icons.__dict__.items():
            if not key.startswith("__") and not key.endswith("__"):
                setattr(Icons.Symbolic, key, "%s-symbolic" % value)

        self.icons_data = {
            "save": Icons.Floppy,
            "snap": Icons.Photos,
            "except": Icons.Properties,
            "warning": Icons.Warning,
            "favorite": Icons.Favorite,
            "multiplayer": Icons.Users,
            "finish": Icons.Smile,
            "unfinish": Icons.Uncertain,
            "no-starred": Icons.NoStarred,
            "starred": Icons.Starred
        }

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

        self.shortcuts_map = Gtk.AccelMap()

        # ------------------------------------
        #   Targets
        # ------------------------------------

        self.targets = [ Gtk.TargetEntry.new("text/uri-list", 0, 1337) ]

        # ------------------------------------
        #   Toolbar size constants
        # ------------------------------------

        self.toolbar_sizes = {
            "menu": Gtk.IconSize.MENU,
            "small-toolbar": Gtk.IconSize.SMALL_TOOLBAR,
            "large-toolbar": Gtk.IconSize.LARGE_TOOLBAR,
            "button": Gtk.IconSize.BUTTON,
            "dnd": Gtk.IconSize.DND,
            "dialog": Gtk.IconSize.DIALOG
        }

        # ------------------------------------
        #   Prepare interface
        # ------------------------------------

        # Init widgets
        self.__init_widgets()

        # Init packing
        self.__init_packing()

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
        """ Initialize interface widgets
        """

        # ------------------------------------
        #   Main window
        # ------------------------------------

        self.set_title(self.title)

        self.set_icon_name(GEM.Icon)
        self.set_default_icon_name(Icons.Gaming)

        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_wmclass(GEM.Acronym.upper(), GEM.Acronym.lower())

        self.add_accel_group(self.shortcuts_group)

        self.drag_dest_set(
            Gtk.DestDefaults.MOTION | Gtk.DestDefaults.DROP, self.targets,
            Gdk.DragAction.COPY)

        # ------------------------------------
        #   Clipboard
        # ------------------------------------

        self.clipboard = Gtk.Clipboard.get(Gdk.Atom.intern("CLIPBOARD", False))

        # ------------------------------------
        #   Grid
        # ------------------------------------

        self.grid = Gtk.Box()

        self.grid_main_popover = Gtk.Grid()

        self.grid_consoles = Gtk.Box()
        self.grid_consoles_item = Gtk.Box()
        self.grid_consoles_popover = Gtk.Grid()

        self.grid_filters = Gtk.Box()
        self.grid_filters_popover = Gtk.Grid()

        self.grid_game_launch = Gtk.Box()
        self.grid_game_options = Gtk.Box()

        self.grid_infobar = Gtk.Box()

        self.grid_games = Gtk.Box()
        self.grid_games_placeholder = Gtk.Box()

        self.grid_sidebar = Gtk.Grid()
        self.grid_sidebar_title = Gtk.Box()
        self.grid_sidebar_tab_tags = Gtk.Box()
        self.grid_sidebar_tab_informations = Gtk.Box()
        self.grid_sidebar_informations = Gtk.Grid()

        # Properties
        self.grid.set_orientation(Gtk.Orientation.VERTICAL)

        self.grid_main_popover.set_border_width(12)
        self.grid_main_popover.set_row_spacing(6)
        self.grid_main_popover.set_column_spacing(12)
        self.grid_main_popover.set_column_homogeneous(False)

        Gtk.StyleContext.add_class(
            self.grid_consoles.get_style_context(), "linked")
        self.grid_consoles.set_spacing(-1)
        self.grid_consoles.set_orientation(Gtk.Orientation.HORIZONTAL)

        self.grid_consoles_item.set_spacing(12)

        self.grid_consoles_popover.set_border_width(12)
        self.grid_consoles_popover.set_row_spacing(6)
        self.grid_consoles_popover.set_column_spacing(12)
        self.grid_consoles_popover.set_column_homogeneous(False)

        Gtk.StyleContext.add_class(
            self.grid_filters.get_style_context(), "linked")
        self.grid_filters.set_spacing(-1)
        self.grid_filters.set_orientation(Gtk.Orientation.HORIZONTAL)

        self.grid_filters_popover.set_border_width(12)
        self.grid_filters_popover.set_row_spacing(6)
        self.grid_filters_popover.set_column_spacing(12)

        Gtk.StyleContext.add_class(
            self.grid_game_launch.get_style_context(), "linked")
        self.grid_game_launch.set_spacing(-1)
        self.grid_game_launch.set_orientation(Gtk.Orientation.HORIZONTAL)

        Gtk.StyleContext.add_class(
            self.grid_game_options.get_style_context(), "linked")
        self.grid_game_options.set_spacing(-1)
        self.grid_game_options.set_orientation(Gtk.Orientation.HORIZONTAL)

        self.grid_games.set_orientation(Gtk.Orientation.VERTICAL)

        self.grid_games_placeholder.set_spacing(12)
        self.grid_games_placeholder.set_border_width(18)
        self.grid_games_placeholder.set_orientation(Gtk.Orientation.VERTICAL)

        self.grid_sidebar.set_column_spacing(12)
        self.grid_sidebar.set_border_width(6)
        self.grid_sidebar.set_row_spacing(6)

        self.grid_sidebar_title.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.grid_sidebar_title.set_border_width(6)
        self.grid_sidebar_title.set_hexpand(True)
        self.grid_sidebar_title.set_spacing(6)

        self.grid_sidebar_tab_informations.set_orientation(
            Gtk.Orientation.HORIZONTAL)
        self.grid_sidebar_tab_informations.set_spacing(6)

        self.grid_sidebar_tab_tags.set_orientation(
            Gtk.Orientation.HORIZONTAL)
        self.grid_sidebar_tab_tags.set_spacing(6)

        self.grid_sidebar_informations.set_column_homogeneous(True)
        self.grid_sidebar_informations.set_column_spacing(12)
        self.grid_sidebar_informations.set_border_width(18)
        self.grid_sidebar_informations.set_row_spacing(6)

        # ------------------------------------
        #   Headerbar
        # ------------------------------------

        self.headerbar = Gtk.HeaderBar()

        self.headerbar_item_launch = Gtk.Button()

        self.headerbar_image_menu = Gtk.Image()
        self.headerbar_item_menu = Gtk.MenuButton()

        self.headerbar_image_fullscreen = Gtk.Image()
        self.headerbar_item_fullscreen = Gtk.ToggleButton()

        self.popover_menu = Gtk.Popover()

        # Properties
        self.headerbar.set_title(self.title)
        self.headerbar.set_subtitle(str())

        self.headerbar_item_launch.set_label(_("Play"))
        self.headerbar_item_launch.set_tooltip_text(
            _("Launch selected game"))
        self.headerbar_item_launch.get_style_context().add_class(
            "suggested-action")

        self.headerbar_item_menu.set_tooltip_text(_("Main menu"))
        self.headerbar_item_menu.set_use_popover(True)

        self.headerbar_item_fullscreen.set_tooltip_text(
            _("Alternate game fullscreen mode"))

        self.popover_menu.set_modal(True)

        # ------------------------------------
        #   Headerbar - Main menu
        # ------------------------------------

        self.menu_image_addons = Gtk.Image()
        self.menu_item_addons = Gtk.Button()

        self.menu_image_preferences = Gtk.Image()
        self.menu_item_preferences = Gtk.Button()

        self.menu_image_about = Gtk.Image()
        self.menu_item_about = Gtk.Button()

        self.menu_image_quit = Gtk.Image()
        self.menu_item_quit = Gtk.Button()

        self.menu_image_gem_log = Gtk.Image()
        self.menu_item_gem_log = Gtk.Button()

        self.menu_item_main_display = Gtk.Label()

        self.menu_label_dark_theme = Gtk.Label()
        self.menu_item_dark_theme = Gtk.Switch()

        self.menu_label_sidebar = Gtk.Label()
        self.menu_item_sidebar = Gtk.Switch()

        self.menu_label_statusbar = Gtk.Label()
        self.menu_item_statusbar = Gtk.Switch()

        # Properties
        self.menu_item_addons.set_label(_("Addons"))
        self.menu_item_addons.set_relief(Gtk.ReliefStyle.NONE)
        self.menu_item_addons.set_image(self.menu_image_addons)
        self.menu_item_addons.set_use_underline(True)
        self.menu_item_addons.set_alignment(0, 0.5)

        self.menu_image_addons.set_valign(Gtk.Align.CENTER)
        self.menu_image_addons.set_margin_right(6)

        self.menu_item_preferences.set_label(_("Preferences"))
        self.menu_item_preferences.set_relief(Gtk.ReliefStyle.NONE)
        self.menu_item_preferences.set_image(self.menu_image_preferences)
        self.menu_item_preferences.set_use_underline(True)
        self.menu_item_preferences.set_alignment(0, 0.5)

        self.menu_image_preferences.set_valign(Gtk.Align.CENTER)
        self.menu_image_preferences.set_margin_right(6)

        self.menu_item_gem_log.set_label(_("Output log"))
        self.menu_item_gem_log.set_relief(Gtk.ReliefStyle.NONE)
        self.menu_item_gem_log.set_image(self.menu_image_gem_log)
        self.menu_item_gem_log.set_use_underline(True)
        self.menu_item_gem_log.set_alignment(0, 0.5)

        self.menu_image_gem_log.set_valign(Gtk.Align.CENTER)
        self.menu_image_gem_log.set_margin_right(6)

        self.menu_item_about.set_label(_("About"))
        self.menu_item_about.set_relief(Gtk.ReliefStyle.NONE)
        self.menu_item_about.set_image(self.menu_image_about)
        self.menu_item_about.set_use_underline(True)
        self.menu_item_about.set_alignment(0, 0.5)

        self.menu_image_about.set_valign(Gtk.Align.CENTER)
        self.menu_image_about.set_margin_right(6)

        self.menu_item_quit.set_label(_("Quit"))
        self.menu_item_quit.set_relief(Gtk.ReliefStyle.NONE)
        self.menu_item_quit.set_image(self.menu_image_quit)
        self.menu_item_quit.set_use_underline(True)
        self.menu_item_quit.set_alignment(0, 0.5)

        self.menu_image_quit.set_valign(Gtk.Align.CENTER)
        self.menu_image_quit.set_margin_right(6)

        self.menu_item_main_display.set_label(_("Display"))
        self.menu_item_main_display.set_halign(Gtk.Align.START)
        self.menu_item_main_display.set_valign(Gtk.Align.CENTER)
        self.menu_item_main_display.get_style_context().add_class("dim-label")

        self.menu_label_dark_theme.set_label(_("Dark theme"))
        self.menu_label_dark_theme.set_halign(Gtk.Align.START)
        self.menu_label_dark_theme.set_valign(Gtk.Align.CENTER)
        self.menu_label_dark_theme.set_hexpand(True)

        self.menu_item_dark_theme.set_valign(Gtk.Align.END)

        self.menu_label_sidebar.set_margin_top(12)
        self.menu_label_sidebar.set_label(_("Sidebar"))
        self.menu_label_sidebar.set_halign(Gtk.Align.START)
        self.menu_label_sidebar.set_valign(Gtk.Align.CENTER)
        self.menu_label_sidebar.set_hexpand(True)

        self.menu_item_sidebar.set_valign(Gtk.Align.END)
        self.menu_item_sidebar.set_margin_top(12)

        self.menu_label_statusbar.set_label(_("Statusbar"))
        self.menu_label_statusbar.set_halign(Gtk.Align.START)
        self.menu_label_statusbar.set_valign(Gtk.Align.CENTER)
        self.menu_label_statusbar.set_hexpand(True)

        self.menu_item_statusbar.set_valign(Gtk.Align.END)

        # ------------------------------------
        #   Menubar
        # ------------------------------------

        self.menubar = Gtk.MenuBar()

        self.menubar_item_main = Gtk.MenuItem()
        self.menubar_item_game = Gtk.MenuItem()
        self.menubar_item_edit = Gtk.MenuItem()
        self.menubar_item_tools = Gtk.MenuItem()
        self.menubar_item_help = Gtk.MenuItem()

        # Properties
        self.menubar_item_main.set_label(_("_GEM"))
        self.menubar_item_main.set_use_underline(True)
        self.menubar_item_game.set_label(_("_Game"))
        self.menubar_item_game.set_use_underline(True)
        self.menubar_item_edit.set_label(_("_Edit"))
        self.menubar_item_edit.set_use_underline(True)
        self.menubar_item_help.set_label(_("_Help"))
        self.menubar_item_help.set_use_underline(True)

        # ------------------------------------
        #   Menubar - Main items
        # ------------------------------------

        self.menubar_main_menu = Gtk.Menu()

        self.menubar_main_item_dark_theme = Gtk.CheckMenuItem()
        self.menubar_main_item_sidebar = Gtk.CheckMenuItem()
        self.menubar_main_item_statusbar = Gtk.CheckMenuItem()

        self.menubar_main_item_preferences = Gtk.MenuItem()
        self.menubar_main_item_addons = Gtk.MenuItem()
        self.menubar_main_item_log = Gtk.MenuItem()

        self.menubar_main_item_quit = Gtk.MenuItem()

        # Properties
        self.menubar_main_item_dark_theme.set_label(
            _("Use _dark theme"))
        self.menubar_main_item_dark_theme.set_use_underline(True)

        self.menubar_main_item_sidebar.set_label(
            _("Show _sidebar"))
        self.menubar_main_item_sidebar.set_use_underline(True)

        self.menubar_main_item_statusbar.set_label(
            _("Show _statusbar"))
        self.menubar_main_item_statusbar.set_use_underline(True)

        self.menubar_main_item_preferences.set_label(
            "%s…" % _("_Preferences"))
        self.menubar_main_item_preferences.set_use_underline(True)

        self.menubar_main_item_addons.set_label(
            "%s…" % _("_Addons"))
        self.menubar_main_item_addons.set_use_underline(True)

        self.menubar_main_item_log.set_label(
            "%s…" % _("_Log"))
        self.menubar_main_item_log.set_use_underline(True)

        self.menubar_main_item_quit.set_label(
            _("_Quit"))
        self.menubar_main_item_quit.set_use_underline(True)

        # ------------------------------------
        #   Menubar - Game items
        # ------------------------------------

        self.menubar_game_menu = Gtk.Menu()

        self.menubar_game_item_launch = Gtk.MenuItem()
        self.menubar_game_item_screenshots = Gtk.MenuItem()
        self.menubar_game_item_output = Gtk.MenuItem()
        self.menubar_game_item_notes = Gtk.MenuItem()
        self.menubar_game_item_properties = Gtk.MenuItem()

        self.menubar_game_item_favorite = Gtk.CheckMenuItem()
        self.menubar_game_item_multiplayer = Gtk.CheckMenuItem()
        self.menubar_game_item_finish = Gtk.CheckMenuItem()
        self.menubar_game_item_fullscreen = Gtk.CheckMenuItem()

        # Properties
        self.menubar_game_item_launch.set_label(
            _("_Launch"))
        self.menubar_game_item_launch.set_use_underline(True)

        self.menubar_game_item_favorite.set_label(
            _("_Favorite"))
        self.menubar_game_item_favorite.set_use_underline(True)

        self.menubar_game_item_multiplayer.set_label(
            _("_Multiplayer"))
        self.menubar_game_item_multiplayer.set_use_underline(True)

        self.menubar_game_item_finish.set_label(
            _("_Finish"))
        self.menubar_game_item_finish.set_use_underline(True)

        self.menubar_game_item_screenshots.set_label(
            "%s…" % _("_Screenshots"))
        self.menubar_game_item_screenshots.set_use_underline(True)

        self.menubar_game_item_output.set_label(
            "%s…" % _("Output _log"))
        self.menubar_game_item_output.set_use_underline(True)

        self.menubar_game_item_notes.set_label(
            "%s…" % _("_Notes"))
        self.menubar_game_item_notes.set_use_underline(True)

        self.menubar_game_item_properties.set_label(
            "%s…" % _("_Properties"))
        self.menubar_game_item_properties.set_use_underline(True)

        self.menubar_game_item_fullscreen.set_label(
            _("Fullscreen mode"))

        # ------------------------------------
        #   Menubar - Edit items
        # ------------------------------------

        self.menubar_edit_menu = Gtk.Menu()

        self.menubar_edit_item_rename = Gtk.MenuItem()
        self.menubar_edit_item_duplicate = Gtk.MenuItem()
        self.menubar_edit_item_copy = Gtk.MenuItem()
        self.menubar_edit_item_open = Gtk.MenuItem()
        self.menubar_edit_item_cover = Gtk.MenuItem()
        self.menubar_edit_item_desktop = Gtk.MenuItem()
        self.menubar_edit_item_database = Gtk.MenuItem()
        self.menubar_edit_item_delete = Gtk.MenuItem()
        self.menubar_edit_item_mednafen = Gtk.MenuItem()

        # Properties
        self.menubar_edit_item_rename.set_label(
            "%s…" % _("_Rename"))
        self.menubar_edit_item_rename.set_use_underline(True)

        self.menubar_edit_item_duplicate.set_label(
            "%s…" % _("_Duplicate"))
        self.menubar_edit_item_duplicate.set_use_underline(True)

        self.menubar_edit_item_copy.set_label(
            _("_Copy path"))
        self.menubar_edit_item_copy.set_use_underline(True)

        self.menubar_edit_item_open.set_label(
            _("_Open path"))
        self.menubar_edit_item_open.set_use_underline(True)

        self.menubar_edit_item_cover.set_label(
            "%s…" % _("Set game _cover"))
        self.menubar_edit_item_cover.set_use_underline(True)

        self.menubar_edit_item_desktop.set_label(
            _("_Generate a menu entry"))
        self.menubar_edit_item_desktop.set_use_underline(True)

        self.menubar_edit_item_database.set_label(
            "%s…" % _("_Reset data"))
        self.menubar_edit_item_database.set_use_underline(True)

        self.menubar_edit_item_delete.set_label(
            "%s…" % _("_Remove from disk"))
        self.menubar_edit_item_delete.set_use_underline(True)

        self.menubar_edit_item_mednafen.set_label(
            "%s…" % _("Specify a _memory type"))
        self.menubar_edit_item_mednafen.set_use_underline(True)

        # ------------------------------------
        #   Menubar - Edit - Score items
        # ------------------------------------

        self.menubar_edit_score = Gtk.Menu()
        self.menubar_edit_item_score = Gtk.MenuItem()

        self.menubar_edit_item_score_up = Gtk.MenuItem()
        self.menubar_edit_item_score_down = Gtk.MenuItem()
        self.menubar_edit_item_score_0 = Gtk.MenuItem()
        self.menubar_edit_item_score_1 = Gtk.MenuItem()
        self.menubar_edit_item_score_2 = Gtk.MenuItem()
        self.menubar_edit_item_score_3 = Gtk.MenuItem()
        self.menubar_edit_item_score_4 = Gtk.MenuItem()
        self.menubar_edit_item_score_5 = Gtk.MenuItem()

        # Properties
        self.menubar_edit_item_score.set_label(
            _("Score"))
        self.menubar_edit_item_score.set_use_underline(True)

        self.menubar_edit_item_score_up.set_label(
            _("Increase score"))
        self.menubar_edit_item_score_up.set_use_underline(True)

        self.menubar_edit_item_score_down.set_label(
            _("Decrease score"))
        self.menubar_edit_item_score_down.set_use_underline(True)

        self.menubar_edit_item_score_0.set_label(
            _("Set score as 0"))
        self.menubar_edit_item_score_0.set_use_underline(True)

        self.menubar_edit_item_score_1.set_label(
            _("Set score as 1"))
        self.menubar_edit_item_score_1.set_use_underline(True)

        self.menubar_edit_item_score_2.set_label(
            _("Set score as 2"))
        self.menubar_edit_item_score_2.set_use_underline(True)

        self.menubar_edit_item_score_3.set_label(
            _("Set score as 3"))
        self.menubar_edit_item_score_3.set_use_underline(True)

        self.menubar_edit_item_score_4.set_label(
            _("Set score as 4"))
        self.menubar_edit_item_score_4.set_use_underline(True)

        self.menubar_edit_item_score_5.set_label(
            _("Set score as 5"))
        self.menubar_edit_item_score_5.set_use_underline(True)

        # ------------------------------------
        #   Menubar - Help items
        # ------------------------------------

        self.menubar_help_menu = Gtk.Menu()

        self.menubar_help_item_about = Gtk.MenuItem()

        # Properties
        self.menubar_help_item_about.set_label(
            _("_About"))
        self.menubar_help_item_about.set_use_underline(True)

        # ------------------------------------
        #   Toolbar
        # ------------------------------------

        self.toolbar = Gtk.Toolbar()

        self.toolbar_item_parameters = Gtk.Button()
        self.toolbar_item_screenshots = Gtk.Button()
        self.toolbar_item_output = Gtk.Button()
        self.toolbar_item_notes = Gtk.Button()

        self.toolbar_item_game_launch = Gtk.ToolItem()
        self.toolbar_item_game_properties = Gtk.ToolItem()
        self.toolbar_item_game_option = Gtk.ToolItem()
        self.toolbar_item_consoles = Gtk.ToolItem()
        self.toolbar_item_search = Gtk.ToolItem()
        self.toolbar_item_filters = Gtk.ToolItem()

        self.toolbar_item_separator = Gtk.SeparatorToolItem()

        self.toolbar_image_parameters = Gtk.Image()
        self.toolbar_image_screenshots = Gtk.Image()
        self.toolbar_image_output = Gtk.Image()
        self.toolbar_image_notes = Gtk.Image()

        # Properties
        self.toolbar_item_parameters.set_tooltip_text(
            _("Set custom parameters"))

        self.toolbar_item_screenshots.set_tooltip_text(
            _("Show selected game screenshots"))
        self.toolbar_item_output.set_tooltip_text(
            _("Show selected game output log"))
        self.toolbar_item_notes.set_tooltip_text(
            _("Show selected game notes"))

        self.toolbar_item_separator.set_draw(False)
        self.toolbar_item_separator.set_expand(True)

        # ------------------------------------
        #   Toolbar - Consoles
        # ------------------------------------

        self.button_consoles = ListBoxSelector(use_static_size=True)

        self.entry_consoles = self.button_consoles.get_entry()
        self.listbox_consoles = self.button_consoles.get_listbox()

        # Properties
        self.button_consoles.set_filter_func(self.__on_filter_consoles)
        self.button_consoles.set_sort_func(self.__on_sort_consoles)

        # ------------------------------------
        #   Toolbar - Consoles options
        # ------------------------------------

        self.popover_consoles_options = Gtk.Popover()

        self.button_consoles_option = Gtk.MenuButton()

        self.toolbar_item_statistic = Gtk.Button()
        self.toolbar_image_statistic = Gtk.Image()

        self.toolbar_item_properties = Gtk.Button()
        self.toolbar_image_properties = Gtk.Image()

        self.toolbar_item_refresh = Gtk.Button()
        self.toolbar_image_refresh = Gtk.Image()

        self.menu_item_filters_options = Gtk.Label()

        self.label_consoles_options_favorite = Gtk.Label()
        self.switch_consoles_favorite = Gtk.Switch()

        self.label_consoles_options_recursive = Gtk.Label()
        self.switch_consoles_recursive = Gtk.Switch()

        # Properties
        self.button_consoles_option.set_popover(self.popover_consoles_options)
        self.button_consoles_option.set_use_popover(True)

        self.toolbar_item_statistic.set_label(_("Show statistics"))
        self.toolbar_item_statistic.set_relief(Gtk.ReliefStyle.NONE)
        self.toolbar_item_statistic.set_image(self.toolbar_image_statistic)
        self.toolbar_item_statistic.set_use_underline(True)
        self.toolbar_item_statistic.set_alignment(0, 0.5)

        self.toolbar_image_statistic.set_valign(Gtk.Align.CENTER)
        self.toolbar_image_statistic.set_margin_right(6)

        self.toolbar_item_properties.set_label(_("Edit emulator"))
        self.toolbar_item_properties.set_relief(Gtk.ReliefStyle.NONE)
        self.toolbar_item_properties.set_image(self.toolbar_image_properties)
        self.toolbar_item_properties.set_use_underline(True)
        self.toolbar_item_properties.set_alignment(0, 0.5)

        self.toolbar_image_properties.set_valign(Gtk.Align.CENTER)
        self.toolbar_image_properties.set_margin_right(6)

        self.toolbar_item_refresh.set_label(_("Refresh games list"))
        self.toolbar_item_refresh.set_relief(Gtk.ReliefStyle.NONE)
        self.toolbar_item_refresh.set_image(self.toolbar_image_refresh)
        self.toolbar_item_refresh.set_use_underline(True)
        self.toolbar_item_refresh.set_alignment(0, 0.5)

        self.toolbar_image_refresh.set_valign(Gtk.Align.CENTER)
        self.toolbar_image_refresh.set_margin_right(6)

        self.menu_item_filters_options.set_label(_("Options"))
        self.menu_item_filters_options.set_halign(Gtk.Align.START)
        self.menu_item_filters_options.set_valign(Gtk.Align.CENTER)
        self.menu_item_filters_options.get_style_context().add_class(
            "dim-label")

        self.label_consoles_options_favorite.set_label(_("Favorite"))
        self.label_consoles_options_favorite.set_halign(Gtk.Align.START)
        self.label_consoles_options_favorite.set_valign(Gtk.Align.CENTER)
        self.label_consoles_options_favorite.set_hexpand(True)

        self.switch_consoles_favorite.set_valign(Gtk.Align.END)

        self.label_consoles_options_recursive.set_label(_("Recursive"))
        self.label_consoles_options_recursive.set_halign(Gtk.Align.START)
        self.label_consoles_options_recursive.set_valign(Gtk.Align.CENTER)
        self.label_consoles_options_recursive.set_hexpand(True)

        self.switch_consoles_recursive.set_valign(Gtk.Align.END)
        self.switch_consoles_recursive.set_tooltip_text(
            _("You need to reload games list to apply changes"))

        # ------------------------------------
        #   Toolbar - Filter
        # ------------------------------------

        self.entry_filter = Gtk.SearchEntry()

        self.tool_menu_filters = Gtk.MenuButton()

        self.popover_menu_filters = Gtk.Popover()

        # Properties
        self.entry_filter.set_placeholder_text("%s…" % _("Filter"))

        self.tool_menu_filters.set_tooltip_text(_("Filters"))
        self.tool_menu_filters.set_use_popover(True)

        self.popover_menu_filters.set_modal(True)

        # ------------------------------------
        #   Toolbar - Filter - Menu
        # ------------------------------------

        self.label_filter_favorite = Gtk.Label()
        self.check_filter_favorite = Gtk.Switch()

        self.label_filter_unfavorite = Gtk.Label()
        self.check_filter_unfavorite = Gtk.Switch()

        self.label_filter_multiplayer = Gtk.Label()
        self.check_filter_multiplayer = Gtk.Switch()

        self.label_filter_singleplayer = Gtk.Label()
        self.check_filter_singleplayer = Gtk.Switch()

        self.label_filter_finish = Gtk.Label()
        self.check_filter_finish = Gtk.Switch()

        self.label_filter_unfinish = Gtk.Label()
        self.check_filter_unfinish = Gtk.Switch()

        self.item_filter_reset = Gtk.Button()

        # Properties
        self.label_filter_favorite.set_label(_("Favorite"))
        self.label_filter_favorite.set_halign(Gtk.Align.END)
        self.label_filter_favorite.set_valign(Gtk.Align.CENTER)
        self.label_filter_favorite.get_style_context().add_class("dim-label")
        self.check_filter_favorite.set_active(True)

        self.label_filter_unfavorite.set_label(_("Unfavorite"))
        self.label_filter_unfavorite.set_halign(Gtk.Align.END)
        self.label_filter_unfavorite.set_valign(Gtk.Align.CENTER)
        self.label_filter_unfavorite.get_style_context().add_class("dim-label")
        self.check_filter_unfavorite.set_active(True)

        self.label_filter_multiplayer.set_margin_top(12)
        self.label_filter_multiplayer.set_label(_("Multiplayer"))
        self.label_filter_multiplayer.set_halign(Gtk.Align.END)
        self.label_filter_multiplayer.set_valign(Gtk.Align.CENTER)
        self.label_filter_multiplayer.get_style_context().add_class("dim-label")
        self.check_filter_multiplayer.set_margin_top(12)
        self.check_filter_multiplayer.set_active(True)

        self.label_filter_singleplayer.set_label(_("Singleplayer"))
        self.label_filter_singleplayer.set_halign(Gtk.Align.END)
        self.label_filter_singleplayer.set_valign(Gtk.Align.CENTER)
        self.label_filter_singleplayer.get_style_context().add_class(
            "dim-label")
        self.check_filter_singleplayer.set_active(True)

        self.label_filter_finish.set_margin_top(12)
        self.label_filter_finish.set_label(_("Finish"))
        self.label_filter_finish.set_halign(Gtk.Align.END)
        self.label_filter_finish.set_valign(Gtk.Align.CENTER)
        self.label_filter_finish.get_style_context().add_class("dim-label")
        self.check_filter_finish.set_margin_top(12)
        self.check_filter_finish.set_active(True)

        self.label_filter_unfinish.set_label(_("Unfinish"))
        self.label_filter_unfinish.set_halign(Gtk.Align.END)
        self.label_filter_unfinish.set_valign(Gtk.Align.CENTER)
        self.label_filter_unfinish.get_style_context().add_class("dim-label")
        self.check_filter_unfinish.set_active(True)

        self.item_filter_reset.set_margin_top(12)
        self.item_filter_reset.set_label(_("Reset filters"))
        self.item_filter_reset.set_halign(Gtk.Align.CENTER)
        self.item_filter_reset.set_valign(Gtk.Align.CENTER)

        # ------------------------------------
        #   Infobar
        # ------------------------------------

        self.infobar = Gtk.InfoBar()

        self.label_infobar = Gtk.Label()

        # Properties
        self.infobar.set_show_close_button(False)

        self.label_infobar.set_use_markup(True)

        # ------------------------------------
        #   Games - Sidebar
        # ------------------------------------

        self.scroll_sidebar = Gtk.ScrolledWindow()

        self.paned_games = Gtk.Paned()

        self.image_sidebar_title = Gtk.Image()
        self.label_sidebar_title = Gtk.Label()

        self.view_image_sidebar_game = Gtk.Viewport()
        self.frame_sidebar_game = Gtk.Frame()
        self.image_sidebar_game = Gtk.Image()

        self.notebook_sidebar_game = Gtk.Notebook()

        # Properties
        self.scroll_sidebar.set_size_request(432, 262)

        self.paned_games.set_orientation(Gtk.Orientation.VERTICAL)

        self.image_sidebar_title.set_no_show_all(True)
        self.image_sidebar_title.set_halign(Gtk.Align.CENTER)
        self.image_sidebar_title.set_valign(Gtk.Align.CENTER)

        self.label_sidebar_title.set_use_markup(True)
        self.label_sidebar_title.set_valign(Gtk.Align.CENTER)
        self.label_sidebar_title.set_ellipsize(Pango.EllipsizeMode.END)

        self.view_image_sidebar_game.drag_source_set(
            Gdk.ModifierType.BUTTON1_MASK, self.targets, Gdk.DragAction.COPY)

        self.frame_sidebar_game.set_valign(Gtk.Align.CENTER)
        self.frame_sidebar_game.set_halign(Gtk.Align.CENTER)

        self.image_sidebar_game.set_halign(Gtk.Align.CENTER)
        self.image_sidebar_game.set_valign(Gtk.Align.CENTER)

        self.notebook_sidebar_game.set_no_show_all(True)
        self.notebook_sidebar_game.set_hexpand(True)
        self.notebook_sidebar_game.set_vexpand(True)

        # ------------------------------------
        #   Games - Sidebar informations
        # ------------------------------------

        self.scroll_sidebar_informations = Gtk.ScrolledWindow()

        self.image_sidebar_informations = Gtk.Image()
        self.label_sidebar_informations = Gtk.Label()

        self.listbox_sidebar_informations = Gtk.ListBox()

        # Properties
        self.scroll_sidebar_informations.set_policy(
            Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.label_sidebar_informations.set_label(_("Informations"))

        self.listbox_sidebar_informations.set_selection_mode(
            Gtk.SelectionMode.NONE)

        # ------------------------------------
        #   Games - Sidebar tags
        # ------------------------------------

        self.scroll_sidebar_tags = Gtk.ScrolledWindow()

        self.image_sidebar_tags = Gtk.Image()
        self.label_sidebar_tags = Gtk.Label()

        self.listbox_sidebar_tags = Gtk.ListBox()

        # Properties
        self.scroll_sidebar_tags.set_policy(
            Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.label_sidebar_tags.set_label(_("Tags"))

        self.listbox_sidebar_tags.set_selection_mode(Gtk.SelectionMode.NONE)

        # ------------------------------------
        #   Games - Sidebar description
        # ------------------------------------

        self.widgets_sidebar = list()

        for key, value in self.sidebar_keys:
            data = ( key, Gtk.Label(), Gtk.Label() )

            # Properties
            data[1].set_text(value)
            data[1].set_halign(Gtk.Align.END)
            data[1].set_valign(Gtk.Align.CENTER)
            data[1].set_ellipsize(Pango.EllipsizeMode.END)
            data[1].get_style_context().add_class("dim-label")

            data[2].set_use_markup(True)
            data[2].set_halign(Gtk.Align.START)
            data[2].set_valign(Gtk.Align.CENTER)
            data[2].set_ellipsize(Pango.EllipsizeMode.END)

            self.widgets_sidebar.append(data)

        # ------------------------------------
        #   Games - Placeholder
        # ------------------------------------

        self.image_game_placeholder = Gtk.Image()
        self.label_game_placeholder = Gtk.Label()

        # Properties
        self.image_game_placeholder.set_from_icon_name(
            Icons.Symbolic.Gaming, Gtk.IconSize.DIALOG)
        self.image_game_placeholder.set_pixel_size(256)
        self.image_game_placeholder.set_halign(Gtk.Align.CENTER)
        self.image_game_placeholder.set_valign(Gtk.Align.END)
        self.image_game_placeholder.get_style_context().add_class("dim-label")

        self.label_game_placeholder.set_label(
            _("Start to play by drag & drop some ROM files into interface"))
        self.label_game_placeholder.set_halign(Gtk.Align.CENTER)
        self.label_game_placeholder.set_valign(Gtk.Align.START)

        # ------------------------------------
        #   Games - Treeview
        # ------------------------------------

        self.scroll_games = Gtk.ScrolledWindow()

        self.model_games = Gtk.ListStore(
            Pixbuf, # Favorite icon
            Pixbuf, # Multiplayer icon
            Pixbuf, # Finish icon
            str,    # Name
            int,    # Played
            str,    # Last play
            str,    # Last time play
            str,    # Time play
            int,    # Score
            str,    # Installed
            Pixbuf, # Custom parameters
            Pixbuf, # Screenshots
            Pixbuf, # Save states
            object  # Game object
        )
        self.treeview_games = Gtk.TreeView()

        self.filter_games = self.model_games.filter_new()
        self.sorted_games = Gtk.TreeModelSort(self.filter_games)

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

        # Properties
        self.sorted_games.set_sort_func(
            Columns.Favorite, self.__on_sort_games, Columns.Favorite)
        self.sorted_games.set_sort_func(
            Columns.Multiplayer, self.__on_sort_games, Columns.Multiplayer)
        self.sorted_games.set_sort_func(
            Columns.Finish, self.__on_sort_games, Columns.Finish)
        self.sorted_games.set_sort_func(
            Columns.LastPlay, self.__on_sort_games, Columns.LastPlay)
        self.sorted_games.set_sort_func(
            Columns.TimePlay, self.__on_sort_games, Columns.TimePlay)
        self.sorted_games.set_sort_func(
            Columns.Installed, self.__on_sort_games, Columns.Installed)

        self.treeview_games.set_model(self.sorted_games)
        self.treeview_games.set_search_column(Columns.Name)
        self.treeview_games.set_headers_clickable(True)
        self.treeview_games.set_headers_visible(True)
        self.treeview_games.set_show_expanders(False)
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

        self.column_game_favorite.pack_start(
            self.cell_game_favorite, False)
        self.column_game_favorite.set_sort_column_id(Columns.Favorite)

        self.column_game_multiplayer.pack_start(
            self.cell_game_multiplayer, False)
        self.column_game_multiplayer.set_sort_column_id(Columns.Multiplayer)

        self.column_game_finish.pack_start(
            self.cell_game_finish, False)
        self.column_game_finish.set_sort_column_id(Columns.Finish)

        self.column_game_name.set_expand(True)
        self.column_game_name.set_resizable(True)
        self.column_game_name.set_min_width(100)
        self.column_game_name.set_fixed_width(300)
        self.column_game_name.set_sort_column_id(Columns.Name)
        self.column_game_name.pack_start(
            self.cell_game_name, True)

        self.column_game_play.set_sort_column_id(Columns.Played)
        self.column_game_play.set_alignment(.5)
        self.column_game_play.pack_start(
            self.cell_game_play, False)

        self.column_game_last_play.set_sort_column_id(Columns.LastPlay)
        self.column_game_last_play.set_alignment(.5)
        self.column_game_last_play.pack_start(
            self.cell_game_last_play, False)
        self.column_game_last_play.pack_start(
            self.cell_game_last_play_time, False)

        self.column_game_play_time.set_sort_column_id(Columns.TimePlay)
        self.column_game_play_time.set_alignment(.5)
        self.column_game_play_time.pack_start(
            self.cell_game_play_time, False)

        self.column_game_score.set_sort_column_id(Columns.Score)
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

        self.column_game_installed.set_sort_column_id(Columns.Installed)
        self.column_game_installed.set_alignment(.5)
        self.column_game_installed.pack_start(
            self.cell_game_installed, False)

        self.column_game_flags.set_alignment(.5)
        self.column_game_flags.pack_start(
            self.cell_game_except, False)
        self.column_game_flags.pack_start(
            self.cell_game_snapshots, False)
        self.column_game_flags.pack_start(
            self.cell_game_save, False)

        self.column_game_favorite.add_attribute(
            self.cell_game_favorite, "pixbuf", Columns.Favorite)
        self.column_game_multiplayer.add_attribute(
            self.cell_game_multiplayer, "pixbuf", Columns.Multiplayer)
        self.column_game_finish.add_attribute(
            self.cell_game_finish, "pixbuf", Columns.Finish)
        self.column_game_name.add_attribute(
            self.cell_game_name, "text", Columns.Name)
        self.column_game_play.add_attribute(
            self.cell_game_play, "text", Columns.Played)
        self.column_game_last_play.add_attribute(
            self.cell_game_last_play, "text", Columns.LastPlay)
        self.column_game_last_play.add_attribute(
            self.cell_game_last_play_time, "text", Columns.LastTimePlay)
        self.column_game_play_time.add_attribute(
            self.cell_game_play_time, "text", Columns.TimePlay)
        self.column_game_installed.add_attribute(
            self.cell_game_installed, "text", Columns.Installed)
        self.column_game_flags.add_attribute(
            self.cell_game_except, "pixbuf", Columns.Except)
        self.column_game_flags.add_attribute(
            self.cell_game_snapshots, "pixbuf", Columns.Snapshots)
        self.column_game_flags.add_attribute(
            self.cell_game_save, "pixbuf", Columns.Save)

        self.column_game_score.set_cell_data_func(
            self.cell_game_score_first, self.__on_append_game)

        self.cell_game_favorite.set_alignment(.5, .5)
        self.cell_game_multiplayer.set_alignment(.5, .5)
        self.cell_game_finish.set_alignment(.5, .5)
        self.cell_game_name.set_alignment(0, .5)
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

        self.cell_game_favorite.set_padding(2, 4)
        self.cell_game_multiplayer.set_padding(2, 4)
        self.cell_game_finish.set_padding(2, 4)
        self.cell_game_name.set_padding(6, 4)
        self.cell_game_play.set_padding(6, 4)
        self.cell_game_last_play.set_padding(6, 4)
        self.cell_game_last_play_time.set_padding(6, 4)
        self.cell_game_score_first.set_padding(4, 4)
        self.cell_game_score_second.set_padding(2, 4)
        self.cell_game_score_third.set_padding(2, 4)
        self.cell_game_score_fourth.set_padding(2, 4)
        self.cell_game_score_fifth.set_padding(4, 4)
        self.cell_game_installed.set_padding(6, 4)
        self.cell_game_except.set_padding(4, 4)
        self.cell_game_snapshots.set_padding(2, 4)
        self.cell_game_save.set_padding(4, 4)

        # ------------------------------------
        #   Games - Menu
        # ------------------------------------

        self.menu_games = Gtk.Menu()

        self.menu_item_launch = Gtk.MenuItem()
        self.menu_item_properties = Gtk.MenuItem()

        self.menu_item_favorite = Gtk.CheckMenuItem()
        self.menu_item_multiplayer = Gtk.CheckMenuItem()
        self.menu_item_finish = Gtk.CheckMenuItem()

        # Properties
        self.menu_item_launch.set_label(
            _("_Launch"))
        self.menu_item_launch.set_use_underline(True)

        self.menu_item_favorite.set_label(
            _("_Favorite"))
        self.menu_item_favorite.set_use_underline(True)

        self.menu_item_multiplayer.set_label(
            _("_Multiplayer"))
        self.menu_item_multiplayer.set_use_underline(True)

        self.menu_item_finish.set_label(
            _("_Finish"))
        self.menu_item_finish.set_use_underline(True)

        self.menu_item_properties.set_label(
            "%s…" % _("_Properties"))
        self.menu_item_properties.set_use_underline(True)

        # ------------------------------------
        #   Games - Menu edit
        # ------------------------------------

        self.menu_games_edit = Gtk.Menu()
        self.menu_item_edit = Gtk.MenuItem()

        self.menu_item_rename = Gtk.MenuItem()
        self.menu_item_duplicate = Gtk.MenuItem()
        self.menu_item_copy = Gtk.MenuItem()
        self.menu_item_open = Gtk.MenuItem()
        self.menu_item_cover = Gtk.MenuItem()
        self.menu_item_remove = Gtk.MenuItem()
        self.menu_item_database = Gtk.MenuItem()

        # Properties
        self.menu_item_edit.set_label(
            _("_Edit"))
        self.menu_item_edit.set_use_underline(True)

        self.menu_item_rename.set_label(
            "%s…" % _("_Rename"))
        self.menu_item_rename.set_use_underline(True)

        self.menu_item_duplicate.set_label(
            "%s…" % _("_Duplicate"))
        self.menu_item_duplicate.set_use_underline(True)

        self.menu_item_copy.set_label(
            _("_Copy path"))
        self.menu_item_copy.set_use_underline(True)

        self.menu_item_open.set_label(
            _("_Open path"))
        self.menu_item_open.set_use_underline(True)

        self.menu_item_cover.set_label(
            "%s…" % _("Set game _cover"))
        self.menu_item_cover.set_use_underline(True)

        self.menu_item_database.set_label(
            "%s…" % _("_Reset data"))
        self.menu_item_database.set_use_underline(True)

        self.menu_item_remove.set_label(
            "%s…" % _("_Remove from disk"))
        self.menu_item_remove.set_use_underline(True)

        # ------------------------------------
        #   Games - Menu score
        # ------------------------------------

        self.menu_games_score = Gtk.Menu()
        self.menu_item_score = Gtk.MenuItem()

        self.menu_item_score_up = Gtk.MenuItem()
        self.menu_item_score_down = Gtk.MenuItem()
        self.menu_item_score_0 = Gtk.MenuItem()
        self.menu_item_score_1 = Gtk.MenuItem()
        self.menu_item_score_2 = Gtk.MenuItem()
        self.menu_item_score_3 = Gtk.MenuItem()
        self.menu_item_score_4 = Gtk.MenuItem()
        self.menu_item_score_5 = Gtk.MenuItem()

        # Properties
        self.menu_item_score.set_label(
            _("_Score"))
        self.menu_item_score.set_use_underline(True)

        self.menu_item_score_up.set_label(
            _("_Increase score"))
        self.menu_item_score_up.set_use_underline(True)

        self.menu_item_score_down.set_label(
            _("_Decrease score"))
        self.menu_item_score_down.set_use_underline(True)

        self.menu_item_score_0.set_label(
            _("Set score as 0"))
        self.menu_item_score_0.set_use_underline(True)

        self.menu_item_score_1.set_label(
            _("Set score as 1"))
        self.menu_item_score_1.set_use_underline(True)

        self.menu_item_score_2.set_label(
            _("Set score as 2"))
        self.menu_item_score_2.set_use_underline(True)

        self.menu_item_score_3.set_label(
            _("Set score as 3"))
        self.menu_item_score_3.set_use_underline(True)

        self.menu_item_score_4.set_label(
            _("Set score as 4"))
        self.menu_item_score_4.set_use_underline(True)

        self.menu_item_score_5.set_label(
            _("Set score as 5"))
        self.menu_item_score_5.set_use_underline(True)

        # ------------------------------------
        #   Games - Menu tools
        # ------------------------------------

        self.menu_games_tools = Gtk.Menu()
        self.menu_item_tools = Gtk.MenuItem()

        self.menu_item_screenshots = Gtk.MenuItem()
        self.menu_item_output = Gtk.MenuItem()
        self.menu_item_notes = Gtk.MenuItem()
        self.menu_item_desktop = Gtk.MenuItem()
        self.menu_item_mednafen = Gtk.MenuItem()

        # Properties
        self.menu_item_tools.set_label(_("_Tools"))
        self.menu_item_tools.set_use_underline(True)

        self.menu_item_screenshots.set_label("%s…" % _("_Screenshots"))
        self.menu_item_screenshots.set_use_underline(True)

        self.menu_item_output.set_label("%s…" % _("Output _log"))
        self.menu_item_output.set_use_underline(True)

        self.menu_item_notes.set_label("%s…" % _("_Notes"))
        self.menu_item_notes.set_use_underline(True)

        self.menu_item_desktop.set_label(_("_Generate a menu entry"))
        self.menu_item_desktop.set_use_underline(True)

        self.menu_item_mednafen.set_label("%s…" % _("Specify a _memory type"))
        self.menu_item_mednafen.set_use_underline(True)

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

        # Properties
        self.statusbar.set_no_show_all(True)

        self.grid_statusbar.set_spacing(12)
        self.grid_statusbar.set_margin_top(0)
        self.grid_statusbar.set_margin_left(0)
        self.grid_statusbar.set_margin_right(0)
        self.grid_statusbar.set_margin_bottom(0)

        self.label_statusbar_console.set_use_markup(True)
        self.label_statusbar_console.set_alignment(0, .5)
        self.label_statusbar_emulator.set_use_markup(True)
        self.label_statusbar_emulator.set_alignment(0, .5)
        self.label_statusbar_game.set_ellipsize(Pango.EllipsizeMode.END)
        self.label_statusbar_game.set_alignment(0, .5)

        self.image_statusbar_properties.set_from_pixbuf(self.empty)
        self.image_statusbar_screenshots.set_from_pixbuf(self.empty)
        self.image_statusbar_savestates.set_from_pixbuf(self.empty)


    def __init_packing(self):
        """ Initialize widgets packing in main window
        """

        # Main widgets
        self.grid.pack_start(self.menubar, False, False, 0)
        self.grid.pack_start(self.toolbar, False, False, 0)
        self.grid.pack_start(self.grid_infobar, False, False, 0)
        self.grid.pack_start(self.paned_games, True, True, 0)
        self.grid.pack_start(self.statusbar, False, False, 0)

        self.grid.set_focus_chain([
            self.headerbar,
            self.toolbar,
            self.scroll_games
        ])

        # ------------------------------------
        #   Headerbar
        # ------------------------------------

        self.headerbar.pack_end(self.headerbar_item_menu)

        # Headerbar game launch
        self.grid_game_launch.pack_start(
            self.headerbar_item_launch, True, True, 0)
        self.grid_game_launch.pack_start(
            self.headerbar_item_fullscreen, True, True, 0)

        self.headerbar_item_fullscreen.add(self.headerbar_image_fullscreen)

        # Headerbar main menu
        self.headerbar_item_menu.add(self.headerbar_image_menu)
        self.headerbar_item_menu.set_popover(self.popover_menu)

        self.popover_menu.add(self.grid_main_popover)

        self.grid_main_popover.attach(
            self.menu_item_main_display, 0, 0, 2, 1)
        self.grid_main_popover.attach(
            self.menu_label_dark_theme, 0, 1, 1, 1)
        self.grid_main_popover.attach(
            self.menu_item_dark_theme, 1, 1, 1, 1)
        self.grid_main_popover.attach(
            self.menu_label_sidebar, 0, 2, 1, 1)
        self.grid_main_popover.attach(
            self.menu_item_sidebar, 1, 2, 1, 1)
        self.grid_main_popover.attach(
            self.menu_label_statusbar, 0, 3, 1, 1)
        self.grid_main_popover.attach(
            self.menu_item_statusbar, 1, 3, 1, 1)
        self.grid_main_popover.attach(
            Gtk.Separator(), 0, 4, 2, 1)
        self.grid_main_popover.attach(
            self.menu_item_preferences, 0, 5, 2, 1)
        self.grid_main_popover.attach(
            self.menu_item_addons, 0, 6, 2, 1)
        self.grid_main_popover.attach(
            Gtk.Separator(), 0, 7, 2, 1)
        self.grid_main_popover.attach(
            self.menu_item_gem_log, 0, 8, 2, 1)
        self.grid_main_popover.attach(
            Gtk.Separator(), 0, 9, 2, 1)
        self.grid_main_popover.attach(
            self.menu_item_about, 0, 11, 2, 1)
        self.grid_main_popover.attach(
            self.menu_item_quit, 0, 12, 2, 1)

        # ------------------------------------
        #   Menubar
        # ------------------------------------

        self.menubar.insert(self.menubar_item_main, -1)
        self.menubar.insert(self.menubar_item_game, -1)
        self.menubar.insert(self.menubar_item_edit, -1)
        self.menubar.insert(self.menubar_item_help, -1)

        # Menu - Main items
        self.menubar_item_main.set_submenu(self.menubar_main_menu)

        self.menubar_main_menu.insert(Gtk.SeparatorMenuItem(), -1)
        self.menubar_main_menu.insert(self.menubar_main_item_dark_theme, -1)
        self.menubar_main_menu.insert(self.menubar_main_item_sidebar, -1)
        self.menubar_main_menu.insert(self.menubar_main_item_statusbar, -1)
        self.menubar_main_menu.insert(Gtk.SeparatorMenuItem(), -1)
        self.menubar_main_menu.insert(self.menubar_main_item_preferences, -1)
        self.menubar_main_menu.insert(self.menubar_main_item_addons, -1)
        self.menubar_main_menu.insert(self.menubar_main_item_log, -1)
        self.menubar_main_menu.insert(Gtk.SeparatorMenuItem(), -1)
        self.menubar_main_menu.insert(self.menubar_main_item_quit, -1)

        # Menu - Game items
        self.menubar_item_game.set_submenu(self.menubar_game_menu)

        self.menubar_game_menu.insert(self.menubar_game_item_launch, -1)
        self.menubar_game_menu.insert(Gtk.SeparatorMenuItem(), -1)
        self.menubar_game_menu.insert(self.menubar_game_item_favorite, -1)
        self.menubar_game_menu.insert(self.menubar_game_item_multiplayer, -1)
        self.menubar_game_menu.insert(self.menubar_game_item_finish, -1)
        self.menubar_game_menu.insert(Gtk.SeparatorMenuItem(), -1)
        self.menubar_game_menu.insert(self.menubar_game_item_properties, -1)
        self.menubar_game_menu.insert(Gtk.SeparatorMenuItem(), -1)
        self.menubar_game_menu.insert(self.menubar_game_item_screenshots, -1)
        self.menubar_game_menu.insert(self.menubar_game_item_output, -1)
        self.menubar_game_menu.insert(self.menubar_game_item_notes, -1)
        self.menubar_game_menu.insert(Gtk.SeparatorMenuItem(), -1)
        self.menubar_game_menu.insert(self.menubar_game_item_fullscreen, -1)

        # Menu - Edit items
        self.menubar_item_edit.set_submenu(self.menubar_edit_menu)

        self.menubar_edit_item_score.set_submenu(self.menubar_edit_score)

        self.menubar_edit_menu.insert(self.menubar_edit_item_score, -1)
        self.menubar_edit_menu.insert(Gtk.SeparatorMenuItem(), -1)
        self.menubar_edit_menu.insert(self.menubar_edit_item_rename, -1)
        self.menubar_edit_menu.insert(Gtk.SeparatorMenuItem(), -1)
        self.menubar_edit_menu.insert(self.menubar_edit_item_duplicate, -1)
        self.menubar_edit_menu.insert(Gtk.SeparatorMenuItem(), -1)
        self.menubar_edit_menu.insert(self.menubar_edit_item_mednafen, -1)
        self.menubar_edit_menu.insert(Gtk.SeparatorMenuItem(), -1)
        self.menubar_edit_menu.insert(self.menubar_edit_item_copy, -1)
        self.menubar_edit_menu.insert(self.menubar_edit_item_open, -1)
        self.menubar_edit_menu.insert(self.menubar_edit_item_desktop, -1)
        self.menubar_edit_menu.insert(Gtk.SeparatorMenuItem(), -1)
        self.menubar_edit_menu.insert(self.menubar_edit_item_cover, -1)
        self.menubar_edit_menu.insert(Gtk.SeparatorMenuItem(), -1)
        self.menubar_edit_menu.insert(self.menubar_edit_item_database, -1)
        self.menubar_edit_menu.insert(Gtk.SeparatorMenuItem(), -1)
        self.menubar_edit_menu.insert(self.menubar_edit_item_delete, -1)

        self.menubar_edit_score.insert(self.menubar_edit_item_score_up, -1)
        self.menubar_edit_score.insert(self.menubar_edit_item_score_down, -1)
        self.menubar_edit_score.insert(Gtk.SeparatorMenuItem(), -1)
        self.menubar_edit_score.insert(self.menubar_edit_item_score_0, -1)
        self.menubar_edit_score.insert(self.menubar_edit_item_score_1, -1)
        self.menubar_edit_score.insert(self.menubar_edit_item_score_2, -1)
        self.menubar_edit_score.insert(self.menubar_edit_item_score_3, -1)
        self.menubar_edit_score.insert(self.menubar_edit_item_score_4, -1)
        self.menubar_edit_score.insert(self.menubar_edit_item_score_5, -1)

        # Menu - Help items
        self.menubar_item_help.set_submenu(self.menubar_help_menu)

        self.menubar_help_menu.insert(self.menubar_help_item_about, -1)

        # ------------------------------------
        #   Toolbar
        # ------------------------------------

        self.toolbar.insert(self.toolbar_item_game_properties, -1)
        self.toolbar.insert(Gtk.SeparatorToolItem(), -1)
        self.toolbar.insert(self.toolbar_item_game_option, -1)
        self.toolbar.insert(self.toolbar_item_separator, -1)
        self.toolbar.insert(self.toolbar_item_consoles, -1)
        self.toolbar.insert(Gtk.SeparatorToolItem(), -1)
        self.toolbar.insert(self.toolbar_item_search, -1)

        self.toolbar_item_game_properties.add(self.toolbar_item_parameters)
        self.toolbar_item_game_option.add(self.grid_game_options)
        self.toolbar_item_consoles.add(self.grid_consoles)
        self.toolbar_item_search.add(self.grid_filters)

        self.toolbar_item_parameters.add(self.toolbar_image_parameters)
        self.toolbar_item_screenshots.add(self.toolbar_image_screenshots)
        self.toolbar_item_output.add(self.toolbar_image_output)
        self.toolbar_item_notes.add(self.toolbar_image_notes)

        self.grid_game_options.pack_start(
            self.toolbar_item_screenshots, False, False, 0)
        self.grid_game_options.pack_start(
            self.toolbar_item_output, False, False, 0)
        self.grid_game_options.pack_start(
            self.toolbar_item_notes, False, False, 0)

        # Toolbar - Consoles
        self.grid_consoles.pack_start(
            self.button_consoles, False, False, 0)
        self.grid_consoles.pack_start(
            self.button_consoles_option, False, False, 0)

        # Toolbar - Consoles options
        self.popover_consoles_options.add(self.grid_consoles_popover)

        self.grid_consoles_popover.attach(
            self.menu_item_filters_options, 0, 0, 2, 1)
        self.grid_consoles_popover.attach(
            self.label_consoles_options_favorite, 0, 1, 1, 1)
        self.grid_consoles_popover.attach(
            self.switch_consoles_favorite, 1, 1, 1, 1)
        self.grid_consoles_popover.attach(
            self.label_consoles_options_recursive, 0, 2, 1, 1)
        self.grid_consoles_popover.attach(
            self.switch_consoles_recursive, 1, 2, 1, 1)
        self.grid_consoles_popover.attach(
            Gtk.Separator(), 0, 3, 2, 1)
        self.grid_consoles_popover.attach(
            self.toolbar_item_properties, 0, 4, 2, 1)
        self.grid_consoles_popover.attach(
            self.toolbar_item_statistic, 0, 5, 2, 1)
        self.grid_consoles_popover.attach(
            Gtk.Separator(), 0, 6, 2, 1)
        self.grid_consoles_popover.attach(
            self.toolbar_item_refresh, 0, 7, 2, 1)

        # Toolbar - Filters menu
        self.tool_menu_filters.set_popover(self.popover_menu_filters)

        self.grid_filters.pack_start(
            self.entry_filter, False, False, 0)
        self.grid_filters.pack_start(
            self.tool_menu_filters, False, False, 0)

        self.grid_filters_popover.attach(
            self.label_filter_favorite, 0, 0, 1, 1)
        self.grid_filters_popover.attach(
            self.check_filter_favorite, 1, 0, 1, 1)
        self.grid_filters_popover.attach(
            self.label_filter_unfavorite, 0, 1, 1, 1)
        self.grid_filters_popover.attach(
            self.check_filter_unfavorite, 1, 1, 1, 1)
        self.grid_filters_popover.attach(
            self.label_filter_multiplayer, 0, 2, 1, 1)
        self.grid_filters_popover.attach(
            self.check_filter_multiplayer, 1, 2, 1, 1)
        self.grid_filters_popover.attach(
            self.label_filter_singleplayer, 0, 3, 1, 1)
        self.grid_filters_popover.attach(
            self.check_filter_singleplayer, 1, 3, 1, 1)
        self.grid_filters_popover.attach(
            self.label_filter_finish, 0, 4, 1, 1)
        self.grid_filters_popover.attach(
            self.check_filter_finish, 1, 4, 1, 1)
        self.grid_filters_popover.attach(
            self.label_filter_unfinish, 0, 5, 1, 1)
        self.grid_filters_popover.attach(
            self.check_filter_unfinish, 1, 5, 1, 1)
        self.grid_filters_popover.attach(
            self.item_filter_reset, 0, 6, 2, 1)

        self.popover_menu_filters.add(self.grid_filters_popover)

        # Infobar
        self.infobar.get_content_area().pack_start(
            self.label_infobar, True, True, 4)

        # ------------------------------------
        #   Games
        # ------------------------------------

        self.paned_games.pack1(self.grid_games, True, False)
        self.paned_games.pack2(self.scroll_sidebar, False, False)

        # Sidebar
        self.scroll_sidebar.add(self.grid_sidebar)

        self.frame_sidebar_game.add(self.view_image_sidebar_game)
        self.view_image_sidebar_game.add(self.image_sidebar_game)

        self.grid_sidebar_title.pack_start(
            self.image_sidebar_title, False, False, 0)
        self.grid_sidebar_title.pack_start(
            self.label_sidebar_title, True, True, 0)

        # Sidebar - Informations
        self.scroll_sidebar_informations.add(self.grid_sidebar_informations)

        self.grid_sidebar_tab_informations.pack_start(
            self.label_sidebar_informations, True, True, 0)

        self.notebook_sidebar_game.append_page(self.scroll_sidebar_informations,
            self.grid_sidebar_tab_informations)

        for key, label_key, label_value in self.widgets_sidebar:
            index = self.widgets_sidebar.index((key, label_key, label_value))

            self.grid_sidebar_informations.attach(label_key, 0, index, 1, 1)
            self.grid_sidebar_informations.attach(label_value, 1, index, 1, 1)

        # Sidebar - Tags
        self.scroll_sidebar_tags.add(self.listbox_sidebar_tags)

        self.grid_sidebar_tab_tags.pack_start(
            self.label_sidebar_tags, True, True, 0)

        self.notebook_sidebar_game.append_page(self.scroll_sidebar_tags,
            self.grid_sidebar_tab_tags)

        # Games
        self.grid_games.pack_start(self.grid_games_placeholder, True, True, 0)
        self.grid_games.pack_start(self.scroll_games, True, True, 0)

        # Games placeholder
        self.grid_games_placeholder.pack_start(
            self.image_game_placeholder, True, True, 0)
        self.grid_games_placeholder.pack_start(
            self.label_game_placeholder, True, True, 0)

        # Games treeview
        self.scroll_games.add(self.treeview_games)

        self.treeview_games.append_column(self.column_game_favorite)
        self.treeview_games.append_column(self.column_game_multiplayer)
        self.treeview_games.append_column(self.column_game_finish)
        self.treeview_games.append_column(self.column_game_name)
        self.treeview_games.append_column(self.column_game_play)
        self.treeview_games.append_column(self.column_game_last_play)
        self.treeview_games.append_column(self.column_game_play_time)
        self.treeview_games.append_column(self.column_game_score)
        self.treeview_games.append_column(self.column_game_installed)
        self.treeview_games.append_column(self.column_game_flags)

        # Games menu
        self.menu_games.append(self.menu_item_launch)
        self.menu_games.append(Gtk.SeparatorMenuItem())
        self.menu_games.append(self.menu_item_favorite)
        self.menu_games.append(self.menu_item_multiplayer)
        self.menu_games.append(self.menu_item_finish)
        self.menu_games.append(Gtk.SeparatorMenuItem())
        self.menu_games.append(self.menu_item_properties)
        self.menu_games.append(Gtk.SeparatorMenuItem())
        self.menu_games.append(self.menu_item_edit)
        self.menu_games.append(self.menu_item_score)
        self.menu_games.append(self.menu_item_tools)

        self.menu_item_edit.set_submenu(self.menu_games_edit)
        self.menu_item_score.set_submenu(self.menu_games_score)
        self.menu_item_tools.set_submenu(self.menu_games_tools)

        self.menu_games_edit.append(self.menu_item_rename)
        self.menu_games_edit.append(Gtk.SeparatorMenuItem())
        self.menu_games_edit.append(self.menu_item_duplicate)
        self.menu_games_edit.append(Gtk.SeparatorMenuItem())
        self.menu_games_edit.append(self.menu_item_copy)
        self.menu_games_edit.append(self.menu_item_open)
        self.menu_games_edit.append(Gtk.SeparatorMenuItem())
        self.menu_games_edit.append(self.menu_item_cover)
        self.menu_games_edit.append(Gtk.SeparatorMenuItem())
        self.menu_games_edit.append(self.menu_item_database)
        self.menu_games_edit.append(Gtk.SeparatorMenuItem())
        self.menu_games_edit.append(self.menu_item_remove)

        self.menu_games_score.append(self.menu_item_score_up)
        self.menu_games_score.append(self.menu_item_score_down)
        self.menu_games_score.append(Gtk.SeparatorMenuItem())
        self.menu_games_score.append(self.menu_item_score_0)
        self.menu_games_score.append(self.menu_item_score_1)
        self.menu_games_score.append(self.menu_item_score_2)
        self.menu_games_score.append(self.menu_item_score_3)
        self.menu_games_score.append(self.menu_item_score_4)
        self.menu_games_score.append(self.menu_item_score_5)

        self.menu_games_tools.append(self.menu_item_screenshots)
        self.menu_games_tools.append(self.menu_item_output)
        self.menu_games_tools.append(self.menu_item_notes)
        self.menu_games_tools.append(Gtk.SeparatorMenuItem())
        self.menu_games_tools.append(self.menu_item_desktop)
        self.menu_games_tools.append(Gtk.SeparatorMenuItem())
        self.menu_games_tools.append(self.menu_item_mednafen)

        # ------------------------------------
        #   Statusbar
        # ------------------------------------

        self.grid_statusbar.pack_start(
            self.label_statusbar_emulator, False, False, 0)
        self.grid_statusbar.pack_start(
            self.label_statusbar_game, True, True, 0)

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

        # ------------------------------------
        #   Window
        # ------------------------------------

        self.connect(
            "delete-event", self.__stop_interface)
        self.connect(
            "key-press-event", self.__on_manage_keys)

        self.connect(
            "drag-data-received", self.__on_dnd_received_data)

        # ------------------------------------
        #   Menubar
        # ------------------------------------

        self.menubar_game_item_launch.connect(
            "activate", self.__on_game_launch)
        self.favorite_signal_menubar = self.menubar_game_item_favorite.connect(
            "activate", self.__on_game_marked_as_favorite)
        self.multi_signal_menubar = self.menubar_game_item_multiplayer.connect(
            "activate", self.__on_game_marked_as_multiplayer)
        self.finish_signal_menubar = self.menubar_game_item_finish.connect(
            "activate", self.__on_game_marked_as_finish)
        self.menubar_game_item_properties.connect(
            "activate", self.__on_game_parameters)
        self.menubar_game_item_screenshots.connect(
            "activate", self.__on_show_viewer)
        self.menubar_game_item_output.connect(
            "activate", self.__on_show_log)
        self.menubar_game_item_notes.connect(
            "activate", self.__on_show_notes)
        self.fullscreen_signal = self.menubar_game_item_fullscreen.connect(
            "toggled", self.__on_activate_fullscreen)
        self.menubar_main_item_quit.connect(
            "activate", self.__stop_interface)

        self.menubar_edit_item_rename.connect(
            "activate", self.__on_game_renamed)
        self.menubar_edit_item_duplicate.connect(
            "activate", self.__on_game_duplicate)
        self.menubar_edit_item_copy.connect(
            "activate", self.__on_game_copy)
        self.menubar_edit_item_open.connect(
            "activate", self.__on_game_open)
        self.menubar_edit_item_desktop.connect(
            "activate", self.__on_game_generate_desktop)
        self.menubar_edit_item_cover.connect(
            "activate", self.__on_game_cover)
        self.menubar_edit_item_database.connect(
            "activate", self.__on_game_clean)
        self.menubar_edit_item_delete.connect(
            "activate", self.__on_game_removed)
        self.menubar_edit_item_mednafen.connect(
            "activate", self.__on_game_backup_memory)
        self.menubar_edit_item_score_up.connect(
            "activate", self.__on_game_score)
        self.menubar_edit_item_score_down.connect(
            "activate", self.__on_game_score)
        self.menubar_edit_item_score_0.connect(
            "activate", self.__on_game_score, 0)
        self.menubar_edit_item_score_1.connect(
            "activate", self.__on_game_score, 1)
        self.menubar_edit_item_score_2.connect(
            "activate", self.__on_game_score, 2)
        self.menubar_edit_item_score_3.connect(
            "activate", self.__on_game_score, 3)
        self.menubar_edit_item_score_4.connect(
            "activate", self.__on_game_score, 4)
        self.menubar_edit_item_score_5.connect(
            "activate", self.__on_game_score, 5)

        self.menubar_main_item_preferences.connect(
            "activate", self.__on_show_preferences)
        self.menubar_main_item_addons.connect(
            "activate", self.__on_show_modules)
        self.menubar_main_item_log.connect(
            "activate", self.__on_show_log)

        self.dark_signal_menubar = self.menubar_main_item_dark_theme.connect(
            "toggled", self.__on_activate_dark_theme)
        self.side_signal_menubar = self.menubar_main_item_sidebar.connect(
            "toggled", self.__on_activate_sidebar)
        self.status_signal_menubar = self.menubar_main_item_statusbar.connect(
            "toggled", self.__on_activate_statusbar)

        self.menubar_help_item_about.connect(
            "activate", self.__on_show_about)

        # ------------------------------------
        #   Toolbar
        # ------------------------------------

        self.headerbar_item_launch.connect(
            "clicked", self.__on_game_launch)
        self.fullscreen_signal_tool = self.headerbar_item_fullscreen.connect(
            "toggled", self.__on_activate_fullscreen)
        self.toolbar_item_screenshots.connect(
            "clicked", self.__on_show_viewer)
        self.toolbar_item_output.connect(
            "clicked", self.__on_game_log)
        self.toolbar_item_notes.connect(
            "clicked", self.__on_show_notes)
        self.toolbar_item_parameters.connect(
            "clicked", self.__on_game_parameters)

        self.listbox_consoles.connect(
            "row-activated", self.__on_selected_console)
        self.entry_consoles.connect(
            "changed", self.__on_update_consoles)

        self.toolbar_item_properties.connect(
            "clicked", self.__on_show_emulator_config)
        self.toolbar_item_refresh.connect(
            "clicked", self.__on_reload_games)

        self.favorite_signal_options = self.switch_consoles_favorite.connect(
            "state-set", self.__on_change_console_option)
        self.recursive_signal_options = self.switch_consoles_recursive.connect(
            "state-set", self.__on_change_console_option)

        self.entry_filter.connect(
            "changed", self.filters_update)

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
        #   Menu
        # ------------------------------------

        self.menu_item_launch.connect(
            "activate", self.__on_game_launch)
        self.favorite_signal_menu = self.menu_item_favorite.connect(
            "activate", self.__on_game_marked_as_favorite)
        self.multi_signal_menu = self.menu_item_multiplayer.connect(
            "activate", self.__on_game_marked_as_multiplayer)
        self.finish_signal_menu = self.menu_item_finish.connect(
            "activate", self.__on_game_marked_as_finish)
        self.menu_item_screenshots.connect(
            "activate", self.__on_show_viewer)
        self.menu_item_output.connect(
            "activate", self.__on_game_log)
        self.menu_item_notes.connect(
            "activate", self.__on_show_notes)

        self.menu_item_rename.connect(
            "activate", self.__on_game_renamed)
        self.menu_item_duplicate.connect(
            "activate", self.__on_game_duplicate)
        self.menu_item_properties.connect(
            "activate", self.__on_game_parameters)
        self.menu_item_copy.connect(
            "activate", self.__on_game_copy)
        self.menu_item_open.connect(
            "activate", self.__on_game_open)
        self.menu_item_cover.connect(
            "activate", self.__on_game_cover)
        self.menu_item_desktop.connect(
            "activate", self.__on_game_generate_desktop)
        self.menu_item_database.connect(
            "activate", self.__on_game_clean)
        self.menu_item_remove.connect(
            "activate", self.__on_game_removed)
        self.menu_item_mednafen.connect(
            "activate", self.__on_game_backup_memory)
        self.menu_item_score_up.connect(
            "activate", self.__on_game_score)
        self.menu_item_score_down.connect(
            "activate", self.__on_game_score)
        self.menu_item_score_0.connect(
            "activate", self.__on_game_score, 0)
        self.menu_item_score_1.connect(
            "activate", self.__on_game_score, 1)
        self.menu_item_score_2.connect(
            "activate", self.__on_game_score, 2)
        self.menu_item_score_3.connect(
            "activate", self.__on_game_score, 3)
        self.menu_item_score_4.connect(
            "activate", self.__on_game_score, 4)
        self.menu_item_score_5.connect(
            "activate", self.__on_game_score, 5)

        self.menu_item_preferences.connect(
            "clicked", self.__on_show_preferences)
        self.menu_item_addons.connect(
            "clicked", self.__on_show_modules)

        self.menu_item_gem_log.connect(
            "clicked", self.__on_show_log)
        self.dark_signal_menu = self.menu_item_dark_theme.connect(
            "state-set", self.__on_activate_dark_theme)
        self.side_signal_menu = self.menu_item_sidebar.connect(
            "state-set", self.__on_activate_sidebar)
        self.status_signal_menu = self.menu_item_statusbar.connect(
            "state-set", self.__on_activate_statusbar)
        self.menu_item_about.connect(
            "clicked", self.__on_show_about)
        self.menu_item_quit.connect(
            "clicked", self.__stop_interface)

        # ------------------------------------
        #   Sidebar
        # ------------------------------------

        self.view_image_sidebar_game.connect(
            "drag-data-get", self.__on_dnd_send_data)

        self.listbox_sidebar_tags.connect(
            "row-activated", self.__on_filter_tag)

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
            "query-tooltip", self.__on_selected_game_tooltip)

        self.filter_games.set_visible_func(self.filters_match)


    def __start_interface(self):
        """ Load data and start interface
        """

        # Define signals per toggle buttons
        self.__signals = {
            self.headerbar_item_fullscreen: self.fullscreen_signal_tool,
            self.menu_item_dark_theme: self.dark_signal_menu,
            self.menu_item_favorite: self.favorite_signal_menu,
            self.menu_item_finish: self.finish_signal_menu,
            self.menu_item_multiplayer: self.multi_signal_menu,
            self.menu_item_sidebar: self.side_signal_menu,
            self.menu_item_statusbar: self.status_signal_menu,
            self.menubar_game_item_favorite: self.favorite_signal_menubar,
            self.menubar_game_item_finish: self.finish_signal_menubar,
            self.menubar_game_item_fullscreen: self.fullscreen_signal,
            self.menubar_game_item_multiplayer: self.multi_signal_menubar,
            self.menubar_main_item_dark_theme: self.dark_signal_menubar,
            self.menubar_main_item_sidebar: self.side_signal_menubar,
            self.menubar_main_item_statusbar: self.status_signal_menubar,
            self.switch_consoles_favorite: self.favorite_signal_options,
            self.switch_consoles_recursive: self.recursive_signal_options,
        }

        self.load_interface(True)

        load_console_startup = \
            self.config.getboolean("gem", "load_console_startup", fallback=True)

        # Check last loaded console in gem.conf
        if load_console_startup:
            console = self.config.item("gem", "last_console", str())

            # A console has been saved
            if len(console) > 0:

                # Check if this console use the old console name value (< 0.8)
                if not console in self.api.consoles.keys():
                    console = generate_identifier(console)

                # Check if current identifier exists
                if console in self.api.consoles.keys() and \
                    console in self.consoles_iter.keys():
                    self.treeview_games.set_visible(True)

                    row = self.consoles_iter[console]

                    # Set console combobox active iter
                    self.button_consoles.select_row(row)

                    self.__on_selected_console(self.button_consoles, row)

                    # Set Console object as selected
                    self.selection["console"] = row.data

        # Check welcome message status in gem.conf
        if self.config.getboolean("gem", "welcome", fallback=True):

            # Load the first console to avoid mini combobox
            if load_console_startup and self.selection["console"] is None:
                self.button_consoles.select_row(
                    list(self.consoles_iter.values())[0])

            dialog = MessageDialog(self, _("Welcome !"),
                _("Welcome and thanks for choosing GEM as emulators manager. "
                "Start using GEM by droping some roms into interface.\n\n"
                "Enjoy and have fun :D"), Icons.SmileBig, False)

            dialog.set_size(500, -1)

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

        # ------------------------------------
        #   Threads
        # ------------------------------------

        # Remove games listing thread
        if not self.list_thread == 0:
            source_remove(self.list_thread)

        # Remove games launcher thread
        if len(self.threads.keys()) > 0:
            for thread in self.threads.copy().keys():
                self.threads[thread].proc.terminate()

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
        row = self.button_consoles.get_selected_row()
        if row is not None:
            last_console = self.config.item("gem", "last_console", None)

            # Avoid to modify gem.conf if console is already in conf
            if last_console is None or not last_console == row.data.id:
                self.config.modify("gem", "last_console", row.data.id)

                self.logger.info(
                    _("Save %s console for next startup") % row.data.id)

        # ------------------------------------
        #   Last sorted column
        # ------------------------------------

        column, order = self.sorted_games.get_sort_column_id()

        if column is not None and order is not None:

            for key, value in Columns.__dict__.items():
                if not key.startswith("__") and not key.endswith("__"):

                    if column == value:
                        self.config.modify("gem", "last_sort_column", key)

            if order == Gtk.SortType.ASCENDING:
                self.config.modify("gem", "last_sort_column_order", "asc")

            elif order == Gtk.SortType.DESCENDING:
                self.config.modify("gem", "last_sort_column_order", "desc")

        # ------------------------------------
        #   Windows size
        # ------------------------------------

        self.config.modify("windows", "main", "%dx%d" % self.get_size())
        self.config.update()

        self.logger.info(_("Close interface"))

        self.main_loop.quit()


    def load_interface(self, init_interface=False):
        """ Load main interface

        Parameters
        ----------
        init_interface : bool, optional
            Interface first initialization (Default: False)
        """

        self.__block_signals()

        self.api.init()

        # ------------------------------------
        #   Configuration
        # ------------------------------------

        self.config = Configuration(self.api.get_config("gem.conf"))

        # Get missing keys from config/gem.conf
        self.config.add_missing_data(get_data(path_join("config", "gem.conf")))

        # ------------------------------------
        #   Toolbar
        # ------------------------------------

        icon_size = self.config.get(
            "gem", "toolbar_icons_size", fallback="small-toolbar")

        if init_interface or \
            not self.toolbar_sizes[icon_size] == self.toolbar.get_icon_size():
            self.headerbar_image_menu.set_from_icon_name(
                Icons.Symbolic.Menu, self.toolbar_sizes[icon_size])
            self.menu_image_addons.set_from_icon_name(
                Icons.Symbolic.Addon, self.toolbar_sizes[icon_size])
            self.headerbar_image_fullscreen.set_from_icon_name(
                Icons.Symbolic.Restore, self.toolbar_sizes[icon_size])
            self.menu_image_preferences.set_from_icon_name(
                Icons.Symbolic.System, self.toolbar_sizes[icon_size])

            self.menu_image_about.set_from_icon_name(
                Icons.Symbolic.About, self.toolbar_sizes[icon_size])
            self.menu_image_quit.set_from_icon_name(
                Icons.Symbolic.Quit, self.toolbar_sizes[icon_size])
            self.menu_image_gem_log.set_from_icon_name(
                Icons.Symbolic.Terminal, self.toolbar_sizes[icon_size])

            self.toolbar.set_icon_size(self.toolbar_sizes[icon_size])

            self.toolbar_image_parameters.set_from_icon_name(
                Icons.Symbolic.Gaming, self.toolbar.get_icon_size())
            self.toolbar_image_screenshots.set_from_icon_name(
                Icons.Symbolic.Camera, self.toolbar.get_icon_size())
            self.toolbar_image_output.set_from_icon_name(
                Icons.Symbolic.Terminal, self.toolbar.get_icon_size())
            self.toolbar_image_notes.set_from_icon_name(
                Icons.Symbolic.Editor, self.toolbar.get_icon_size())

            self.toolbar_image_statistic.set_from_icon_name(
                Icons.Symbolic.Monitor, self.toolbar.get_icon_size())
            self.toolbar_image_properties.set_from_icon_name(
                Icons.Symbolic.Properties, self.toolbar.get_icon_size())
            self.toolbar_image_refresh.set_from_icon_name(
                Icons.Symbolic.Refresh, self.toolbar.get_icon_size())

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
        #   Window first drawing
        # ------------------------------------

        if init_interface:

            # ------------------------------------
            #   Column sorting
            # ------------------------------------

            if self.config.getboolean(
                "gem", "load_sort_column_startup", fallback=True):

                column = getattr(Columns, self.config.get(
                    "gem", "last_sort_column", fallback="Name"), None)
                order = self.config.get(
                    "gem", "last_sort_column_order", fallback="asc")

                if column is None:
                    column = Columns.Name
                    order = "asc"

                if order == "desc":
                    self.sorted_games.set_sort_column_id(
                        column, Gtk.SortType.DESCENDING)

                else:
                    self.sorted_games.set_sort_column_id(
                        column, Gtk.SortType.ASCENDING)

            else:
                self.sorted_games.set_sort_column_id(
                    Columns.Name, Gtk.SortType.ASCENDING)

            # ------------------------------------
            #   Color theme
            # ------------------------------------

            dark_theme_status = self.config.getboolean(
                "gem", "dark_theme", fallback=False)

            on_change_theme(dark_theme_status)

            self.menu_item_dark_theme.set_active(dark_theme_status)
            self.menubar_main_item_dark_theme.set_active(dark_theme_status)

            if dark_theme_status:
                self.logger.debug("Use dark variant for GTK+ theme")
            else:
                self.logger.debug("Use light variant for GTK+ theme")

            self.use_classic_theme = self.config.getboolean(
                "gem", "use_classic_theme", fallback=False)

            # ------------------------------------
            #   Window classic theme
            # ------------------------------------

            if not self.use_classic_theme:
                self.set_titlebar(self.headerbar)

                self.headerbar.pack_start(self.grid_game_launch)

            else:
                self.toolbar.insert(self.toolbar_item_game_launch, 0)
                self.toolbar.insert(Gtk.SeparatorToolItem(), 1)

                self.toolbar_item_game_launch.add(self.grid_game_launch)

            # ------------------------------------
            #   Window size
            # ------------------------------------

            try:
                width, height = self.config.get(
                    "windows", "main", fallback="1024x768").split('x')

                self.set_default_size(int(width), int(height))
                self.resize(int(width), int(height))

            except ValueError as error:
                self.logger.error(
                    _("Cannot resize main window: %s") % str(error))

                self.set_default_size(1024, 768)

            self.set_position(Gtk.WindowPosition.CENTER)

            self.hide()
            self.unrealize()

        # ------------------------------------
        #   Shortcuts
        # ------------------------------------

        self.__init_shortcuts()

        # ------------------------------------
        #   Modules
        # ------------------------------------

        self.__init_modules()

        # ------------------------------------
        #   Widgets
        # ------------------------------------

        self.show_all()

        self.menu_games.show_all()

        self.grid_main_popover.show_all()
        self.grid_filters_popover.show_all()

        self.grid_consoles_item.show_all()
        self.grid_consoles_popover.show_all()

        self.infobar.show_all()
        self.infobar.get_content_area().show_all()

        self.scroll_sidebar_tags.show_all()
        self.grid_sidebar_tab_tags.show_all()

        self.scroll_sidebar_informations.show_all()
        self.grid_sidebar_tab_informations.show_all()
        self.grid_sidebar_informations.show_all()

        if self.use_classic_theme:
            self.logger.debug("Use classic theme for GTK+ interface")
            self.menubar.show_all()

        else:
            self.logger.debug("Use default theme for GTK+ interface")
            self.menubar.hide()

        self.set_infobar()
        self.sensitive_interface()

        # ------------------------------------
        #   Sidebar notebook
        # ------------------------------------

        if init_interface:
            # Switch on "Informations" tab by default in sidebar notebook
            self.notebook_sidebar_game.set_current_page(0)

        # ------------------------------------
        #   Header
        # ------------------------------------

        if not self.config.getboolean("gem", "show_header", fallback=True):
            self.headerbar.set_show_close_button(False)
        else:
            self.headerbar.set_show_close_button(True)

        # ------------------------------------
        #   Sidebar
        # ------------------------------------

        self.sidebar_image = None

        sidebar_status = self.config.getboolean(
            "gem", "show_sidebar", fallback=True)

        self.menu_item_sidebar.set_active(sidebar_status)
        self.menubar_main_item_sidebar.set_active(sidebar_status)

        # Avoid to reload paned_game if user has not change orientation
        previous_mode = self.paned_games.get_orientation()
        if init_interface:
            previous_mode = None

        # Wanted sidebar orientation
        sidebar_orientation = self.config.get(
            "gem", "sidebar_orientation", fallback="vertical")

        # Right-side sidebar
        if sidebar_orientation == "horizontal" and \
            not previous_mode == Gtk.Orientation.HORIZONTAL:

            self.paned_games.set_position(-1)
            self.paned_games.set_orientation(Gtk.Orientation.HORIZONTAL)

            for child in self.grid_sidebar.get_children():
                self.grid_sidebar.remove(child)

            self.grid_sidebar.attach(
                self.grid_sidebar_title, 0, 0, 1, 1)
            self.grid_sidebar.attach(
                self.frame_sidebar_game, 0, 1, 1, 1)
            self.grid_sidebar.attach(
                self.notebook_sidebar_game, 0, 2, 1, 1)

            self.label_sidebar_title.set_halign(Gtk.Align.CENTER)

            self.grid_sidebar_informations.set_halign(Gtk.Align.FILL)

            self.view_image_sidebar_game.set_vexpand(False)
            self.view_image_sidebar_game.set_hexpand(True)

        # Bottom-side sidebar
        elif sidebar_orientation == "vertical" and \
            not previous_mode == Gtk.Orientation.VERTICAL:

            self.paned_games.set_position(-1)
            self.paned_games.set_orientation(Gtk.Orientation.VERTICAL)

            for child in self.grid_sidebar.get_children():
                self.grid_sidebar.remove(child)

            self.grid_sidebar.attach(
                self.grid_sidebar_title, 0, 0, 1, 1)
            self.grid_sidebar.attach(
                self.notebook_sidebar_game, 0, 1, 1, 1)
            self.grid_sidebar.attach(
                self.frame_sidebar_game, 1, 0, 1, 2)

            self.label_sidebar_title.set_halign(Gtk.Align.START)

            self.grid_sidebar_title.set_valign(Gtk.Align.START)

            self.grid_sidebar_informations.set_halign(Gtk.Align.START)

            self.view_image_sidebar_game.set_hexpand(False)
            self.view_image_sidebar_game.set_vexpand(True)

        # Show sidebar
        if sidebar_status:
            self.scroll_sidebar.show_all()

            self.frame_sidebar_game.set_visible(False)
            self.notebook_sidebar_game.set_visible(False)

        # Hide sidebar
        else:
            self.scroll_sidebar.hide()

        for key, label_key, label_value in self.widgets_sidebar:
            label_key.hide()
            label_value.hide()

        # ------------------------------------
        #   Statusbar
        # ------------------------------------

        statusbar_status = self.config.getboolean(
            "gem", "show_statusbar", fallback=True)

        self.menu_item_statusbar.set_active(statusbar_status)
        self.menubar_main_item_statusbar.set_active(statusbar_status)

        if statusbar_status:
            self.statusbar.show()

            self.image_statusbar_properties.show()
            self.image_statusbar_screenshots.show()
            self.image_statusbar_savestates.show()

        else:
            self.statusbar.hide()

        # ------------------------------------
        #   Games
        # ------------------------------------

        # Game rename status
        self.is_rename = False

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
            "score": self.column_game_score,
            "installed": self.column_game_installed,
            "flags": self.column_game_flags }

        for key, widget in columns.items():
            if not self.config.getboolean("columns", key, fallback=True):
                widget.set_visible(False)
            else:
                widget.set_visible(True)

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

        self.scroll_games.set_visible(False)
        self.grid_games_placeholder.set_visible(False)

        current_console = self.append_consoles()

        # Show games placeholder when no console available or selected
        if current_console is None or len(self.listbox_consoles) == 0:
            self.grid_games_placeholder.set_visible(True)

        self.selection = dict(
            console=None,
            game=None)

        if current_console is None:
            self.model_games.clear()

            if len(self.consoles_iter.keys()) > 0:
                row = list(self.consoles_iter.values())[0]

                self.button_consoles.select_row(row)

                self.__on_selected_console(self.button_consoles, row)

        else:
            self.button_consoles.select_row(current_console)

            self.__on_selected_console(self.button_consoles, current_console)

        self.__unblock_signals()


    def __init_modules(self):
        """ Initialize available modules

        Notes
        -----
        The modules are available in two folders

          - GEM source folder as gem/plugins/
          - User local folder as ~/.local/share/gem/plugins

        The modules in user local folder are taken hover GEM source folder
        """

        self.modules = dict()

        for path in [ get_data("plugins"), self.api.get_local("plugins") ]:

            if exists(path):

                # List available modules
                for plugin in glob(path_join(path, '*', "manifest.conf")):
                    config = Configuration(plugin)

                    # Check if module manifest is okay
                    if config.has_section("plugin"):
                        name = config.get("plugin", "name", fallback=str())

                        if len(name) > 0:
                            self.modules[name] = AddonThread(name, plugin)


    def sensitive_interface(self, status=False):
        """ Update sensitive status for main widgets

        Parameters
        ----------
        status : bool, optional
            Sensitive status (Default: False)
        """

        self.__on_game_launch_button_update(True)
        self.headerbar_item_launch.set_sensitive(status)

        self.menu_item_rename.set_sensitive(status)
        self.menu_item_favorite.set_sensitive(status)
        self.menu_item_multiplayer.set_sensitive(status)
        self.menu_item_finish.set_sensitive(status)
        self.menu_item_screenshots.set_sensitive(status)
        self.menu_item_output.set_sensitive(status)
        self.menu_item_notes.set_sensitive(status)
        self.menu_item_copy.set_sensitive(status)
        self.menu_item_open.set_sensitive(status)
        self.menu_item_cover.set_sensitive(status)
        self.menu_item_desktop.set_sensitive(status)
        self.menu_item_remove.set_sensitive(status)
        self.menu_item_database.set_sensitive(status)
        self.menu_item_mednafen.set_sensitive(status)
        self.menu_item_duplicate.set_sensitive(status)

        self.toolbar_item_output.set_sensitive(status)
        self.toolbar_item_notes.set_sensitive(status)
        self.toolbar_item_parameters.set_sensitive(status)
        self.toolbar_item_screenshots.set_sensitive(status)

        self.toolbar_item_statistic.set_sensitive(status)
        self.toolbar_item_properties.set_sensitive(status)
        self.toolbar_item_refresh.set_sensitive(status)
        self.switch_consoles_favorite.set_sensitive(status)
        self.switch_consoles_recursive.set_sensitive(status)

        self.menubar_game_item_launch.set_sensitive(status)
        self.menubar_game_item_favorite.set_sensitive(status)
        self.menubar_game_item_multiplayer.set_sensitive(status)
        self.menubar_game_item_finish.set_sensitive(status)
        self.menubar_game_item_screenshots.set_sensitive(status)
        self.menubar_game_item_output.set_sensitive(status)
        self.menubar_game_item_notes.set_sensitive(status)
        self.menubar_game_item_properties.set_sensitive(status)
        self.menubar_edit_item_rename.set_sensitive(status)
        self.menubar_edit_item_copy.set_sensitive(status)
        self.menubar_edit_item_open.set_sensitive(status)
        self.menubar_edit_item_cover.set_sensitive(status)
        self.menubar_edit_item_desktop.set_sensitive(status)
        self.menubar_edit_item_database.set_sensitive(status)
        self.menubar_edit_item_delete.set_sensitive(status)
        self.menubar_edit_item_mednafen.set_sensitive(status)
        self.menubar_edit_item_score.set_sensitive(status)
        self.menubar_edit_item_duplicate.set_sensitive(status)


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

        active_filter = False
        for child in self.grid_filters_popover.get_children():

            if type(child) is Gtk.Switch:
                active_filter = active_filter or not child.get_active()

        if active_filter:
            self.tool_menu_filters.get_style_context().add_class(
                "suggested-action")
        else:
            self.tool_menu_filters.get_style_context().remove_class(
                "suggested-action")

        self.filter_games.refilter()

        self.check_selection()

        self.set_informations_headerbar(
            self.selection["game"], self.selection["console"])


    def filters_reset(self, widget=None, events=None):
        """ Reset game filters

        Parameters
        ----------
        widget : Gtk.Widget, optional
            Object which receive signal (Default: None)
        event : Gdk.EventButton or Gdk.EventKey, optional
            Event which triggered this signal (Default: None)
        """

        for child in self.grid_filters_popover.get_children():

            if type(child) is Gtk.Switch:
                child.set_active(True)

        self.tool_menu_filters.get_style_context().remove_class(
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
        game = model.get_value(row, Columns.Object)

        try:
            text = self.entry_filter.get_text()

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

                # Check if one the two checkbox is not active
                if not (first and second):
                    found = found and (
                        (status and first) or (not status and second))

        except:
            pass

        return found


    def __on_filter_tag(self, widget, row):
        """ Refilter games list with a new tag

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        row : Gtk.ListBoxRow
            Activated ListBox row which contain a specific tag
        """

        text = str()

        if len(row.get_children()) > 0:
            box = row.get_children()[0]

            if len(box.get_children()) > 0:
                label = box.get_children()[0]

                if not self.entry_filter.get_text() == label.get_label():
                    text = label.get_label()

        self.entry_filter.set_text(text)


    def __init_shortcuts(self):
        """ Generate shortcuts signals from user configuration
        """

        shortcuts = [
            {
                "path": "<GEM>/game/open",
                "widgets": [
                    self.menu_item_open,
                    self.menubar_edit_item_open
                ],
                "keys": self.config.item("keys", "open", "<Control>O")
            },
            {
                "path": "<GEM>/game/copy",
                "widgets": [
                    self.menu_item_copy,
                    self.menubar_edit_item_copy
                ],
                "keys": self.config.item("keys", "copy", "<Control>C")
            },
            {
                "path": "<GEM>/game/desktop",
                "widgets": [
                    self.menu_item_desktop,
                    self.menubar_edit_item_desktop
                ],
                "keys": self.config.item("keys", "desktop", "<Control>G")
            },
            {
                "path": "<GEM>/game/start",
                "widgets": [
                    self.menu_item_launch,
                    self.menubar_game_item_launch
                ],
                "keys": self.config.item("keys", "start", "Return")
            },
            {
                "path": "<GEM>/game/rename",
                "widgets": [
                    self.menu_item_rename,
                    self.menubar_edit_item_rename
                ],
                "keys": self.config.item("keys", "rename", "F2")
            },
            {
                "path": "<GEM>/game/duplicate",
                "widgets": [
                    self.menu_item_duplicate,
                    self.menubar_edit_item_duplicate
                ],
                "keys": self.config.item("keys", "duplicate", "<Control>U")
            },
            {
                "path": "<GEM>/game/favorite",
                "widgets": [
                    self.menu_item_favorite,
                    self.menubar_game_item_favorite
                ],
                "keys": self.config.item("keys", "favorite", "F3")
            },
            {
                "path": "<GEM>/game/multiplayer",
                "widgets": [
                    self.menu_item_multiplayer,
                    self.menubar_game_item_multiplayer
                ],
                "keys": self.config.item("keys", "multiplayer", "F4")
            },
            {
                "path": "<GEM>/game/finish",
                "widgets": [
                    self.menu_item_finish,
                    self.menubar_game_item_finish
                ],
                "keys": self.config.item("keys", "finish", "<Control>F3")
            },
            {
                "path": "<GEM>/game/score/up",
                "widgets": [
                    self.menu_item_score_up,
                    self.menubar_edit_item_score_up
                ],
                "keys": self.config.item(
                    "keys", "score-up", "<Control>Page_Up")
            },
            {
                "path": "<GEM>/game/score/down",
                "widgets": [
                    self.menu_item_score_down,
                    self.menubar_edit_item_score_down
                ],
                "keys": self.config.item(
                    "keys", "score-down", "<Control>Page_Down")
            },
            {
                "path": "<GEM>/game/score/0",
                "widgets": [
                    self.menu_item_score_0,
                    self.menubar_edit_item_score_0
                ],
                "keys": self.config.item(
                    "keys", "score-0", "<Primary>0")
            },
            {
                "path": "<GEM>/game/score/1",
                "widgets": [
                    self.menu_item_score_1,
                    self.menubar_edit_item_score_1
                ],
                "keys": self.config.item(
                    "keys", "score-1", "<Primary>1")
            },
            {
                "path": "<GEM>/game/score/2",
                "widgets": [
                    self.menu_item_score_2,
                    self.menubar_edit_item_score_2
                ],
                "keys": self.config.item(
                    "keys", "score-2", "<Primary>2")
            },
            {
                "path": "<GEM>/game/score/3",
                "widgets": [
                    self.menu_item_score_3,
                    self.menubar_edit_item_score_3
                ],
                "keys": self.config.item(
                    "keys", "score-3", "<Primary>3")
            },
            {
                "path": "<GEM>/game/score/4",
                "widgets": [
                    self.menu_item_score_4,
                    self.menubar_edit_item_score_4
                ],
                "keys": self.config.item(
                    "keys", "score-4", "<Primary>4")
            },
            {
                "path": "<GEM>/game/score/5",
                "widgets": [
                    self.menu_item_score_5,
                    self.menubar_edit_item_score_5
                ],
                "keys": self.config.item(
                    "keys", "score-5", "<Primary>5")
            },
            {
                "path": "<GEM>/game/cover",
                "widgets": [
                    self.menu_item_cover,
                    self.menubar_edit_item_cover
                ],
                "keys": self.config.item("keys", "cover", "<Control>I")
            },
            {
                "path": "<GEM>/game/screenshots",
                "widgets": [
                    self.menu_item_screenshots,
                    self.menubar_game_item_screenshots,
                    self.toolbar_item_screenshots
                ],
                "keys": self.config.item("keys", "snapshots", "F5")
            },
            {
                "path": "<GEM>/game/log",
                "widgets": [
                    self.menu_item_output,
                    self.menubar_game_item_output
                ],
                "keys": self.config.item("keys", "log", "F6")
            },
            {
                "path": "<GEM>/game/notes",
                "widgets": [
                    self.menu_item_notes,
                    self.menubar_game_item_notes
                ],
                "keys": self.config.item("keys", "notes", "F7")
            },
            {
                "path": "<GEM>/game/memory",
                "widgets": [
                    self.menu_item_mednafen,
                    self.menubar_edit_item_mednafen
                ],
                "keys": self.config.item("keys", "memory", "F8")
            },
            {
                "path": "<GEM>/fullscreen",
                "widgets": [
                    self,
                    self.menubar_game_item_fullscreen
                ],
                "keys": self.config.item("keys", "fullscreen", "F11"),
                "function": self.__on_activate_fullscreen
            },
            {
                "path": "<GEM>/sidebar",
                "widgets": [
                    self,
                    self.menubar_main_item_sidebar
                ],
                "keys": self.config.item("keys", "sidebar", "F9"),
                "function": self.__on_activate_sidebar
            },
            {
                "path": "<GEM>/statusbar",
                "widgets": [
                    self,
                    self.menubar_main_item_statusbar
                ],
                "keys": self.config.item("keys", "statusbar", "<Control>F9"),
                "function": self.__on_activate_statusbar
            },
            {
                "path": "<GEM>/game/exceptions",
                "widgets": [
                    self.menu_item_properties,
                    self.menubar_game_item_properties
                ],
                "keys": self.config.item("keys", "exceptions", "F12")
            },
            {
                "path": "<GEM>/game/delete",
                "widgets": [
                    self.menu_item_remove,
                    self.menubar_edit_item_delete
                ],
                "keys": self.config.item("keys", "delete", "<Control>Delete")
            },
            {
                "path": "<GEM>/game/remove",
                "widgets": [
                    self.menu_item_database,
                    self.menubar_edit_item_database
                ],
                "keys": self.config.item("keys", "remove", "Delete")
            },
            {
                "path": "<GEM>/preferences",
                "widgets": [
                    self,
                    self.menubar_main_item_preferences
                ],
                "keys": self.config.item("keys", "preferences", "<Control>P"),
                "function": self.__on_show_preferences
            },
            {
                "path": "<GEM>/addons",
                "widgets": [
                    self,
                    self.menubar_main_item_addons
                ],
                "keys": self.config.item("keys", "addons", "<Control>M"),
                "function": self.__on_show_modules
            },
            {
                "path": "<GEM>/log",
                "widgets": [
                    self,
                    self.menubar_main_item_log
                ],
                "keys": self.config.item("keys", "gem", "<Control>L"),
                "function": self.__on_show_log
            },
            {
                "path": "<GEM>/quit",
                "widgets": [
                    self,
                    self.menubar_main_item_quit
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
                            self.shortcuts_group.connect(key, mod,
                                Gtk.AccelFlags.VISIBLE, data["function"])

                    # Local signals
                    else:
                        widget.add_accelerator("activate", self.shortcuts_group,
                            key, mod, Gtk.AccelFlags.VISIBLE)

                    # Store current shortcut to remove it properly later
                    self.shortcuts.append((key, mod))


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
        konami_code = [Gdk.KEY_Up, Gdk.KEY_Up, Gdk.KEY_Down, Gdk.KEY_Down,
            Gdk.KEY_Left, Gdk.KEY_Right, Gdk.KEY_Left, Gdk.KEY_Right]

        if event.keyval in konami_code:
            self.keys.append(event.keyval)

            if self.keys == konami_code:
                dialog = MessageDialog(self, "Someone wrote the KONAMI CODE !",
                    "Nice catch ! You have discover an easter-egg ! But, this "
                    "kind of code is usefull in a game, not in an emulators "
                    "manager !", Icons.Symbolic.Monkey)

                dialog.set_size(500, -1)

                dialog.run()
                dialog.destroy()

                self.keys = list()

            if not self.keys == konami_code[0:len(self.keys)]:
                self.keys = list()


    def set_informations(self):
        """ Update headerbar title and subtitle
        """

        self.sidebar_image = None

        game = self.selection["game"]
        console = self.selection["console"]

        self.set_informations_headerbar(game, console)

        self.frame_sidebar_game.set_visible(False)
        self.image_sidebar_title.set_visible(False)
        self.notebook_sidebar_game.set_visible(False)

        # ----------------------------
        #   Game informations
        # ----------------------------

        children = self.listbox_sidebar_tags.get_children()

        # Remove previous tags
        for widget in children:
            self.listbox_sidebar_tags.remove(widget)
            # Delete widget instance
            del widget

        if game is not None:

            if console is not None:
                self.notebook_sidebar_game.set_visible(True)

                self.label_sidebar_title.set_markup(
                    "<span weight='bold' size='x-large'>%s</span>" % \
                    replace_for_markup(game.name))

                # Get rom specified emulator
                emulator = console.emulator

                if game.emulator is not None:
                    emulator = game.emulator

                # ----------------------------
                #   Show screenshot
                # ----------------------------

                image = None

                screenshots = sorted(emulator.get_screenshots(game))

                # Check if rom has some screenshots
                if len(screenshots) > 0:
                    self.image_statusbar_screenshots.set_from_pixbuf(
                        self.icons["snap"])

                    # Get the latest screenshot from list
                    index = -1

                    # Get a random file from rom screenshots
                    if self.config.getboolean(
                        "gem", "show_random_screenshot", fallback=True):
                        index = randint(0, len(screenshots) - 1)

                    image = screenshots[index]

                # No screenshots available
                else:
                    self.image_statusbar_screenshots.set_from_pixbuf(
                        self.alternative["snap"])

                # A special cover image has been set by user
                # if game.cover is not None and exists(game.cover):
                    # image = game.cover

                # An image has been set
                if image is not None and exists(image):
                    self.sidebar_image = image

                    orientation = self.paned_games.get_orientation()

                    if orientation == Gtk.Orientation.HORIZONTAL:
                        image = Pixbuf.new_from_file_at_scale(
                            image, 418, 418, True)

                    else:
                        image = Pixbuf.new_from_file_at_scale(
                            image, 260, 260, True)

                self.image_sidebar_game.set_from_pixbuf(image)

                if image is not None:
                    self.frame_sidebar_game.set_visible(True)

                # ----------------------------
                #   Show cover
                # ----------------------------

                image = None

                # A special cover image has been set by user
                if game.cover is not None and exists(game.cover):
                    image = game.cover

                    image = Pixbuf.new_from_file_at_scale(
                        image, 64, 24, True)

                self.image_sidebar_title.set_from_pixbuf(image)

                if image is not None:
                    self.image_sidebar_title.set_visible(True)

                # ----------------------------
                #   Show informations
                # ----------------------------

                widgets = {
                    "played": {
                        "condition": game.played > 0,
                        "markup": str(game.played),
                        "tooltip": None
                    },
                    "play_time": {
                        "condition": not game.play_time == timedelta(),
                        "markup": string_from_time(game.play_time),
                        "tooltip": parse_timedelta(game.play_time)
                    },
                    "last_play": {
                        "condition": game.last_launch_date is not None,
                        "markup": string_from_date(game.last_launch_date),
                        "tooltip": str(game.last_launch_date)
                    },
                    "last_time": {
                        "condition": not game.last_launch_time == timedelta(),
                        "markup": string_from_time(game.last_launch_time),
                        "tooltip": parse_timedelta(game.last_launch_time)
                    }
                }

                for key, label_key, label_value in self.widgets_sidebar:
                    data = widgets[key]

                    if data["condition"]:
                        label_key.show()
                        label_value.show()

                        label_value.set_markup(data["markup"])

                        if data["tooltip"] is not None:
                            label_value.set_tooltip_text(data["tooltip"])

                    else:
                        label_key.hide()
                        label_value.hide()

                        label_value.set_markup(str())
                        label_value.set_tooltip_text(str())

                # Game tags
                for tag in sorted(game.tags):
                    label = Gtk.Label.new(tag)
                    label.set_halign(Gtk.Align.START)

                    box = Gtk.Box()
                    box.set_orientation(Gtk.Orientation.HORIZONTAL)
                    box.set_border_width(6)

                    box.pack_start(label, True, True, 0)

                    row = Gtk.ListBoxRow()
                    row.add(box)
                    row.show_all()

                    self.listbox_sidebar_tags.add(row)

                # Game emulator
                if emulator is not None:

                    # Game savestates
                    if len(emulator.get_savestates(game)) > 0:
                        self.image_statusbar_savestates.set_from_pixbuf(
                            self.icons["save"])
                    else:
                        self.image_statusbar_savestates.set_from_pixbuf(
                            self.alternative["save"])

                    # Game custom parameters
                    if (game.emulator is not None and \
                        not game.emulator.name == console.emulator.name) or \
                        game.default is not None:
                        self.image_statusbar_properties.set_from_pixbuf(
                            self.icons["except"])
                    else:
                        self.image_statusbar_properties.set_from_pixbuf(
                            self.alternative["except"])

                else:
                    self.image_statusbar_savestates.set_from_pixbuf(self.empty)
                    self.image_statusbar_properties.set_from_pixbuf(self.empty)
                    self.image_statusbar_screenshots.set_from_pixbuf(self.empty)

        else:
            for key, label_key, label_value in self.widgets_sidebar:
                label_key.hide()
                label_value.hide()

            self.label_sidebar_title.set_text(str())

            self.image_sidebar_game.set_from_pixbuf(None)

            self.image_statusbar_properties.set_from_pixbuf(self.empty)
            self.image_statusbar_savestates.set_from_pixbuf(self.empty)
            self.image_statusbar_screenshots.set_from_pixbuf(self.empty)


    def set_informations_headerbar(self, game, console):
        """ Update headerbar and statusbar informations from games list

        Parameters
        ----------
        game : gem.engine.api.Game
            Game object
        console : gem.api.Console
            Console object
        """

        self.label_statusbar_console.set_visible(False)
        self.label_statusbar_emulator.set_visible(False)

        texts = list()
        emulator = None

        # ----------------------------
        #   Console
        # ----------------------------

        if console is not None:
            emulator = console.emulator

            if len(self.filter_games) == 1:
                text = _("1 game available")

                texts.append(text)

            elif len(self.filter_games) > 1:
                text = _("%d games available") % len(self.filter_games)

                texts.append(text)

            else:
                text = _("N/A")

            self.label_statusbar_console.set_visible(True)
            self.label_statusbar_console.set_markup(
                "<b>%s</b> : %s" % (console.name, text))

        else:
            self.label_statusbar_console.set_visible(False)

        # ----------------------------
        #   Game
        # ----------------------------

        if game is not None:
            self.label_statusbar_game.set_visible(True)
            self.label_statusbar_game.set_text(game.name)

            if game.emulator is not None:
                emulator = game.emulator

            texts.append(game.name)

        else:
            self.label_statusbar_game.set_visible(False)

        # ----------------------------
        #   Emulator
        # ----------------------------

        if emulator is not None:
            self.label_statusbar_emulator.set_visible(True)
            self.label_statusbar_emulator.set_markup(
                "<b>%s</b> : %s" % (_("Emulator"), emulator.name))

        else:
            self.label_statusbar_emulator.set_visible(False)

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

        if icon == Icons.Error:
            self.logger.error(message)
        elif icon == Icons.Warning:
            self.logger.warning(message)
        else:
            self.logger.info(message)

        if popup:
            dialog = MessageDialog(self, title, message, icon)

            dialog.run()
            dialog.destroy()


    def set_infobar(self,
        text=str(), log=str(), message_type=Gtk.MessageType.INFO):
        """ Set infobar content

        This function set the infobar widget to inform user for specific things

        Parameters
        ----------
        text : str, optional
            Message text (Default: None)
        text : str, optional
            Logger text (Default: None)
        message_type : Gtk.MessageType, optional
            Message type (Default: Gtk.MessageType.INFO)
        """

        if len(log) == 0 and len(text) > 0:
            log = text

        # Set a logger message
        if len(log) > 0:
            if message_type is Gtk.MessageType.ERROR:
                self.logger.error(log)
            elif message_type is Gtk.MessageType.WARNING:
                self.logger.warning(log)

        self.infobar.set_message_type(message_type)

        # Set infobar visibility
        if len(text) > 0:
            if len(self.grid_infobar.get_children()) == 0:
                self.grid_infobar.pack_start(self.infobar, True, True, 0)

        elif len(self.grid_infobar.get_children()) > 0:
            self.grid_infobar.remove(self.infobar)

        self.label_infobar.set_markup(text)


    def __on_show_about(self, *args):
        """ Show about dialog
        """

        self.set_sensitive(False)

        about = Gtk.AboutDialog(use_header_bar=not self.use_classic_theme)

        about.set_transient_for(self)

        about.set_program_name(GEM.Name)
        about.set_version("%s (%s)" % (GEM.Version, GEM.CodeName))
        about.set_comments(GEM.Description)
        about.set_copyright(GEM.Copyleft)
        about.set_website(GEM.Website)

        about.set_logo_icon_name(GEM.Icon)

        about.set_authors([
            "Lubert Aurélien (PacMiam)" ])
        about.set_artists([
            "Tango projects - GPLv3",
            "Gelide projects - GPLv3",
            "Evan-Amos - CC-by-SA 3.0" ])
        about.set_translator_credits(
            _("translator-credits"))
        about.set_license_type(
            Gtk.License.GPL_3_0)

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

        game = self.selection["game"]
        console = self.selection["console"]

        if game is not None and console is not None:
            # Get name and extension from game
            gamename, ext = splitext(game.path[-1])

            # Get rom specified emulator
            emulator = console.emulator

            if game.emulator is not None:
                emulator = game.emulator

            # Check if rom has some screenshots
            results = emulator.get_screenshots(game)

            # ----------------------------
            #   Show screenshots viewer
            # ----------------------------

            if len(results) > 0:
                title = "%s (%s)" % (game.name, console.name)

                self.set_sensitive(False)

                # Get external viewer
                viewer = self.config.get("viewer", "binary")

                if self.config.getboolean("viewer", "native", fallback=True):
                    try:
                        size = self.config.get(
                            "windows", "viewer", fallback="800x600").split('x')

                    except ValueError as error:
                        size = (800, 600)

                    dialog = ViewerDialog(self, title, size, sorted(results))
                    dialog.run()

                    self.config.modify(
                        "windows", "viewer", "%dx%d" % dialog.get_size())
                    self.config.update()

                    dialog.destroy()

                elif exists(viewer):
                    command = list()

                    # Append binaries
                    command.extend(shlex_split(viewer))

                    # Append arguments
                    args = self.config.item("viewer", "options")

                    if args is not None:
                        command.extend(shlex_split(args))

                    # Append game file
                    command.extend(sorted(results))

                    process = Popen(command)
                    process.wait()

                else:
                    self.set_message(_("Cannot open screenshots viewer"),
                        _("Cannot find <b>%s</b>") % viewer, Icons.Warning)

                self.set_sensitive(True)

                # ----------------------------
                #   Check screenshots
                # ----------------------------

                if len(emulator.get_screenshots(game)) == 0:
                    self.set_game_data(Columns.Snapshots,
                        self.alternative["snap"], game.filename)


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


    def __on_show_modules(self, *args):
        """ Show modules window
        """

        self.set_sensitive(False)

        dialog = ModulesDialog(self)

        dialog.run()
        dialog.destroy()

        self.set_sensitive(True)


    def __on_show_log(self, *args):
        """ Show gem log

        This function show the gem log content in a non-editable dialog
        """

        path = self.api.get_local("gem.log")

        game = self.selection["game"]

        if path is not None and exists(expanduser(path)):
            try:
                size = self.config.get(
                    "windows", "log", fallback="800x600").split('x')

            except ValueError as error:
                size = (800, 600)

            self.set_sensitive(False)

            dialog = EditorDialog(self, _("GEM"),
                expanduser(path), size, False, Icons.Symbolic.Terminal)

            dialog.run()

            self.config.modify("windows", "log", "%dx%d" % dialog.get_size())
            self.config.update()

            self.set_sensitive(True)

            dialog.destroy()


    def __on_show_notes(self, *args):
        """ Edit game notes

        This function allow user to write some notes for a specific game. The
        user can open as many notes he wants but cannot open a note already
        open
        """

        game = self.selection["game"]

        if game is not None:
            path = self.api.get_local("notes", game.id + ".txt")

            if path is not None and not expanduser(path) in self.notes.keys():
                try:
                    size = self.config.get(
                        "windows", "notes", fallback="800x600").split('x')

                except ValueError as error:
                    size = (800, 600)

                dialog = EditorDialog(self, game.name,
                    expanduser(path), size, icon=Icons.Symbolic.Document)

                # Allow to launch games with open notes
                dialog.set_modal(False)

                dialog.window.connect("response", self.__on_show_notes_response,
                    dialog, game.name, expanduser(path))

                dialog.show_all()

                # Save dialogs to close it properly when gem terminate and avoid
                # to reopen existing one
                self.notes[expanduser(path)] = dialog

            elif expanduser(path) in self.notes.keys():
                self.notes[expanduser(path)].grab_focus()


    def __on_show_notes_response(self, widget, response, dialog, title, path):
        """ Close notes dialog

        This function close current notes dialog and save his textview buffer to
        the game notes file

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
        path : str
            Notes path
        """

        if response == Gtk.ResponseType.APPLY:
            text_buffer = dialog.buffer_editor.get_text(
                dialog.buffer_editor.get_start_iter(),
                dialog.buffer_editor.get_end_iter(), True)

            if len(text_buffer) > 0:
                with open(path, 'w') as pipe:
                    pipe.write(text_buffer)

                self.logger.info(_("Update note for %s") % title)

        self.config.modify("windows", "notes", "%dx%d" % dialog.get_size())
        self.config.update()

        dialog.destroy()

        if path in self.notes.keys():
            del self.notes[path]


    def __on_show_emulator_config(self, *args):
        """ Edit emulator configuration file
        """

        game = self.selection["game"]
        console = self.selection["console"]

        if console is not None:
            emulator = console.emulator

            if game is not None and game.emulator is not None:
                emulator = game.emulator

            if emulator.configuration is not None:
                path = emulator.configuration

                if path is not None and exists(expanduser(path)):
                    try:
                        size = self.config.get(
                            "windows", "editor", fallback="800x600").split('x')

                    except ValueError as error:
                        size = (800, 600)

                    self.set_sensitive(False)

                    dialog = EditorDialog(self,
                        _("Edit %s configuration") % (emulator.name),
                        expanduser(path), size, icon=Icons.Symbolic.Document)

                    if dialog.run() == Gtk.ResponseType.APPLY:
                        with open(path, 'w') as pipe:
                            pipe.write(dialog.buffer_editor.get_text(
                                dialog.buffer_editor.get_start_iter(),
                                dialog.buffer_editor.get_end_iter(), True))

                        self.logger.info(
                            _("Update %s configuration file") % emulator.name)

                    self.config.modify(
                        "windows", "editor", "%dx%d" % dialog.get_size())
                    self.config.update()

                    self.set_sensitive(True)

                    dialog.destroy()


    def append_consoles(self):
        """ Append to consoles combobox all available consoles

        This function add every consoles into consoles combobox and inform user
        when an emulator binary is missing

        Returns
        -------
        Gtk.TreeIter or None
            Selected row
        """

        item = None

        size = 24

        # Reset consoles caches
        self.consoles_iter.clear()

        # Remove previous consoles objects
        self.button_consoles.clear()

        # Get toolbar icons size
        data = Gtk.IconSize.lookup(self.toolbar.get_icon_size())
        if data is not None and len(data) == 3:
            # Get maximum icon size (this size cannot be under 24 pixels)
            size = max(size, data[1], data[2])

        for console in self.api.consoles:
            console_data = self.__on_generate_console_row(console, size)

            if console_data is not None:
                row = self.button_consoles.append_row(*console_data)

                # Store console iter
                self.consoles_iter[row.data.id] = row

                # Check if previous selected console was this one
                selection = self.selection.get("console")
                if selection is not None and selection.name == row.data.name:
                    item = row

        self.__on_update_consoles()

        if len(self.listbox_consoles) > 0:
            self.logger.debug(
                "%d console(s) has been added" % len(self.listbox_consoles))

        return item


    def __on_generate_console_row(self, identifier, size):
        """ Generate console row data from a specific console

        Parameters
        ----------
        identifier : str
            Console identifier
        size : int
            Console icon size in pixels

        Returns
        -------
        tuple or None
            Generation results
        """

        console = self.api.get_console(identifier)

        # Reload games list
        console.set_games(self.api)

        # Check if console ROM path exist
        if console.emulator is not None and exists(console.path):
            status = self.empty

            # Check if current emulator can be launched
            if not console.emulator.exists:
                status = self.icons["warning"]

                self.logger.warning(
                    _("Cannot find %(binary)s for %(console)s") % {
                        "binary": console.emulator.binary,
                        "console": console.name })

            elif console.favorite:
                status = self.icons["favorite"]

            icon = console.icon
            if not exists(expanduser(icon)):
                icon = self.api.get_local(
                    "icons", "consoles", "%s.%s" % (icon, Icons.Ext))

            # Get console icon
            icon = icon_from_data(icon, self.empty, size, size)

            return(console, icon, status)

        return None


    def __on_selected_console(self, widget, row):
        """ Select a console

        This function occurs when the user select a console in the consoles
        listbox

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        row : gem.gtk.widgets.ListBoxSelectorItem
            Activated row
        """

        self.__block_signals()

        self.selection["name"] = None
        self.selection["game"] = None
        self.selection["console"] = row.data

        self.set_infobar()
        self.set_informations()

        # ------------------------------------
        #   Check data
        # ------------------------------------

        self.sensitive_interface()

        # Check console emulator
        if row.data.emulator is not None:
            configuration = row.data.emulator.configuration

            # Check emulator configurator
            if configuration is not None and exists(configuration):
                self.toolbar_item_properties.set_sensitive(True)
            else:
                self.toolbar_item_properties.set_sensitive(False)

        # Check console options
        self.switch_consoles_favorite.set_active(row.data.favorite)
        self.switch_consoles_recursive.set_active(row.data.recursive)

        # Activate console options buttons
        self.toolbar_item_refresh.set_sensitive(True)
        self.switch_consoles_favorite.set_sensitive(True)
        self.switch_consoles_recursive.set_sensitive(True)

        # Set console informations into button grid widgets
        self.button_consoles.select_row(row)

        self.__unblock_signals()

        # ------------------------------------
        #   Load game list
        # ------------------------------------

        if not self.list_thread == 0:
            source_remove(self.list_thread)

        loader = self.append_games(row.data)
        self.list_thread = idle_add(loader.__next__)


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
        if first_row.data.favorite == second_row.data.favorite:
            return first_row.data.name.lower() > \
                second_row.data.name.lower()

        return first_row.data.favorite < second_row.data.favorite


    def __on_filter_consoles(self, row, *args):
        """ Filter list with consoles searchentry text

        Parameters
        ----------
        row : gem.gtk.widgets.ListBoxSelectorItem
            Activated row
        """

        hide = self.config.getboolean(
            "gem", "hide_empty_console", fallback=False)

        if hide and len(row.data.games) == 0:
            return False

        # Retrieve row label text
        text = row.get_label().get_text().lower()

        try:
            filter_text = self.entry_consoles.get_text().strip().lower()

            if len(filter_text) == 0:
                return True

            return filter_text in text

        except:
            return False


    def __on_update_consoles(self, *args):
        """ Reload consoles list when user set a filter
        """

        self.button_consoles.invalidate_sort()
        self.button_consoles.invalidate_filter()


    def __on_change_console_option(self, widget, status):
        """ Change a console option switch

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        status : bool
            New status for current widget
        """

        widget.set_active(status)

        row = self.button_consoles.get_selected_row()

        if row is not None:

            if widget == self.switch_consoles_recursive:
                row.data.recursive = status

                self.api.write_object(row.data)

            elif widget == self.switch_consoles_favorite:
                row.data.favorite = status

                pixbuf = self.empty
                if status:
                    pixbuf = self.icons["favorite"]

                self.button_consoles.set_row_status(row, pixbuf)

                self.api.write_object(row.data)

                self.__on_update_consoles()


    def append_games(self, console):
        """ Append to games treeview all games from console

        This function add every games which match console extensions to games
        treeview

        Parameters
        ----------
        console : gem.engine.api.Console
            Console object

        Raises
        ------
        TypeError
            if console type is not gem.engine.api.Console

        Notes
        -----
        Using yield avoid an UI freeze when append a lot of games
        """

        if type(console) is not Console:
            raise TypeError(
                "Wrong type for console, expected gem.engine.api.Console")

        iteration = int()

        # Get current thread id
        current_thread_id = self.list_thread

        self.game_path = dict()

        # ------------------------------------
        #   Check errors
        # ------------------------------------

        if console.emulator is None:
            self.set_infobar(
                _("There is no default emulator set for this console"),
                _("Cannot find emulator for %s") % console.name,
                Gtk.MessageType.WARNING)

        elif not console.emulator.exists:
            self.set_infobar(_("<b>%s</b> cannot been found on your "
                "system") % console.emulator.name,
                _("%s emulator not exist") % console.emulator.name,
                Gtk.MessageType.ERROR)

        # ------------------------------------
        #   Load data
        # ------------------------------------

        self.scroll_games.set_visible(False)
        self.grid_games_placeholder.set_visible(True)

        self.model_games.clear()

        if console.emulator is not None:
            self.selection["console"] = console

            # ------------------------------------
            #   Refresh treeview
            # ------------------------------------

            self.treeview_games.set_enable_search(False)
            self.treeview_games.freeze_child_notify()

            # ------------------------------------
            #   Load games
            # ------------------------------------

            console.set_games(self.api)

            emulator = self.api.get_emulator(console.emulator.id)

            games = console.get_games()

            if len(games) > 0:
                self.scroll_games.set_visible(True)
                self.grid_games_placeholder.set_visible(False)

            yield True

            for game in games:

                # Another thread has been called by user, close this one
                if not current_thread_id == self.list_thread:
                    yield False

                # Hide games which match ignores regex
                show = True
                for element in console.ignores:
                    try:
                        if match(element, game.name, IGNORECASE) is not None:
                            show = False
                            break
                    except:
                        pass

                # Check if rom file exists
                if exists(game.filepath) and show:

                    row_data = [
                        self.alternative["favorite"],
                        self.alternative["multiplayer"],
                        self.alternative["unfinish"],
                        game.name,
                        int(),          # Played
                        str(),          # Last launch date
                        str(),          # Last launch time
                        str(),          # Total play time
                        game.score,
                        str(),          # Installed date
                        self.alternative["except"],
                        self.alternative["snap"],
                        self.alternative["save"],
                        game ]

                    # Favorite
                    if game.favorite:
                        row_data[Columns.Favorite] = self.icons["favorite"]

                    # Multiplayer
                    if game.multiplayer:
                        row_data[Columns.Multiplayer] = \
                            self.icons["multiplayer"]

                    # Finish
                    if game.finish:
                        row_data[Columns.Finish] = self.icons["finish"]

                    # Played
                    if game.played > 0:
                        row_data[Columns.Played] = game.played

                    # Last launch date
                    if game.last_launch_date is not None:
                        row_data[Columns.LastPlay] = \
                            string_from_date(game.last_launch_date)

                    # Last launch time
                    if not game.last_launch_time == timedelta():
                        row_data[Columns.LastTimePlay] = \
                            string_from_time(game.last_launch_time)

                    # Play time
                    if not game.play_time == timedelta():
                        row_data[Columns.TimePlay] = \
                            string_from_time(game.play_time)

                    # Parameters
                    if game.default is not None:
                        row_data[Columns.Except] = self.icons["except"]

                    elif game.emulator is not None:
                        if not game.emulator.name == console.emulator.name:
                            row_data[Columns.Except] = self.icons["except"]

                    # Installed time
                    if game.installed is not None:
                        row_data[Columns.Installed] = \
                            string_from_date(game.installed)

                    # Get global emulator
                    rom_emulator = emulator

                    # Set specified emulator is available
                    if game.emulator is not None:
                        rom_emulator = game.emulator

                    # Snap
                    if len(rom_emulator.get_screenshots(game)) > 0:
                        row_data[Columns.Snapshots] = self.icons["snap"]

                    # Save state
                    if len(rom_emulator.get_savestates(game)) > 0:
                        row_data[Columns.Save] = self.icons["save"]

                    row = self.model_games.append(row_data)

                    self.game_path[game.filename] = [game, row]

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

        if not access(console.path, W_OK):
            pass

        # ------------------------------------
        #   Close thread
        # ------------------------------------

        self.list_thread = int()

        yield False


    def __on_append_game(self, column, cell, model, treeiter, *args):
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
            score = model.get_value(treeiter, Columns.Score)

            for widget in self.__rating_score:

                if score >= self.__rating_score.index(widget) + 1:
                    widget.set_property(
                        "pixbuf", self.icons["starred"])
                else:
                    widget.set_property(
                        "pixbuf", self.alternative["no-starred"])


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

        available_events = [
            EventType.BUTTON_PRESS,
            EventType._2BUTTON_PRESS,
            EventType._3BUTTON_PRESS
        ]

        game = None
        treeiter = None

        run_game = False

        # ----------------------------
        #   Keyboard
        # ----------------------------

        if event.type == EventType.KEY_RELEASE:
            model, treeiter = treeview.get_selection().get_selected()

        # ----------------------------
        #   Mouse
        # ----------------------------

        elif event.type in available_events and event.button in (1, 3):

            # Get selection from cursor position
            if event.type == EventType.BUTTON_PRESS:
                selection = treeview.get_path_at_pos(int(event.x), int(event.y))

                if selection is not None:
                    model = treeview.get_model()
                    treeiter = model.get_iter(selection[0])

            # Get selection from treeview
            else:
                model, treeiter = treeview.get_selection().get_selected()

            # Mouse - Double click with left mouse button
            if event.type == EventType._2BUTTON_PRESS and event.button == 1:
                run_game = True and not self.is_rename

        # ----------------------------
        #   Game selected
        # ----------------------------

        # Get game data
        if treeiter is not None:
            game = model.get_value(treeiter, Columns.Object)

        # Check if the selected game has already been showed
        same_game = (self.selection["game"] == game)

        self.selection["game"] = game

        if game is not None:
            console = self.selection["console"]

            if console is not None:
                if not same_game:
                    self.sensitive_interface(True)

                # Get Game emulator
                emulator = console.emulator
                if game.emulator is not None:
                    emulator = game.emulator

                # ----------------------------
                #   Game data
                # ----------------------------

                if game.filename in self.threads:
                    self.__on_game_launch_button_update(False)
                    self.headerbar_item_launch.set_sensitive(True)

                    self.menu_item_launch.set_sensitive(False)
                    self.menu_item_database.set_sensitive(False)
                    self.menu_item_remove.set_sensitive(False)
                    self.menu_item_mednafen.set_sensitive(False)

                    self.menubar_game_item_launch.set_sensitive(False)
                    self.menubar_edit_item_database.set_sensitive(False)
                    self.menubar_edit_item_delete.set_sensitive(False)
                    self.menubar_edit_item_mednafen.set_sensitive(False)

                if not same_game:
                    # Check extension and emulator for GBA game on mednafen
                    if not game.extension.lower() == ".gba" or \
                        not "mednafen" in emulator.binary or \
                        not self.__mednafen_status:
                        self.menu_item_mednafen.set_sensitive(False)
                        self.menubar_edit_item_mednafen.set_sensitive(False)

                    iter_snaps = model.get_value(treeiter, Columns.Snapshots)

                    # Check snaps icon to avoid to check screenshots again
                    if iter_snaps == self.alternative["snap"]:
                        self.toolbar_item_screenshots.set_sensitive(False)
                        self.menu_item_screenshots.set_sensitive(False)
                        self.menubar_game_item_screenshots.set_sensitive(False)

                    if self.check_log() is None:
                        self.toolbar_item_output.set_sensitive(False)
                        self.menu_item_output.set_sensitive(False)
                        self.menubar_game_item_output.set_sensitive(False)

                    # Block signals
                    self.__block_signals()

                    self.menubar_game_item_favorite.set_active(
                        game.favorite)
                    self.menubar_game_item_multiplayer.set_active(
                        game.multiplayer)
                    self.menubar_game_item_finish.set_active(
                        game.finish)

                    self.menu_item_favorite.set_active(
                        game.favorite)
                    self.menu_item_multiplayer.set_active(
                        game.multiplayer)
                    self.menu_item_finish.set_active(
                        game.finish)

                    self.__unblock_signals()

                if run_game:
                    self.__on_game_launch()

        else:
            self.treeview_games.get_selection().unselect_all()

            self.selection["game"] = None

            self.__on_game_launch_button_update(True)
            self.headerbar_item_launch.set_sensitive(False)

        if not same_game:
            self.set_informations()


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

            # Get relative treerow position based on absolute cursor coordinates
            x, y = treeview.convert_widget_to_bin_window_coords(x, y)

            selection = treeview.get_path_at_pos(x, y)
            if selection is not None:
                model = treeview.get_model()
                treeiter = model.get_iter(selection[0])

                game = model.get_value(treeiter, Columns.Object)

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
                if console is not None and \
                    self.__current_tooltip_pixbuf is None:

                    image = None

                    # Get Game emulator
                    emulator = console.emulator
                    if game.emulator is not None:
                        emulator = game.emulator

                    screenshots = sorted(emulator.get_screenshots(game))
                    if len(screenshots) > 0:
                        image = screenshots[-1]

                    if game.cover is not None and exists(game.cover):
                        image = game.cover

                    if image is not None and exists(image):
                        pixbuf = Pixbuf.new_from_file(image)

                        # Resize pixbuf to have a 96 pixels height
                        pixbuf = pixbuf.scale_simple(pixbuf.get_width() * float(
                            96 / pixbuf.get_height()), 96, InterpType.TILES)

                        self.__current_tooltip_pixbuf = pixbuf

                # Only show tooltip when data are available
                if len(self.__current_tooltip_data) > 0:
                    tooltip.set_markup('\n'.join(self.__current_tooltip_data))

                    if self.__current_tooltip_pixbuf is not None:
                        tooltip.set_icon(self.__current_tooltip_pixbuf)

                    self.__current_tooltip = game

                    return True

        return False


    def __on_reload_games(self, *args):
        """ Reload games list from selected console
        """

        row = self.button_consoles.get_selected_row()

        if row is not None:
            self.__on_selected_console(None, row)


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

        data1 = model.get_value(row1, Columns.Object)
        data2 = model.get_value(row2, Columns.Object)

        # Favorite
        if column == Columns.Favorite:
            first = data1.favorite
            second = data2.favorite

        # Favorite
        elif column == Columns.Multiplayer:
            first = data1.multiplayer
            second = data2.multiplayer

        # Finish
        elif column == Columns.Finish:
            first = data1.finish
            second = data2.finish

        # Last play
        elif column == Columns.LastPlay:
            first = data1.last_launch_date
            second = data2.last_launch_date

        # Play time
        elif column == Columns.TimePlay:
            first = data1.play_time
            second = data2.play_time

        # Installed
        elif column == Columns.Installed:
            first = data1.installed
            second = data2.installed

        # ----------------------------
        #   Compare
        # ----------------------------

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
            return 0

        return 1


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
            model, treeiter = self.treeview_games.get_selection().get_selected()

            if treeiter is not None:
                treeview_name = model.get_value(treeiter, Columns.Name)

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

        label = self.headerbar_item_launch.get_label()

        if status and not label == _("Play"):
            self.headerbar_item_launch.set_label(
                _("Play"))
            self.headerbar_item_launch.set_tooltip_text(
                _("Launch selected game"))
            self.headerbar_item_launch.get_style_context().remove_class(
                "destructive-action")
            self.headerbar_item_launch.get_style_context().add_class(
                "suggested-action")

        elif not status and not label == _("Stop"):
            self.headerbar_item_launch.set_label(
                _("Stop"))
            self.headerbar_item_launch.set_tooltip_text(
                _("Stop selected game"))
            self.headerbar_item_launch.get_style_context().remove_class(
                "suggested-action")
            self.headerbar_item_launch.get_style_context().add_class(
                "destructive-action")


    def __on_game_launch(self, widget=None, *args):
        """ Prepare the game launch

        This function prepare the game launch and start a thread when everything
        are done

        Parameters
        ----------
        widget : Gtk.Widget, optional
            Object which receive signal (Default: None)
        """

        binary = str()

        # ----------------------------
        #   Check selection
        # ----------------------------

        game = self.selection["game"]

        if game is None:
            return False

        if not self.check_selection():
            return False

        if game.filename in self.threads:
            if widget is not None and type(widget) is Gtk.Button:
                self.threads[game.filename].proc.terminate()

            return False

        if self.is_rename:
            return False

        # ----------------------------
        #   Check emulator
        # ----------------------------

        console = self.selection["console"]

        if console is not None:
            emulator = console.emulator

            if game.emulator is not None:
                emulator = game.emulator

            if emulator is not None and emulator.id in self.api.emulators:
                self.logger.info(_("Initialize %s") % game.name)

                # ----------------------------
                #   Generate correct command
                # ----------------------------

                try:
                    command = emulator.command(game,
                        self.headerbar_item_fullscreen.get_active())

                except FileNotFoundError as error:
                    self.set_message(_("Cannot launch game"),
                        _("%s binary cannot be found") % emulator.name)
                    return False

                if len(command) > 0:

                    # ----------------------------
                    #   Run game
                    # ----------------------------

                    thread = GameThread(self, console, emulator, game, command)

                    # Save thread references
                    self.threads[game.filename] = thread

                    # Launch thread
                    thread.start()

                    self.__on_game_launch_button_update(False)
                    self.headerbar_item_launch.set_sensitive(True)

                    self.menu_item_output.set_sensitive(True)
                    self.toolbar_item_output.set_sensitive(True)
                    self.menubar_game_item_output.set_sensitive(True)

                    return True

        return False


    def __on_game_started(self, widget, game):
        """ Started the game processus

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        game : gem.engine.api.Game
            Game object
        """

        pass


    def __on_game_terminate(self, widget, thread):
        """ Terminate the game processus and update data

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        thread : gem.game.GameThread
            Game thread
        """

        # ----------------------------
        #   Save game data
        # ----------------------------

        emulator = thread.emulator

        if not thread.error:

            # Get the last occurence from database
            game = self.api.get_game(thread.console.id, thread.game.id)

            # ----------------------------
            #   Update data
            # ----------------------------

            # Play data
            game.played += 1
            game.play_time = thread.game.play_time + thread.delta
            game.last_launch_time = thread.delta
            game.last_launch_date = date.today()

            # Update game from database
            self.api.update_game(game)

            # Played
            self.set_game_data(Columns.Played, game.played, game.filename)

            # Last played
            self.set_game_data(Columns.LastPlay,
                string_from_date(game.last_launch_date), game.filename)

            # Last time played
            self.set_game_data(Columns.LastTimePlay,
                string_from_time(game.last_launch_time), game.filename)

            # Play time
            self.set_game_data(Columns.TimePlay,
                string_from_time(game.play_time), game.filename)

            # Snaps
            if len(emulator.get_screenshots(game)) > 0:
                self.set_game_data(
                    Columns.Snapshots, self.icons["snap"], game.filename)
                self.toolbar_item_screenshots.set_sensitive(True)
                self.menubar_game_item_screenshots.set_sensitive(True)

            else:
                self.set_game_data(Columns.Snapshots,
                    self.alternative["snap"], game.filename)

            # Save state
            if len(emulator.get_savestates(game)) > 0:
                self.set_game_data(
                    Columns.Save, self.icons["save"], game.filename)

            else:
                self.set_game_data(
                    Columns.Save, self.alternative["save"], game.filename)

            self.set_informations()

        # ----------------------------
        #   Refresh widgets
        # ----------------------------

        # Get current selected file
        select_game = self.selection["game"]

        # Check if current selected file is the same as thread file
        if select_game is not None and select_game.id == game.id:
            self.logger.debug("Restore widgets status for %s" % game.name)

            self.__on_game_launch_button_update(True)
            self.headerbar_item_launch.set_sensitive(True)

            self.menu_item_launch.set_sensitive(True)
            self.menu_item_database.set_sensitive(True)
            self.menu_item_remove.set_sensitive(True)

            self.menubar_game_item_launch.set_sensitive(True)
            self.menubar_edit_item_database.set_sensitive(True)
            self.menubar_edit_item_delete.set_sensitive(True)

            # Check extension and emulator for GBA game on mednafen
            if not game.extension.lower() == ".gba" or \
                not "mednafen" in emulator.binary or \
                not self.__mednafen_status:
                self.menu_item_mednafen.set_sensitive(True)
                self.menubar_edit_item_mednafen.set_sensitive(True)

            # Avoid to launch the game again when use Enter in game terminate
            # self.treeview_games.get_selection().unselect_all()

        # Remove this game from threads list
        if game.filename in self.threads:
            self.logger.debug("Remove %s from process cache" % game.name)

            del self.threads[game.filename]

        if len(self.threads) == 0:
            self.menu_item_preferences.set_sensitive(True)
            self.menubar_main_item_preferences.set_sensitive(True)


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

        game = self.selection["game"]

        if game is not None:
            treeiter = self.game_path[game.filename][1]

            self.set_sensitive(False)

            dialog = RenameDialog(self, game)

            if dialog.run() == Gtk.ResponseType.APPLY:

                new_name = dialog.get_name()

                # Check if game name has been changed
                if not new_name == game.name:
                    self.logger.info(_("Rename %(old)s to %(new)s") % {
                        "old": game.name, "new": dialog.get_name() })

                    game.name = new_name

                    treepath = self.model_games.get_path(
                        self.game_path[game.filename][1])

                    # Update game name
                    self.model_games[treepath][Columns.Name] = str(new_name)
                    self.model_games[treepath][Columns.Object] = game

                    # Update game from database
                    self.api.update_game(game)

                    # Store modified game
                    self.selection["game"] = game

                    self.__current_tooltip = None

                    self.set_informations()

            self.set_sensitive(True)

            dialog.destroy()


    def __on_game_clean(self, *args):
        """ Reset game informations from database
        """

        game = self.selection["game"]

        if game is not None:
            treeiter = self.game_path[game.filename][1]

            self.set_sensitive(False)

            dialog = QuestionDialog(self, _("Reset game"),
                _("Would you really want to reset this game informations ?"))

            if dialog.run() == Gtk.ResponseType.YES:
                data = {
                    Columns.Favorite: self.alternative["favorite"],
                    Columns.Name: game.filename,
                    Columns.Played: None,
                    Columns.LastPlay: None,
                    Columns.TimePlay: None,
                    Columns.LastTimePlay: None,
                    Columns.Score: 0,
                    Columns.Except: self.alternative["except"],
                    Columns.Multiplayer: self.alternative["multiplayer"],
                }

                for key, value in data.items():
                    self.model_games[treeiter][key] = value

                game.reset()

                # Update game from database
                self.api.update_game(game)

                self.set_informations()

            self.set_sensitive(True)

            dialog.destroy()


    def __on_game_removed(self, *args):
        """ Remove a game

        This function also remove files from user disk as screenshots,
        savestates and game file.
        """

        game = self.selection["game"]
        console = self.selection["console"]

        if game is not None and console is not None:

            # Avoid trying to remove an executed game
            if not game.filename in self.threads:
                treeiter = self.game_path[game.filename][1]

                emulator = console.emulator
                if game.emulator is not None:
                    emulator = game.emulator

                need_to_reload = False

                # ----------------------------
                #   Dialog
                # ----------------------------

                self.set_sensitive(False)

                dialog = DeleteDialog(self, game, emulator)

                if dialog.run() == Gtk.ResponseType.YES:
                    try:
                        self.logger.info(_("Remove %s") % game.name)

                        data = dialog.get_data()

                        # Duplicate game files
                        for element in data["paths"]:
                            self.logger.debug("Remove %s" % element)

                            remove(element)

                        # Remove game from database
                        if data["database"]:
                            self.api.delete_game(game)

                        # Reload the games list
                        if len(data["paths"]) > 0 or data["database"]:
                            need_to_reload = True

                    except Exception as error:
                        self.logger.exception("An error occur during removing")

                dialog.destroy()

                if need_to_reload:
                    self.__on_reload_games()

                    self.set_message(_("Remove a game"),
                        _("This game was removed successfully"),
                        Icons.Information)

                self.set_sensitive(True)


    def __on_game_duplicate(self, *args):
        """ Duplicate a game

        This function allow the user to duplicate a game and his associate
        data
        """

        game = self.selection["game"]

        if game is not None:
            console = self.selection["console"]

            # Get Game emulator
            emulator = console.emulator
            if game.emulator is not None:
                emulator = game.emulator

            need_to_reload = False

            # ----------------------------
            #   Dialog
            # ----------------------------

            self.set_sensitive(False)

            dialog = DuplicateDialog(self, game, emulator)

            if dialog.run() == Gtk.ResponseType.APPLY:
                try:
                    self.logger.info(_("Duplicate %s") % game.name)

                    data = dialog.get_data()

                    # Duplicate game files
                    for original, path in data["paths"]:
                        self.logger.debug("Copy %s" % original)

                        copy(original, path)

                    # Update game from database
                    if data["database"]:
                        self.api.update_game(game.copy(data["filepath"]))

                    # Reload the games list
                    if len(data["paths"]) > 0 or data["database"]:
                        need_to_reload = True

                except Exception as error:
                    self.logger.exception("An error occur during duplication")

            dialog.destroy()

            if need_to_reload:
                self.__on_reload_games()

                self.set_message(_("Duplicate a game"),
                    _("This game was duplicated successfully"),
                    Icons.Information)

            self.set_sensitive(True)


    def __on_game_parameters(self, *args):
        """ Manage game default parameters

        This function allow the user to specify default emulator and default
        emulator arguments for the selected game
        """

        game = self.selection["game"]

        if game is not None:
            console = self.selection["console"]

            parameters = None

            emulator = {
                "rom": None,
                "console": None,
                "parameters": None }

            # Current console default emulator
            if console is not None and console.emulator is not None:
                emulator["console"] = console.emulator

                if console.emulator.default is not None:
                    parameters = console.emulator.default

            # ----------------------------
            #   Generate data
            # ----------------------------

            if game.emulator is not None and \
                not game.emulator == emulator["console"]:
                emulator["rom"] = game.emulator

            if game.default is not None and \
                not game.default == parameters:
                emulator["parameters"] = game.default

            # ----------------------------
            #   Dialog
            # ----------------------------

            self.set_sensitive(False)

            dialog = ParametersDialog(self, game, emulator)

            if dialog.run() == Gtk.ResponseType.APPLY:
                self.logger.info(_("Update %s parameters") % game.name)

                game.emulator = self.api.get_emulator(
                    dialog.combo.get_active_id())

                game.default = dialog.entry_arguments.get_text()
                if len(game.default) == 0:
                    game.default = None

                game.key = dialog.entry_key.get_text()
                if len(game.key) == 0:
                    game.key = None

                game.tags = dialog.entry_tags.get_text().split()

                game.environment = dict()

                for row in dialog.store_environment:
                    key = dialog.store_environment.get_value(row.iter, 0)

                    if key is not None and len(key) > 0:
                        value = dialog.store_environment.get_value(row.iter, 1)

                        if value is not None and len(value) > 0:
                            game.environment[key] = value

                # Update game from database
                self.api.update_game(game)

                # ----------------------------
                #   Check diferences
                # ----------------------------

                custom = False

                if game.emulator is not None and \
                    not game.emulator.name == console.emulator.name:
                    custom = True

                elif game.default is not None:
                    custom = True

                if custom:
                    self.set_game_data(Columns.Except,
                        self.icons["except"], game.filename)
                else:
                    self.set_game_data(Columns.Except,
                        self.alternative["except"], game.filename)

                # ----------------------------
                #   Update icons
                # ----------------------------

                new_emulator = emulator["console"]
                if game.emulator is not None:
                    new_emulator = game.emulator

                # Screenshots
                if len(new_emulator.get_screenshots(game)) > 0:
                    self.set_game_data(Columns.Snapshots,
                        self.icons["snap"], game.filename)

                    self.toolbar_item_screenshots.set_sensitive(True)
                    self.menubar_game_item_screenshots.set_sensitive(True)

                else:
                    self.set_game_data(Columns.Snapshots,
                        self.alternative["snap"], game.filename)

                    self.toolbar_item_screenshots.set_sensitive(False)
                    self.menubar_game_item_screenshots.set_sensitive(False)

                # Savestates
                if len(new_emulator.get_savestates(game)) > 0:
                    self.set_game_data(Columns.Save,
                        self.icons["save"], game.filename)

                else:
                    self.set_game_data(Columns.Save,
                        self.alternative["save"], game.filename)

                self.set_informations()

            self.set_sensitive(True)

            dialog.destroy()


    def __on_game_log(self, *args):
        """ Show game log

        This function show the gem log content in a non-editable dialog
        """

        path = self.check_log()

        game = self.selection["game"]

        if path is not None and exists(expanduser(path)):
            try:
                size = self.config.get(
                    "windows", "log", fallback="800x600").split('x')

            except ValueError as error:
                size = (800, 600)

            self.set_sensitive(False)

            dialog = EditorDialog(self, game.name,
                expanduser(path), size, False, Icons.Symbolic.Terminal)

            dialog.run()

            self.config.modify("windows", "log", "%dx%d" % dialog.get_size())
            self.config.update()

            self.set_sensitive(True)

            dialog.destroy()


    def __on_game_backup_memory(self, *args):
        """ Manage game backup memory

        This function can only be used with a GBA game and Mednafen emulator.
        """

        if self.menu_item_mednafen.get_sensitive():

            game = self.selection["game"]
            console = self.selection["console"]

            if game is not None and console is not None:
                content = dict()

                emulator = console.emulator
                if game.emulator is not None:
                    emulator = game.emulator

                filepath = get_mednafen_memory_type(game)

                # Check if a type file already exist in mednafen sav folder
                if exists(filepath):
                    with open(filepath, 'r') as pipe:
                        for line in pipe.readlines():
                            data = line.split()

                            if len(data) == 2:
                                content[data[0]] = int(data[1])

                # ----------------------------
                #   Dialog
                # ----------------------------

                self.set_sensitive(False)

                dialog = MednafenDialog(self, game.name, content)

                if dialog.run() == Gtk.ResponseType.APPLY:
                    data = list()
                    for key, value in dialog.model:
                        data.append(' '.join([key, str(value)]))

                    # Write data into type file
                    if len(data) > 0:
                        with open(filepath, 'w') as pipe:
                            pipe.write('\n'.join(data))

                    # Remove type file when no data are available
                    elif exists(filepath):
                        remove(filepath)

                self.set_sensitive(True)

                dialog.destroy()


    def __on_game_marked_as_favorite(self, *args):
        """ Mark or unmark a game as favorite

        This function update the database when user change the game favorite
        status
        """

        self.__block_signals()

        game = self.selection["game"]

        if game is not None:
            treeiter = self.game_path[game.filename][1]

            if not game.favorite:
                self.logger.debug("Mark %s as favorite" % game.name)

                icon = self.icons["favorite"]

                game.favorite = True

            else:
                self.logger.debug("Unmark %s as favorite" % game.name)

                icon = self.alternative["favorite"]

                game.favorite = False

            self.model_games.set_value(
                treeiter, Columns.Favorite, icon)
            self.model_games.set_value(
                treeiter, Columns.Object, game)

            # Update game from database
            self.api.update_game(game)

            self.menubar_game_item_favorite.set_active(game.favorite)
            self.menu_item_favorite.set_active(game.favorite)

            self.check_selection()

        else:
            self.menubar_game_item_favorite.set_active(False)
            self.menu_item_favorite.set_active(False)

        self.filters_update(None)

        self.__unblock_signals()


    def __on_game_marked_as_multiplayer(self, *args):
        """ Mark or unmark a game as multiplayer

        This function update the database when user change the game multiplayers
        status
        """

        self.__block_signals()

        game = self.selection["game"]

        if game is not None:
            treeiter = self.game_path[game.filename][1]

            if not game.multiplayer:
                self.logger.debug("Mark %s as multiplayers" % game.name)

                icon = self.icons["multiplayer"]

                game.multiplayer = True

            else:
                self.logger.debug("Unmark %s as multiplayers" % game.name)

                icon = self.alternative["multiplayer"]

                game.multiplayer = False

            self.model_games.set_value(
                treeiter, Columns.Multiplayer, icon)
            self.model_games.set_value(
                treeiter, Columns.Object, game)

            # Update game from database
            self.api.update_game(game)

            self.menubar_game_item_multiplayer.set_active(game.multiplayer)
            self.menu_item_multiplayer.set_active(game.multiplayer)

            self.check_selection()

        else:
            self.menubar_game_item_multiplayer.set_active(False)
            self.menu_item_multiplayer.set_active(False)

        self.filters_update(None)

        self.__unblock_signals()


    def __on_game_marked_as_finish(self, *args):
        """ Mark or unmark a game as finish

        This function update the database when user change the game finish
        status
        """

        self.__block_signals()

        game = self.selection["game"]

        if game is not None:
            treeiter = self.game_path[game.filename][1]

            if not game.finish:
                self.logger.debug("Mark %s as finish" % game.name)

                icon = self.icons["finish"]

                game.finish = True

            else:
                self.logger.debug("Unmark %s as finish" % game.name)

                icon = self.alternative["finish"]

                game.finish = False

            self.model_games.set_value(
                treeiter, Columns.Finish, icon)
            self.model_games.set_value(
                treeiter, Columns.Object, game)

            # Update game from database
            self.api.update_game(game)

            self.menubar_game_item_finish.set_active(game.finish)
            self.menu_item_finish.set_active(game.finish)

            self.check_selection()

        else:
            self.menubar_game_item_finish.set_active(False)
            self.menu_item_finish.set_active(False)

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

        game = self.selection["game"]

        if game is not None:

            if widget in [
                self.menubar_edit_item_score_up, self.menu_item_score_up]:

                if game.score < 5:
                    game.score += 1

                    modification = True

            elif widget in [
                self.menubar_edit_item_score_down, self.menu_item_score_down]:

                if game.score > 0:
                    game.score -= 1

                    modification = True

            elif score is not None:
                game.score = score

                modification = True

        if modification:
            self.model_games.set_value(
                self.game_path[game.filename][1], Columns.Score, game.score)
            self.model_games.set_value(
                self.game_path[game.filename][1], Columns.Object, game)

            self.api.update_game(game)


    def __on_game_copy(self, *args):
        """ Copy path folder which contains selected game to clipboard
        """

        game = self.selection["game"]

        if game is not None:
            self.clipboard.set_text(game.filepath, -1)


    def __on_game_open(self, *args):
        """ Open game directory

        This function open the folder which contains game with the default
        files manager

        Based on http://stackoverflow.com/a/6631329
        """

        game = self.selection["game"]

        if game is not None:
            path = game.path[0]

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


    def __on_game_cover(self, *args):
        """ Set a new cover for selected game
        """

        game = self.selection["game"]

        if game is not None:
            self.set_sensitive(False)

            dialog = CoverDialog(self, game)

            response = dialog.run()

            if response == Gtk.ResponseType.APPLY:
                path = dialog.file_image_selector.get_filename()

                # Avoid to update the database with same contents
                if not path == game.cover:

                    # Reset cover for current game
                    if path is None:
                        path = str()

                    game.cover = path

                    # Update game from database
                    self.api.update_game(game)

                    self.set_informations()

            self.set_sensitive(True)

            dialog.destroy()


    def __on_game_generate_desktop(self, *args):
        """ Generate application desktop file

        This function generate a .desktop file to allow user to launch the game
        from his favorite applications launcher
        """

        model, treeiter = self.treeview_games.get_selection().get_selected()

        game = self.selection["game"]
        console = self.selection["console"]

        if treeiter is not None and game is not None and console is not None:

            # Check emulator
            emulator = console.emulator

            if game.emulator is not None:
                emulator = game.emulator

            if emulator is not None and emulator.id in self.api.emulators:
                name = "%s.desktop" % game.filename

                # ----------------------------
                #   Fill template
                # ----------------------------

                icon = console.icon
                if not exists(icon):
                    icon = self.api.get_local(
                        "icons", "consoles", '.'.join([icon, Icons.Ext]))

                values = {
                    "%name%": game.name,
                    "%icon%": icon,
                    "%path%": game.path[0],
                    "%command%": ' '.join(emulator.command(game))
                }

                # Put game path between quotes
                values["%command%"] = values["%command%"].replace(
                    game.filepath, "\"%s\"" % game.filepath)

                self.set_sensitive(False)

                try:
                    # Read default template
                    desktop = path_join("config", Documents.Desktop)

                    with open(get_data(desktop), 'r') as pipe:
                        template = pipe.readlines()

                    content = str()

                    # Replace custom variables
                    for line in template:
                        for key in values.keys():
                            line = line.replace(key, values[key])

                        content += line

                    # Check ~/.local/share/applications
                    if not exists(Folders.Apps):
                        mkdir(Folders.Apps)

                    # Write the new desktop file
                    with open(path_join(Folders.Apps, name), 'w') as pipe:
                        pipe.write(content)

                    self.set_message(_("Generate menu entry"),
                        _("%s was generated successfully")  % name,
                        Icons.Information)

                except OSError as error:
                    self.set_message(
                        _("Generate menu entry for %s") % game.name,
                        _("An error occur during generation, consult log for "
                        "futher details."), Icons.Error)

                self.set_sensitive(True)


    def __on_menu_show(self, treeview, event):
        """ Open context menu

        This function open context-menu when user right-click or use context key
        on games treeview

        Parameters
        ----------
        treeview : Gtk.Treeview
            Object which receive signal
        event : Gdk.EventButton or Gdk.EventKey
            Event which triggered this signal

        Returns
        -------
        bool
            Context menu popup status
        """

        # Gdk.EventButton - Mouse
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

        # Gdk.EventKey - Keyboard
        elif event.type == EventType.KEY_RELEASE:
            if event.keyval == Gdk.KEY_Menu:
                model, treeiter = treeview.get_selection().get_selected()

                if treeiter is not None:
                    self.menu_games.popup(None, None, None, None, 0, event.time)

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

            self.headerbar_image_fullscreen.set_from_icon_name(
                Icons.Symbolic.Restore, Gtk.IconSize.SMALL_TOOLBAR)
            self.headerbar_item_fullscreen.get_style_context().remove_class(
                "suggested-action")

        else:
            self.logger.debug("Switch game launch to fullscreen mode")

            self.headerbar_image_fullscreen.set_from_icon_name(
                Icons.Symbolic.Fullscreen, Gtk.IconSize.SMALL_TOOLBAR)
            self.headerbar_item_fullscreen.get_style_context().add_class(
                "suggested-action")

        self.headerbar_item_fullscreen.set_active(self.__fullscreen_status)
        self.menubar_game_item_fullscreen.set_active(self.__fullscreen_status)

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

        self.menu_item_dark_theme.set_active(dark_theme_status)
        self.menubar_main_item_dark_theme.set_active(dark_theme_status)

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

        if sidebar_status:
            self.scroll_sidebar.show()
        else:
            self.scroll_sidebar.hide()

        self.config.modify("gem", "show_sidebar", sidebar_status)
        self.config.update()

        self.menu_item_sidebar.set_active(sidebar_status)
        self.menubar_main_item_sidebar.set_active(sidebar_status)

        self.__unblock_signals()


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

        self.menu_item_statusbar.set_active(statusbar_status)
        self.menubar_main_item_statusbar.set_active(statusbar_status)

        self.__unblock_signals()


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

        if type(widget) is Gtk.TreeView:

            if self.selection["game"] is not None:
                data.set_uris(["file://%s" % self.selection["game"].filepath])

        elif type(widget) is Gtk.Viewport:

            if self.sidebar_image is not None:
                data.set_uris(["file://%s" % self.sidebar_image])


    def __on_dnd_received_data(self, widget, context, x, y, data, info, time):
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
        time : int
            Timestamp at which the data was received
        """

        self.logger.debug("Received data from drag & drop")

        widget.stop_emission("drag_data_received")

        # Current acquisition not respect text/uri-list
        if not info == 1337:
            return

        previous_console = None

        keep_console = False
        need_to_reload = False

        consoles_to_reload = dict()

        for uri in data.get_uris():
            result = urlparse(uri)

            console = None

            if result.scheme == "file":
                path = expanduser(url2pathname(result.path))

                if exists(path):
                    self.logger.debug("Check %s" % path)
                    filename, ext = splitext(basename(path))

                    # Lowercase extension
                    ext = ext.lower()

                    # ----------------------------
                    #   Get right console for rom
                    # ----------------------------

                    if not keep_console:

                        consoles_list = list()
                        for console in self.api.get_consoles():
                            extensions = console.extensions

                            if extensions is not None and ext[1:] in extensions:
                                consoles_list.append(console)

                        console = None

                        if len(consoles_list) > 0:
                            console = consoles_list[0]

                            if len(consoles_list) > 1:
                                self.set_sensitive(False)

                                dialog = DnDConsoleDialog(self, basename(path),
                                    consoles_list, previous_console)

                                if dialog.run() == Gtk.ResponseType.APPLY:
                                    console = self.api.get_console(
                                        dialog.current)

                                    keep_console = dialog.switch.get_active()

                                    previous_console = console

                                else:
                                    console = None

                                dialog.destroy()

                                self.set_sensitive(True)

            # ----------------------------
            #   Check console
            # ----------------------------

            if console is not None:
                rom_path = expanduser(console.path)

                # ----------------------------
                #   Install roms
                # ----------------------------

                if rom_path is not None and not dirname(path) == rom_path and \
                    exists(rom_path) and access(rom_path, W_OK):
                    move = True

                    # Check if this game already exists in roms folder
                    if exists(path_join(rom_path, basename(path))):
                        dialog = QuestionDialog(self, basename(path),
                            _("This rom already exists in %s. Do you want to "
                            "replace it ?") % rom_path)

                        move = False
                        if dialog.run() == Gtk.ResponseType.YES:
                            move = True

                            self.logger.debug(
                                "Move %s to %s" % (path, rom_path))

                            remove(path_join(rom_path, basename(path)))

                        dialog.destroy()

                    # The game can be moved in roms folder
                    if move:
                        rename(path, rom_path)

                        self.logger.info(_("Drop %(rom)s to %(path)s") % {
                            "rom": basename(path), "path": rom_path })

                        if console == self.selection["console"]:
                            need_to_reload = True

                        if not console.id in consoles_to_reload:
                            consoles_to_reload[console.id] = console

                        hide = self.config.getboolean(
                            "gem", "hide_empty_console", fallback=False)

                        # Console path is not empty
                        if hide and len(glob(path_join(rom_path, '*'))) == 1:
                            need_to_reload = True

                # ----------------------------
                #   Errors
                # ----------------------------

                if dirname(path) == rom_path:
                    pass

                elif not exists(rom_path):
                    self.set_message(basename(path), _("Destination %s not "
                        "exist. Canceling operation.") % rom_path)

                elif not access(rom_path, W_OK):
                    self.set_message(basename(path), _("Cannot write into %s. "
                        "Canceling operation.") % rom_path)

        # Reload console games
        for console in consoles_to_reload.values():
            console.set_games(self.api)

        # Reload interface when games list was modified
        if need_to_reload:
            self.load_interface()


    def __block_signals(self):
        """ Block check button signals to avoid stack overflow when toggled
        """

        for widget, signal in self.__signals.items():
            widget.handler_block(signal)


    def __unblock_signals(self):
        """ Unblock check button signals
        """

        for widget, signal in self.__signals.items():
            widget.handler_unblock(signal)


    def check_desktop(self, filename):
        """ Check user applications folder for specific desktop file

        Parameters
        ----------
        filename : str
            Application name

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

        name, extension = splitext(filename)

        return exists(path_join(Folders.Apps, "%s.desktop" % name))


    def check_log(self):
        """ Check if a game has an output file available

        Returns
        -------
        str or None
            Output file path
        """

        game = self.selection["game"]

        if game is not None:
            log_path = self.api.get_local(game.log)

            if exists(expanduser(log_path)):
                return log_path

        return None


    def check_mednafen(self):
        """ Check if Mednafen exists on user system

        This function read the first line of mednafen default output and check
        if this one match "Starting Mednafen [\d+\.?]+".

        Returns
        -------
        bool
            Mednafen exists status

        Notes
        -----
        Still possible to troll this function with a script call mednafen which
        send the match string as output. But, this problem only appear if a user
        want to do that, so ...
        """

        if len(get_binary_path("mednafen")) > 0:
            proc = Popen(
                [ "mednafen" ],
                stdin=PIPE,
                stdout=PIPE,
                stderr=STDOUT,
                universal_newlines=True)

            output, error_output = proc.communicate()

            if output is not None:
                result = match(
                    "Starting Mednafen [\d+\.?]+", output.split('\n')[0])

                if result is not None:
                    return True

        return False


    def set_game_data(self, index, data, gamename):
        """ Update game informations in games treeview

        Parameters
        ----------
        index : int
            Column index
        data : object
            Value to set
        gamename : str
            Game basename without extension
        """

        treeiter = self.game_path.get(gamename, None)

        if treeiter is not None:
            self.model_games[treeiter[1]][index] = data


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
        game : gem.engine.api.Game
            Game object

        Returns
        -------
        str
            Memory type file path
        """

        # FIXME: Maybe a better way to determine type file
        return expanduser(
            path_join('~', ".mednafen", "sav", game.filename + ".type"))


    def emit(self, *args):
        """ Override emit function

        This override allow to use Interface function from another thread in
        MainThread
        """

        idle_add(GObject.emit, self, *args)
