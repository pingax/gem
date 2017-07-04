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

# ------------------------------------------------------------------------------
#   Modules
# ------------------------------------------------------------------------------

# Date
from datetime import date
from datetime import time
from datetime import datetime

# Filesystem
from os import W_OK
from os import mkdir
from os import access
from os import remove

from os.path import exists
from os.path import dirname
from os.path import getctime
from os.path import splitext
from os.path import basename
from os.path import expanduser
from os.path import join as path_join

from glob import glob
from shutil import copy2 as copy

# Processus
from subprocess import PIPE
from subprocess import Popen
from subprocess import STDOUT

# Random
from random import randint

# Regex
from re import match
from re import IGNORECASE

# System
from sys import exit as sys_exit
from shlex import split as shlex_split
from shutil import move as rename
from platform import system

# Threading
from threading import Thread

# URL
from urllib.parse import urlparse
from urllib.request import url2pathname

# ------------------------------------------------------------------------------
#   Modules - Interface
# ------------------------------------------------------------------------------

try:
    from gi import require_version

    require_version("Gtk", "3.0")

    from gi.repository import Gtk
    from gi.repository import Gdk

    from gi.repository.Gdk import EventType

    from gi.repository.GLib import idle_add
    from gi.repository.GLib import source_remove

    from gi.repository.GObject import GObject
    from gi.repository.GObject import MainLoop
    from gi.repository.GObject import SIGNAL_RUN_LAST

    from gi.repository.GdkPixbuf import Pixbuf
    from gi.repository.GdkPixbuf import InterpType
    from gi.repository.GdkPixbuf import Colorspace

except ImportError as error:
    sys_exit("Import error with python3-gobject module: %s" % str(error))

# ------------------------------------------------------------------------------
#   Modules - GEM
# ------------------------------------------------------------------------------

try:
    from gem.utils import *
    from gem.configuration import Configuration

    from gem.api import GEM
    from gem.api import Game
    from gem.api import Console
    from gem.api import Emulator

    from gem.gtk import *
    from gem.gtk.game import GameThread
    from gem.gtk.windows import *
    from gem.gtk.mednafen import DialogMednafenMemory
    from gem.gtk.preferences import Preferences

except ImportError as error:
    sys_exit("Import error with gem module: %s" % str(error))

# ------------------------------------------------------------------------------
#   Modules - Translation
# ------------------------------------------------------------------------------

from gettext import gettext as _
from gettext import textdomain
from gettext import bindtextdomain

bindtextdomain("gem", get_data("i18n"))
textdomain("gem")

# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class Interface(Gtk.Window):

    __gsignals__ = { "game-terminate": (SIGNAL_RUN_LAST, None, [object]) }

    def __init__(self, api):
        """ Constructor

        Parameters
        ----------
        api : gem.api.GEM
            GEM API instance

        Raises
        ------
        TypeError
            if api type is not gem.api.GEM
        """

        if not type(api) is GEM:
            raise TypeError("Wrong type for api, expected gem.api.GEM")

        Gtk.Window.__init__(self)

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
        # Store selected game informations with console, game and name as keys
        self.selection = dict()
        # Store shortcut with Gtk.Widget as key
        self.shortcuts_data = dict()
        # Store sidebar description ordre
        self.sidebar_widgets = {
            "play_time": _("Play time"),
            "last_play": _("Last launch")
        }

        # Store user keys input
        self.keys = list()

        # Avoid to resize the main window everytime user modify preferences
        self.__first_draw = False

        # Avoid to reload interface when switch between default & classic theme
        self.__theme = None

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

        self.icons_data = {
            "save": Icons.Download,
            "snap": Icons.Photos,
            "except": Icons.Important,
            "warning": Icons.Warning,
            "favorite": Icons.Favorite,
            "multiplayer": Icons.Users }

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

        # ------------------------------------
        #   Clipboard
        # ------------------------------------

        self.clipboard = Gtk.Clipboard.get(Gdk.Atom.intern("CLIPBOARD", False))

        # ------------------------------------
        #   Grid
        # ------------------------------------

        self.grid = Gtk.Box()

        self.grid_options = Gtk.Box()

        self.grid_paned = Gtk.Box()
        self.grid_informations = Gtk.Box()

        # Properties
        self.grid.set_orientation(Gtk.Orientation.VERTICAL)

        Gtk.StyleContext.add_class(
            self.grid_options.get_style_context(), "linked")

        self.grid_paned.set_spacing(8)
        self.grid_paned.set_border_width(8)
        self.grid_paned.set_homogeneous(False)
        self.grid_paned.set_size_request(432, 216)
        self.grid_paned.set_orientation(Gtk.Orientation.HORIZONTAL)

        self.grid_informations.set_spacing(8)
        self.grid_informations.set_homogeneous(False)
        self.grid_informations.set_orientation(Gtk.Orientation.VERTICAL)

        # ------------------------------------
        #   Headerbar
        # ------------------------------------

        self.headerbar = Gtk.HeaderBar()

        self.tool_item_launch = Gtk.Button()
        self.tool_item_screenshots = Gtk.Button()
        self.tool_item_output = Gtk.Button()
        self.tool_item_notes = Gtk.Button()
        self.tool_item_parameters = Gtk.Button()

        self.tool_item_fullscreen = Gtk.ToggleButton()

        self.tool_item_menu = Gtk.MenuButton()

        # Properties
        self.headerbar.set_title(self.title)
        self.headerbar.set_subtitle(str())

        self.tool_item_launch.set_tooltip_text(
            _("Launch selected game"))
        self.tool_item_parameters.set_tooltip_text(
            _("Set custom parameters"))
        self.tool_item_screenshots.set_tooltip_text(
            _("Show selected game screenshots"))
        self.tool_item_output.set_tooltip_text(
            _("Show selected game output log"))
        self.tool_item_notes.set_tooltip_text(
            _("Show selected game notes"))

        self.tool_item_fullscreen.set_tooltip_text(
            _("Alternate game fullscreen mode"))

        # ------------------------------------
        #   Headerbar - Images
        # ------------------------------------

        self.tool_image_launch = Gtk.Image()
        self.tool_image_parameters = Gtk.Image()
        self.tool_image_screenshots = Gtk.Image()
        self.tool_image_output = Gtk.Image()
        self.tool_image_notes = Gtk.Image()
        self.tool_image_fullscreen = Gtk.Image()
        self.tool_image_menu = Gtk.Image()

        # Properties
        self.tool_image_launch.set_from_icon_name(
            Icons.Launch, Gtk.IconSize.LARGE_TOOLBAR)
        self.tool_image_parameters.set_from_icon_name(
            Icons.Important, Gtk.IconSize.LARGE_TOOLBAR)
        self.tool_image_screenshots.set_from_icon_name(
            Icons.Image, Gtk.IconSize.LARGE_TOOLBAR)
        self.tool_image_output.set_from_icon_name(
            Icons.Terminal, Gtk.IconSize.LARGE_TOOLBAR)
        self.tool_image_notes.set_from_icon_name(
            Icons.Document, Gtk.IconSize.LARGE_TOOLBAR)
        self.tool_image_fullscreen.set_from_icon_name(
            Icons.Restore, Gtk.IconSize.LARGE_TOOLBAR)
        self.tool_image_menu.set_from_icon_name(
            Icons.System, Gtk.IconSize.LARGE_TOOLBAR)

        # ------------------------------------
        #   Headerbar - Menu
        # ------------------------------------

        self.menu = Gtk.Menu()

        self.menu_image_preferences = Gtk.Image()
        self.menu_image_gem_log = Gtk.Image()
        self.menu_image_about = Gtk.Image()
        self.menu_image_quit = Gtk.Image()

        self.menu_item_preferences = Gtk.ImageMenuItem()
        self.menu_item_gem_log = Gtk.ImageMenuItem()
        self.menu_item_about = Gtk.ImageMenuItem()
        self.menu_item_quit = Gtk.ImageMenuItem()

        self.menu_item_dark_theme = Gtk.CheckMenuItem()
        self.menu_item_sidebar = Gtk.CheckMenuItem()

        # Properties
        self.menu_image_preferences.set_from_icon_name(
            Icons.System, Gtk.IconSize.MENU)
        self.menu_image_gem_log.set_from_icon_name(
            Icons.Terminal, Gtk.IconSize.MENU)
        self.menu_image_about.set_from_icon_name(
            Icons.About, Gtk.IconSize.MENU)
        self.menu_image_quit.set_from_icon_name(
            Icons.Quit, Gtk.IconSize.MENU)

        self.menu_item_preferences.set_label(_("_Preferences"))
        self.menu_item_preferences.set_image(self.menu_image_preferences)
        self.menu_item_preferences.set_use_underline(True)

        self.menu_item_gem_log.set_label(_("Show main _log"))
        self.menu_item_gem_log.set_image(self.menu_image_gem_log)
        self.menu_item_gem_log.set_use_underline(True)

        self.menu_item_about.set_label(_("_About"))
        self.menu_item_about.set_image(self.menu_image_about)
        self.menu_item_about.set_use_underline(True)

        self.menu_item_quit.set_label(_("_Quit"))
        self.menu_item_quit.set_image(self.menu_image_quit)
        self.menu_item_quit.set_use_underline(True)

        self.menu_item_dark_theme.set_label(_("Use _dark theme"))
        self.menu_item_dark_theme.set_use_underline(True)

        self.menu_item_sidebar.set_label(_("Show _sidebar"))
        self.menu_item_sidebar.set_use_underline(True)

        # ------------------------------------
        #   Menubar
        # ------------------------------------

        self.menubar = Gtk.MenuBar()

        self.menubar_item_main = Gtk.MenuItem()
        self.menubar_item_edit = Gtk.MenuItem()
        self.menubar_item_tools = Gtk.MenuItem()
        self.menubar_item_help = Gtk.MenuItem()

        # Properties
        self.menubar_item_main.set_label(_("_Game"))
        self.menubar_item_main.set_use_underline(True)
        self.menubar_item_edit.set_label(_("_Edit"))
        self.menubar_item_edit.set_use_underline(True)
        self.menubar_item_tools.set_label(_("_Tools"))
        self.menubar_item_tools.set_use_underline(True)
        self.menubar_item_help.set_label(_("_Help"))
        self.menubar_item_help.set_use_underline(True)

        # ------------------------------------
        #   Menubar - Main items
        # ------------------------------------

        self.menubar_main_menu = Gtk.Menu()

        self.menubar_main_image_launch = Gtk.Image()
        self.menubar_main_image_favorite = Gtk.Image()
        self.menubar_main_image_multiplayer = Gtk.Image()
        self.menubar_main_image_screenshots = Gtk.Image()
        self.menubar_main_image_output = Gtk.Image()
        self.menubar_main_image_notes = Gtk.Image()
        self.menubar_main_image_quit = Gtk.Image()

        self.menubar_main_item_launch = Gtk.ImageMenuItem()
        self.menubar_main_item_favorite = Gtk.ImageMenuItem()
        self.menubar_main_item_multiplayer = Gtk.ImageMenuItem()
        self.menubar_main_item_screenshots = Gtk.ImageMenuItem()
        self.menubar_main_item_output = Gtk.ImageMenuItem()
        self.menubar_main_item_notes = Gtk.ImageMenuItem()
        self.menubar_main_item_quit = Gtk.ImageMenuItem()

        self.menubar_main_item_fullscreen = Gtk.CheckMenuItem()

        # Properties
        self.menubar_main_image_launch.set_from_icon_name(
            Icons.Launch, Gtk.IconSize.MENU)
        self.menubar_main_image_favorite.set_from_icon_name(
            Icons.Favorite, Gtk.IconSize.MENU)
        self.menubar_main_image_multiplayer.set_from_icon_name(
            Icons.Users, Gtk.IconSize.MENU)
        self.menubar_main_image_screenshots.set_from_icon_name(
            Icons.Image, Gtk.IconSize.MENU)
        self.menubar_main_image_output.set_from_icon_name(
            Icons.Terminal, Gtk.IconSize.MENU)
        self.menubar_main_image_notes.set_from_icon_name(
            Icons.Document, Gtk.IconSize.MENU)
        self.menubar_main_image_quit.set_from_icon_name(
            Icons.Quit, Gtk.IconSize.MENU)

        self.menubar_main_item_launch.set_label(_("_Launch"))
        self.menubar_main_item_launch.set_image(
            self.menubar_main_image_launch)
        self.menubar_main_item_launch.set_use_underline(True)

        self.menubar_main_item_favorite.set_label(_("Mark as _favorite"))
        self.menubar_main_item_favorite.set_image(
            self.menubar_main_image_favorite)
        self.menubar_main_item_favorite.set_use_underline(True)

        self.menubar_main_item_multiplayer.set_label(_("Mark as _multiplayer"))
        self.menubar_main_item_multiplayer.set_image(
            self.menubar_main_image_multiplayer)
        self.menubar_main_item_multiplayer.set_use_underline(True)

        self.menubar_main_item_screenshots.set_label(_("Show _screenshots"))
        self.menubar_main_item_screenshots.set_image(
            self.menubar_main_image_screenshots)
        self.menubar_main_item_screenshots.set_use_underline(True)

        self.menubar_main_item_output.set_label(_("Show output _log"))
        self.menubar_main_item_output.set_image(
            self.menubar_main_image_output)
        self.menubar_main_item_output.set_use_underline(True)

        self.menubar_main_item_notes.set_label(_("Show _notes"))
        self.menubar_main_item_notes.set_image(
            self.menubar_main_image_notes)
        self.menubar_main_item_notes.set_use_underline(True)

        self.menubar_main_item_quit.set_label(_("_Quit"))
        self.menubar_main_item_quit.set_image(
            self.menubar_main_image_quit)
        self.menubar_main_item_quit.set_use_underline(True)

        self.menubar_main_item_fullscreen.set_label(
            _("Activate game fullscreen mode"))
        self.menubar_main_item_fullscreen.set_use_underline(True)

        # ------------------------------------
        #   Menubar - Edit items
        # ------------------------------------

        self.menubar_edit_menu = Gtk.Menu()

        self.menubar_edit_image_rename = Gtk.Image()
        self.menubar_edit_image_parameters = Gtk.Image()
        self.menubar_edit_image_copy = Gtk.Image()
        self.menubar_edit_image_open = Gtk.Image()
        self.menubar_edit_image_desktop = Gtk.Image()
        self.menubar_edit_image_database = Gtk.Image()
        self.menubar_edit_image_delete = Gtk.Image()
        self.menubar_edit_image_mednafen = Gtk.Image()

        self.menubar_edit_item_rename = Gtk.ImageMenuItem()
        self.menubar_edit_item_parameters = Gtk.ImageMenuItem()
        self.menubar_edit_item_copy = Gtk.ImageMenuItem()
        self.menubar_edit_item_open = Gtk.ImageMenuItem()
        self.menubar_edit_item_desktop = Gtk.ImageMenuItem()
        self.menubar_edit_item_database = Gtk.ImageMenuItem()
        self.menubar_edit_item_delete = Gtk.ImageMenuItem()
        self.menubar_edit_item_mednafen = Gtk.ImageMenuItem()

        # Properties
        self.menubar_edit_image_rename.set_from_icon_name(
            Icons.Editor, Gtk.IconSize.MENU)
        self.menubar_edit_image_parameters.set_from_icon_name(
            Icons.Properties, Gtk.IconSize.MENU)
        self.menubar_edit_image_copy.set_from_icon_name(
            Icons.Copy, Gtk.IconSize.MENU)
        self.menubar_edit_image_open.set_from_icon_name(
            Icons.Open, Gtk.IconSize.MENU)
        self.menubar_edit_image_desktop.set_from_icon_name(
            Icons.Desktop, Gtk.IconSize.MENU)
        self.menubar_edit_image_database.set_from_icon_name(
            Icons.Clear, Gtk.IconSize.MENU)
        self.menubar_edit_image_delete.set_from_icon_name(
            Icons.Delete, Gtk.IconSize.MENU)
        self.menubar_edit_image_mednafen.set_from_icon_name(
            Icons.Save, Gtk.IconSize.MENU)

        self.menubar_edit_item_rename.set_label(_("_Rename"))
        self.menubar_edit_item_rename.set_image(
            self.menubar_edit_image_rename)
        self.menubar_edit_item_rename.set_use_underline(True)

        self.menubar_edit_item_parameters.set_label(_("Custom _parameters"))
        self.menubar_edit_item_parameters.set_image(
            self.menubar_edit_image_parameters)
        self.menubar_edit_item_parameters.set_use_underline(True)

        self.menubar_edit_item_copy.set_label(_("_Copy file path"))
        self.menubar_edit_item_copy.set_image(
            self.menubar_edit_image_copy)
        self.menubar_edit_item_copy.set_use_underline(True)

        self.menubar_edit_item_open.set_label(_("_Open file path"))
        self.menubar_edit_item_open.set_image(
            self.menubar_edit_image_open)
        self.menubar_edit_item_open.set_use_underline(True)

        self.menubar_edit_item_desktop.set_label(_("_Generate a menu entry"))
        self.menubar_edit_item_desktop.set_image(
            self.menubar_edit_image_desktop)
        self.menubar_edit_item_desktop.set_use_underline(True)

        self.menubar_edit_item_database.set_label(_("_Reset game informations"))
        self.menubar_edit_item_database.set_image(
            self.menubar_edit_image_database)
        self.menubar_edit_item_database.set_use_underline(True)

        self.menubar_edit_item_delete.set_label(_("_Remove game from disk"))
        self.menubar_edit_item_delete.set_image(
            self.menubar_edit_image_delete)
        self.menubar_edit_item_delete.set_use_underline(True)

        self.menubar_edit_item_mednafen.set_label(_("Specify a _memory type"))
        self.menubar_edit_item_mednafen.set_image(
            self.menubar_edit_image_mednafen)
        self.menubar_edit_item_mednafen.set_use_underline(True)

        # ------------------------------------
        #   Menubar - Tools items
        # ------------------------------------

        self.menubar_tools_menu = Gtk.Menu()

        self.menubar_tools_image_preferences = Gtk.Image()

        self.menubar_tools_item_preferences = Gtk.ImageMenuItem()

        self.menubar_tools_item_dark_theme = Gtk.CheckMenuItem()
        self.menubar_tools_item_sidebar = Gtk.CheckMenuItem()

        # Properties
        self.menubar_tools_image_preferences.set_from_icon_name(
            Icons.System, Gtk.IconSize.MENU)

        self.menubar_tools_item_preferences.set_label(_("_Preferences"))
        self.menubar_tools_item_preferences.set_image(
            self.menubar_tools_image_preferences)
        self.menubar_tools_item_preferences.set_use_underline(True)

        self.menubar_tools_item_dark_theme.set_label(_("Use _dark theme"))
        self.menubar_tools_item_dark_theme.set_use_underline(True)

        self.menubar_tools_item_sidebar.set_label(_("Show _sidebar"))
        self.menubar_tools_item_sidebar.set_use_underline(True)

        # ------------------------------------
        #   Menubar - Help items
        # ------------------------------------

        self.menubar_help_menu = Gtk.Menu()

        self.menubar_help_image_log = Gtk.Image()
        self.menubar_help_image_about = Gtk.Image()

        self.menubar_help_item_log = Gtk.ImageMenuItem()
        self.menubar_help_item_about = Gtk.ImageMenuItem()

        # Properties
        self.menubar_help_image_log.set_from_icon_name(
            Icons.Terminal, Gtk.IconSize.MENU)
        self.menubar_help_image_about.set_from_icon_name(
            Icons.About, Gtk.IconSize.MENU)

        self.menubar_help_item_log.set_label(_("Show main _log"))
        self.menubar_help_item_log.set_image(
            self.menubar_help_image_log)
        self.menubar_help_item_log.set_use_underline(True)
        self.menubar_help_item_about.set_label(_("_About"))
        self.menubar_help_item_about.set_image(
            self.menubar_help_image_about)
        self.menubar_help_item_about.set_use_underline(True)

        # ------------------------------------
        #   Toolbar
        # ------------------------------------

        self.toolbar = Gtk.Toolbar()

        self.tool_item_properties = Gtk.ToolButton()

        self.tool_filter_favorite = Gtk.ToggleToolButton()
        self.tool_filter_multiplayer = Gtk.ToggleToolButton()

        self.tool_item_consoles = Gtk.ToolItem()
        self.tool_search = Gtk.ToolItem()

        self.tool_separator = Gtk.SeparatorToolItem()

        # Properties
        self.toolbar.set_icon_size(Gtk.IconSize.LARGE_TOOLBAR)

        self.tool_item_properties.set_tooltip_text(
            _("Edit emulator"))

        self.tool_filter_favorite.set_tooltip_text(
            _("Show favorite games"))
        self.tool_filter_multiplayer.set_tooltip_text(
            _("Show multiplayer games"))

        self.tool_item_properties.set_icon_name(Icons.Properties)
        self.tool_filter_favorite.set_icon_name(Icons.Favorite)
        self.tool_filter_multiplayer.set_icon_name(Icons.Users)

        self.tool_separator.set_draw(False)
        self.tool_separator.set_expand(True)

        # ------------------------------------
        #   Toolbar - Consoles
        # ------------------------------------

        self.model_consoles = Gtk.ListStore(
            Pixbuf, # Console icon
            str,    # Console name
            Pixbuf, # Emulator binary status
            str     # Console identifier
        )

        self.combo_consoles = Gtk.ComboBox()

        self.cell_consoles_icon = Gtk.CellRendererPixbuf()
        self.cell_consoles_name = Gtk.CellRendererText()
        self.cell_consoles_status = Gtk.CellRendererPixbuf()

        # Properties
        self.model_consoles.set_sort_column_id(1, Gtk.SortType.ASCENDING)

        self.combo_consoles.set_model(self.model_consoles)

        self.combo_consoles.pack_start(self.cell_consoles_icon, False)
        self.combo_consoles.pack_start(self.cell_consoles_name, True)
        self.combo_consoles.pack_start(self.cell_consoles_status, False)

        self.combo_consoles.add_attribute(
            self.cell_consoles_icon, "pixbuf", 0)
        self.combo_consoles.add_attribute(
            self.cell_consoles_name, "text", 1)
        self.combo_consoles.add_attribute(
            self.cell_consoles_status, "pixbuf", 2)

        self.cell_consoles_name.set_padding(8, 0)

        # ------------------------------------
        #   Toolbar - Filter
        # ------------------------------------

        self.entry_filter = Gtk.SearchEntry()

        # Properties
        self.entry_filter.set_size_request(300, -1)
        self.entry_filter.set_placeholder_text(_("Filter"))
        self.entry_filter.set_icon_from_icon_name(
            Gtk.EntryIconPosition.PRIMARY, Icons.Find)
        self.entry_filter.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, Icons.Clear)
        self.entry_filter.set_icon_activatable(
            Gtk.EntryIconPosition.PRIMARY, False)
        self.entry_filter.set_icon_sensitive(
            Gtk.EntryIconPosition.PRIMARY, False)

        # ------------------------------------
        #   Games - Sidebar
        # ------------------------------------

        self.paned_games = Gtk.Paned()

        self.label_game_title = Gtk.Label()
        self.label_game_description = Gtk.Label()
        self.label_game_footer = Gtk.Label()

        self.image_game_screen = Gtk.Image()

        self.separator_game = Gtk.Separator()

        # Properties
        self.paned_games.set_orientation(Gtk.Orientation.VERTICAL)

        self.label_game_title.set_hexpand(True)
        self.label_game_title.set_alignment(0, 0)
        self.label_game_title.set_use_markup(True)
        self.label_game_title.set_ellipsize(Pango.EllipsizeMode.END)

        self.label_game_description.set_use_markup(True)
        self.label_game_description.set_alignment(0, 0)
        self.label_game_description.set_ellipsize(Pango.EllipsizeMode.END)

        self.label_game_footer.set_use_markup(True)
        self.label_game_footer.set_alignment(0, 0)
        self.label_game_footer.set_ellipsize(Pango.EllipsizeMode.END)

        self.image_game_screen.set_alignment(0, 0)

        self.separator_game.set_no_show_all(True)

        # ------------------------------------
        #   Games - Sidebar description
        # ------------------------------------

        self.widgets_sidebar = dict()

        for widget in self.sidebar_widgets:
            self.widgets_sidebar[widget] = {
                "box": Gtk.Box(),
                "key": Gtk.Label(),
                "value": Gtk.Label()
            }

            # Properties
            self.widgets_sidebar[widget]["box"].set_spacing(8)
            self.widgets_sidebar[widget]["box"].set_orientation(
                Gtk.Orientation.HORIZONTAL)

            self.widgets_sidebar[widget]["key"].set_use_markup(True)
            self.widgets_sidebar[widget]["key"].set_alignment(0, 0)
            self.widgets_sidebar[widget]["key"].set_ellipsize(
                Pango.EllipsizeMode.END)
            self.widgets_sidebar[widget]["key"].set_markup("<b>%s</b>:" % (
                self.sidebar_widgets[widget]))

            self.widgets_sidebar[widget]["value"].set_use_markup(True)
            self.widgets_sidebar[widget]["value"].set_alignment(0, 0)
            self.widgets_sidebar[widget]["value"].set_ellipsize(
                Pango.EllipsizeMode.END)

            self.widgets_sidebar[widget]["box"].pack_start(
                self.widgets_sidebar[widget]["key"], False, False, 0)
            self.widgets_sidebar[widget]["box"].pack_start(
                self.widgets_sidebar[widget]["value"], True, True, 0)

        # ------------------------------------
        #   Games - Treeview
        # ------------------------------------

        self.scroll_games = Gtk.ScrolledWindow()

        self.model_games = Gtk.ListStore(
            bool,   # Favorite status
            Pixbuf, # Favorite icon
            str,    # Name
            str,    # Played
            str,    # Last play
            str,    # Last time play
            str,    # Time play
            str,    # Installed
            Pixbuf, # Custom parameters
            Pixbuf, # Screenshots
            Pixbuf, # Multiplayer
            Pixbuf, # Save states
            str     # Filename
        )
        self.treeview_games = Gtk.TreeView()

        self.filter_games = self.model_games.filter_new()

        self.column_game_favorite = Gtk.TreeViewColumn()
        self.column_game_name = Gtk.TreeViewColumn()
        self.column_game_play = Gtk.TreeViewColumn()
        self.column_game_last_play = Gtk.TreeViewColumn()
        self.column_game_play_time = Gtk.TreeViewColumn()
        self.column_game_installed = Gtk.TreeViewColumn()
        self.column_game_flags = Gtk.TreeViewColumn()

        self.cell_game_favorite = Gtk.CellRendererPixbuf()
        self.cell_game_name = Gtk.CellRendererText()
        self.cell_game_play = Gtk.CellRendererText()
        self.cell_game_last_play = Gtk.CellRendererText()
        self.cell_game_last_play_time = Gtk.CellRendererText()
        self.cell_game_play_time = Gtk.CellRendererText()
        self.cell_game_installed = Gtk.CellRendererText()
        self.cell_game_except = Gtk.CellRendererPixbuf()
        self.cell_game_snapshots = Gtk.CellRendererPixbuf()
        self.cell_game_multiplayer = Gtk.CellRendererPixbuf()
        self.cell_game_save = Gtk.CellRendererPixbuf()

        # Properties
        self.model_games.set_sort_column_id(2, Gtk.SortType.ASCENDING)

        self.treeview_games.set_model(self.filter_games)
        self.treeview_games.set_headers_clickable(False)
        self.treeview_games.set_headers_visible(True)
        self.treeview_games.set_show_expanders(False)
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

        self.column_game_name.set_expand(True)
        self.column_game_name.set_resizable(True)
        self.column_game_name.set_min_width(100)
        self.column_game_name.set_fixed_width(300)
        self.column_game_favorite.pack_start(
            self.cell_game_favorite, False)

        self.column_game_name.pack_start(
            self.cell_game_name, True)

        self.column_game_play.set_alignment(.5)
        self.column_game_play.pack_start(
            self.cell_game_play, False)

        self.column_game_last_play.set_alignment(.5)
        self.column_game_last_play.pack_start(
            self.cell_game_last_play, False)
        self.column_game_last_play.pack_start(
            self.cell_game_last_play_time, False)

        self.column_game_play_time.set_alignment(.5)
        self.column_game_play_time.pack_start(
            self.cell_game_play_time, False)

        self.column_game_installed.set_alignment(.5)
        self.column_game_installed.pack_start(
            self.cell_game_installed, False)

        self.column_game_flags.set_alignment(.5)
        self.column_game_flags.pack_start(
            self.cell_game_except, False)
        self.column_game_flags.pack_start(
            self.cell_game_snapshots, False)
        self.column_game_flags.pack_start(
            self.cell_game_multiplayer, False)
        self.column_game_flags.pack_start(
            self.cell_game_save, False)

        self.column_game_favorite.add_attribute(
            self.cell_game_favorite, "pixbuf", Columns.Icon)
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
            self.cell_game_multiplayer, "pixbuf", Columns.Multiplayer)
        self.column_game_flags.add_attribute(
            self.cell_game_save, "pixbuf", Columns.Save)

        self.cell_game_favorite.set_alignment(.5, .5)
        self.cell_game_name.set_alignment(0, .5)
        self.cell_game_play.set_alignment(.5, .5)
        self.cell_game_last_play.set_alignment(0, .5)
        self.cell_game_last_play_time.set_alignment(1, .5)
        self.cell_game_play_time.set_alignment(.5, .5)
        self.cell_game_installed.set_alignment(.5, .5)

        self.cell_game_name.set_property("ellipsize", Pango.EllipsizeMode.END)

        self.cell_game_name.set_padding(4, 0)
        self.cell_game_play.set_padding(8, 0)
        self.cell_game_last_play.set_padding(8, 0)
        self.cell_game_last_play_time.set_padding(8, 0)
        self.cell_game_installed.set_padding(8, 0)
        self.cell_game_except.set_padding(4, 0)
        self.cell_game_snapshots.set_padding(4, 0)
        self.cell_game_multiplayer.set_padding(4, 0)
        self.cell_game_save.set_padding(4, 0)

        # ------------------------------------
        #   Games - Menu
        # ------------------------------------

        self.menu_games = Gtk.Menu()
        self.menu_games_edit = Gtk.Menu()

        self.menu_image_launch = Gtk.Image()
        self.menu_image_favorite = Gtk.Image()
        self.menu_image_multiplayer = Gtk.Image()
        self.menu_image_screenshots = Gtk.Image()
        self.menu_image_output = Gtk.Image()
        self.menu_image_notes = Gtk.Image()
        self.menu_image_edit = Gtk.Image()

        self.menu_item_launch = Gtk.ImageMenuItem()
        self.menu_item_favorite = Gtk.ImageMenuItem()
        self.menu_item_multiplayer = Gtk.ImageMenuItem()
        self.menu_item_screenshots = Gtk.ImageMenuItem()
        self.menu_item_output = Gtk.ImageMenuItem()
        self.menu_item_notes = Gtk.ImageMenuItem()
        self.menu_item_edit = Gtk.ImageMenuItem()

        # Properties
        self.menu_image_launch.set_from_icon_name(
            Icons.Launch, Gtk.IconSize.MENU)
        self.menu_image_favorite.set_from_icon_name(
            Icons.Favorite, Gtk.IconSize.MENU)
        self.menu_image_multiplayer.set_from_icon_name(
            Icons.Users, Gtk.IconSize.MENU)
        self.menu_image_screenshots.set_from_icon_name(
            Icons.Image, Gtk.IconSize.MENU)
        self.menu_image_output.set_from_icon_name(
            Icons.Terminal, Gtk.IconSize.MENU)
        self.menu_image_notes.set_from_icon_name(
            Icons.Document, Gtk.IconSize.MENU)
        self.menu_image_edit.set_from_icon_name(
            Icons.Other, Gtk.IconSize.MENU)

        self.menu_item_launch.set_label(_("_Launch"))
        self.menu_item_launch.set_image(self.menu_image_launch)
        self.menu_item_launch.set_use_underline(True)

        self.menu_item_favorite.set_label(_("Mark as _favorite"))
        self.menu_item_favorite.set_image(self.menu_image_favorite)
        self.menu_item_favorite.set_use_underline(True)

        self.menu_item_multiplayer.set_label(_("Mark as _multiplayer"))
        self.menu_item_multiplayer.set_image(self.menu_image_multiplayer)
        self.menu_item_multiplayer.set_use_underline(True)

        self.menu_item_screenshots.set_label(_("Show _screenshots"))
        self.menu_item_screenshots.set_image(self.menu_image_screenshots)
        self.menu_item_screenshots.set_use_underline(True)

        self.menu_item_output.set_label(_("Show output _log"))
        self.menu_item_output.set_image(self.menu_image_output)
        self.menu_item_output.set_use_underline(True)

        self.menu_item_notes.set_label(_("Show _notes"))
        self.menu_item_notes.set_image(self.menu_image_notes)
        self.menu_item_notes.set_use_underline(True)

        self.menu_item_edit.set_label(_("_Edit"))
        self.menu_item_edit.set_image(self.menu_image_edit)
        self.menu_item_edit.set_use_underline(True)

        # ------------------------------------
        #   Games - Menu edit
        # ------------------------------------

        self.menu_image_rename = Gtk.Image()
        self.menu_image_parameters = Gtk.Image()
        self.menu_image_copy = Gtk.Image()
        self.menu_image_open = Gtk.Image()
        self.menu_image_desktop = Gtk.Image()
        self.menu_image_remove = Gtk.Image()
        self.menu_image_database = Gtk.Image()
        self.menu_image_mednafen = Gtk.Image()

        self.menu_item_rename = Gtk.ImageMenuItem()
        self.menu_item_parameters = Gtk.ImageMenuItem()
        self.menu_item_copy = Gtk.ImageMenuItem()
        self.menu_item_open = Gtk.ImageMenuItem()
        self.menu_item_desktop = Gtk.ImageMenuItem()
        self.menu_item_remove = Gtk.ImageMenuItem()
        self.menu_item_database = Gtk.ImageMenuItem()
        self.menu_item_mednafen = Gtk.ImageMenuItem()

        # Properties
        self.menu_image_rename.set_from_icon_name(
            Icons.Editor, Gtk.IconSize.MENU)
        self.menu_image_parameters.set_from_icon_name(
            Icons.Important, Gtk.IconSize.MENU)
        self.menu_image_copy.set_from_icon_name(
            Icons.Copy, Gtk.IconSize.MENU)
        self.menu_image_open.set_from_icon_name(
            Icons.Open, Gtk.IconSize.MENU)
        self.menu_image_desktop.set_from_icon_name(
            Icons.Desktop, Gtk.IconSize.MENU)
        self.menu_image_remove.set_from_icon_name(
            Icons.Clear, Gtk.IconSize.MENU)
        self.menu_image_database.set_from_icon_name(
            Icons.Delete, Gtk.IconSize.MENU)
        self.menu_image_mednafen.set_from_icon_name(
            Icons.Save, Gtk.IconSize.MENU)

        self.menu_item_rename.set_label(_("_Rename"))
        self.menu_item_rename.set_image(self.menu_image_rename)
        self.menu_item_rename.set_use_underline(True)

        self.menu_item_parameters.set_label(_("Custom _parameters"))
        self.menu_item_parameters.set_image(self.menu_image_parameters)
        self.menu_item_parameters.set_use_underline(True)

        self.menu_item_copy.set_label(_("_Copy file path"))
        self.menu_item_copy.set_image(self.menu_image_copy)
        self.menu_item_copy.set_use_underline(True)

        self.menu_item_open.set_label(_("_Open file path"))
        self.menu_item_open.set_image(self.menu_image_open)
        self.menu_item_open.set_use_underline(True)

        self.menu_item_desktop.set_label(_("_Generate a menu entry"))
        self.menu_item_desktop.set_image(self.menu_image_desktop)
        self.menu_item_desktop.set_use_underline(True)

        self.menu_item_database.set_label(_("_Reset game informations"))
        self.menu_item_database.set_image(self.menu_image_database)
        self.menu_item_database.set_use_underline(True)

        self.menu_item_remove.set_label(_("_Remove game from disk"))
        self.menu_item_remove.set_image(self.menu_image_remove)
        self.menu_item_remove.set_use_underline(True)

        self.menu_item_mednafen.set_label(_("Specify a _memory type"))
        self.menu_item_mednafen.set_image(self.menu_image_mednafen)
        self.menu_item_mednafen.set_use_underline(True)

        # ------------------------------------
        #   Statusbar
        # ------------------------------------

        self.statusbar = Gtk.Statusbar()

        # Properties
        self.statusbar.set_no_show_all(True)

        self.statusbar.get_message_area().set_margin_top(0)
        self.statusbar.get_message_area().set_margin_left(0)
        self.statusbar.get_message_area().set_margin_right(0)
        self.statusbar.get_message_area().set_margin_bottom(0)


    def __init_packing(self):
        """ Initialize widgets packing in main window
        """

        # Main widgets
        self.grid.pack_start(self.menubar, False, False, 0)
        self.grid.pack_start(self.toolbar, False, False, 0)
        self.grid.pack_start(self.paned_games, True, True, 0)
        self.grid.pack_start(self.statusbar, False, False, 0)

        # Headerbar
        self.headerbar.pack_start(self.tool_item_launch)
        self.headerbar.pack_start(self.tool_item_fullscreen)
        self.headerbar.pack_start(Gtk.Separator())
        self.headerbar.pack_start(self.grid_options)
        self.headerbar.pack_start(self.tool_item_parameters)
        self.headerbar.pack_end(self.tool_item_menu)

        self.grid_options.pack_start(
            self.tool_item_screenshots, False, False, 0)
        self.grid_options.pack_start(
            self.tool_item_output, False, False, 0)
        self.grid_options.pack_start(
            self.tool_item_notes, False, False, 0)

        # Headerbar menu
        self.tool_item_menu.set_popup(self.menu)

        self.menu.append(self.menu_item_preferences)
        self.menu.append(self.menu_item_gem_log)
        self.menu.append(Gtk.SeparatorMenuItem())
        self.menu.append(self.menu_item_dark_theme)
        self.menu.append(Gtk.SeparatorMenuItem())
        self.menu.append(self.menu_item_sidebar)
        self.menu.append(Gtk.SeparatorMenuItem())
        self.menu.append(self.menu_item_about)
        self.menu.append(Gtk.SeparatorMenuItem())
        self.menu.append(self.menu_item_quit)

        # Menu
        self.menubar.insert(self.menubar_item_main, -1)
        self.menubar.insert(self.menubar_item_edit, -1)
        self.menubar.insert(self.menubar_item_tools, -1)
        self.menubar.insert(self.menubar_item_help, -1)

        # Menu - Main items
        self.menubar_item_main.set_submenu(self.menubar_main_menu)

        self.menubar_main_menu.insert(self.menubar_main_item_launch, -1)
        self.menubar_main_menu.insert(Gtk.SeparatorMenuItem(), -1)
        self.menubar_main_menu.insert(self.menubar_main_item_favorite, -1)
        self.menubar_main_menu.insert(self.menubar_main_item_multiplayer, -1)
        self.menubar_main_menu.insert(Gtk.SeparatorMenuItem(), -1)
        self.menubar_main_menu.insert(self.menubar_main_item_screenshots, -1)
        self.menubar_main_menu.insert(self.menubar_main_item_output, -1)
        self.menubar_main_menu.insert(self.menubar_main_item_notes, -1)
        self.menubar_main_menu.insert(Gtk.SeparatorMenuItem(), -1)
        self.menubar_main_menu.insert(self.menubar_main_item_fullscreen, -1)
        self.menubar_main_menu.insert(Gtk.SeparatorMenuItem(), -1)
        self.menubar_main_menu.insert(self.menubar_main_item_quit, -1)

        # Menu - Edit items
        self.menubar_item_edit.set_submenu(self.menubar_edit_menu)

        self.menubar_edit_menu.insert(self.menubar_edit_item_rename, -1)
        self.menubar_edit_menu.insert(self.menubar_edit_item_parameters, -1)
        self.menubar_edit_menu.insert(self.menubar_edit_item_mednafen, -1)
        self.menubar_edit_menu.insert(Gtk.SeparatorMenuItem(), -1)
        self.menubar_edit_menu.insert(self.menubar_edit_item_copy, -1)
        self.menubar_edit_menu.insert(self.menubar_edit_item_open, -1)
        self.menubar_edit_menu.insert(self.menubar_edit_item_desktop, -1)
        self.menubar_edit_menu.insert(Gtk.SeparatorMenuItem(), -1)
        self.menubar_edit_menu.insert(self.menubar_edit_item_database, -1)
        self.menubar_edit_menu.insert(self.menubar_edit_item_delete, -1)

        # Menu - Tools items
        self.menubar_item_tools.set_submenu(self.menubar_tools_menu)

        self.menubar_tools_menu.insert(self.menubar_tools_item_dark_theme, -1)
        self.menubar_tools_menu.insert(Gtk.SeparatorMenuItem(), -1)
        self.menubar_tools_menu.insert(self.menubar_tools_item_sidebar, -1)
        self.menubar_tools_menu.insert(Gtk.SeparatorMenuItem(), -1)
        self.menubar_tools_menu.insert(self.menubar_tools_item_preferences, -1)

        # Menu - Help items
        self.menubar_item_help.set_submenu(self.menubar_help_menu)

        self.menubar_help_menu.insert(self.menubar_help_item_log, -1)
        self.menubar_help_menu.insert(Gtk.SeparatorMenuItem(), -1)
        self.menubar_help_menu.insert(self.menubar_help_item_about, -1)

        # Toolbar
        self.toolbar.insert(self.tool_item_consoles, -1)
        self.toolbar.insert(self.tool_item_properties, -1)
        self.toolbar.insert(self.tool_separator, -1)
        self.toolbar.insert(self.tool_search, -1)
        self.toolbar.insert(self.tool_filter_favorite, -1)
        self.toolbar.insert(self.tool_filter_multiplayer, -1)

        self.tool_item_consoles.add(self.combo_consoles)
        self.tool_search.add(self.entry_filter)

        self.tool_item_launch.add(self.tool_image_launch)
        self.tool_item_fullscreen.add(self.tool_image_fullscreen)
        self.tool_item_screenshots.add(self.tool_image_screenshots)
        self.tool_item_output.add(self.tool_image_output)
        self.tool_item_notes.add(self.tool_image_notes)
        self.tool_item_parameters.add(self.tool_image_parameters)
        self.tool_item_menu.add(self.tool_image_menu)

        # Games paned
        self.paned_games.pack1(self.scroll_games, True, False)
        self.paned_games.pack2(self.grid_paned, False, False)

        self.grid_paned.pack_start(self.grid_informations, True, True, 0)
        self.grid_paned.pack_start(self.image_game_screen, False, False, 0)

        self.grid_informations.pack_start(
            self.label_game_title, False, False, 0)
        self.grid_informations.pack_start(
            self.separator_game, False, False, 0)

        for widget in self.sidebar_widgets:
            self.grid_informations.pack_start(
                self.widgets_sidebar[widget]["box"], False, False, 0)

        self.grid_informations.pack_end(
            self.label_game_footer, False, False, 0)

        # Games treeview
        self.scroll_games.add(self.treeview_games)

        self.treeview_games.append_column(self.column_game_favorite)
        self.treeview_games.append_column(self.column_game_name)
        self.treeview_games.append_column(self.column_game_play)
        self.treeview_games.append_column(self.column_game_last_play)
        self.treeview_games.append_column(self.column_game_play_time)
        self.treeview_games.append_column(self.column_game_installed)
        self.treeview_games.append_column(self.column_game_flags)

        # Games menu
        self.menu_games.append(self.menu_item_launch)
        self.menu_games.append(Gtk.SeparatorMenuItem())
        self.menu_games.append(self.menu_item_favorite)
        self.menu_games.append(self.menu_item_multiplayer)
        self.menu_games.append(Gtk.SeparatorMenuItem())
        self.menu_games.append(self.menu_item_screenshots)
        self.menu_games.append(self.menu_item_output)
        self.menu_games.append(self.menu_item_notes)
        self.menu_games.append(Gtk.SeparatorMenuItem())
        self.menu_games.append(self.menu_item_edit)

        self.menu_item_edit.set_submenu(self.menu_games_edit)

        self.menu_games_edit.append(self.menu_item_rename)
        self.menu_games_edit.append(self.menu_item_parameters)
        self.menu_games_edit.append(self.menu_item_mednafen)
        self.menu_games_edit.append(Gtk.SeparatorMenuItem())
        self.menu_games_edit.append(self.menu_item_copy)
        self.menu_games_edit.append(self.menu_item_open)
        self.menu_games_edit.append(self.menu_item_desktop)
        self.menu_games_edit.append(Gtk.SeparatorMenuItem())
        self.menu_games_edit.append(self.menu_item_remove)
        self.menu_games_edit.append(self.menu_item_database)

        self.add(self.grid)


    def __init_signals(self):
        """ Initialize widgets signals
        """

        self.connect("game-terminate", self.__on_game_terminate)

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

        self.menubar_main_item_launch.connect(
            "activate", self.__on_game_launch)
        self.menubar_main_item_favorite.connect(
            "activate", self.__on_game_marked_as_favorite)
        self.menubar_main_item_multiplayer.connect(
            "activate", self.__on_game_marked_as_multiplayer)
        self.menubar_main_item_screenshots.connect(
            "activate", self.__on_show_viewer)
        self.menubar_main_item_output.connect(
            "activate", self.__on_show_log)
        self.menubar_main_item_notes.connect(
            "activate", self.__on_show_notes)
        self.fullscreen_signal = self.menubar_main_item_fullscreen.connect(
            "toggled", self.__on_activate_fullscreen)
        self.menubar_main_item_quit.connect(
            "activate", self.__stop_interface)

        self.menubar_edit_item_rename.connect(
            "activate", self.__on_game_renamed)
        self.menubar_edit_item_parameters.connect(
            "activate", self.__on_game_parameters)
        self.menubar_edit_item_copy.connect(
            "activate", self.__on_game_copy)
        self.menubar_edit_item_open.connect(
            "activate", self.__on_game_open)
        self.menubar_edit_item_desktop.connect(
            "activate", self.__on_game_generate_desktop)
        self.menubar_edit_item_database.connect(
            "activate", self.__on_game_clean)
        self.menubar_edit_item_delete.connect(
            "activate", self.__on_game_removed)
        self.menubar_edit_item_mednafen.connect(
            "activate", self.__on_game_backup_memory)

        self.menubar_tools_item_preferences.connect(
            "activate", self.__on_show_preferences)
        self.dark_signal_menubar = self.menubar_tools_item_dark_theme.connect(
            "toggled", self.__on_activate_dark_theme)
        self.side_signal_menubar = self.menubar_tools_item_sidebar.connect(
            "toggled", self.__on_activate_sidebar)

        self.menubar_help_item_log.connect(
            "activate", self.__on_show_log)
        self.menubar_help_item_about.connect(
            "activate", self.__on_show_about)

        # ------------------------------------
        #   Toolbar
        # ------------------------------------

        self.tool_item_launch.connect(
            "clicked", self.__on_game_launch)
        self.fullscreen_signal_tool = self.tool_item_fullscreen.connect(
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
        self.menu_item_mednafen.connect(
            "activate", self.__on_game_backup_memory)

        self.menu_item_preferences.connect(
            "activate", self.__on_show_preferences)
        self.menu_item_gem_log.connect(
            "activate", self.__on_show_log)
        self.dark_signal_menu = self.menu_item_dark_theme.connect(
            "toggled", self.__on_activate_dark_theme)
        self.side_signal_menu = self.menu_item_sidebar.connect(
            "toggled", self.__on_activate_sidebar)
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
        """ Load data and start interface
        """

        self.load_interface()

        # Check last loaded console in gem.conf
        if self.config.getboolean("gem", "load_console_startup", fallback=True):
            console = self.config.item("gem", "last_console", str())

            # A console has been saved
            if len(console) > 0:
                for row in self.model_consoles:
                    if row[1] == console:
                        self.treeview_games.set_visible(True)
                        self.combo_consoles.set_active_iter(row.iter)

                        # Set Console object as selected
                        self.selection["console"] = \
                            self.api.get_console(console)

                        break

        # Check welcome message status in gem.conf
        if self.config.getboolean("gem", "welcome", fallback=True):
            dialog = Message(self, _("Welcome !"), _("Welcome and thanks for "
                "choosing GEM as emulators manager. Start using GEM by "
                "droping some roms into interface.\n\nEnjoy and have fun :D"),
                Icons.SmileBig, False)

            dialog.set_size_request(500, -1)

            dialog.run()
            dialog.destroy()

            # Disallow welcome message for next boot
            self.config.modify("gem", "welcome", 0)
            self.config.update()


    def __stop_interface(self, widget=None, event=None):
        """ Save data and stop interface

        Other Parameters
        ----------------
        widget : Gtk.Widget
            Object which receive signal
        event : Gdk.EventButton or Gdk.EventKey
            Event which triggered this signal
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
                self.notes[dialog].response(Gtk.ResponseType.APPLY)

        # ------------------------------------
        #   Last console
        # ------------------------------------

        # Save current console as last_console in gem.conf
        row = self.combo_consoles.get_active_iter()
        if row is not None:
            console = self.model_consoles.get_value(row, 1)

            last_console = self.config.item("gem", "last_console", None)

            # Avoid to modify gem.conf if console is already in conf
            if last_console is None or not last_console == console:
                self.config.modify("gem", "last_console", console)
                self.config.update()

                self.logger.info(_("Save %s for next startup") % console)

        # ------------------------------------
        #   Windows size
        # ------------------------------------

        self.config.modify("windows", "main", "%dx%d" % self.get_size())
        self.config.update()

        self.logger.info(_("Close interface"))

        self.main_loop.quit()


    def load_interface(self):
        """ Load main interface
        """

        # Avoid to reload API when GEM just started
        if self.__first_draw:
            self.logger.debug("Initialize API")

            self.api.init_data()

        # ------------------------------------
        #   Configuration
        # ------------------------------------

        self.config = Configuration(path_join(GEM.Config, "gem.conf"))

        # Get missing keys from config/gem.conf
        self.config.add_missing_data(get_data(path_join("config", "gem.conf")))

        # ------------------------------------
        #   Shortcuts
        # ------------------------------------

        self.__init_shortcuts()

        # ------------------------------------
        #   Theme
        # ------------------------------------

        # Block signal to avoid stack overflow when toggled
        self.menu_item_dark_theme.handler_block(
            self.dark_signal_menu)
        self.menubar_tools_item_dark_theme.handler_block(
            self.dark_signal_menubar)

        dark_theme_status = self.config.getboolean(
            "gem", "dark_theme", fallback=False)

        on_change_theme(dark_theme_status)

        self.menu_item_dark_theme.set_active(dark_theme_status)
        self.menubar_tools_item_dark_theme.set_active(dark_theme_status)

        # Unblock signal
        self.menu_item_dark_theme.handler_unblock(
            self.dark_signal_menu)
        self.menubar_tools_item_dark_theme.handler_unblock(
            self.dark_signal_menubar)

        self.logger.debug(
            "Set dark theme status to %s" % str(dark_theme_status))

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

        if self.__theme is None:
            self.__theme = self.config.getboolean(
                "gem", "use_classic_theme", fallback=False)

        if not self.__first_draw:

            # ------------------------------------
            #   Window classic theme
            # ------------------------------------

            if not self.__theme:
                self.set_titlebar(self.headerbar)

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

            self.__first_draw = True

        # ------------------------------------
        #   Widgets
        # ------------------------------------

        self.show_all()
        self.menu.show_all()
        self.menu_games.show_all()

        if self.__theme is not None:
            if self.__theme:
                self.logger.debug("Set interface theme to classic")
                self.menubar.show_all()
                self.statusbar.show()

            else:
                self.logger.debug("Set interface theme to default")
                self.menubar.hide()
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
        #   Sidebar
        # ------------------------------------

        sidebar_status = self.config.getboolean(
            "gem", "show_sidebar", fallback=True)

        # Block signal to avoid stack overflow when toggled
        self.menu_item_sidebar.handler_block(
            self.side_signal_menu)
        self.menubar_tools_item_sidebar.handler_block(
            self.side_signal_menubar)

        self.menu_item_sidebar.set_active(sidebar_status)
        self.menubar_tools_item_sidebar.set_active(sidebar_status)

        # Unblock signal
        self.menu_item_sidebar.handler_unblock(
            self.side_signal_menu)
        self.menubar_tools_item_sidebar.handler_unblock(
            self.side_signal_menubar)

        if sidebar_status:
            self.grid_paned.show_all()

            # Avoid to reload paned_game if user has not change orientation
            previous_mode = self.paned_games.get_orientation()

            if self.config.get("gem", "sidebar_orientation") == "horizontal" and \
                not previous_mode == Gtk.Orientation.HORIZONTAL:
                self.paned_games.set_position(-1)
                self.paned_games.set_orientation(Gtk.Orientation.HORIZONTAL)

                self.grid_paned.set_orientation(Gtk.Orientation.VERTICAL)
                self.grid_paned.reorder_child(self.image_game_screen, 0)

                self.image_game_screen.set_alignment(0.5, 0)

            elif not previous_mode == Gtk.Orientation.VERTICAL:
                self.paned_games.set_position(-1)
                self.paned_games.set_orientation(Gtk.Orientation.VERTICAL)

                self.grid_paned.set_orientation(Gtk.Orientation.HORIZONTAL)
                self.grid_paned.reorder_child(self.image_game_screen, -1)

                self.image_game_screen.set_alignment(0, 0)

            if not "game" in self.selection:
                for widget in self.widgets_sidebar.values():
                    widget["box"].hide()

        else:
            self.grid_paned.hide()

        # ------------------------------------
        #   Consoles
        # ------------------------------------

        current_console = self.append_consoles()

        # ------------------------------------
        #   Variables
        # ------------------------------------

        self.selection = dict(
            console=None,
            game=None)

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

            if self.config.getboolean(
                "gem", "hide_empty_console", fallback=False):
                self.combo_consoles.set_active(0)

        else:
            self.combo_consoles.set_active_iter(current_console)


    def sensitive_interface(self, status=False):
        """ Update sensitive status for main widgets

        Parameters
        ----------
        status : bool
            Sensitive status
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
        self.menu_item_mednafen.set_sensitive(status)

        self.tool_item_launch.set_sensitive(status)
        self.tool_item_output.set_sensitive(status)
        self.tool_item_notes.set_sensitive(status)
        self.tool_item_parameters.set_sensitive(status)
        self.tool_item_screenshots.set_sensitive(status)

        self.menubar_main_item_launch.set_sensitive(status)
        self.menubar_main_item_favorite.set_sensitive(status)
        self.menubar_main_item_multiplayer.set_sensitive(status)
        self.menubar_main_item_screenshots.set_sensitive(status)
        self.menubar_main_item_output.set_sensitive(status)
        self.menubar_main_item_notes.set_sensitive(status)
        self.menubar_edit_item_rename.set_sensitive(status)
        self.menubar_edit_item_parameters.set_sensitive(status)
        self.menubar_edit_item_copy.set_sensitive(status)
        self.menubar_edit_item_open.set_sensitive(status)
        self.menubar_edit_item_desktop.set_sensitive(status)
        self.menubar_edit_item_database.set_sensitive(status)
        self.menubar_edit_item_delete.set_sensitive(status)
        self.menubar_edit_item_mednafen.set_sensitive(status)


    def filters_update(self, widget=None):
        """ Reload packages filter when user change filters from menu

        Other Parameters
        ----------------
        widget : Gtk.Widget
            Object which receive signal

        Notes
        -----
        Check widget utility in this function
        """

        self.filter_games.refilter()

        self.check_selection()


    def filters_match(self, model, row, data=None):
        """ Update treeview rows

        This function update games treeview with filter entry content. A row is
        visible if the content match the filter.

        Parameters
        ----------
        model : Gtk.TreeModel
            Treeview model which receive signal
        row : Gtk.TreeModelRow
            Treeview current row

        Other Parameters
        ----------------
        data : object
            User data to pass to the visible function (Default: None)
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
        """ Generate shortcuts signals from user configuration
        """

        shortcuts = {
            self.menubar_edit_item_open:
                self.config.item("keys", "open", "<Control>O"),
            self.menu_item_open:
                self.config.item("keys", "open", "<Control>O"),
            self.menubar_edit_item_copy:
                self.config.item("keys", "copy", "<Control>C"),
            self.menu_item_copy:
                self.config.item("keys", "copy", "<Control>C"),
            self.menubar_edit_item_desktop:
                self.config.item("keys", "desktop", "<Control>G"),
            self.menu_item_desktop:
                self.config.item("keys", "desktop", "<Control>G"),
            self.menubar_main_item_launch:
                self.config.item("keys", "start", "Return"),
            self.menu_item_launch:
                self.config.item("keys", "start", "Return"),
            self.tool_item_launch:
                self.config.item("keys", "start", "Return"),
            self.menubar_edit_item_rename:
                self.config.item("keys", "rename", "F2"),
            self.menu_item_rename:
                self.config.item("keys", "rename", "F2"),
            self.menubar_main_item_favorite:
                self.config.item("keys", "favorite", "F3"),
            self.menu_item_favorite:
                self.config.item("keys", "favorite", "F3"),
            self.menubar_main_item_multiplayer:
                self.config.item("keys", "multiplayer", "F4"),
            self.menu_item_multiplayer:
                self.config.item("keys", "multiplayer", "F4"),
            self.menubar_main_item_screenshots:
                self.config.item("keys", "snapshots", "F5"),
            self.tool_item_screenshots:
                self.config.item("keys", "snapshots", "F5"),
            self.menu_item_screenshots:
                self.config.item("keys", "snapshots", "F5"),
            self.menubar_main_item_output:
                self.config.item("keys", "log", "F6"),
            self.menu_item_output:
                self.config.item("keys", "log", "F6"),
            self.menubar_main_item_notes:
                self.config.item("keys", "notes", "F7"),
            self.menu_item_notes:
                self.config.item("keys", "notes", "F7"),
            self.menu_item_mednafen:
                self.config.item("keys", "memory", "F8"),
            self.menubar_edit_item_mednafen:
                self.config.item("keys", "memory", "F8"),
            self.menu_item_sidebar:
                self.config.item("keys", "sidebar", "F9"),
            self.menubar_tools_item_sidebar:
                self.config.item("keys", "sidebar", "F9"),
            self.menubar_edit_item_parameters:
                self.config.item("keys", "exceptions", "F12"),
            self.tool_item_parameters:
                self.config.item("keys", "exceptions", "F12"),
            self.menu_item_parameters:
                self.config.item("keys", "exceptions", "F12"),
            self.menubar_edit_item_delete:
                self.config.item("keys", "delete", "<Control>Delete"),
            self.menu_item_remove:
                self.config.item("keys", "delete", "<Control>Delete"),
            self.menubar_edit_item_database:
                self.config.item("keys", "remove", "Delete"),
            self.menu_item_database:
                self.config.item("keys", "remove", "Delete"),
            self.menubar_tools_item_preferences:
                self.config.item("keys", "preferences", "<Control>P"),
            self.menu_item_preferences:
                self.config.item("keys", "preferences", "<Control>P"),
            self.menubar_help_item_log:
                self.config.item("keys", "gem", "<Control>L"),
            self.menu_item_gem_log:
                self.config.item("keys", "gem", "<Control>L"),
            self.menubar_main_item_quit:
                self.config.item("keys", "quit", "<Control>Q"),
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
        """ Manage widgets for specific keymaps

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        event : Gdk.EventButton or Gdk.EventKey
            Event which triggered this signal
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
                    "manager !", Icons.Monkey)

                dialog.set_size_request(500, -1)

                dialog.run()
                dialog.destroy()

                self.keys = list()

            if not self.keys == konami_code[0:len(self.keys)]:
                self.keys = list()


    def set_informations(self):
        """ Update headerbar title and subtitle
        """

        game = self.selection["game"]
        console = self.selection["console"]

        texts = list()
        informations = list()

        if(len(self.model_games) == 1):
            texts = [_("1 game available")]
        elif(len(self.model_games) > 1):
            texts = [_("%s games availables") % len(self.model_games)]

        # ----------------------------
        #   Game informations
        # ----------------------------

        if game is not None:
            texts.append(game.name)

            if console is not None:
                self.separator_game.show()

                self.label_game_title.set_markup(
                    "<span weight='bold' size='x-large'>%s</span>" % \
                    game.name.replace('&', "&amp;").replace(
                        '<', "&lt;").replace('>', "&gt;"))

                # Get rom specified emulator
                emulator = console.emulator

                if game.emulator is not None:
                    emulator = game.emulator

                # ----------------------------
                #   Show screenshot
                # ----------------------------

                results = emulator.get_screenshots(game)

                # Check if rom has some screenshots
                if len(results) > 0:
                    index = -1

                    # Get a random file from rom screenshots
                    if self.config.getboolean(
                        "gem", "show_random_screenshot", fallback=True):
                        index = randint(0, len(results) - 1)

                    # Scale screenshot height to 200px
                    pixbuf = Pixbuf.new_from_file_at_scale(
                        results[index], -1, 200, True)

                    if pixbuf is not None:
                        self.image_game_screen.set_from_pixbuf(pixbuf)

                else:
                    self.image_game_screen.set_from_pixbuf(None)

                # ----------------------------
                #   Show informations
                # ----------------------------

                # Play time
                if not game.play_time == time.min:
                    self.widgets_sidebar["play_time"]["box"].show_all()
                    self.widgets_sidebar["play_time"]["value"].set_markup(
                        string_from_time(game.play_time))

                else:
                    self.widgets_sidebar["play_time"]["box"].hide()
                    self.widgets_sidebar["play_time"]["value"].set_text(str())

                # Last launch
                if game.last_launch_date is not None:
                    self.widgets_sidebar["last_play"]["box"].show_all()
                    self.widgets_sidebar["last_play"]["value"].set_markup(
                        string_from_date(game.last_launch_date))
                else:
                    self.widgets_sidebar["last_play"]["box"].hide()
                    self.widgets_sidebar["last_play"]["value"].set_text(str())

                # Game emulator
                if emulator is not None:
                    self.label_game_footer.set_markup("<b>%s</b>: %s" % (
                        _("Emulator"), emulator.name))

        else:
            self.separator_game.hide()

            self.label_game_title.set_text(str())
            self.label_game_footer.set_text(str())
            self.label_game_description.set_text(str())

            self.image_game_screen.set_from_pixbuf(None)

        # ----------------------------
        #   Interface theme specific
        # ----------------------------

        # Default theme
        self.headerbar.set_subtitle(" - ".join(texts))

        # Classic theme
        self.statusbar.push(0, " - ".join(texts))


    def set_message(self, title, message, icon="dialog-error"):
        """ Open a message dialog

        This function open a dialog to inform user and write message to logger
        output.

        Parameters
        ----------
        title : str
            Dialog title
        message : str
            Dialog message
        icon : str
            Dialog icon, set also the logging mode
        """

        if icon == Icons.Error:
            self.logger.error(message)
        elif icon == Icons.Warning:
            self.logger.warning(message)
        else:
            self.logger.info(message)

        dialog = Message(self, title, message, icon)

        dialog.run()
        dialog.destroy()


    def __on_show_about(self, widget):
        """ Show about dialog

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        about = Gtk.AboutDialog()

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

        about.run()
        about.destroy()


    def __on_show_viewer(self, widget):
        """ Show game screenshots

        This function open game screenshots in a viewer. This viewer can be a
        custom one or the gem native viewer. This choice can be do in gem
        configuration file

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
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

                # Get external viewer
                viewer = self.config.get("viewer", "binary")

                if self.config.getboolean("viewer", "native", fallback=True):
                    DialogViewer(self, title, sorted(results))

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
                    self.set_message(_("Missing binary"),
                        _("Cannot find <b>%s</b> viewer !") % viewer,
                        Icons.Warning)

                # ----------------------------
                #   Check screenshots
                # ----------------------------

                if len(emulator.get_screenshots(game)) == 0:
                    self.set_game_data(Columns.Snapshots,
                        self.alternative["snap"], game.filename)


    def __on_show_preferences(self, widget):
        """ Show preferences window

        This function show the gem preferences manager

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        self.set_sensitive(False)

        Preferences(self.api, self).start()

        self.set_sensitive(True)


    def __on_show_log(self, widget):
        """ Show game log

        This function show the gem log content in a non-editable dialog

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        path = None

        game = self.selection["game"]

        # Open main log
        if widget in (self.menu_item_gem_log, self.menubar_help_item_log):
            path = path_join(GEM.Local, "gem.log")

            title = _("GEM")

        # Open game log
        elif game is not None:
            path = self.check_log()

            title = game.name

        if path is not None and exists(expanduser(path)):
            try:
                size = self.config.get(
                    "windows", "log", fallback="800x600").split('x')

            except ValueError as error:
                size = (800, 600)

            dialog = DialogEditor(self,
                title, expanduser(path), size, False, Icons.Terminal)

            dialog.run()

            self.config.modify("windows", "log", "%dx%d" % dialog.get_size())
            self.config.update()

            dialog.destroy()


    def __on_show_notes(self, widget):
        """ Edit game notes

        This function allow user to write some notes for a specific game. The
        user can open as many notes he wants but cannot open a note already
        open

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        game = self.selection["game"]

        if game is not None:
            path = path_join(GEM.Local, "notes", game.filename + ".txt")

            if path is not None and not expanduser(path) in self.notes.keys():
                try:
                    size = self.config.get(
                        "windows", "notes", fallback="800x600").split('x')

                except ValueError as error:
                    size = (800, 600)

                dialog = DialogEditor(self,
                    game.name, expanduser(path), size, icon=Icons.Document)

                # Allow to launch games with open notes
                dialog.set_modal(False)

                dialog.connect("response", self.__on_show_notes_response,
                    game.name, expanduser(path))

                dialog.show()

                # Save dialogs to close it properly when gem terminate and avoid
                # to reopen existing one
                self.notes[expanduser(path)] = dialog

            elif expanduser(path) in self.notes.keys():
                self.notes[expanduser(path)].grab_focus()


    def __on_show_notes_response(self, dialog, response, title, path):
        """ Close notes dialog

        This function close current notes dialog and save his textview buffer to
        the game notes file

        Parameters
        ----------
        dialog : Gtk.Dialog
            Dialog object
        response : Gtk.ResponseType
            Dialog object user response
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

                self.logger.info(_("Update %s notes") % title)

        self.config.modify("windows", "notes", "%dx%d" % dialog.get_size())
        self.config.update()

        dialog.destroy()

        if path in self.notes.keys():
            del self.notes[path]


    def __on_show_emulator_config(self, widget):
        """ Edit emulator configuration file

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
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

                    dialog = DialogEditor(self, _("Configuration for %s") % (
                        emulator.name), expanduser(path), size)

                    response = dialog.run()

                    if response == Gtk.ResponseType.APPLY:
                        with open(path, 'w') as pipe:
                            pipe.write(dialog.buffer_editor.get_text(
                                dialog.buffer_editor.get_start_iter(),
                                dialog.buffer_editor.get_end_iter(), True))

                        self.logger.info(
                            _("Update %s configuration file") % emulator.name)

                    self.config.modify(
                        "windows", "editor", "%dx%d" % dialog.get_size())
                    self.config.update()

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

        self.model_consoles.clear()

        for console in self.api.consoles:
            console = self.api.get_console(console)

            # Reload games list
            console.set_games(self.api)

            if console.emulator is not None:

                # Check if console ROM path exist
                if exists(console.path):
                    status = self.empty

                    hide = self.config.getboolean(
                        "gem", "hide_empty_console", fallback=False)

                    # Check if console ROM path is empty
                    if not hide or (hide and len(console.games) > 0):

                        # Check if current emulator can be launched
                        if not console.emulator.exists:
                            status = self.icons["warning"]

                            self.logger.warning(
                                _("Cannot find %(binary)s for %(console)s") % {
                                    "binary": console.emulator.binary,
                                    "console": console })

                        # Get console icon
                        icon = icon_from_data(
                            console.icon, self.empty, subfolder="consoles")

                        # Append a new console in combobox model
                        row = self.model_consoles.append(
                            [icon, console.name, status, console.id])

                        selection = self.selection.get("console")

                        if selection is not None and \
                            selection.name == console.name:
                            item = row

        if len(self.model_consoles) > 0:
            self.logger.debug(
                "%d console(s) has been added" % len(self.model_consoles))

        return item


    def __on_selected_console(self, widget=None):
        """ Select a console

        This function occurs when the user select a console in the consoles
        combobox

        Other Parameters
        ----------------
        widget : Gtk.Widget
            Object which receive signal (Default: None)
        """

        self.selection["name"] = None
        self.selection["game"] = None

        self.set_informations()

        error = False

        treeiter = self.combo_consoles.get_active_iter()
        if treeiter is not None:

            console_id = self.model_consoles.get_value(treeiter, 3)
            if console_id is not None:
                console = self.api.get_console(console_id)

                # Save selected console
                self.selection["console"] = console

                # ------------------------------------
                #   Check emulator
                # ------------------------------------

                if console.emulator is None:
                    message = _("Cannot find emulator for %s") % console.name
                    error = True

                # Check emulator data
                elif not console.emulator.exists:
                    message = _("%s emulator not exist !") % (emulator.name)
                    error = True

                # ------------------------------------
                #   Set sensitive widgets
                # ------------------------------------

                self.sensitive_interface()

                # Check emulator configurator
                if console.emulator is not None:
                    configuration = console.emulator.configuration

                    if configuration is not None and exists(configuration):
                        self.tool_item_properties.set_sensitive(True)
                    else:
                        self.tool_item_properties.set_sensitive(False)

                # ------------------------------------
                #   Load game list
                # ------------------------------------

                if error:
                    self.model_games.clear()
                    self.filter_games.refilter()

                    self.set_message(console.name, message)

                else:
                    if not self.list_thread == 0:
                        source_remove(self.list_thread)

                    # Load console games list into treeview
                    loader = self.append_games(console)
                    self.list_thread = idle_add(loader.__next__)

                    self.selection["game"] = None


    def append_games(self, console):
        """ Append to games treeview all games from console

        This function add every games which match console extensions to games
        treeview

        Parameters
        ----------
        console : gem.api.Console
            Console object

        Raises
        ------
        TypeError
            if console type is not gem.api.Console

        Notes
        -----
        Using yield avoid an UI freeze when append a lot of games
        """

        if type(console) is not Console:
            raise TypeError("Wrong type for console, expected gem.api.Console")

        iteration = int()

        # Get current thread id
        current_thread_id = self.list_thread

        self.game_path = dict()

        # ------------------------------------
        #   Load data
        # ------------------------------------

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

            emulator = self.api.get_emulator(console.emulator.id)

            for game in console.games.values():

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

                    # Get path from Game
                    path, filepath = game.path
                    # Get name and extension from filename
                    filename, extension = splitext(filepath)

                    row_data = [
                        game.favorite,
                        self.alternative["favorite"],
                        game.name,
                        str(),          # Played
                        str(),          # Last launch date
                        str(),          # Last launch time
                        str(),          # Total play time
                        str(),          # Installed date
                        self.alternative["except"],
                        self.alternative["snap"],
                        self.alternative["multiplayer"],
                        self.alternative["save"],
                        filename ]

                    # Favorite
                    if game.favorite:
                        row_data[Columns.Icon] = self.icons["favorite"]

                    # Multiplayer
                    if game.multiplayer:
                        row_data[Columns.Multiplayer] = \
                            self.icons["multiplayer"]

                    # Played
                    if game.played > 0:
                        row_data[Columns.Played] = str(game.played)

                    # Last launch date
                    if game.last_launch_date is not None:
                        row_data[Columns.LastPlay] = \
                            string_from_date(game.last_launch_date)

                    # Last launch time
                    if not game.last_launch_time == time.min:
                        row_data[Columns.LastTimePlay] = \
                            string_from_time(game.last_launch_time)

                    # Play time
                    if not game.play_time == time.min:
                        row_data[Columns.TimePlay] = \
                            string_from_time(game.play_time)

                    # Parameters
                    if game.default is not None:
                        row_data[Columns.Except] = self.icons["except"]

                    elif game.emulator is not None:
                        if not game.emulator.name == console.emulator.name:
                            row_data[Columns.Except] = self.icons["except"]

                    # Installed time
                    row_data[Columns.Installed] = string_from_date(
                        datetime.fromtimestamp(getctime(game.filepath)).date())

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

        if not access(console.path, W_OK):
            pass

        # ------------------------------------
        #   Close thread
        # ------------------------------------

        self.list_thread = int()

        yield False


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

        console = self.selection["console"]

        if filename is not None and console is not None:
            game = self.api.get_game(console.id, generate_identifier(filename))

            # Store game
            self.selection["game"] = game

            if game is not None:
                self.sensitive_interface(True)

                # Get Game emulator
                emulator = console.emulator
                if game.emulator is not None:
                    emulator = game.emulator

                # ----------------------------
                #   Game data
                # ----------------------------

                if filename in self.threads:
                    self.tool_item_launch.set_sensitive(False)
                    self.tool_item_parameters.set_sensitive(False)
                    self.tool_item_output.set_sensitive(False)

                    self.menu_item_launch.set_sensitive(False)
                    self.menu_item_output.set_sensitive(False)
                    self.menu_item_parameters.set_sensitive(False)
                    self.menu_item_database.set_sensitive(False)
                    self.menu_item_remove.set_sensitive(False)
                    self.menu_item_rename.set_sensitive(False)
                    self.menu_item_mednafen.set_sensitive(False)

                    self.menubar_main_item_launch.set_sensitive(False)
                    self.menubar_main_item_output.set_sensitive(False)
                    self.menubar_edit_item_rename.set_sensitive(False)
                    self.menubar_edit_item_parameters.set_sensitive(False)
                    self.menubar_edit_item_database.set_sensitive(False)
                    self.menubar_edit_item_delete.set_sensitive(False)
                    self.menubar_edit_item_mednafen.set_sensitive(False)

                # Check extension and emulator for GBA game on mednafen
                if not game.extension == ".gba" or \
                    not "mednafen" in emulator.binary or \
                    not self.__mednafen_status:
                    self.menu_item_mednafen.set_sensitive(False)
                    self.menubar_edit_item_mednafen.set_sensitive(False)

                iter_snaps = model.get_value(treeiter, Columns.Snapshots)

                # Check snaps icon to avoid to check screenshots again
                if iter_snaps == self.alternative["snap"]:
                    self.tool_item_screenshots.set_sensitive(False)
                    self.menu_item_screenshots.set_sensitive(False)
                    self.menubar_main_item_screenshots.set_sensitive(False)

                if self.check_log() is None:
                    self.tool_item_output.set_sensitive(False)
                    self.menu_item_output.set_sensitive(False)
                    self.menubar_main_item_output.set_sensitive(False)

                if run_game:
                    self.__on_game_launch()

        self.set_informations()


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


    def __on_game_launch(self, widget=None):
        """ Prepare the game launch

        This function prepare the game launch and start a thread when everything
        are done

        Other Parameters
        ----------------
        widget : Gtk.Widget
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

                command = emulator.command(game,
                    self.tool_item_fullscreen.get_active())

                if len(command) > 0:

                    # ----------------------------
                    #   Run game
                    # ----------------------------

                    thread = GameThread(self, emulator, game, command)

                    # Save thread references
                    self.threads[game.filename] = thread

                    # Launch thread
                    thread.start()

                    self.sensitive_interface()

                    self.tool_item_notes.set_sensitive(True)
                    self.menu_item_notes.set_sensitive(True)
                    self.menubar_main_item_notes.set_sensitive(True)

                    self.menu_item_preferences.set_sensitive(False)
                    self.menubar_tools_item_preferences.set_sensitive(False)

                    return True

        return False


    def __on_game_terminate(self, widget, thread):
        """ Terminate the game processus and update data

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        thread : gem.game.GameThread
            Game thread
        """

        game = thread.game
        emulator = thread.emulator

        # ----------------------------
        #   Save game data
        # ----------------------------

        if not thread.error:
            play_time = datetime.combine(
                date.today(), game.play_time) + thread.delta
            last_launch_time = datetime.combine(
                date.today(), time()) + thread.delta

            # ----------------------------
            #   Update data
            # ----------------------------

            # Play data
            game.played += 1
            game.play_time = play_time.time()
            game.last_launch_time = last_launch_time.time()
            game.last_launch_date = date.today()

            # Update game from database
            self.api.update_game(game)

            # Played
            self.set_game_data(Columns.Played, str(game.played), game.filename)

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
                self.tool_item_screenshots.set_sensitive(True)
                self.menubar_main_image_screenshots.set_sensitive(True)

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
        if select_game is not None and select_game.filename == game.filename:
            self.logger.debug("Restore widgets status for %s" % game.name)
            self.tool_item_launch.set_sensitive(True)
            self.tool_item_output.set_sensitive(True)
            self.tool_item_parameters.set_sensitive(True)

            self.menu_item_launch.set_sensitive(True)
            self.menu_item_parameters.set_sensitive(True)
            self.menu_item_output.set_sensitive(True)
            self.menu_item_database.set_sensitive(True)
            self.menu_item_remove.set_sensitive(True)
            self.menu_item_rename.set_sensitive(True)

            self.menubar_main_item_launch.set_sensitive(True)
            self.menubar_main_item_output.set_sensitive(True)
            self.menubar_edit_item_rename.set_sensitive(True)
            self.menubar_edit_item_parameters.set_sensitive(True)
            self.menubar_edit_item_database.set_sensitive(True)
            self.menubar_edit_item_delete.set_sensitive(True)

            # Avoid to launch the game again when use Enter in game terminate
            self.treeview_games.get_selection().unselect_all()

        # Remove this game from threads list
        if game.filename in self.threads:
            self.logger.debug("Remove %s from process cache" % game.name)

            del self.threads[game.filename]

        if len(self.threads) == 0:
            self.menu_item_preferences.set_sensitive(True)
            self.menubar_tools_item_preferences.set_sensitive(True)


    def __on_game_renamed(self, widget):
        """ Set a custom name for a specific game

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        game = self.selection["game"]

        if game is not None:
            treeiter = self.game_path[game.filename][1]

            # ----------------------------
            #   Dialog
            # ----------------------------

            # Save previous name for logger
            old_name = game.name

            dialog = DialogRename(self, _("Rename a game"),
                _("Set a custom name for %s") % game.filename, game.name)

            if dialog.run() == Gtk.ResponseType.APPLY:
                if not dialog.entry.get_text() == old_name and \
                    len(dialog.entry.get_text()) > 0:

                    self.model_games[treeiter][Columns.Name] = \
                        dialog.entry.get_text()

                    game.name = dialog.entry.get_text()

                    # Update game from database
                    self.api.update_game(game)

                    # Store modified game
                    self.selection["game"] = game

                    self.set_informations()

                    self.logger.info(_("Rename %(old)s to %(new)s") % {
                        "old": old_name, "new": game.name })

            dialog.destroy()


    def __on_game_clean(self, widget):
        """ Reset game informations from database

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        game = self.selection["game"]

        if game is not None:
            treeiter = self.game_path[game.filename][1]

            dialog = Question(self, game.name, _("Would you really want to "
                "clean informations for this game ?"))

            if dialog.run() == Gtk.ResponseType.YES:
                data = {
                    Columns.Name: game.name,
                    Columns.Favorite: False,
                    Columns.Icon: self.alternative["favorite"],
                    Columns.Played: None,
                    Columns.LastPlay: None,
                    Columns.TimePlay: None,
                    Columns.LastTimePlay: None,
                    Columns.Except: self.alternative["except"],
                    Columns.Multiplayer: self.alternative["multiplayer"],
                }

                for key, value in data.items():
                    self.model_games[treeiter][key] = value

                # Remove game from database
                self.api.delete_game(game)

            dialog.destroy()


    def __on_game_removed(self, widget):
        """ Remove a game

        This function also remove files from user disk as screenshots,
        savestates and game file.

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        game = self.selection["game"]
        console = self.selection["console"]

        if game is not None and console is not None:
            treeiter = self.game_path[game.filename][1]

            emulator = console.emulator

            file_to_remove = list()

            need_to_reload = False

            # ----------------------------
            #   Dialog
            # ----------------------------

            title = game.name

            dialog = DialogRemove(self, title)

            if dialog.run() == Gtk.ResponseType.YES:
                file_to_remove.append(game.filepath)

                # ----------------------------
                #   Database
                # ----------------------------

                if dialog.check_database.get_active():
                    # Remove game from database
                    self.api.delete_game(game)

                # ----------------------------
                #   Emulator specific files
                # ----------------------------

                if emulator is not None:

                    # Savestates files
                    if dialog.check_save_state.get_active():
                        file_to_remove.extend(
                            emulator.get_savestates(game))

                    # Screenshots files
                    if dialog.check_screenshots.get_active():
                        file_to_remove.extend(
                            emulator.get_screenshots(game))

                # ----------------------------
                #   Remove files from disk
                # ----------------------------

                for element in file_to_remove:
                    self.logger.info(
                        _("%s has been deleted from disk") % element)

                    remove(element)

                need_to_reload = True

            dialog.destroy()

            if need_to_reload:
                self.load_interface()

                self.set_message(
                    _("Remove %s") % title,
                    _("This game was removed successfully"), Icons.Information)


    def __on_game_parameters(self, widget):
        """ Manage game default parameters

        This function allow the user to specify default emulator and default
        emulator arguments for the selected game

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
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

            dialog = DialogParameters(self, game.name, emulator)

            if dialog.run() == Gtk.ResponseType.OK:
                self.logger.info(
                    _("Update default parameters for %s") % game.name)

                game.emulator = self.api.get_emulator(
                    dialog.combo.get_active_id())

                game.default = dialog.entry.get_text()
                if len(game.default) == 0:
                    game.default = None

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

                    self.tool_item_screenshots.set_sensitive(True)
                    self.menubar_main_item_screenshots.set_sensitive(True)

                else:
                    self.set_game_data(Columns.Snapshots,
                        self.alternative["snap"], game.filename)

                    self.tool_item_screenshots.set_sensitive(False)
                    self.menubar_main_item_screenshots.set_sensitive(False)

                # Savestates
                if len(new_emulator.get_savestates(game)) > 0:
                    self.set_game_data(Columns.Save,
                        self.icons["save"], game.filename)

                else:
                    self.set_game_data(Columns.Save,
                        self.alternative["save"], game.filename)

                self.set_informations()

            dialog.hide()


    def __on_game_backup_memory(self, widget):
        """ Manage game backup memory

        This function can only be used with a GBA game and Mednafen emulator.

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        game = self.selection["game"]
        console = self.selection["console"]

        if game is not None and console is not None:
            content = dict()

            emulator = console.emulator
            if game.emulator is not None:
                emulator = game.emulator

            # FIXME: Maybe a better way to determine type file
            filepath = expanduser(
                path_join('~', ".mednafen", "sav", game.filename + ".type"))

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

            dialog = DialogMednafenMemory(self, game.name, content)

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

            dialog.hide()


    def __on_game_marked_as_favorite(self, widget):
        """ Mark or unmark a game as favorite

        This function update the database when user change the game favorite
        status

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        game = self.selection["game"]

        if game is not None:
            treeiter = self.game_path[game.filename][1]

            if self.model_games[treeiter][Columns.Icon] == \
                self.alternative["favorite"]:
                self.model_games[treeiter][Columns.Favorite] = True
                self.model_games[treeiter][Columns.Icon] = \
                    self.icons["favorite"]

                game.favorite = True

                # Update game from database
                self.api.update_game(game)

                self.logger.debug("Mark %s as favorite" % game.name)

            else:
                self.model_games[treeiter][Columns.Favorite] = False
                self.model_games[treeiter][Columns.Icon] = \
                    self.alternative["favorite"]

                game.favorite = False

                # Update game from database
                self.api.update_game(game)

                self.logger.debug("Unmark %s as favorite" % game.name)

            self.check_selection()


    def __on_game_marked_as_multiplayer(self, widget):
        """ Mark or unmark a game as multiplayer

        This function update the database when user change the game multiplayers
        status

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        game = self.selection["game"]

        if game is not None:
            treeiter = self.game_path[game.filename][1]

            if self.model_games[treeiter][Columns.Multiplayer] == \
                self.alternative["multiplayer"]:
                self.model_games[treeiter][Columns.Multiplayer] = \
                    self.icons["multiplayer"]

                game.multiplayer = True

                # Update game from database
                self.api.update_game(game)

                self.logger.debug("Mark %s as multiplayers" % game.name)

            else:
                self.model_games[treeiter][Columns.Multiplayer] = \
                    self.alternative["multiplayer"]

                game.multiplayer = False

                # Update game from database
                self.api.update_game(game)

                self.logger.debug("Unmark %s as multiplayers" % game.name)

            self.check_selection()


    def __on_game_copy(self, widget):
        """ Copy path folder which contains selected game to clipboard

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        game = self.selection["game"]

        if game is not None:
            self.clipboard.set_text(game.filepath, -1)


    def __on_game_open(self, widget):
        """ Open game directory

        This function open the folder which contains game with the default
        files manager

        Based on http://stackoverflow.com/a/6631329

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
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


    def __on_game_generate_desktop(self, widget):
        """ Generate application desktop file

        This function generate a .desktop file to allow user to launch the game
        from his favorite applications launcher

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        model, treeiter = self.treeview_games.get_selection().get_selected()

        if treeiter is not None:
            game = self.selection["game"]
            console = self.selection["console"]

            # ----------------------------
            #   Check emulator
            # ----------------------------

            emulator = console.emulator

            if game is not None and game.emulator is not None:
                emulator = game.emulator

            if emulator is not None and emulator.id in self.api.emulators:
                name = "%s.desktop" % game.filename

                # ----------------------------
                #   Fill template
                # ----------------------------

                icon = console.icon
                if not exists(icon):
                    icon = path_join(GEM.Local, "icons", "consoles",
                        '.'.join([icon, Icons.Ext]))

                values = {
                    "%name%": game.name,
                    "%icon%": icon,
                    "%path%": game.path[0],
                    "%command%": ' '.join(emulator.command(game)) }

                # Quote game path
                values["%command%"] = values["%command%"].replace(
                    game.filepath, "\"%s\"" % game.filepath)

                try:
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

                    self.set_message(
                        _("Generate menu entry for %s") % game.name,
                        _("%s was generated successfully")  % name,
                        Icons.Information)

                except OSError as error:
                    self.set_message(
                        _("Generate menu entry for %s") % game.name,
                        _("An error occur during generation, consult log for "
                        "futher details."), Icons.Error)


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


    def __on_activate_fullscreen(self, widget):
        """ Update fullscreen button

        This function alternate fullscreen status between active and inactive
        state when user use fullscreen button in toolbar

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        # Block signal
        self.menubar_main_item_fullscreen.handler_block(
            self.fullscreen_signal)
        self.tool_item_fullscreen.handler_block(
            self.fullscreen_signal_tool)

        if not widget.get_active():
            self.logger.debug("Switch game launch to windowed mode")

            self.tool_image_fullscreen.set_from_icon_name(
                Icons.Restore, Gtk.IconSize.LARGE_TOOLBAR)

            self.menubar_main_item_fullscreen.set_active(False)

            if widget == self.menubar_main_item_fullscreen:
                self.tool_item_fullscreen.set_active(False)

        else:
            self.logger.debug("Switch game launch to fullscreen mode")

            self.tool_image_fullscreen.set_from_icon_name(
                Icons.Fullscreen, Gtk.IconSize.LARGE_TOOLBAR)

            self.menubar_main_item_fullscreen.set_active(True)

            if widget == self.menubar_main_item_fullscreen:
                self.tool_item_fullscreen.set_active(True)

        # Unblock signal
        self.menubar_main_item_fullscreen.handler_unblock(
            self.fullscreen_signal)
        self.tool_item_fullscreen.handler_unblock(
            self.fullscreen_signal_tool)


    def __on_activate_dark_theme(self, widget):
        """ Update dark theme status

        This function alternate between dark and light theme when user use
        dark theme entry in main menu

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        # Block signal to avoid stack overflow when toggled
        self.menu_item_dark_theme.handler_block(
            self.dark_signal_menu)
        self.menubar_tools_item_dark_theme.handler_block(
            self.dark_signal_menubar)

        dark_theme_status = not self.config.getboolean(
            "gem", "dark_theme", fallback=False)

        on_change_theme(dark_theme_status)

        self.config.modify("gem", "dark_theme", int(dark_theme_status))
        self.config.update()

        self.menu_item_dark_theme.set_active(dark_theme_status)
        self.menubar_tools_item_dark_theme.set_active(dark_theme_status)

        # Unblock signal
        self.menu_item_dark_theme.handler_unblock(
            self.dark_signal_menu)
        self.menubar_tools_item_dark_theme.handler_unblock(
            self.dark_signal_menubar)


    def __on_activate_sidebar(self, widget):
        """ Update sidebar status

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        # Block signal to avoid stack overflow when toggled
        self.menu_item_sidebar.handler_block(
            self.side_signal_menu)
        self.menubar_tools_item_sidebar.handler_block(
            self.side_signal_menubar)

        sidebar_status = not self.config.getboolean(
            "gem", "show_sidebar", fallback=True)

        if sidebar_status:
            self.grid_paned.show_all()

        else:
            self.grid_paned.hide()

        self.config.modify("gem", "show_sidebar", int(sidebar_status))
        self.config.update()

        self.menu_item_sidebar.set_active(sidebar_status)
        self.menubar_tools_item_sidebar.set_active(sidebar_status)

        # Unblock signal
        self.menu_item_sidebar.handler_unblock(
            self.side_signal_menu)
        self.menubar_tools_item_sidebar.handler_unblock(
            self.side_signal_menubar)


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
            info that has been registered with the target in the Gtk.TargetList
        time : int
            timestamp at which the data was received
        """

        if self.selection["game"] is not None:
            data.set_uris(["file://%s" % self.selection["game"].filepath])


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
            info that has been registered with the target in the Gtk.TargetList
        time : int
            timestamp at which the data was received
        """

        self.logger.debug("Received data from drag & drop")

        widget.stop_emission("drag_data_received")

        # Current acquisition not respect text/uri-list
        if not info == 1337:
            return

        previous_console = None

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

                    # ----------------------------
                    #   Get right console for rom
                    # ----------------------------

                    consoles_list = list()
                    for console in self.api.consoles:
                        console = self.api.get_console(console)

                        if console is not None:
                            extensions = console.extensions

                            if extensions is not None and ext[1:] in extensions:
                                consoles_list.append(console)

                    console = None

                    if len(consoles_list) > 0:
                        console = consoles_list[0]

                        if len(consoles_list) > 1:
                            dialog = DialogConsoles(self,
                                basename(path), consoles_list, previous_console)

                            if dialog.run() == Gtk.ResponseType.APPLY:
                                console = self.api.get_console(dialog.current)

                            previous_console = console

                            dialog.destroy()

            # ----------------------------
            #   Check console
            # ----------------------------

            if console is not None:
                rom_path = console.path

                # ----------------------------
                #   Install roms
                # ----------------------------

                if rom_path is not None and not dirname(path) == rom_path and \
                    exists(rom_path) and access(rom_path, W_OK):
                    move = True

                    # Check if this game already exists in roms folder
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
                    self.set_message(basename(path), _("%s is already in the "
                        "roms folder. Canceling operation.") % basename(path))

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
            log_path = path_join(GEM.Local, "logs", game.filename + ".log")

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
            proc = Popen([ "mednafen" ], stdin=PIPE, stdout=PIPE, stderr=STDOUT,
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


    def emit(self, *args):
        """ Override emit function

        This override allow to use Interface function from another thread in
        MainThread
        """

        idle_add(GObject.emit, self, *args)


class Splash(Gtk.Window):
    """ Splash window which inform user for database migration progress

    Attributes
    ----------
    length : int
        Steps length
    index : int
        Current step
    icons_theme : Gtk.IconTheme
        Default icons theme
    """

    def __init__(self, length):
        """ Constructor

        Parameters
        ----------
        length : int
            Progress steps length
        """

        Gtk.Window.__init__(self)

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

        self.icons_theme.append_search_path(get_data(path_join("icons", "ui")))

        # ------------------------------------
        #   Prepare interface
        # ------------------------------------

        # Init widgets
        self.__init_widgets()

        # Init packing
        self.__init_packing()

        # Start interface
        self.__start_interface()


    def __init_widgets (self):
        """ Load widgets into main interface
        """

        # ------------------------------------
        #   Main window
        # ------------------------------------

        self.set_title("Graphical Emulators Manager")

        self.set_modal(True)
        self.set_can_focus(True)
        self.set_resizable(False)
        self.set_keep_above(True)
        self.set_skip_taskbar_hint(True)
        self.set_type_hint(Gdk.WindowTypeHint.SPLASHSCREEN)

        self.set_position(Gtk.WindowPosition.CENTER)

        # ------------------------------------
        #   Grid
        # ------------------------------------

        self.grid = Gtk.Box()

        # Properties
        self.grid.set_spacing(4)
        self.grid.set_border_width(8)
        self.grid.set_homogeneous(False)
        self.grid.set_orientation(Gtk.Orientation.VERTICAL)

        # ------------------------------------
        #   Image
        # ------------------------------------

        self.image_splash = Gtk.Image()

        # Properties
        self.image_splash.set_from_icon_name(GEM.Icon, Gtk.IconSize.DND)
        self.image_splash.set_pixel_size(256)

        # ------------------------------------
        #   Progressbar
        # ------------------------------------

        self.label_splash = Gtk.Label()

        self.progressbar = Gtk.ProgressBar()

        # Properties
        self.label_splash.set_text(_("Migrating entries from old database"))
        self.label_splash.set_line_wrap_mode(Pango.WrapMode.WORD)
        self.label_splash.set_line_wrap(True)

        self.progressbar.set_show_text(True)


    def __init_packing(self):
        """ Initialize widgets packing in main window
        """

        self.grid.pack_start(self.image_splash, True, True, 0)
        self.grid.pack_start(self.label_splash, False, False, 8)
        self.grid.pack_start(self.progressbar, False, False, 0)

        self.add(self.grid)


    def __start_interface(self):
        """ Load data and start interface
        """

        self.show_all()

        self.refresh()


    def update(self):
        """ Update progress in progressbar widgets
        """

        self.refresh()

        if self.index <= self.length:
            self.progressbar.set_text("%d / %d" % (self.index, self.length))
            self.progressbar.set_fraction(float(self.index) / (self.length))

            self.index += 1

            self.refresh()


    def refresh(self):
        """ Refresh all pendings event in main interface
        """

        while Gtk.events_pending():
            Gtk.main_iteration()
