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
from gem.ui.widgets.script import ScriptThread
from gem.ui.widgets.widgets import ListBoxPopover
from gem.ui.widgets.widgets import ListBoxSelector
from gem.ui.widgets.widgets import PreferencesItem
from gem.ui.widgets.widgets import IconsGenerator

from gem.ui.dialog import *

from gem.ui.preferences.interface import PreferencesWindow

# Random
from random import randint

# Regex
from re import match
from re import search
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
        "game-started": (SignalFlags.RUN_FIRST, None, [object]),
        "game-terminate": (SignalFlags.RUN_LAST, None, [object]),
        "script-terminate": (SignalFlags.RUN_LAST, None, [object]),
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
        #   Initialize API
        # ------------------------------------

        # GEM API
        self.api = api

        # Quick access to API logger
        self.logger = api.logger

        # Check development version
        self.__version = self.check_version()

        # ------------------------------------
        #   Initialize variables
        # ------------------------------------

        # Generate a title from GEM informations
        self.title = "%s - %s (%s)" % (GEM.Name, self.__version, GEM.CodeName)

        # Store thread id for game listing
        self.list_thread = int()

        # Store normal icons with icon name as key
        self.icons = dict()
        # Store alternative icons with icon name as key
        self.alternative = dict()
        # Store started notes with note file path as key
        self.notes = dict()
        # Store script threads with basename game file without extension as key
        self.scripts = dict()
        # Store started threads with basename game file without extension as key
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

        # Store previous sizes for resize function
        self.__previous_window_size = tuple()

        # Avoid to reload game tooltip every time the user move in line
        self.__current_tooltip = None
        self.__current_tooltip_data = list()
        self.__current_tooltip_pixbuf = None

        # Check mednafen status
        self.__mednafen_status = self.check_mednafen()

        # ------------------------------------
        #   Initialize icons
        # ------------------------------------

        self.icons = IconsGenerator(
            savestate=Icons.Floppy,
            screenshot=Icons.Photos,
            parameter=Icons.Properties,
            warning=Icons.Warning,
            favorite=Icons.Favorite,
            multiplayer=Icons.Users,
            finish=Icons.Smile,
            unfinish=Icons.Uncertain,
            nostarred=Icons.NoStarred,
            starred=Icons.Starred)

        self.icons.theme.append_search_path(get_data(path_join("icons", "ui")))

        # Generate symbolic icons class
        for key, value in Icons.__dict__.items():
            if not key.startswith("__") and not key.endswith("__"):
                setattr(Icons.Symbolic, key, "%s-symbolic" % value)

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
            self.main_loop = MainLoop()
            self.main_loop.run()

        except KeyboardInterrupt as error:
            self.logger.warning("Terminate by keyboard interrupt")

            self.__stop_interface()


    def __init_widgets(self):
        """ Initialize interface widgets
        """

        # ------------------------------------
        #   Main window
        # ------------------------------------

        self.window_size = Gdk.Geometry()

        # Properties
        self.window_size.min_width = 800
        self.window_size.min_height = 600
        self.window_size.base_width = 1024
        self.window_size.base_height = 768

        self.set_title(self.title)

        self.set_icon_name(GEM.Icon)
        self.set_default_icon_name(Icons.Gaming)

        self.set_position(Gtk.WindowPosition.CENTER)

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

        self.grid_menu = Gtk.Box()

        self.grid_consoles = Gtk.Box()
        self.grid_consoles_item = Gtk.Box()
        self.grid_consoles_menu = Gtk.Box()

        self.grid_filters = Gtk.Box()
        self.grid_filters_popover = Gtk.Box()

        self.grid_game_launch = Gtk.Box()
        self.grid_game_options = Gtk.Box()
        self.grid_game_view_mode = Gtk.Box()

        self.grid_infobar = Gtk.Box()

        self.grid_games = Gtk.Box()
        self.grid_games_placeholder = Gtk.Box()

        self.grid_sidebar = Gtk.Box()
        self.grid_sidebar_title = Gtk.Box()
        self.grid_sidebar_content = Gtk.Box()
        self.grid_sidebar_informations = Gtk.Box()
        self.grid_sidebar_informations_header = Gtk.Grid()
        self.grid_sidebar_informations_footer = Gtk.Grid()
        self.grid_sidebar_score = Gtk.Box()

        # Properties
        self.grid.set_orientation(Gtk.Orientation.VERTICAL)

        self.grid_menu.set_spacing(6)
        self.grid_menu.set_border_width(6)
        self.grid_menu.set_orientation(Gtk.Orientation.VERTICAL)

        Gtk.StyleContext.add_class(
            self.grid_consoles.get_style_context(), "linked")
        self.grid_consoles.set_spacing(-1)
        self.grid_consoles.set_orientation(Gtk.Orientation.HORIZONTAL)

        self.grid_consoles_item.set_spacing(12)

        self.grid_consoles_menu.set_spacing(6)
        self.grid_consoles_menu.set_border_width(6)
        self.grid_consoles_menu.set_halign(Gtk.Align.FILL)
        self.grid_consoles_menu.set_orientation(Gtk.Orientation.VERTICAL)

        Gtk.StyleContext.add_class(
            self.grid_filters.get_style_context(), "linked")
        self.grid_filters.set_spacing(-1)
        self.grid_filters.set_orientation(Gtk.Orientation.HORIZONTAL)

        self.grid_filters_popover.set_spacing(6)
        self.grid_filters_popover.set_border_width(6)
        self.grid_filters_popover.set_orientation(Gtk.Orientation.VERTICAL)

        Gtk.StyleContext.add_class(
            self.grid_game_launch.get_style_context(), "linked")
        self.grid_game_launch.set_spacing(-1)
        self.grid_game_launch.set_orientation(Gtk.Orientation.HORIZONTAL)

        Gtk.StyleContext.add_class(
            self.grid_game_options.get_style_context(), "linked")
        self.grid_game_options.set_spacing(-1)
        self.grid_game_options.set_orientation(Gtk.Orientation.HORIZONTAL)

        Gtk.StyleContext.add_class(
            self.grid_game_view_mode.get_style_context(), "linked")
        self.grid_game_view_mode.set_spacing(-1)
        self.grid_game_view_mode.set_orientation(Gtk.Orientation.HORIZONTAL)

        self.grid_games.set_orientation(Gtk.Orientation.VERTICAL)

        self.grid_games_placeholder.set_spacing(12)
        self.grid_games_placeholder.set_border_width(18)
        self.grid_games_placeholder.set_orientation(Gtk.Orientation.VERTICAL)

        self.grid_sidebar.set_orientation(Gtk.Orientation.VERTICAL)
        self.grid_sidebar.set_border_width(6)
        self.grid_sidebar.set_hexpand(True)
        self.grid_sidebar.set_vexpand(True)
        self.grid_sidebar.set_spacing(6)

        self.grid_sidebar_title.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.grid_sidebar_title.set_hexpand(True)
        self.grid_sidebar_title.set_spacing(6)

        self.grid_sidebar_content.set_valign(Gtk.Align.START)
        self.grid_sidebar_content.set_halign(Gtk.Align.FILL)
        self.grid_sidebar_content.set_hexpand(True)
        self.grid_sidebar_content.set_vexpand(True)
        self.grid_sidebar_content.set_spacing(6)

        self.grid_sidebar_informations.set_hexpand(True)
        self.grid_sidebar_informations.set_vexpand(True)
        self.grid_sidebar_informations.set_spacing(0)

        self.grid_sidebar_informations_header.set_column_homogeneous(True)
        self.grid_sidebar_informations_header.set_halign(Gtk.Align.FILL)
        self.grid_sidebar_informations_header.set_column_spacing(12)
        self.grid_sidebar_informations_header.set_border_width(6)
        self.grid_sidebar_informations_header.set_row_spacing(6)
        self.grid_sidebar_informations_header.set_hexpand(True)
        self.grid_sidebar_informations_header.set_vexpand(True)

        self.grid_sidebar_informations_footer.set_column_homogeneous(True)
        self.grid_sidebar_informations_footer.set_halign(Gtk.Align.FILL)
        self.grid_sidebar_informations_footer.set_column_spacing(12)
        self.grid_sidebar_informations_footer.set_border_width(6)
        self.grid_sidebar_informations_footer.set_row_spacing(6)
        self.grid_sidebar_informations_footer.set_hexpand(True)
        self.grid_sidebar_informations_footer.set_vexpand(True)

        self.grid_sidebar_score.set_halign(Gtk.Align.START)
        self.grid_sidebar_score.set_valign(Gtk.Align.CENTER)
        self.grid_sidebar_score.set_hexpand(True)
        self.grid_sidebar_score.set_spacing(6)

        # ------------------------------------
        #   Headerbar
        # ------------------------------------

        self.headerbar = Gtk.HeaderBar()

        self.button_headerbar_launch = Gtk.Button()

        self.image_headerbar_fullscreen = Gtk.Image()
        self.button_headerbar_fullscreen = Gtk.ToggleButton()

        self.image_headerbar_menu = Gtk.Image()
        self.button_headerbar_menu = Gtk.MenuButton()

        self.popover_menu = Gtk.Popover()

        # Properties
        self.headerbar.set_title(self.title)
        self.headerbar.set_subtitle(str())

        self.button_headerbar_launch.set_label(_("Play"))
        self.button_headerbar_launch.set_tooltip_text(
            _("Launch selected game"))
        self.button_headerbar_launch.get_style_context().add_class(
            "suggested-action")

        self.button_headerbar_fullscreen.set_tooltip_text(
            _("Alternate game fullscreen mode"))

        self.button_headerbar_menu.set_tooltip_text(_("Main menu"))
        self.button_headerbar_menu.set_use_popover(True)

        self.popover_menu.set_modal(True)

        # ------------------------------------
        #   Headerbar - Main menu
        # ------------------------------------

        self.frame_menu_actions = Gtk.Frame()
        self.listbox_menu_actions = Gtk.ListBox()

        self.widget_menu_preferences = PreferencesItem()
        self.image_menu_preferences = Gtk.Image()
        self.button_menu_preferences = Gtk.Button()

        self.widget_menu_log = PreferencesItem()
        self.image_menu_log = Gtk.Image()
        self.button_menu_log = Gtk.Button()

        self.frame_menu_system = Gtk.Frame()
        self.listbox_menu_system = Gtk.ListBox()

        self.widget_menu_about = PreferencesItem()
        self.image_menu_about = Gtk.Image()
        self.button_menu_about = Gtk.Button()

        self.widget_menu_quit = PreferencesItem()
        self.image_menu_quit = Gtk.Image()
        self.button_menu_quit = Gtk.Button()

        self.frame_menu_options = Gtk.Frame()
        self.listbox_menu_options = Gtk.ListBox()

        self.widget_menu_dark_theme = PreferencesItem()
        self.switch_menu_dark_theme = Gtk.Switch()

        self.widget_menu_sidebar = PreferencesItem()
        self.switch_menu_sidebar = Gtk.Switch()

        self.widget_menu_statusbar = PreferencesItem()
        self.switch_menu_statusbar = Gtk.Switch()

        # Properties
        self.listbox_menu_actions.set_activate_on_single_click(True)
        self.listbox_menu_actions.set_selection_mode(
            Gtk.SelectionMode.NONE)

        self.button_menu_preferences.set_image(
            self.image_menu_preferences)
        self.button_menu_preferences.set_relief(Gtk.ReliefStyle.NONE)

        self.widget_menu_preferences.set_widget(
            self.button_menu_preferences)
        self.widget_menu_preferences.set_option_label(
            _("Preferences"))

        self.button_menu_log.set_image(
            self.image_menu_log)
        self.button_menu_log.set_relief(Gtk.ReliefStyle.NONE)

        self.widget_menu_log.set_widget(
            self.button_menu_log)
        self.widget_menu_log.set_option_label(
            _("Output log"))

        self.button_menu_about.set_image(
            self.image_menu_about)
        self.button_menu_about.set_relief(Gtk.ReliefStyle.NONE)

        self.listbox_menu_system.set_activate_on_single_click(True)
        self.listbox_menu_system.set_selection_mode(
            Gtk.SelectionMode.NONE)

        self.widget_menu_about.set_widget(
            self.button_menu_about)
        self.widget_menu_about.set_option_label(
            _("About"))

        self.button_menu_quit.set_image(
            self.image_menu_quit)
        self.button_menu_quit.set_relief(Gtk.ReliefStyle.NONE)

        self.widget_menu_quit.set_widget(
            self.button_menu_quit)
        self.widget_menu_quit.set_option_label(
            _("Quit"))

        self.listbox_menu_options.set_activate_on_single_click(True)
        self.listbox_menu_options.set_selection_mode(
            Gtk.SelectionMode.NONE)

        self.widget_menu_dark_theme.set_widget(
            self.switch_menu_dark_theme)
        self.widget_menu_dark_theme.set_option_label(
            _("Dark theme"))

        self.widget_menu_sidebar.set_widget(
            self.switch_menu_sidebar)
        self.widget_menu_sidebar.set_option_label(
            _("Sidebar"))

        self.widget_menu_statusbar.set_widget(
            self.switch_menu_statusbar)
        self.widget_menu_statusbar.set_option_label(
            _("Statusbar"))

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
        self.menubar_edit_item_maintenance = Gtk.MenuItem()
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

        self.menubar_edit_item_maintenance.set_label(
            "%s…" % _("_Maintenance"))
        self.menubar_edit_item_maintenance.set_use_underline(True)

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

        self.item_toolbar_launch = Gtk.ToolItem()
        self.item_toolbar_properties = Gtk.ToolItem()
        self.item_toolbar_option = Gtk.ToolItem()
        self.item_toolbar_view_mode = Gtk.ToolItem()
        self.item_toolbar_consoles = Gtk.ToolItem()
        self.item_toolbar_search = Gtk.ToolItem()
        self.item_toolbar_filters = Gtk.ToolItem()
        self.item_toolbar_separator = Gtk.SeparatorToolItem()

        self.button_toolbar_parameters = Gtk.Button()
        self.button_toolbar_screenshots = Gtk.Button()
        self.button_toolbar_output = Gtk.Button()
        self.button_toolbar_notes = Gtk.Button()
        self.button_toolbar_grid = Gtk.ToggleButton()
        self.button_toolbar_list = Gtk.ToggleButton()

        self.image_toolbar_parameters = Gtk.Image()
        self.image_toolbar_screenshots = Gtk.Image()
        self.image_toolbar_output = Gtk.Image()
        self.image_toolbar_notes = Gtk.Image()
        self.image_toolbar_grid = Gtk.Image()
        self.image_toolbar_list = Gtk.Image()

        # Properties
        self.item_toolbar_consoles.set_halign(Gtk.Align.END)
        self.item_toolbar_consoles.set_expand(True)

        self.item_toolbar_separator.set_draw(False)

        self.button_toolbar_parameters.set_tooltip_text(
            _("Set custom parameters"))

        self.button_toolbar_screenshots.set_tooltip_text(
            _("Show selected game screenshots"))
        self.button_toolbar_output.set_tooltip_text(
            _("Show selected game output log"))
        self.button_toolbar_notes.set_tooltip_text(
            _("Show selected game notes"))

        # ------------------------------------
        #   Toolbar - Consoles
        # ------------------------------------

        self.button_consoles = ListBoxSelector(-1, use_static_size=True)

        self.entry_consoles = self.button_consoles.get_entry()
        self.listbox_consoles = self.button_consoles.get_listbox()

        # Properties
        self.button_consoles.set_filter_func(self.__on_filter_consoles)
        self.button_consoles.set_sort_func(self.__on_sort_consoles)

        # ------------------------------------
        #   Toolbar - Consoles options
        # ------------------------------------

        self.image_consoles_menu = Gtk.Image()
        self.button_consoles_menu = Gtk.MenuButton()

        self.popover_consoles_menu = Gtk.Popover()

        self.frame_consoles_actions = Gtk.Frame()
        self.listbox_consoles_actions = Gtk.ListBox()

        self.widget_consoles_properties = PreferencesItem()
        self.button_consoles_properties = Gtk.Button()
        self.image_consoles_properties = Gtk.Image()

        self.widget_consoles_refresh = PreferencesItem()
        self.button_consoles_refresh = Gtk.Button()
        self.image_consoles_refresh = Gtk.Image()

        self.frame_consoles_options = Gtk.Frame()
        self.listbox_consoles_options = Gtk.ListBox()

        self.widget_consoles_options_favorite = PreferencesItem()
        self.switch_consoles_favorite = Gtk.Switch()

        self.widget_consoles_options_recursive = PreferencesItem()
        self.switch_consoles_recursive = Gtk.Switch()

        # Properties
        self.button_consoles_menu.set_popover(self.popover_consoles_menu)
        self.button_consoles_menu.set_use_popover(True)

        self.listbox_consoles_actions.set_activate_on_single_click(True)
        self.listbox_consoles_actions.set_selection_mode(
            Gtk.SelectionMode.NONE)

        self.button_consoles_properties.set_image(
            self.image_consoles_properties)
        self.button_consoles_properties.set_relief(Gtk.ReliefStyle.NONE)

        self.widget_consoles_properties.set_widget(
            self.button_consoles_properties)
        self.widget_consoles_properties.set_option_label(
            _("Edit emulator"))

        self.button_consoles_refresh.set_image(self.image_consoles_refresh)
        self.button_consoles_refresh.set_relief(Gtk.ReliefStyle.NONE)

        self.widget_consoles_refresh.set_widget(
            self.button_consoles_refresh)
        self.widget_consoles_refresh.set_option_label(
            _("Refresh games list"))

        self.listbox_consoles_options.set_activate_on_single_click(True)
        self.listbox_consoles_options.set_selection_mode(
            Gtk.SelectionMode.NONE)

        self.widget_consoles_options_favorite.set_widget(
            self.switch_consoles_favorite)
        self.widget_consoles_options_favorite.set_option_label(
            _("Favorite"))

        self.widget_consoles_options_recursive.set_widget(
            self.switch_consoles_recursive)
        self.widget_consoles_options_recursive.set_option_label(
            _("Recursive"))
        self.widget_consoles_options_recursive.set_tooltip_text(
            _("You need to reload games list to apply changes"))

        # ------------------------------------
        #   Toolbar - Filter
        # ------------------------------------

        self.entry_toolbar_filters = Gtk.SearchEntry()

        self.button_toolbar_filters = Gtk.MenuButton()

        self.popover_toolbar_filters = Gtk.Popover()

        # Properties
        self.entry_toolbar_filters.set_placeholder_text("%s…" % _("Filter"))

        self.button_toolbar_filters.set_tooltip_text(_("Filters"))
        self.button_toolbar_filters.set_use_popover(True)

        self.popover_toolbar_filters.set_modal(True)

        # ------------------------------------
        #   Toolbar - Filter - Menu
        # ------------------------------------

        self.frame_filters_favorite = Gtk.Frame()
        self.listbox_filters_favorite = Gtk.ListBox()

        self.widget_filters_favorite = PreferencesItem()
        self.check_filter_favorite = Gtk.Switch()

        self.widget_filters_unfavorite = PreferencesItem()
        self.check_filter_unfavorite = Gtk.Switch()

        self.frame_filters_multiplayer = Gtk.Frame()
        self.listbox_filters_multiplayer = Gtk.ListBox()

        self.widget_filters_multiplayer = PreferencesItem()
        self.check_filter_multiplayer = Gtk.Switch()

        self.widget_filters_singleplayer = PreferencesItem()
        self.check_filter_singleplayer = Gtk.Switch()

        self.frame_filters_finish = Gtk.Frame()
        self.listbox_filters_finish = Gtk.ListBox()

        self.widget_filters_finish = PreferencesItem()
        self.check_filter_finish = Gtk.Switch()

        self.widget_filters_unfinish = PreferencesItem()
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
        #   Games - Sidebar
        # ------------------------------------

        self.scroll_sidebar = Gtk.ScrolledWindow()

        self.paned_games = Gtk.Paned()

        # Properties
        self.paned_games.set_orientation(Gtk.Orientation.VERTICAL)

        # ------------------------------------
        #   Games - Sidebar title
        # ------------------------------------

        self.image_sidebar_title = Gtk.Image()
        self.label_sidebar_title = Gtk.Label()

        # Properties
        self.image_sidebar_title.set_no_show_all(True)
        self.image_sidebar_title.set_halign(Gtk.Align.CENTER)
        self.image_sidebar_title.set_valign(Gtk.Align.CENTER)

        self.label_sidebar_title.set_use_markup(True)
        self.label_sidebar_title.set_halign(Gtk.Align.START)
        self.label_sidebar_title.set_valign(Gtk.Align.CENTER)
        self.label_sidebar_title.set_ellipsize(Pango.EllipsizeMode.END)

        # ------------------------------------
        #   Games - Sidebar tags
        # ------------------------------------

        self.image_sidebar_tags = Gtk.Image()
        self.button_sidebar_tags = Gtk.MenuButton()

        self.popover_sidebar_tags = Gtk.Popover()

        self.scroll_sidebar_tags = Gtk.ScrolledWindow()
        self.frame_sidebar_tags = Gtk.Frame()

        self.listbox_sidebar_tags = Gtk.ListBox()

        # Properties
        self.button_sidebar_tags.set_tooltip_text(_("Tags"))
        self.button_sidebar_tags.set_use_popover(True)

        self.popover_sidebar_tags.set_modal(True)

        self.scroll_sidebar_tags.set_size_request(150, 200)
        self.scroll_sidebar_tags.set_border_width(6)
        self.scroll_sidebar_tags.set_policy(
            Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.listbox_sidebar_tags.set_selection_mode(Gtk.SelectionMode.NONE)
        self.listbox_sidebar_tags.set_valign(Gtk.Align.FILL)
        self.listbox_sidebar_tags.set_vexpand(True)

        # ------------------------------------
        #   Games - Sidebar screenshot
        # ------------------------------------

        self.scroll_sidebar_screenshot = Gtk.ScrolledWindow()
        self.view_sidebar_screenshot = Gtk.Viewport()

        self.frame_sidebar_screenshot = Gtk.Frame()
        self.image_sidebar_screenshot = Gtk.Image()

        # Properties
        self.scroll_sidebar_screenshot.set_propagate_natural_width(True)
        self.scroll_sidebar_screenshot.set_propagate_natural_height(True)
        self.scroll_sidebar_screenshot.set_hexpand(False)

        self.view_sidebar_screenshot.drag_source_set(
            Gdk.ModifierType.BUTTON1_MASK, self.targets, Gdk.DragAction.COPY)

        self.frame_sidebar_screenshot.set_valign(Gtk.Align.CENTER)
        self.frame_sidebar_screenshot.set_halign(Gtk.Align.CENTER)

        self.image_sidebar_screenshot.set_halign(Gtk.Align.CENTER)
        self.image_sidebar_screenshot.set_valign(Gtk.Align.CENTER)

        # ------------------------------------
        #   Games - Sidebar content
        # ------------------------------------

        self.scroll_sidebar_informations = Gtk.ScrolledWindow()

        # Properties
        self.scroll_sidebar_informations.set_propagate_natural_width(True)
        self.scroll_sidebar_informations.set_propagate_natural_height(True)
        self.scroll_sidebar_informations.set_policy(
            Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        # ------------------------------------
        #   Games - Sidebar description
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

        self.label_sidebar_installed_value.set_use_markup(True)
        self.label_sidebar_installed_value.set_halign(Gtk.Align.START)
        self.label_sidebar_installed_value.set_valign(Gtk.Align.CENTER)

        self.label_sidebar_emulator.set_text(_("Emulator"))
        self.label_sidebar_emulator.set_halign(Gtk.Align.END)
        self.label_sidebar_emulator.set_valign(Gtk.Align.CENTER)
        self.label_sidebar_emulator.get_style_context().add_class("dim-label")
        self.label_sidebar_emulator.set_margin_bottom(12)

        self.label_sidebar_emulator_value.set_use_markup(True)
        self.label_sidebar_emulator_value.set_halign(Gtk.Align.START)
        self.label_sidebar_emulator_value.set_valign(Gtk.Align.CENTER)
        self.label_sidebar_emulator_value.set_margin_bottom(12)

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
        #   Games - Treeview / Grid mode
        # ------------------------------------

        self.scroll_games_grid = Gtk.ScrolledWindow()

        self.model_games_grid = Gtk.ListStore(
            Pixbuf, # Cover icon
            str,    # Name
            object  # Game object
        )
        self.iconview_games = Gtk.IconView()

        self.filter_games_grid = self.model_games_grid.filter_new()
        self.sorted_games_grid = Gtk.TreeModelSort(model=self.filter_games_grid)

        # Properties
        self.scroll_games_grid.set_no_show_all(True)

        self.sorted_games_grid.set_sort_column_id(
            Columns.Grid.Name, Gtk.SortType.ASCENDING)

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

        self.filter_games_list = self.model_games_list.filter_new()
        self.sorted_games_list = Gtk.TreeModelSort(model=self.filter_games_list)

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
        self.scroll_games_list.set_no_show_all(True)

        self.sorted_games_list.set_sort_func(Columns.List.Favorite,
            self.__on_sort_games, Columns.List.Favorite)
        self.sorted_games_list.set_sort_func(Columns.List.Multiplayer,
            self.__on_sort_games, Columns.List.Multiplayer)
        self.sorted_games_list.set_sort_func(Columns.List.Finish,
            self.__on_sort_games, Columns.List.Finish)
        self.sorted_games_list.set_sort_func(Columns.List.LastPlay,
            self.__on_sort_games, Columns.List.LastPlay)
        self.sorted_games_list.set_sort_func(Columns.List.TimePlay,
            self.__on_sort_games, Columns.List.TimePlay)
        self.sorted_games_list.set_sort_func(Columns.List.Score,
            self.__on_sort_games, Columns.List.Score)
        self.sorted_games_list.set_sort_func(Columns.List.Installed,
            self.__on_sort_games, Columns.List.Installed)

        self.treeview_games.set_model(self.sorted_games_list)
        self.treeview_games.set_search_column(Columns.List.Name)
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
        self.column_game_favorite.set_sort_column_id(Columns.List.Favorite)

        self.column_game_multiplayer.pack_start(
            self.cell_game_multiplayer, False)
        self.column_game_multiplayer.set_sort_column_id(
            Columns.List.Multiplayer)

        self.column_game_finish.pack_start(
            self.cell_game_finish, False)
        self.column_game_finish.set_sort_column_id(Columns.List.Finish)

        self.column_game_name.set_expand(True)
        self.column_game_name.set_resizable(True)
        self.column_game_name.set_min_width(100)
        self.column_game_name.set_fixed_width(300)
        self.column_game_name.set_sort_column_id(Columns.List.Name)
        self.column_game_name.pack_start(
            self.cell_game_name, True)

        self.column_game_play.set_sort_column_id(Columns.List.Played)
        self.column_game_play.set_alignment(.5)
        self.column_game_play.pack_start(
            self.cell_game_play, False)

        self.column_game_last_play.set_sort_column_id(Columns.List.LastPlay)
        self.column_game_last_play.set_alignment(.5)
        self.column_game_last_play.pack_start(
            self.cell_game_last_play, False)
        self.column_game_last_play.pack_start(
            self.cell_game_last_play_time, False)

        self.column_game_play_time.set_sort_column_id(Columns.List.TimePlay)
        self.column_game_play_time.set_alignment(.5)
        self.column_game_play_time.pack_start(
            self.cell_game_play_time, False)

        self.column_game_score.set_sort_column_id(Columns.List.Score)
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

        self.column_game_installed.set_sort_column_id(Columns.List.Installed)
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
            self.cell_game_favorite, "pixbuf", Columns.List.Favorite)
        self.column_game_multiplayer.add_attribute(
            self.cell_game_multiplayer, "pixbuf", Columns.List.Multiplayer)
        self.column_game_finish.add_attribute(
            self.cell_game_finish, "pixbuf", Columns.List.Finish)
        self.column_game_name.add_attribute(
            self.cell_game_name, "text", Columns.List.Name)
        self.column_game_play.add_attribute(
            self.cell_game_play, "text", Columns.List.Played)
        self.column_game_last_play.add_attribute(
            self.cell_game_last_play, "text", Columns.List.LastPlay)
        self.column_game_last_play.add_attribute(
            self.cell_game_last_play_time, "text", Columns.List.LastTimePlay)
        self.column_game_play_time.add_attribute(
            self.cell_game_play_time, "text", Columns.List.TimePlay)
        self.column_game_installed.add_attribute(
            self.cell_game_installed, "text", Columns.List.Installed)
        self.column_game_flags.add_attribute(
            self.cell_game_except, "pixbuf", Columns.List.Except)
        self.column_game_flags.add_attribute(
            self.cell_game_snapshots, "pixbuf", Columns.List.Snapshots)
        self.column_game_flags.add_attribute(
            self.cell_game_save, "pixbuf", Columns.List.Save)

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

        self.cell_game_name.set_padding(4, 4)
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
        self.menu_item_maintenance = Gtk.MenuItem()
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

        self.menu_item_maintenance.set_label(
            "%s…" % _("_Maintenance"))
        self.menu_item_maintenance.set_use_underline(True)

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


    def __init_packing(self):
        """ Initialize widgets packing in main window
        """

        # Main widgets
        self.grid.pack_start(self.menubar, False, False, 0)
        self.grid.pack_start(self.toolbar, False, False, 0)
        self.grid.pack_start(self.grid_infobar, False, False, 0)
        self.grid.pack_start(self.paned_games, True, True, 0)
        self.grid.pack_start(self.statusbar, False, False, 0)

        # ------------------------------------
        #   Headerbar
        # ------------------------------------

        self.headerbar.pack_end(self.button_headerbar_menu)

        # Headerbar game launch
        self.grid_game_launch.pack_start(
            self.button_headerbar_launch, True, True, 0)
        self.grid_game_launch.pack_start(
            self.button_headerbar_fullscreen, True, True, 0)

        self.button_headerbar_fullscreen.add(self.image_headerbar_fullscreen)

        # Headerbar main menu
        self.button_headerbar_menu.add(self.image_headerbar_menu)
        self.button_headerbar_menu.set_popover(self.popover_menu)

        self.popover_menu.add(self.grid_menu)

        self.grid_menu.pack_start(
            self.frame_menu_options, False, False, 0)
        self.grid_menu.pack_start(
            self.frame_menu_actions, False, False, 0)
        self.grid_menu.pack_start(
            self.frame_menu_system, False, False, 0)

        self.frame_menu_options.add(self.listbox_menu_options)

        self.listbox_menu_options.add(
            self.widget_menu_dark_theme)
        self.listbox_menu_options.add(
            self.widget_menu_sidebar)
        self.listbox_menu_options.add(
            self.widget_menu_statusbar)

        self.frame_menu_actions.add(self.listbox_menu_actions)

        self.listbox_menu_actions.add(
            self.widget_menu_preferences)
        self.listbox_menu_actions.add(
            self.widget_menu_log)

        self.frame_menu_system.add(self.listbox_menu_system)

        self.listbox_menu_system.add(
            self.widget_menu_about)
        self.listbox_menu_system.add(
            self.widget_menu_quit)

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
        self.menubar_edit_menu.insert(self.menubar_edit_item_maintenance, -1)
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

        self.toolbar.insert(self.item_toolbar_properties, -1)
        self.toolbar.insert(Gtk.SeparatorToolItem(), -1)
        self.toolbar.insert(self.item_toolbar_option, -1)
        self.toolbar.insert(Gtk.SeparatorToolItem(), -1)
        self.toolbar.insert(self.item_toolbar_view_mode, -1)
        self.toolbar.insert(self.item_toolbar_separator, -1)
        self.toolbar.insert(self.item_toolbar_consoles, -1)
        self.toolbar.insert(Gtk.SeparatorToolItem(), -1)
        self.toolbar.insert(self.item_toolbar_search, -1)

        self.item_toolbar_properties.add(self.button_toolbar_parameters)
        self.item_toolbar_option.add(self.grid_game_options)
        self.item_toolbar_view_mode.add(self.grid_game_view_mode)
        self.item_toolbar_consoles.add(self.grid_consoles)
        self.item_toolbar_search.add(self.grid_filters)

        self.button_toolbar_parameters.add(self.image_toolbar_parameters)
        self.button_toolbar_screenshots.add(self.image_toolbar_screenshots)
        self.button_toolbar_output.add(self.image_toolbar_output)
        self.button_toolbar_notes.add(self.image_toolbar_notes)

        self.button_consoles_menu.add(self.image_consoles_menu)

        self.grid_game_options.pack_start(
            self.button_toolbar_screenshots, False, False, 0)
        self.grid_game_options.pack_start(
            self.button_toolbar_output, False, False, 0)
        self.grid_game_options.pack_start(
            self.button_toolbar_notes, False, False, 0)

        # Headerbar games list view mode
        self.grid_game_view_mode.pack_start(
            self.button_toolbar_list, True, True, 0)
        self.grid_game_view_mode.pack_start(
            self.button_toolbar_grid, True, True, 0)

        self.button_toolbar_grid.add(self.image_toolbar_grid)
        self.button_toolbar_list.add(self.image_toolbar_list)

        # Toolbar - Consoles
        self.grid_consoles.pack_start(
            self.button_consoles, False, False, 0)
        self.grid_consoles.pack_start(
            self.button_consoles_menu, False, False, 0)

        # Toolbar - Consoles menu
        self.popover_consoles_menu.add(self.grid_consoles_menu)

        self.grid_consoles_menu.pack_start(
            self.frame_consoles_options, False, False, 0)
        self.grid_consoles_menu.pack_start(
            self.frame_consoles_actions, False, False, 0)

        self.frame_consoles_actions.add(self.listbox_consoles_actions)

        self.listbox_consoles_actions.add(
            self.widget_consoles_properties)
        self.listbox_consoles_actions.add(
            self.widget_consoles_refresh)

        self.frame_consoles_options.add(self.listbox_consoles_options)

        self.listbox_consoles_options.add(
            self.widget_consoles_options_favorite)
        self.listbox_consoles_options.add(
            self.widget_consoles_options_recursive)

        # Toolbar - Filters menu
        self.button_toolbar_filters.set_popover(self.popover_toolbar_filters)

        self.grid_filters.pack_start(
            self.entry_toolbar_filters, False, False, 0)
        self.grid_filters.pack_start(
            self.button_toolbar_filters, False, False, 0)

        self.popover_toolbar_filters.add(self.grid_filters_popover)

        self.grid_filters_popover.pack_start(
            self.frame_filters_favorite, False, False, 0)
        self.grid_filters_popover.pack_start(
            self.frame_filters_multiplayer, False, False, 0)
        self.grid_filters_popover.pack_start(
            self.frame_filters_finish, False, False, 0)
        self.grid_filters_popover.pack_start(
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

        self.paned_games.pack1(self.grid_games, False, True)
        self.paned_games.pack2(self.scroll_sidebar, True, True)

        # Sidebar
        self.scroll_sidebar.add(self.grid_sidebar)

        self.scroll_sidebar_screenshot.add(self.view_sidebar_screenshot)
        self.view_sidebar_screenshot.add(self.frame_sidebar_screenshot)
        self.frame_sidebar_screenshot.add(self.image_sidebar_screenshot)

        self.scroll_sidebar_informations.add(self.grid_sidebar_informations)

        self.grid_sidebar.pack_start(
            self.grid_sidebar_title, False, False, 0)
        self.grid_sidebar.pack_start(
            self.grid_sidebar_content, True, True, 0)

        self.grid_sidebar_title.pack_start(
            self.image_sidebar_title, False, False, 0)
        self.grid_sidebar_title.pack_start(
            self.label_sidebar_title, True, True, 0)
        self.grid_sidebar_title.pack_start(
            self.button_sidebar_tags, False, False, 0)

        self.grid_sidebar_content.pack_start(
            self.scroll_sidebar_screenshot, False, False, 0)
        self.grid_sidebar_content.pack_start(
            self.scroll_sidebar_informations, True, True, 0)

        # Sidebar - Tags
        self.button_sidebar_tags.add(self.image_sidebar_tags)
        self.button_sidebar_tags.set_popover(self.popover_sidebar_tags)

        self.popover_sidebar_tags.add(self.scroll_sidebar_tags)

        self.scroll_sidebar_tags.add(self.frame_sidebar_tags)

        self.frame_sidebar_tags.add(self.listbox_sidebar_tags)

        # Sidebar - Informations
        self.grid_sidebar_informations.pack_start(
            self.grid_sidebar_informations_header, True, True, 0)
        self.grid_sidebar_informations.pack_start(
            self.grid_sidebar_informations_footer, True, True, 0)

        self.grid_sidebar_informations_header.attach(
            self.label_sidebar_played, 0, 0, 1, 1)
        self.grid_sidebar_informations_header.attach(
            self.label_sidebar_played_value, 1, 0, 1, 1)
        self.grid_sidebar_informations_header.attach(
            self.label_sidebar_play_time, 0, 1, 1, 1)
        self.grid_sidebar_informations_header.attach(
            self.label_sidebar_play_time_value, 1, 1, 1, 1)
        self.grid_sidebar_informations_header.attach(
            self.label_sidebar_last_play, 0, 2, 1, 1)
        self.grid_sidebar_informations_header.attach(
            self.label_sidebar_last_play_value, 1, 2, 1, 1)
        self.grid_sidebar_informations_header.attach(
            self.label_sidebar_last_time, 0, 3, 1, 1)
        self.grid_sidebar_informations_header.attach(
            self.label_sidebar_last_time_value, 1, 3, 1, 1)
        self.grid_sidebar_informations_header.attach(
            self.label_sidebar_installed, 0, 4, 1, 1)
        self.grid_sidebar_informations_header.attach(
            self.label_sidebar_installed_value, 1, 4, 1, 1)

        self.grid_sidebar_informations_footer.attach(
            self.label_sidebar_emulator, 0, 0, 1, 1)
        self.grid_sidebar_informations_footer.attach(
            self.label_sidebar_emulator_value, 1, 0, 1, 1)
        self.grid_sidebar_informations_footer.attach(
            self.label_sidebar_score, 0, 1, 1, 1)
        self.grid_sidebar_informations_footer.attach(
            self.grid_sidebar_score, 1, 1, 1, 1)

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

        # Games
        self.grid_games.pack_start(self.scroll_games_placeholder, True, True, 0)
        self.grid_games.pack_start(self.scroll_games_list, True, True, 0)
        self.grid_games.pack_start(self.scroll_games_grid, True, True, 0)

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
        self.menu_games_edit.append(self.menu_item_maintenance)
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
        self.connect("script-terminate", self.__on_script_terminate)

        # ------------------------------------
        #   Window
        # ------------------------------------

        self.connect(
            "delete-event", self.__stop_interface)
        self.connect(
            "key-press-event", self.__on_manage_keys)
        # self.connect(
            # "configure-event", self.__on_resize_window)

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
        self.menubar_edit_item_maintenance.connect(
            "activate", self.__on_game_maintenance)
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

        self.button_headerbar_launch.connect(
            "clicked", self.__on_game_launch)
        self.fullscreen_signal_tool = self.button_headerbar_fullscreen.connect(
            "toggled", self.__on_activate_fullscreen)
        self.button_toolbar_screenshots.connect(
            "clicked", self.__on_show_viewer)
        self.button_toolbar_output.connect(
            "clicked", self.__on_game_log)
        self.button_toolbar_notes.connect(
            "clicked", self.__on_show_notes)
        self.button_toolbar_parameters.connect(
            "clicked", self.__on_game_parameters)

        self.list_view_signal = self.button_toolbar_list.connect(
            "toggled", self.__on_switch_games_view)
        self.grid_view_signal = self.button_toolbar_grid.connect(
            "toggled", self.__on_switch_games_view)

        self.listbox_menu_options.connect(
            "row-activated", on_activate_listboxrow)
        self.listbox_menu_actions.connect(
            "row-activated", on_activate_listboxrow)
        self.listbox_menu_system.connect(
            "row-activated", on_activate_listboxrow)

        self.listbox_consoles.connect(
            "row-activated", self.__on_selected_console)
        self.entry_consoles.connect(
            "changed", self.__on_update_consoles)

        self.listbox_consoles_options.connect(
            "row-activated", on_activate_listboxrow)
        self.listbox_consoles_actions.connect(
            "row-activated", on_activate_listboxrow)

        self.button_consoles_properties.connect(
            "clicked", self.__on_show_emulator_config)
        self.button_consoles_refresh.connect(
            "clicked", self.__on_reload_games)

        self.favorite_signal_options = self.switch_consoles_favorite.connect(
            "state-set", self.__on_change_console_option)
        self.recursive_signal_options = self.switch_consoles_recursive.connect(
            "state-set", self.__on_change_console_option)

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
        self.menu_item_maintenance.connect(
            "activate", self.__on_game_maintenance)
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

        self.button_menu_preferences.connect(
            "clicked", self.__on_show_preferences)

        self.button_menu_log.connect(
            "clicked", self.__on_show_log)
        self.dark_signal_menu = self.switch_menu_dark_theme.connect(
            "state-set", self.__on_activate_dark_theme)
        self.side_signal_menu = self.switch_menu_sidebar.connect(
            "state-set", self.__on_activate_sidebar)
        self.status_signal_menu = self.switch_menu_statusbar.connect(
            "state-set", self.__on_activate_statusbar)
        self.button_menu_about.connect(
            "clicked", self.__on_show_about)
        self.button_menu_quit.connect(
            "clicked", self.__stop_interface)

        # ------------------------------------
        #   Sidebar
        # ------------------------------------

        self.view_sidebar_screenshot.connect(
            "drag-data-get", self.__on_dnd_send_data)

        self.listbox_sidebar_tags.connect(
            "row-activated", self.__on_filter_tag)

        # ------------------------------------
        #   Games - List
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

        self.filter_games_list.set_visible_func(self.filters_match)

        # ------------------------------------
        #   Games - Grid
        # ------------------------------------

        self.iconview_games.connect(
            "button-press-event", self.__on_selected_game)
        self.iconview_games.connect(
            "key-release-event", self.__on_selected_game)

        self.iconview_games.connect(
            "button-press-event", self.__on_menu_show)
        self.iconview_games.connect(
            "key-release-event", self.__on_menu_show)

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
            self.button_headerbar_fullscreen: self.fullscreen_signal_tool,
            self.button_toolbar_list: self.list_view_signal,
            self.button_toolbar_grid: self.grid_view_signal,
            self.switch_menu_dark_theme: self.dark_signal_menu,
            self.menu_item_favorite: self.favorite_signal_menu,
            self.menu_item_finish: self.finish_signal_menu,
            self.menu_item_multiplayer: self.multi_signal_menu,
            self.switch_menu_sidebar: self.side_signal_menu,
            self.switch_menu_statusbar: self.status_signal_menu,
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

        # Store image references with associate icons
        self.__images_storage = {
            self.image_headerbar_menu: Icons.Symbolic.Menu,
            self.image_headerbar_fullscreen: Icons.Symbolic.Restore,
            self.image_menu_preferences: Icons.Symbolic.System,
            self.image_menu_log: Icons.Symbolic.Terminal,
            self.image_menu_about: Icons.Symbolic.About,
            self.image_menu_quit: Icons.Symbolic.Quit,
            self.image_toolbar_grid: Icons.Symbolic.Grid,
            self.image_toolbar_list: Icons.Symbolic.List,
            self.image_toolbar_parameters: Icons.Symbolic.Gaming,
            self.image_toolbar_screenshots: Icons.Symbolic.Camera,
            self.image_toolbar_output: Icons.Symbolic.Terminal,
            self.image_toolbar_notes: Icons.Symbolic.Editor,
            self.image_sidebar_tags: Icons.Symbolic.Paperclip,
            self.image_consoles_properties: Icons.Symbolic.Properties,
            self.image_consoles_refresh: Icons.Symbolic.Refresh,
            self.image_consoles_menu: Icons.Symbolic.ViewMore
        }

        # Store treeview columns references
        self.__columns_storage = {
            "play": self.column_game_play,
            "last_play": self.column_game_last_play,
            "play_time": self.column_game_play_time,
            "score": self.column_game_score,
            "installed": self.column_game_installed,
            "flags": self.column_game_flags
        }

        # Store widgets references which can change sensitive state
        self.__widgets_storage = (
            self.button_headerbar_launch,
            # Menubar
            self.menubar_game_item_launch,
            self.menubar_game_item_favorite,
            self.menubar_game_item_multiplayer,
            self.menubar_game_item_finish,
            self.menubar_game_item_screenshots,
            self.menubar_game_item_output,
            self.menubar_game_item_notes,
            self.menubar_game_item_properties,
            self.menubar_edit_item_rename,
            self.menubar_edit_item_copy,
            self.menubar_edit_item_open,
            self.menubar_edit_item_cover,
            self.menubar_edit_item_desktop,
            self.menubar_edit_item_maintenance,
            self.menubar_edit_item_database,
            self.menubar_edit_item_delete,
            self.menubar_edit_item_mednafen,
            self.menubar_edit_item_score,
            self.menubar_edit_item_duplicate,
            # Toolbar
            self.button_toolbar_output,
            self.button_toolbar_notes,
            self.button_toolbar_parameters,
            self.button_toolbar_screenshots,
            # Consoles
            self.widget_consoles_properties,
            self.widget_consoles_options_favorite,
            self.widget_consoles_options_recursive,
            # Game menu
            self.menu_item_rename,
            self.menu_item_favorite,
            self.menu_item_multiplayer,
            self.menu_item_finish,
            self.menu_item_screenshots,
            self.menu_item_output,
            self.menu_item_notes,
            self.menu_item_copy,
            self.menu_item_open,
            self.menu_item_cover,
            self.menu_item_desktop,
            self.menu_item_remove,
            self.menu_item_maintenance,
            self.menu_item_database,
            self.menu_item_mednafen,
            self.menu_item_duplicate
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


    def __start_interface(self):
        """ Load data and start interface
        """

        self.logger.debug("Use GTK+ library v.%d.%d.%d" % (
            Gtk.get_major_version(), Gtk.get_minor_version(),
            Gtk.get_micro_version()))

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
                "Enjoy and have fun :D"), Icons.Symbolic.SmileBig, False)

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

        self.logger.info(_("Close interface"))

        # ------------------------------------
        #   Threads
        # ------------------------------------

        # Remove games listing thread
        if not self.list_thread == 0:
            source_remove(self.list_thread)

        # Remove game and script threads
        for thread in threading.enumerate().copy():

            # Avoid to remove the main thread
            if thread is not threading.main_thread():
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
        self.config.update()

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

        if init_interface and icon_size in self.__toolbar_sizes:
            size = self.__toolbar_sizes[icon_size]

            # Avoid to change icon size if there is no change
            if not size == self.toolbar.get_icon_size():

                self.toolbar.set_icon_size(self.__toolbar_sizes[icon_size])

                for widget, icon in self.__images_storage.items():
                    widget.set_from_icon_name(
                        icon, self.toolbar.get_icon_size())

        # ------------------------------------
        #   Icons
        # ------------------------------------

        self.icons.set_translucent_status(self.config.getboolean(
            "gem", "use_translucent_icons", fallback=False))

        # ------------------------------------
        #   Window first drawing
        # ------------------------------------

        if init_interface:

            view_mode = self.config.get(
                "gem", "games_view_mode", fallback=Columns.Key.List)

            if view_mode == Columns.Key.Grid:
                self.button_toolbar_grid.set_active(True)

            else:
                self.button_toolbar_list.set_active(True)

            # ------------------------------------
            #   Column sorting
            # ------------------------------------

            if self.config.getboolean(
                "gem", "load_sort_column_startup", fallback=True):

                column = getattr(Columns.List, self.config.get(
                    "gem", "last_sort_column", fallback="Name"), None)
                order = self.config.get(
                    "gem", "last_sort_column_order", fallback="asc")

                if column is None:
                    column, order = (Columns.List.Name, "asc")

                if order == "desc":
                    self.sorted_games_list.set_sort_column_id(
                        column, Gtk.SortType.DESCENDING)

                else:
                    self.sorted_games_list.set_sort_column_id(
                        column, Gtk.SortType.ASCENDING)

            else:
                self.sorted_games_list.set_sort_column_id(
                    Columns.List.Name, Gtk.SortType.ASCENDING)

            # ------------------------------------
            #   Color theme
            # ------------------------------------

            dark_theme_status = self.config.getboolean(
                "gem", "dark_theme", fallback=False)

            on_change_theme(dark_theme_status)

            self.switch_menu_dark_theme.set_active(dark_theme_status)
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
                self.toolbar.insert(self.item_toolbar_launch, 0)
                self.toolbar.insert(Gtk.SeparatorToolItem(), 1)

                self.item_toolbar_launch.add(self.grid_game_launch)

            # ------------------------------------
            #   Window size
            # ------------------------------------

            try:
                width, height = self.config.get(
                    "windows", "main", fallback="1024x768").split('x')

                self.window_size.base_width = int(width)
                self.window_size.base_height = int(height)

                self.resize(int(width), int(height))

            except ValueError as error:
                self.logger.error(
                    _("Cannot resize main window: %s") % str(error))

            self.set_geometry_hints(self, self.window_size,
                Gdk.WindowHints.MIN_SIZE | Gdk.WindowHints.BASE_SIZE)

            self.__previous_window_size = (
                self.window_size.base_width, self.window_size.base_height)

            self.set_position(Gtk.WindowPosition.CENTER)

            self.hide()
            self.unrealize()

        # ------------------------------------
        #   Shortcuts
        # ------------------------------------

        self.__init_shortcuts()

        # ------------------------------------
        #   Widgets
        # ------------------------------------

        self.show_all()

        self.menu_games.show_all()

        self.grid_menu.show_all()
        self.grid_filters_popover.show_all()

        self.grid_consoles_item.show_all()
        self.grid_consoles_menu.show_all()

        self.infobar.show_all()
        self.infobar.get_content_area().show_all()

        self.scroll_sidebar.show_all()
        self.scroll_sidebar_tags.show_all()
        self.scroll_sidebar_screenshot.show_all()
        self.scroll_sidebar_informations.show_all()

        self.grid_games_placeholder.show_all()

        if self.use_classic_theme:
            self.logger.debug("Use classic theme for GTK+ interface")
            self.menubar.show_all()

        else:
            self.logger.debug("Use default theme for GTK+ interface")
            self.menubar.hide()

        self.set_infobar()
        self.sensitive_interface()

        # ------------------------------------
        #   Header
        # ------------------------------------

        self.headerbar.set_show_close_button(
            self.config.getboolean("gem", "show_header", fallback=True))

        # ------------------------------------
        #   Consoles
        # ------------------------------------

        consoles_position = self.config.getboolean(
            "gem", "use_combobox_consoles", fallback=True)

        # ------------------------------------
        #   Sidebar
        # ------------------------------------

        self.sidebar_image = None

        sidebar_status = self.config.getboolean(
            "gem", "show_sidebar", fallback=True)

        self.switch_menu_sidebar.set_active(sidebar_status)
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

            self.grid_sidebar.show_all()

            self.grid_sidebar_content.set_orientation(
                Gtk.Orientation.VERTICAL)
            self.grid_sidebar_content.reorder_child(
                self.scroll_sidebar_screenshot, 0)

            self.grid_sidebar_informations.set_halign(Gtk.Align.FILL)
            self.grid_sidebar_informations.set_hexpand(True)
            self.grid_sidebar_informations.set_orientation(
                Gtk.Orientation.VERTICAL)

            self.grid_sidebar_informations_header.set_margin_bottom(6)

            self.paned_games.set_orientation(Gtk.Orientation.HORIZONTAL)
            self.paned_games.set_position(
                self.paned_games.get_allocated_width() - 350)

        # Bottom-side sidebar
        elif sidebar_orientation == "vertical" and \
            not previous_mode == Gtk.Orientation.VERTICAL:

            self.grid_sidebar.show_all()

            self.grid_sidebar_title.set_valign(Gtk.Align.START)

            self.grid_sidebar_content.set_orientation(
                Gtk.Orientation.HORIZONTAL)
            self.grid_sidebar_content.reorder_child(
                self.scroll_sidebar_screenshot, -1)

            self.grid_sidebar_informations.set_halign(Gtk.Align.START)
            self.grid_sidebar_informations.set_hexpand(False)
            self.grid_sidebar_informations.set_orientation(
                Gtk.Orientation.HORIZONTAL)

            self.grid_sidebar_informations_header.set_margin_bottom(0)

            self.paned_games.set_orientation(Gtk.Orientation.VERTICAL)
            self.paned_games.set_position(
                self.paned_games.get_allocated_height() - 220)

        # Show sidebar
        if sidebar_status:
            self.scroll_sidebar.set_visible(True)

            self.scroll_sidebar_screenshot.set_visible(False)
            self.frame_sidebar_screenshot.set_visible(False)

            self.grid_sidebar_informations.show_all()

        # Hide sidebar
        else:
            self.scroll_sidebar.set_visible(False)

        # ------------------------------------
        #   Statusbar
        # ------------------------------------

        statusbar_status = self.config.getboolean(
            "gem", "show_statusbar", fallback=True)

        self.switch_menu_statusbar.set_active(statusbar_status)
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
        line = self.config.item("gem", "games_treeview_lines", "none")

        if line in self.__treeview_lines:
            self.treeview_games.set_grid_lines(self.__treeview_lines[line])

        # Games - Treeview columns
        for key, widget in self.__columns_storage.items():
            widget.set_visible(
                self.config.getboolean("columns", key, fallback=True))

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

        self.scroll_games_list.set_visible(False)
        self.scroll_games_grid.set_visible(False)
        self.scroll_games_placeholder.set_visible(False)

        current_console = self.append_consoles()

        # Show games placeholder when no console available or selected
        if current_console is None or len(self.listbox_consoles) == 0:
            self.scroll_games_placeholder.set_visible(True)

        self.selection = dict(console=None, game=None)

        if current_console is None:
            self.model_games_list.clear()

            if len(self.consoles_iter.keys()) > 0:
                row = list(self.consoles_iter.values())[0]

                self.button_consoles.select_row(row)

                self.__on_selected_console(self.button_consoles, row)

        else:
            self.button_consoles.select_row(current_console)

            self.__on_selected_console(self.button_consoles, current_console)

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
            game = model.get_value(row, Columns.List.Object)

        elif model == self.model_games_grid:
            game = model.get_value(row, Columns.Grid.Object)

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

                if not self.entry_toolbar_filters.get_text() == label.get_label():
                    text = label.get_label()

        self.entry_toolbar_filters.set_text(text)


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
                "keys": self.config.item("keys", "start", "<Control>Return")
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
                    self.button_toolbar_screenshots
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
                "path": "<GEM>/game/maintenance",
                "widgets": [
                    self.menu_item_maintenance,
                    self.menubar_edit_item_maintenance
                ],
                "keys": self.config.item("keys", "maintenance", "<Control>D")
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

                dialog.set_size_request(500, -1)

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

        self.scroll_sidebar_screenshot.set_visible(False)
        self.scroll_sidebar_informations.set_visible(False)
        self.button_sidebar_tags.set_visible(False)
        self.image_sidebar_title.set_visible(False)

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
            self.scroll_sidebar_informations.set_visible(True)

            if console is not None:
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
                        self.icons.get("screenshot"))

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
                        self.icons.get_translucent("screenshot"))

                # Set maximum size with current file
                if image is not None and exists(image):
                    self.sidebar_image = image

                    orientation = self.paned_games.get_orientation()

                    # Right side
                    if orientation == Gtk.Orientation.HORIZONTAL:
                        size = (400, 180)

                    # Bottom side
                    else:
                        size = (350, 150)

                    image = Pixbuf.new_from_file_at_scale(image, *size, True)

                self.image_sidebar_screenshot.set_from_pixbuf(image)

                if image is not None:
                    self.scroll_sidebar_screenshot.set_visible(True)
                    self.scroll_sidebar_screenshot.show_all()

                # ----------------------------
                #   Show cover
                # ----------------------------

                image = None

                # A special cover image has been set by user
                if game.cover is not None and exists(game.cover):
                    image = Pixbuf.new_from_file_at_scale(
                        game.cover, 64, 24, True)

                self.image_sidebar_title.set_from_pixbuf(image)

                if image is not None:
                    self.image_sidebar_title.set_visible(True)

                # ----------------------------
                #   Show informations
                # ----------------------------

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
                        "condition": game.last_launch_date is not None,
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
                        "condition": emulator is not None,
                        "markup": emulator.name
                    }
                ]

                for data in widgets:

                    # Default label value widget
                    if "condition" in data:

                        if data["condition"]:
                            data["widget"].set_markup(data["markup"])

                            if "tooltip" in data:
                                data["widget"].set_tooltip_text(data["tooltip"])

                        else:
                            data["widget"].set_markup(str())
                            data["widget"].set_tooltip_text(str())

                    # Score case
                    elif data["widget"] == self.grid_sidebar_score:
                        children = data["widget"].get_children()

                        for child in children:
                            index = children.index(child)

                            if game.score >= index + 1:
                                child.set_from_pixbuf(
                                    self.icons.get("starred"))

                            else:
                                child.set_from_pixbuf(
                                    self.icons.get_translucent("nostarred"))

                # Game tags
                for tag in sorted(game.tags):
                    label = Gtk.Label.new(tag)
                    label.set_halign(Gtk.Align.FILL)

                    box = Gtk.Box()
                    box.set_orientation(Gtk.Orientation.HORIZONTAL)
                    box.set_border_width(6)

                    box.pack_start(label, True, True, 0)

                    row = Gtk.ListBoxRow()
                    row.add(box)
                    row.show_all()

                    self.listbox_sidebar_tags.add(row)

                if len(game.tags) > 0:
                    self.button_sidebar_tags.set_visible(True)

                # Game emulator
                if emulator is not None:

                    # Game savestates
                    if len(emulator.get_savestates(game)) > 0:
                        self.image_statusbar_savestates.set_from_pixbuf(
                            self.icons.get("savestate"))
                    else:
                        self.image_statusbar_savestates.set_from_pixbuf(
                            self.icons.get_translucent("savestate"))

                    # Game custom parameters
                    if (game.emulator is not None and \
                        not game.emulator.name == console.emulator.name) or \
                        game.default is not None:
                        self.image_statusbar_properties.set_from_pixbuf(
                            self.icons.get("parameter"))
                    else:
                        self.image_statusbar_properties.set_from_pixbuf(
                            self.icons.get_translucent("parameter"))

                else:
                    self.image_statusbar_savestates.set_from_pixbuf(
                        self.icons.blank())
                    self.image_statusbar_properties.set_from_pixbuf(
                        self.icons.blank())
                    self.image_statusbar_screenshots.set_from_pixbuf(
                        self.icons.blank())

        else:
            self.label_sidebar_title.set_text(str())

            self.image_sidebar_screenshot.set_from_pixbuf(None)

            self.image_statusbar_properties.set_from_pixbuf(self.icons.blank())
            self.image_statusbar_savestates.set_from_pixbuf(self.icons.blank())
            self.image_statusbar_screenshots.set_from_pixbuf(self.icons.blank())


    def set_informations_headerbar(self, game=None, console=None):
        """ Update headerbar and statusbar informations from games list

        Parameters
        ----------
        game : gem.engine.api.Game
            Game object
        console : gem.api.Console
            Console object
        """

        if game is None:
            game = self.selection["game"]

        if console is None:
            console = self.selection["console"]

        self.label_statusbar_console.set_visible(False)
        self.label_statusbar_emulator.set_visible(False)

        texts = list()
        emulator = None

        # ----------------------------
        #   Console
        # ----------------------------

        if console is not None:
            emulator = console.emulator

            if len(self.filter_games_list) == 1:
                text = _("1 game available")

                texts.append(text)

            elif len(self.filter_games_list) > 1:
                text = _("%d games available") % len(self.filter_games_list)

                texts.append(text)

            else:
                text = _("N/A")

            self.label_statusbar_console.set_visible(True)
            self.label_statusbar_console.set_markup(
                "<b>%s</b> : %s" % (_("Console"), text))

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
        about.set_version("%s (%s)" % (self.__version, GEM.CodeName))
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
                    self.set_game_data(Columns.List.Snapshots,
                        self.icons.get_translucent("screenshot"), game.filename)


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

            elif exists(path):
                remove(path)

                self.logger.debug("Remove note for %s" % title)

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

        # Retrieve available consoles
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
            self.button_consoles.set_sensitive(True)
            self.button_consoles_menu.set_sensitive(True)

            self.logger.debug(
                "%d console(s) has been added" % len(self.listbox_consoles))

        else:
            self.button_consoles.set_sensitive(False)
            self.button_consoles_menu.set_sensitive(False)

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

        hide = self.config.getboolean(
            "gem", "hide_empty_console", fallback=False)

        console = self.api.get_console(identifier)

        # Check if console ROM path exist
        if console.emulator is not None and exists(console.path):

            # Reload games list
            console.set_games(self.api)

            if not hide or len(console.games) > 0:
                status = self.icons.blank()

                # Check if current emulator can be launched
                if not console.emulator.exists:
                    status = self.icons.get("warning")

                    self.logger.warning(
                        _("Cannot find %(binary)s for %(console)s") % {
                            "binary": console.emulator.binary,
                            "console": console.name })

                elif console.favorite:
                    status = self.icons.get("favorite")

                icon = console.icon

                if icon is not None:
                    if not exists(expanduser(icon)):
                        icon = self.api.get_local(
                            "icons", "consoles", "%s.%s" % (icon, Icons.Ext))

                    # Get console icon
                    icon = icon_from_data(
                        icon, self.icons.blank(size), size, size)

                else:
                    icon = self.icons.blank()

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
        self.set_informations_headerbar()

        icon = row.data.icon

        if icon is not None:
            if not exists(expanduser(icon)):
                icon = self.api.get_local(
                    "icons", "consoles", "%s.%s" % (icon, Icons.Ext))

            self.__console_icon = set_pixbuf_opacity(
                icon_from_data(icon, self.icons.blank(96), 96, 96), 50)

        else:
            image = self.icons.blank()

        # ------------------------------------
        #   Check data
        # ------------------------------------

        self.sensitive_interface()

        # Check console emulator
        if row.data.emulator is not None:
            configuration = row.data.emulator.configuration

            # Check emulator configurator
            if configuration is not None and exists(configuration):
                self.widget_consoles_properties.set_sensitive(True)
            else:
                self.widget_consoles_properties.set_sensitive(False)

        # Check console options
        self.switch_consoles_favorite.set_active(row.data.favorite)
        self.switch_consoles_recursive.set_active(row.data.recursive)

        # Activate console options buttons
        self.widget_consoles_options_favorite.set_sensitive(True)
        self.widget_consoles_options_recursive.set_sensitive(True)

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

                pixbuf = self.icons.blank()
                if status:
                    pixbuf = self.icons.get("favorite")

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

        self.scroll_games_list.set_visible(False)
        self.scroll_games_grid.set_visible(False)

        self.scroll_games_placeholder.set_visible(True)

        self.model_games_list.clear()
        self.model_games_grid.clear()

        self.set_informations()

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
            games.sort(key=lambda game: game.name.lower().replace(' ', ''))

            if len(games) > 0:
                self.scroll_sidebar.set_visible(True)

                if self.button_toolbar_list.get_active():
                    self.scroll_games_list.set_visible(True)
                    self.treeview_games.show_all()

                if self.button_toolbar_grid.get_active():
                    self.scroll_games_grid.set_visible(True)
                    self.iconview_games.show_all()

                self.scroll_games_placeholder.set_visible(False)

            else:
                self.scroll_sidebar.set_visible(False)

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
                        game ]

                    # Favorite
                    if game.favorite:
                        row_data[Columns.List.Favorite] = \
                            self.icons.get("favorite")

                    # Multiplayer
                    if game.multiplayer:
                        row_data[Columns.List.Multiplayer] = \
                            self.icons.get("multiplayer")

                    # Finish
                    if game.finish:
                        row_data[Columns.List.Finish] = \
                            self.icons.get("finish")

                    # Last launch date
                    if game.last_launch_date is not None:
                        row_data[Columns.List.LastPlay] = \
                            string_from_date(game.last_launch_date)

                    # Last launch time
                    if not game.last_launch_time == timedelta():
                        row_data[Columns.List.LastTimePlay] = \
                            string_from_time(game.last_launch_time)

                    # Play time
                    if not game.play_time == timedelta():
                        row_data[Columns.List.TimePlay] = \
                            string_from_time(game.play_time)

                    # Parameters
                    if game.default is not None:
                        row_data[Columns.List.Except] = \
                            self.icons.get("parameter")

                    elif game.emulator is not None:
                        if not game.emulator.name == console.emulator.name:
                            row_data[Columns.List.Except] = \
                                self.icons.get("parameter")

                    # Installed time
                    if game.installed is not None:
                        row_data[Columns.List.Installed] = \
                            string_from_date(game.installed)

                    # Get global emulator
                    rom_emulator = emulator

                    # Set specified emulator is available
                    if game.emulator is not None:
                        rom_emulator = game.emulator

                    # Snap
                    if len(rom_emulator.get_screenshots(game)) > 0:
                        row_data[Columns.List.Snapshots] = \
                            self.icons.get("screenshot")

                    # Save state
                    if len(rom_emulator.get_savestates(game)) > 0:
                        row_data[Columns.List.Save] = \
                            self.icons.get("savestate")

                    row_list = self.model_games_list.append(row_data)

                    # ------------------------------------
                    #   Grid mode
                    # ------------------------------------

                    row_data = [
                        self.__console_icon,
                        game.name,
                        game ]

                    # Cover icon
                    if game.cover is not None and exists(game.cover):
                        row_data[Columns.Grid.Icon] = \
                            Pixbuf.new_from_file_at_scale(
                            expanduser(game.cover), 96, 96, True)

                    row_grid = self.model_games_grid.append(row_data)

                    # ------------------------------------
                    #   Refesh view
                    # ------------------------------------

                    # Store both Gtk.TreeIter under game filename key
                    self.game_path[game.filename] = [game, row_list, row_grid]

                    self.set_informations_headerbar()

                    self.treeview_games.thaw_child_notify()
                    yield True
                    self.treeview_games.freeze_child_notify()

            # Restore options for packages treeviews
            self.treeview_games.set_enable_search(True)
            self.treeview_games.thaw_child_notify()

        self.set_informations_headerbar()

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
            score = model.get_value(treeiter, Columns.List.Score)

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

            if treeview == self.treeview_games:
                model, treeiter = treeview.get_selection().get_selected()

            elif treeview == self.iconview_games:
                model = treeview.get_model()
                items = treeview.get_selected_items()

                if len(items) >= 1:
                    treeiter = model.get_iter(items[0])

        # ----------------------------
        #   Mouse
        # ----------------------------

        elif event.type in available_events and event.button in (1, 3):

            # Get selection from cursor position
            if event.type == EventType.BUTTON_PRESS:
                selection = treeview.get_path_at_pos(int(event.x), int(event.y))

                if selection is not None:
                    model = treeview.get_model()

                    if treeview == self.treeview_games:
                        treeiter = model.get_iter(selection[0])

                    elif treeview == self.iconview_games:
                        treeiter = model.get_iter(selection)

            # Get selection from TreeView
            elif treeview == self.treeview_games:
                model, treeiter = treeview.get_selection().get_selected()

            # Get selection from IconView
            elif treeview == self.iconview_games:
                model = treeview.get_model()
                items = treeview.get_selected_items()

                if len(items) >= 1:
                    treeiter = model.get_iter(items[0])

            # Mouse - Double click with left mouse button
            if event.type == EventType._2BUTTON_PRESS and event.button == 1:
                run_game = True and not self.is_rename

        # ----------------------------
        #   Retrieve selection
        # ----------------------------

        # Get game data
        if type(treeiter) is Gtk.TreeIter:

            column_id = Columns.List.Object
            if type(treeview) is Gtk.IconView:
                column_id = Columns.Grid.Object

            game = model.get_value(treeiter, column_id)

        # ----------------------------
        #   Game selected
        # ----------------------------

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

                if emulator.configuration is None or \
                    not exists(emulator.configuration):
                    self.widget_consoles_properties.set_sensitive(False)

                # ----------------------------
                #   Manage widgets
                # ----------------------------

                # This game is currently running
                if game.filename in self.threads:
                    self.__on_game_launch_button_update(False)
                    self.button_headerbar_launch.set_sensitive(True)

                    self.menu_item_launch.set_sensitive(False)
                    self.menu_item_database.set_sensitive(False)
                    self.menu_item_remove.set_sensitive(False)
                    self.menu_item_mednafen.set_sensitive(False)

                    self.menubar_game_item_launch.set_sensitive(False)
                    self.menubar_edit_item_database.set_sensitive(False)
                    self.menubar_edit_item_delete.set_sensitive(False)
                    self.menubar_edit_item_mednafen.set_sensitive(False)

                # This is not the same selection, so we change widgets status
                if not same_game:

                    # Check extension and emulator for GBA game on mednafen
                    if not game.extension.lower() == ".gba" or \
                        not "mednafen" in emulator.binary or \
                        not self.__mednafen_status:
                        self.menu_item_mednafen.set_sensitive(False)
                        self.menubar_edit_item_mednafen.set_sensitive(False)

                    # Check screenshots
                    if len(emulator.get_screenshots(game)) == 0:
                        self.button_toolbar_screenshots.set_sensitive(False)
                        self.menu_item_screenshots.set_sensitive(False)
                        self.menubar_game_item_screenshots.set_sensitive(False)

                    if self.check_log() is None:
                        self.button_toolbar_output.set_sensitive(False)
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

                    # Retrieve path from storage cache
                    treeiter, griditer = self.game_path[game.filename][1:]

                    # Update selection in grid view
                    if type(treeview) is Gtk.TreeView:
                        subiter = \
                            self.sorted_games_grid.convert_child_iter_to_iter(
                            self.filter_games_grid.convert_child_iter_to_iter(
                            griditer)[1])[1]

                        path = self.sorted_games_grid.get_path(subiter)

                        if path is not None:
                            self.iconview_games.select_path(path)
                            self.iconview_games.scroll_to_path(
                                path, True, 0.5, 0.5)

                        else:
                            self.iconview_games.unselect_all()

                    # Update selection in list view
                    elif type(treeview) is Gtk.IconView:
                        subiter = \
                            self.sorted_games_list.convert_child_iter_to_iter(
                            self.filter_games_list.convert_child_iter_to_iter(
                            treeiter)[1])[1]

                        path = self.sorted_games_list.get_path(subiter)

                        if path is not None:
                            self.treeview_games.set_cursor(path, None, False)
                            self.treeview_games.scroll_to_cell(
                                path, None, True, 0.5, 0.5)

                        else:
                            self.treeview_games.get_selection().unselect_all()

                    self.__unblock_signals()

                # The user has do a specific action to launch current game
                if run_game:
                    self.__on_game_launch()

        # No game has been choosen (when the user click in the empty view area)
        else:
            self.treeview_games.get_selection().unselect_all()
            self.iconview_games.unselect_all()

            self.selection["game"] = None

            self.__on_game_launch_button_update(True)

            self.sensitive_interface()

        # Update sidebar when this is another selection
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

            if treeview == self.treeview_games:
                selection = treeview.get_path_at_pos(x, y)

            else:
                selection = treeview.get_item_at_pos(x, y)

            if selection is not None:
                model = treeview.get_model()
                treeiter = model.get_iter(selection[0])

                column_id = Columns.Grid.Object
                if treeview == self.treeview_games:
                    column_id = Columns.List.Object

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
                if console is not None and \
                    self.__current_tooltip_pixbuf is None:

                    image = None

                    # Get Game emulator
                    emulator = console.emulator
                    if game.emulator is not None:
                        emulator = game.emulator

                    # Retrieve user choice for tooltip image
                    tooltip_image = self.config.get(
                        "gem", "tooltip_image_type", fallback="screenshot")

                    if not tooltip_image == "none":

                        if tooltip_image in ["both", "cover"]:
                            if game.cover is not None and exists(game.cover):
                                image = game.cover

                        if tooltip_image in ["both", "screenshot"]:
                            screenshots = sorted(emulator.get_screenshots(game))

                            if len(screenshots) > 0:
                                image = screenshots[-1]

                        if image is not None and exists(image):
                            # Resize pixbuf to have a 96 pixels height
                            pixbuf = Pixbuf.new_from_file_at_scale(
                                image, -1, 96, True)

                            self.__current_tooltip_pixbuf = pixbuf

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

        order = Gtk.SortType.ASCENDING

        data1 = model.get_value(row1, Columns.List.Object)
        data2 = model.get_value(row2, Columns.List.Object)

        # Favorite
        if column == Columns.List.Favorite:
            first = data1.favorite
            second = data2.favorite

            order = self.column_game_favorite.get_sort_order()

        # Multiplayer
        elif column == Columns.List.Multiplayer:
            first = data1.multiplayer
            second = data2.multiplayer

            order = self.column_game_multiplayer.get_sort_order()

        # Finish
        elif column == Columns.List.Finish:
            first = data1.finish
            second = data2.finish

            order = self.column_game_finish.get_sort_order()

        # Last play
        elif column == Columns.List.LastPlay:
            first = data1.last_launch_date
            second = data2.last_launch_date

        # Play time
        elif column == Columns.List.TimePlay:
            first = data1.play_time
            second = data2.play_time

        # Score
        elif column == Columns.List.Score:
            first = data1.score
            second = data2.score

            order = self.column_game_score.get_sort_order()

        # Installed
        elif column == Columns.List.Installed:
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

        elif widget == self.button_toolbar_grid:
            self.button_toolbar_list.set_active(not status)

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
                treeview_name = model.get_value(treeiter, Columns.List.Name)

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

        label = self.button_headerbar_launch.get_label()

        if status and not label == _("Play"):
            self.button_headerbar_launch.set_label(
                _("Play"))
            self.button_headerbar_launch.set_tooltip_text(
                _("Launch selected game"))
            self.button_headerbar_launch.get_style_context().remove_class(
                "destructive-action")
            self.button_headerbar_launch.get_style_context().add_class(
                "suggested-action")

        elif not status and not label == _("Stop"):
            self.button_headerbar_launch.set_label(
                _("Stop"))
            self.button_headerbar_launch.set_tooltip_text(
                _("Stop selected game"))
            self.button_headerbar_launch.get_style_context().remove_class(
                "suggested-action")
            self.button_headerbar_launch.get_style_context().add_class(
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
                        self.button_headerbar_fullscreen.get_active())

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
                    self.button_headerbar_launch.set_sensitive(True)

                    self.menu_item_output.set_sensitive(True)
                    self.button_toolbar_output.set_sensitive(True)
                    self.menubar_game_item_output.set_sensitive(True)

                    return True

        return False


    def __on_game_started(self, widget, game):
        """ The game processus has been started

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        game : gem.engine.api.Game
            Game object
        """

        path = self.api.get_local("ongamestarted")

        if exists(path) and access(path, X_OK):
            thread = ScriptThread(self, path, game)

            # Save thread references
            self.scripts[game.filename] = thread

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
        if thread.game.filename in self.scripts:
            self.logger.debug("Remove %s from scripts cache" % thread.game.name)

            del self.scripts[thread.game.filename]


    def __on_game_terminate(self, widget, thread):
        """ Terminate the game processus and update data

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        thread : gem.widgets.game.GameThread
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
            self.set_game_data(Columns.List.Played, game.played, game.filename)

            # Last played
            self.set_game_data(Columns.List.LastPlay,
                string_from_date(game.last_launch_date), game.filename)

            # Last time played
            self.set_game_data(Columns.List.LastTimePlay,
                string_from_time(game.last_launch_time), game.filename)

            # Play time
            self.set_game_data(Columns.List.TimePlay,
                string_from_time(game.play_time), game.filename)

            # Snaps
            if len(emulator.get_screenshots(game)) > 0:
                self.set_game_data(Columns.List.Snapshots,
                    self.icons.get("screenshot"), game.filename)
                self.button_toolbar_screenshots.set_sensitive(True)
                self.menubar_game_item_screenshots.set_sensitive(True)

            else:
                self.set_game_data(Columns.List.Snapshots,
                    self.icons.get_translucent("screenshot"), game.filename)

            # Save state
            if len(emulator.get_savestates(game)) > 0:
                self.set_game_data(Columns.List.Save,
                    self.icons.get("savestate"), game.filename)

            else:
                self.set_game_data(Columns.List.Save,
                    self.icons.get_translucent("savestate"), game.filename)

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
            self.button_headerbar_launch.set_sensitive(True)

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

        # ----------------------------
        #   Manage thread
        # ----------------------------

        # Remove this game from threads list
        if game.filename in self.threads:
            self.logger.debug("Remove %s from process cache" % game.name)

            del self.threads[game.filename]

        if len(self.threads) == 0:
            self.widget_menu_preferences.set_sensitive(True)
            self.menubar_main_item_preferences.set_sensitive(True)

        # ----------------------------
        #   Manage script
        # ----------------------------

        # Remove this script from threads list
        if game.filename in self.scripts:
            self.logger.debug("Remove %s from scripts cache" % game.name)

            del self.scripts[game.filename]

        path = self.api.get_local("ongamestopped")

        if exists(path) and access(path, X_OK):
            thread = ScriptThread(self, path, game)

            # Save thread references
            self.scripts[game.filename] = thread

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

                    row, treepath, gridpath = self.game_path[game.filename]

                    treepath = self.model_games_list.get_path(
                        self.game_path[game.filename][1])

                    # Update game name
                    self.model_games_list[treepath][Columns.List.Name] = str(
                        new_name)
                    self.model_games_list[treepath][Columns.List.Object] = game

                    self.model_games_grid[gridpath][Columns.Grid.Name] = str(
                        new_name)
                    self.model_games_grid[gridpath][Columns.Grid.Object] = game

                    # Update game from database
                    self.api.update_game(game)

                    # Store modified game
                    self.selection["game"] = game

                    self.__current_tooltip = None

                    self.set_informations()

            self.set_sensitive(True)

            dialog.destroy()


    def __on_game_maintenance(self, *args):
        """ Set some maintenance for selected game
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

                dialog = MaintenanceDialog(self, game, emulator)

                if dialog.run() == Gtk.ResponseType.APPLY:
                    try:
                        self.logger.info(_("%s maintenance") % game.name)

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
                                Columns.List.Favorite: \
                                    self.icons.get_translucent("favorite"),
                                Columns.List.Name: game.filename,
                                Columns.List.Played: None,
                                Columns.List.LastPlay: None,
                                Columns.List.TimePlay: None,
                                Columns.List.LastTimePlay: None,
                                Columns.List.Score: 0,
                                Columns.List.Except: \
                                    self.icons.get_translucent("parameter"),
                                Columns.List.Multiplayer: \
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
                            self.menu_item_output.set_sensitive(False)
                            self.menubar_game_item_output.set_sensitive(False)

                    except Exception as error:
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

                        # Reload the games list
                        if len(data["paths"]) > 0:

                            # Duplicate game files
                            for element in data["paths"]:
                                self.logger.debug("Remove %s" % element)

                                remove(element)

                            need_to_reload = True

                        # Remove game from database
                        if data["database"]:
                            self.api.delete_game(game)

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

                    # Reload the games list
                    if len(data["paths"]) > 0 or data["database"]:

                        # Duplicate game files
                        for original, path in data["paths"]:
                            self.logger.debug("Copy %s" % original)

                            copy(original, path)

                        need_to_reload = True

                    # Update game from database
                    if data["database"]:
                        self.api.update_game(game.copy(data["filepath"]))

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

                game.tags.clear()
                for tag in dialog.entry_tags.get_text().split(","):
                    game.tags.append(tag.strip())

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
                    self.set_game_data(Columns.List.Except,
                        self.icons.get("parameter"), game.filename)
                else:
                    self.set_game_data(Columns.List.Except,
                        self.icons.get_translucent("parameter"), game.filename)

                # ----------------------------
                #   Update icons
                # ----------------------------

                new_emulator = emulator["console"]
                if game.emulator is not None:
                    new_emulator = game.emulator

                # Screenshots
                if len(new_emulator.get_screenshots(game)) > 0:
                    self.set_game_data(Columns.List.Snapshots,
                        self.icons.get("screenshot"), game.filename)

                    self.button_toolbar_screenshots.set_sensitive(True)
                    self.menubar_game_item_screenshots.set_sensitive(True)

                else:
                    self.set_game_data(Columns.List.Snapshots,
                        self.icons.get_translucent("screenshot"), game.filename)

                    self.button_toolbar_screenshots.set_sensitive(False)
                    self.menubar_game_item_screenshots.set_sensitive(False)

                # Savestates
                if len(new_emulator.get_savestates(game)) > 0:
                    self.set_game_data(Columns.List.Save,
                        self.icons.get("savestate"), game.filename)

                else:
                    self.set_game_data(Columns.List.Save,
                        self.icons.get_translucent("savestate"), game.filename)

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

                filepath = self.get_mednafen_memory_type(game)

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
            row, treepath, gridpath = self.game_path[game.filename]

            if not game.favorite:
                self.logger.debug("Mark %s as favorite" % game.name)

                icon = self.icons.get("favorite")

                game.favorite = True

            else:
                self.logger.debug("Unmark %s as favorite" % game.name)

                icon = self.icons.get_translucent("favorite")

                game.favorite = False

            self.model_games_list.set_value(
                treepath, Columns.List.Favorite, icon)
            self.model_games_list.set_value(
                treepath, Columns.List.Object, game)

            self.model_games_grid.set_value(
                gridpath, Columns.Grid.Object, game)

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
            row, treepath, gridpath = self.game_path[game.filename]

            if not game.multiplayer:
                self.logger.debug("Mark %s as multiplayers" % game.name)

                icon = self.icons.get("multiplayer")

                game.multiplayer = True

            else:
                self.logger.debug("Unmark %s as multiplayers" % game.name)

                icon = self.icons.get_translucent("multiplayer")

                game.multiplayer = False

            self.model_games_list.set_value(
                treepath, Columns.List.Multiplayer, icon)
            self.model_games_list.set_value(
                treepath, Columns.List.Object, game)

            self.model_games_grid.set_value(
                gridpath, Columns.Grid.Object, game)

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
            row, treepath, gridpath = self.game_path[game.filename]

            if not game.finish:
                self.logger.debug("Mark %s as finish" % game.name)

                icon = self.icons.get("finish")

                game.finish = True

            else:
                self.logger.debug("Unmark %s as finish" % game.name)

                icon = self.icons.get_translucent("finish")

                game.finish = False

            self.model_games_list.set_value(
                treepath, Columns.List.Finish, icon)
            self.model_games_list.set_value(
                treepath, Columns.List.Object, game)

            self.model_games_grid.set_value(
                gridpath, Columns.Grid.Object, game)

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
            row, treepath, gridpath = self.game_path[game.filename]

            self.model_games_list.set_value(
                treepath, Columns.List.Score, game.score)
            self.model_games_list.set_value(
                treepath, Columns.List.Object, game)

            self.model_games_grid.set_value(
                gridpath, Columns.Grid.Object, game)

            self.api.update_game(game)

            self.set_informations()


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

                    # Update games icon in grid view
                    treeiter = self.game_path[game.filename][2]

                    if game.cover is not None and exists(game.cover):
                        icon = Pixbuf.new_from_file_at_scale(
                            expanduser(game.cover), 96, 96, True)

                        self.model_games_grid.set_value(
                            treeiter, Columns.Grid.Icon, icon)

                    else:
                        self.model_games_grid.set_value(
                            treeiter, Columns.Grid.Icon, self.__console_icon)

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

        treeiter = None

        # Gdk.EventButton - Mouse
        if event.type == EventType.BUTTON_PRESS:
            if event.button == Gdk.BUTTON_SECONDARY:
                treeiter = treeview.get_path_at_pos(int(event.x), int(event.y))

                if treeiter is not None:

                    if treeview == self.treeview_games:
                        path, col = treeiter[0:2]

                        treeview.set_cursor(path, col, 0)

                    if treeview == self.iconview_games:
                        treeview.select_path(treeiter)

                    treeview.grab_focus()

                    self.menu_games.popup_at_pointer(event)

                    return True

        # Gdk.EventKey - Keyboard
        elif event.type == EventType.KEY_RELEASE:
            if event.keyval == Gdk.KEY_Menu:

                if treeview == self.treeview_games:
                    model, treeiter = treeview.get_selection().get_selected()

                elif treeview == self.iconview_games:
                    model = treeview.get_model()
                    items = treeview.get_selected_items()

                    if len(items) >= 1:
                        treeiter = model.get_iter(items[0])

                if treeiter is not None:
                    self.menu_games.popup(None, None, None, None, 0, event.time)

                    return True

        return False


    def __on_resize_window(self, widget, event):
        """ Update widgets size when user resize main window

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        event : Gdk.EventConfigure
            Event which triggered the signal
        """

        if event.type == Gdk.EventType.CONFIGURE:

            if not self.__previous_window_size == (event.width, event.height):
                orientation = self.paned_games.get_orientation()

                # Right side
                if orientation == Gtk.Orientation.HORIZONTAL:
                    pass

                # Bottom side
                else:
                    pass

                # Update size cache
                self.__previous_window_size = (event.width, event.height)


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

            self.image_headerbar_fullscreen.set_from_icon_name(
                Icons.Symbolic.Restore, Gtk.IconSize.SMALL_TOOLBAR)
            self.button_headerbar_fullscreen.get_style_context().remove_class(
                "suggested-action")

        else:
            self.logger.debug("Switch game launch to fullscreen mode")

            self.image_headerbar_fullscreen.set_from_icon_name(
                Icons.Symbolic.Fullscreen, Gtk.IconSize.SMALL_TOOLBAR)
            self.button_headerbar_fullscreen.get_style_context().add_class(
                "suggested-action")

        self.button_headerbar_fullscreen.set_active(self.__fullscreen_status)
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

        self.switch_menu_dark_theme.set_active(dark_theme_status)
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

        self.switch_menu_sidebar.set_active(sidebar_status)
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

        self.switch_menu_statusbar.set_active(statusbar_status)
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

        if type(widget) is Gtk.TreeView or type(widget) is Gtk.IconView:

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

        for widget, signal in self.__signals_storage.items():
            widget.handler_block(signal)


    def __unblock_signals(self):
        """ Unblock check button signals
        """

        for widget, signal in self.__signals_storage.items():
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
        if this one match "Starting Mednafen [0-9+.?]+".

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

        if self.api.debug:

            if len(get_binary_path("git")) > 0:
                proc = Popen(
                    [ "git", "rev-parse", "--short", "HEAD" ],
                    stdin=PIPE,
                    stdout=PIPE,
                    stderr=STDOUT,
                    universal_newlines=True)

                output, error_output = proc.communicate()

                if output is not None:
                    output = output.split('\n')[0]

                    if match(r'[\d\w]+', output) is not None:
                        return "%s-%s" % (GEM.Version, output)

        return GEM.Version


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
            self.model_games_list[treeiter[1]][index] = data


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
