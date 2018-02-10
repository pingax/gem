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

# Filesystem
from os.path import exists
from os.path import basename
from os.path import splitext
from os.path import expanduser
from os.path import join as path_join

from glob import glob

# System
from sys import exit as sys_exit

# ------------------------------------------------------------------------------
#   Modules - Interface
# ------------------------------------------------------------------------------

try:
    from gi import require_version

    require_version("Gtk", "3.0")

    from gi.repository import Gtk
    from gi.repository import Gdk
    from gi.repository import Pango

    from gi.repository.Gdk import EventType

    from gi.repository.GdkPixbuf import Pixbuf
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
    from gem.gtk.windows import *

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

class Manager(object):
    CONSOLE  = 0
    EMULATOR = 1


class Preferences(CommonWindow):

    def __init__(self, api, parent=None):
        """ Constructor

        Parameters
        ----------
        api : gem.api.GEM
            GEM API instance

        Other Parameters
        ----------------
        parent : Gtk.Window or None
            Parent window for transient mode (default: None)

        Raises
        ------
        TypeError
            if api type is not gem.api.GEM
        """

        if type(api) is not GEM:
            raise TypeError("Wrong type for api, expected gem.api.GEM")

        # ------------------------------------
        #   Initialize variables
        # ------------------------------------

        # API instance
        self.api = api

        self.shortcuts = {
            _("Interface"): {
                "sidebar": [
                    _("Show sidebar"), "F9"],
                "gem": [
                    _("Open main log"), "<Control>L"],
                "preferences": [
                    _("Open preferences"), "<Control>P"],
                "quit": [
                    _("Quit application"), "<Control>Q"] },
            _("Game"): {
                "start": [
                    _("Launch a game"), "Return"],
                "favorite": [
                    _("Mark a game as favorite"), "F3"],
                "multiplayer": [
                    _("Mark a game as multiplayer"), "F4"],
                "finish": [
                    _("Mark a game as finish"), "<Control>F3"],
                "snapshots": [
                    _("Show game screenshots"), "F5"],
                "log": [
                    _("Open game log"), "F6"],
                "notes": [
                    _("Open game notes"), "F7"],
                "memory": [
                    _("Generate a backup memory file"), "F8"] },
            _("Edit"): {
                "remove": [
                    _("Remove a game from database"), "Delete"],
                "delete": [
                    _("Remove a game from disk"), "<Control>Delete"],
                "rename": [
                    _("Rename a game"), "F2"],
                "exceptions": [
                    _("Set specific arguments for a game"), "F12"],
                "open": [
                    _("Open selected game directory"), "<Control>O"],
                "copy": [
                    _("Copy selected game path"), "<Control>C"],
                "desktop": [
                    _("Generate desktop entry for a game"), "<Control>G"] }}

        self.lines = {
            _("None"): "none",
            _("Horizontal"): "horizontal",
            _("Vertical"): "vertical",
            _("Both"): "both" }

        self.sidebar = {
            _("Right"): "horizontal",
            _("Bottom"): "vertical" }

        self.toolbar = {
            _("Menu"): "menu",
            _("Small Toolbar"): "small-toolbar",
            _("Large Toolbar"): "large-toolbar",
            _("Button"): "button",
            _("Drag and Drop"): "dnd",
            _("Dialog"): "dialog" }

        self.selection = {
            "console": None,
            "emulator": None }

        # ------------------------------------
        #   Initialize configuration files
        # ------------------------------------

        self.config = Configuration(
            expanduser(path_join(GEM.Config, "gem.conf")))

        if parent is not None:
            # Get user icon theme
            self.icons_theme = parent.icons_theme

            self.empty = parent.empty

            self.use_classic_theme = parent.use_classic_theme

        else:
            # Initialize GEM
            self.api.init()

            # Get user icon theme
            self.icons_theme = Gtk.IconTheme.get_default()

            self.icons_theme.append_search_path(
                get_data(path_join("icons", "ui")))

            # HACK: Create an empty image to avoid g_object_set_qdata warning
            self.empty = Pixbuf.new(Colorspace.RGB, True, 8, 24, 24)
            self.empty.fill(0x00000000)

            # Generate symbolic icons class
            for key, value in Icons.__dict__.items():
                if not key.startswith("__") and not key.endswith("__"):
                    setattr(Icons.Symbolic, key, "%s-symbolic" % value)

            # Set light/dark theme
            on_change_theme(self.config.getboolean(
                "gem", "dark_theme", fallback=False))

            self.use_classic_theme = self.config.getboolean(
                "gem", "use_classic_theme", fallback=False)

        CommonWindow.__init__(self, parent, _("Preferences"), Icons.Desktop,
            self.use_classic_theme)

        # ------------------------------------
        #   Initialize logger
        # ------------------------------------

        self.logger = self.api.logger

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


    def __init_widgets(self):
        """ Initialize interface widgets
        """

        self.set_resizable(True)

        self.set_spacing(6)

        if self.use_classic_theme:
            self.set_border_width(6)
        else:
            self.set_border_width(0)

        self.set_subtitle(
            "%s - %s (%s)" % (GEM.Name, GEM.Version, GEM.CodeName))

        # ------------------------------------
        #   Grids
        # ------------------------------------

        self.box_notebook_general = Gtk.Box()
        self.box_notebook_interface = Gtk.Box()
        self.box_notebook_shortcuts = Gtk.Box()
        self.box_notebook_consoles = Gtk.Box()
        self.box_notebook_emulators = Gtk.Box()

        self.grid_general = Gtk.Box()
        self.grid_interface = Gtk.Box()
        self.grid_shortcuts = Gtk.Grid()
        self.grid_consoles = Gtk.Grid()
        self.grid_emulators = Gtk.Grid()

        self.grid_last_console = Gtk.Box()
        self.grid_hide_console = Gtk.Box()
        self.grid_lines = Gtk.Box()
        self.grid_colorsheme = Gtk.Box()
        self.grid_font = Gtk.Box()
        self.grid_viewer = Gtk.Box()
        self.grid_binary = Gtk.Box()
        self.grid_options = Gtk.Box()

        self.grid_theme_classic = Gtk.Box()
        self.grid_theme_header = Gtk.Box()
        self.grid_toolbar_icons = Gtk.Box()
        self.grid_sidebar_show = Gtk.Box()
        self.grid_sidebar_screenshot = Gtk.Box()
        self.grid_sidebar_position = Gtk.Box()
        self.grid_games_lines = Gtk.Box()
        self.grid_games_icons = Gtk.Box()
        self.grid_columns_play = Gtk.Box()
        self.grid_columns_last_play = Gtk.Box()
        self.grid_columns_play_time = Gtk.Box()
        self.grid_columns_installed = Gtk.Box()
        self.grid_columns_flags = Gtk.Box()

        self.grid_consoles_buttons = Gtk.ButtonBox()
        self.grid_emulators_buttons = Gtk.ButtonBox()

        # Properties
        self.box_notebook_general.set_spacing(8)
        self.box_notebook_interface.set_spacing(8)
        self.box_notebook_shortcuts.set_spacing(8)
        self.box_notebook_consoles.set_spacing(8)
        self.box_notebook_emulators.set_spacing(8)

        self.grid_general.set_spacing(6)
        self.grid_general.set_border_width(18)
        self.grid_general.set_halign(Gtk.Align.CENTER)
        self.grid_general.set_orientation(Gtk.Orientation.VERTICAL)

        self.grid_interface.set_spacing(6)
        self.grid_interface.set_border_width(18)
        self.grid_interface.set_halign(Gtk.Align.CENTER)
        self.grid_interface.set_orientation(Gtk.Orientation.VERTICAL)

        self.grid_shortcuts.set_row_spacing(6)
        self.grid_shortcuts.set_column_spacing(12)
        self.grid_shortcuts.set_border_width(18)
        self.grid_shortcuts.set_column_homogeneous(False)

        self.grid_consoles.set_row_spacing(6)
        self.grid_consoles.set_column_spacing(12)
        self.grid_consoles.set_border_width(18)
        self.grid_consoles.set_column_homogeneous(False)

        self.grid_emulators.set_row_spacing(6)
        self.grid_emulators.set_column_spacing(12)
        self.grid_emulators.set_border_width(18)
        self.grid_emulators.set_column_homogeneous(False)

        self.grid_last_console.set_spacing(12)
        self.grid_last_console.set_homogeneous(True)
        self.grid_hide_console.set_spacing(12)
        self.grid_hide_console.set_homogeneous(True)

        self.grid_lines.set_spacing(12)
        self.grid_lines.set_homogeneous(True)
        self.grid_colorsheme.set_spacing(12)
        self.grid_colorsheme.set_margin_top(6)
        self.grid_colorsheme.set_homogeneous(True)
        self.grid_font.set_spacing(12)
        self.grid_font.set_homogeneous(True)

        self.grid_viewer.set_spacing(12)
        self.grid_viewer.set_homogeneous(True)
        self.grid_binary.set_spacing(12)
        self.grid_binary.set_margin_top(6)
        self.grid_binary.set_homogeneous(True)
        self.grid_options.set_spacing(12)
        self.grid_options.set_homogeneous(True)

        self.grid_theme_classic.set_spacing(12)
        self.grid_theme_classic.set_homogeneous(True)
        self.grid_theme_header.set_spacing(12)
        self.grid_theme_header.set_homogeneous(True)

        self.grid_toolbar_icons.set_spacing(12)
        self.grid_toolbar_icons.set_homogeneous(True)

        self.grid_sidebar_show.set_spacing(12)
        self.grid_sidebar_show.set_homogeneous(True)
        self.grid_sidebar_screenshot.set_spacing(12)
        self.grid_sidebar_screenshot.set_homogeneous(True)
        self.grid_sidebar_position.set_spacing(12)
        self.grid_sidebar_position.set_homogeneous(True)

        self.grid_games_lines.set_spacing(12)
        self.grid_games_lines.set_homogeneous(True)
        self.grid_games_icons.set_spacing(12)
        self.grid_games_icons.set_homogeneous(True)

        self.grid_columns_play.set_spacing(12)
        self.grid_columns_play.set_homogeneous(True)
        self.grid_columns_last_play.set_spacing(12)
        self.grid_columns_last_play.set_homogeneous(True)
        self.grid_columns_play_time.set_spacing(12)
        self.grid_columns_play_time.set_homogeneous(True)
        self.grid_columns_installed.set_spacing(12)
        self.grid_columns_installed.set_homogeneous(True)
        self.grid_columns_flags.set_spacing(12)
        self.grid_columns_flags.set_homogeneous(True)

        Gtk.StyleContext.add_class(
            self.grid_consoles_buttons.get_style_context(), "linked")
        self.grid_consoles_buttons.set_spacing(-1)
        self.grid_consoles_buttons.set_halign(Gtk.Align.CENTER)
        self.grid_consoles_buttons.set_orientation(Gtk.Orientation.HORIZONTAL)

        Gtk.StyleContext.add_class(
            self.grid_emulators_buttons.get_style_context(), "linked")
        self.grid_emulators_buttons.set_spacing(-1)
        self.grid_emulators_buttons.set_halign(Gtk.Align.CENTER)
        self.grid_emulators_buttons.set_orientation(Gtk.Orientation.HORIZONTAL)

        # ------------------------------------
        #   Notebook
        # ------------------------------------

        self.notebook = Gtk.Notebook()

        self.label_notebook_general = Gtk.Label()
        self.image_notebook_general = Gtk.Image()

        self.label_notebook_interface = Gtk.Label()
        self.image_notebook_interface = Gtk.Image()

        self.label_notebook_shortcuts = Gtk.Label()
        self.image_notebook_shortcuts = Gtk.Image()

        self.label_notebook_consoles = Gtk.Label()
        self.image_notebook_consoles = Gtk.Image()

        self.label_notebook_emulators = Gtk.Label()
        self.image_notebook_emulators = Gtk.Image()

        # Properties
        self.notebook.set_tab_pos(Gtk.PositionType.LEFT)
        self.notebook.set_show_border(False)

        self.label_notebook_general.set_markup("<b>%s</b>" % _("General"))
        self.label_notebook_general.set_use_markup(True)
        self.label_notebook_general.set_alignment(0, .5)
        self.image_notebook_general.set_from_icon_name(
            Icons.Other, Gtk.IconSize.MENU)

        self.label_notebook_interface.set_markup("<b>%s</b>" % _("Interface"))
        self.label_notebook_interface.set_use_markup(True)
        self.label_notebook_interface.set_alignment(0, .5)
        self.image_notebook_interface.set_from_icon_name(
            Icons.Video, Gtk.IconSize.MENU)

        self.label_notebook_shortcuts.set_markup("<b>%s</b>" % _("Shortcuts"))
        self.label_notebook_shortcuts.set_use_markup(True)
        self.label_notebook_shortcuts.set_alignment(0, .5)
        self.image_notebook_shortcuts.set_from_icon_name(
            Icons.Keyboard, Gtk.IconSize.MENU)

        self.label_notebook_consoles.set_markup("<b>%s</b>" % _("Consoles"))
        self.label_notebook_consoles.set_use_markup(True)
        self.label_notebook_consoles.set_alignment(0, .5)
        self.image_notebook_consoles.set_from_icon_name(
            Icons.Gaming, Gtk.IconSize.MENU)

        self.label_notebook_emulators.set_markup("<b>%s</b>" % _("Emulators"))
        self.label_notebook_emulators.set_use_markup(True)
        self.label_notebook_emulators.set_alignment(0, .5)
        self.image_notebook_emulators.set_from_icon_name(
            Icons.Desktop, Gtk.IconSize.MENU)

        # ------------------------------------
        #   General
        # ------------------------------------

        self.scroll_general = Gtk.ScrolledWindow()
        self.view_general = Gtk.Viewport()

        # ------------------------------------
        #   General - Behavior
        # ------------------------------------

        self.label_behavior = Gtk.Label()

        self.label_last_console = Gtk.Label()
        self.check_last_console = Gtk.Switch()

        self.label_hide_console = Gtk.Label()
        self.check_hide_console = Gtk.Switch()

        # Properties
        self.label_behavior.set_hexpand(True)
        self.label_behavior.set_use_markup(True)
        self.label_behavior.set_halign(Gtk.Align.CENTER)
        self.label_behavior.set_markup("<b>%s</b>" % _("Behavior"))

        self.label_last_console.set_line_wrap(True)
        self.label_last_console.set_alignment(1, 0.5)
        self.label_last_console.set_halign(Gtk.Align.END)
        self.label_last_console.set_valign(Gtk.Align.CENTER)
        self.label_last_console.set_justify(Gtk.Justification.RIGHT)
        self.label_last_console.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.label_last_console.get_style_context().add_class("dim-label")
        self.label_last_console.set_text(
            _("Store the last selected console"))

        self.check_last_console.set_halign(Gtk.Align.START)
        self.check_last_console.set_valign(Gtk.Align.CENTER)

        self.label_hide_console.set_line_wrap(True)
        self.label_hide_console.set_alignment(1, 0.5)
        self.label_hide_console.set_halign(Gtk.Align.END)
        self.label_hide_console.set_valign(Gtk.Align.CENTER)
        self.label_hide_console.set_justify(Gtk.Justification.RIGHT)
        self.label_hide_console.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.label_hide_console.get_style_context().add_class("dim-label")
        self.label_hide_console.set_text(
            _("Hide empty consoles"))

        self.check_hide_console.set_halign(Gtk.Align.START)
        self.check_hide_console.set_valign(Gtk.Align.CENTER)

        # ------------------------------------
        #   General - Editor
        # ------------------------------------

        self.label_editor = Gtk.Label()

        self.label_lines = Gtk.Label()
        self.check_lines = Gtk.Switch()

        self.label_editor_colorscheme = Gtk.Label()
        self.model_colorsheme = Gtk.ListStore(str)
        self.combo_colorsheme = Gtk.ComboBox()
        self.cell_colorsheme = Gtk.CellRendererText()

        self.label_editor_font = Gtk.Label()
        self.font_editor = Gtk.FontButton()

        # Properties
        self.label_editor.set_margin_top(18)
        self.label_editor.set_hexpand(True)
        self.label_editor.set_use_markup(True)
        self.label_editor.set_halign(Gtk.Align.CENTER)
        self.label_editor.set_markup("<b>%s</b>" % _("Editor"))

        self.label_lines.set_line_wrap(True)
        self.label_lines.set_alignment(1, 0.5)
        self.label_lines.set_halign(Gtk.Align.END)
        self.label_lines.set_valign(Gtk.Align.CENTER)
        self.label_lines.set_justify(Gtk.Justification.RIGHT)
        self.label_lines.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.label_lines.get_style_context().add_class("dim-label")
        self.label_lines.set_label(
            _("Show line numbers"))

        self.check_lines.set_halign(Gtk.Align.START)
        self.check_lines.set_valign(Gtk.Align.CENTER)

        self.label_editor_colorscheme.set_line_wrap(True)
        self.label_editor_colorscheme.set_alignment(1, 0.5)
        self.label_editor_colorscheme.set_halign(Gtk.Align.END)
        self.label_editor_colorscheme.set_valign(Gtk.Align.CENTER)
        self.label_editor_colorscheme.set_justify(Gtk.Justification.RIGHT)
        self.label_editor_colorscheme.set_line_wrap_mode(
            Pango.WrapMode.WORD_CHAR)
        self.label_editor_colorscheme.get_style_context().add_class("dim-label")
        self.label_editor_colorscheme.set_label(
            _("Colorscheme"))

        self.combo_colorsheme.set_model(self.model_colorsheme)
        self.combo_colorsheme.set_id_column(0)
        self.combo_colorsheme.pack_start(self.cell_colorsheme, True)
        self.combo_colorsheme.add_attribute(self.cell_colorsheme, "text", 0)
        self.combo_colorsheme.set_size_request(300, -1)
        self.combo_colorsheme.set_halign(Gtk.Align.START)
        self.combo_colorsheme.set_valign(Gtk.Align.CENTER)

        self.label_editor_font.set_line_wrap(True)
        self.label_editor_font.set_alignment(1, 0.5)
        self.label_editor_font.set_halign(Gtk.Align.END)
        self.label_editor_font.set_valign(Gtk.Align.CENTER)
        self.label_editor_font.set_justify(Gtk.Justification.RIGHT)
        self.label_editor_font.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.label_editor_font.get_style_context().add_class("dim-label")
        self.label_editor_font.set_label(
            _("Font"))

        # HACK: Set an ellipsize mode for the label inside FontButton
        for child in self.font_editor.get_child():
            if type(child) == Gtk.Label:
                child.set_ellipsize(Pango.EllipsizeMode.END)

        # ------------------------------------
        #   General - Viewer
        # ------------------------------------

        self.label_viewer = Gtk.Label()

        self.label_native_viewer = Gtk.Label()
        self.check_native_viewer = Gtk.Switch()

        self.label_viewer_binary = Gtk.Label()
        self.file_viewer_binary = Gtk.FileChooserButton()

        self.label_viewer_options = Gtk.Label()
        self.entry_viewer_options = Gtk.Entry()

        # Properties
        self.label_viewer.set_margin_top(18)
        self.label_viewer.set_hexpand(True)
        self.label_viewer.set_use_markup(True)
        self.label_viewer.set_halign(Gtk.Align.CENTER)
        self.label_viewer.set_markup("<b>%s</b>" % _("Screenshots viewer"))

        self.label_native_viewer.set_line_wrap(True)
        self.label_native_viewer.set_alignment(1, 0.5)
        self.label_native_viewer.set_halign(Gtk.Align.END)
        self.label_native_viewer.set_valign(Gtk.Align.CENTER)
        self.label_native_viewer.set_justify(Gtk.Justification.RIGHT)
        self.label_native_viewer.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.label_native_viewer.get_style_context().add_class("dim-label")
        self.label_native_viewer.set_text(
            _("Use alternative viewer"))

        self.check_native_viewer.set_halign(Gtk.Align.START)
        self.check_native_viewer.set_valign(Gtk.Align.CENTER)

        self.label_viewer_binary.set_line_wrap(True)
        self.label_viewer_binary.set_alignment(1, 0.5)
        self.label_viewer_binary.set_halign(Gtk.Align.END)
        self.label_viewer_binary.set_valign(Gtk.Align.CENTER)
        self.label_viewer_binary.set_justify(Gtk.Justification.RIGHT)
        self.label_viewer_binary.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.label_viewer_binary.get_style_context().add_class("dim-label")
        self.label_viewer_binary.set_text(
            _("Viewer binary"))

        self.file_viewer_binary.set_hexpand(True)
        self.file_viewer_binary.set_size_request(300, -1)
        self.file_viewer_binary.set_halign(Gtk.Align.START)
        self.file_viewer_binary.set_valign(Gtk.Align.CENTER)

        self.label_viewer_options.set_line_wrap(True)
        self.label_viewer_options.set_alignment(1, 0.5)
        self.label_viewer_options.set_halign(Gtk.Align.END)
        self.label_viewer_options.set_valign(Gtk.Align.CENTER)
        self.label_viewer_options.set_justify(Gtk.Justification.RIGHT)
        self.label_viewer_options.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.label_viewer_options.get_style_context().add_class("dim-label")
        self.label_viewer_options.set_text(
            _("Parameters"))

        self.entry_viewer_options.set_hexpand(True)
        self.entry_viewer_options.set_icon_from_icon_name(
            Gtk.EntryIconPosition.PRIMARY, Icons.Symbolic.Terminal)
        self.entry_viewer_options.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, Icons.Symbolic.Clear)
        self.entry_viewer_options.set_size_request(300, -1)
        self.entry_viewer_options.set_halign(Gtk.Align.START)
        self.entry_viewer_options.set_valign(Gtk.Align.CENTER)

        # ------------------------------------
        #   Interface
        # ------------------------------------

        self.scroll_interface = Gtk.ScrolledWindow()
        self.view_interface = Gtk.Viewport()

        self.label_interface = Gtk.Label()

        self.label_classic_theme = Gtk.Label()
        self.check_classic_theme = Gtk.Switch()

        self.label_header = Gtk.Label()
        self.check_header = Gtk.Switch()

        # Properties
        self.label_interface.set_hexpand(True)
        self.label_interface.set_use_markup(True)
        self.label_interface.set_halign(Gtk.Align.CENTER)
        self.label_interface.set_markup("<b>%s</b>" % _("Interface"))

        self.label_classic_theme.set_line_wrap(True)
        self.label_classic_theme.set_alignment(1, 0.5)
        self.label_classic_theme.set_halign(Gtk.Align.END)
        self.label_classic_theme.set_justify(Gtk.Justification.RIGHT)
        self.label_classic_theme.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.label_classic_theme.get_style_context().add_class("dim-label")
        self.label_classic_theme.set_text(
            _("Switch to classic theme"))

        self.check_classic_theme.set_halign(Gtk.Align.START)
        self.check_classic_theme.set_valign(Gtk.Align.CENTER)

        self.label_header.set_line_wrap(True)
        self.label_header.set_alignment(1, 0.5)
        self.label_header.set_halign(Gtk.Align.END)
        self.label_header.set_justify(Gtk.Justification.RIGHT)
        self.label_header.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.label_header.get_style_context().add_class("dim-label")
        self.label_header.set_text(
            _("Show window buttons in header bar"))

        self.check_header.set_halign(Gtk.Align.START)
        self.check_header.set_valign(Gtk.Align.CENTER)

        # ------------------------------------
        #   Interface - Sidebar
        # ------------------------------------

        self.label_toolbar = Gtk.Label()

        self.label_toolbar_icons = Gtk.Label()
        self.model_toolbar = Gtk.ListStore(str)
        self.combo_toolbar = Gtk.ComboBox()
        self.cell_toolbar = Gtk.CellRendererText()

        # Properties
        self.label_toolbar.set_margin_top(18)
        self.label_toolbar.set_hexpand(True)
        self.label_toolbar.set_use_markup(True)
        self.label_toolbar.set_halign(Gtk.Align.CENTER)
        self.label_toolbar.set_markup("<b>%s</b>" % _("Toolbar"))

        self.label_toolbar_icons.set_line_wrap(True)
        self.label_toolbar_icons.set_alignment(1, 0.5)
        self.label_toolbar_icons.set_halign(Gtk.Align.END)
        self.label_toolbar_icons.set_justify(Gtk.Justification.RIGHT)
        self.label_toolbar_icons.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.label_toolbar_icons.get_style_context().add_class("dim-label")
        self.label_toolbar_icons.set_label(
            _("Toolbar icons size"))

        self.model_toolbar.set_sort_column_id(0, Gtk.SortType.ASCENDING)

        self.combo_toolbar.set_model(self.model_toolbar)
        self.combo_toolbar.set_id_column(0)
        self.combo_toolbar.pack_start(self.cell_toolbar, True)
        self.combo_toolbar.add_attribute(self.cell_toolbar, "text", 0)
        self.combo_toolbar.set_size_request(300, -1)
        self.combo_toolbar.set_halign(Gtk.Align.START)
        self.combo_toolbar.set_valign(Gtk.Align.CENTER)

        # ------------------------------------
        #   Interface - Sidebar
        # ------------------------------------

        self.label_sidebar = Gtk.Label()

        self.label_sidebar_show = Gtk.Label()
        self.check_sidebar_show = Gtk.Switch()

        self.label_sidebar_screenshot = Gtk.Label()
        self.check_sidebar_screenshot = Gtk.Switch()

        self.label_sidebar_position = Gtk.Label()
        self.model_sidebar = Gtk.ListStore(str)
        self.combo_sidebar = Gtk.ComboBox()
        self.cell_sidebar = Gtk.CellRendererText()

        # Properties
        self.label_sidebar.set_margin_top(18)
        self.label_sidebar.set_hexpand(True)
        self.label_sidebar.set_use_markup(True)
        self.label_sidebar.set_halign(Gtk.Align.CENTER)
        self.label_sidebar.set_markup("<b>%s</b>" % _("Sidebar"))

        self.label_sidebar_show.set_line_wrap(True)
        self.label_sidebar_show.set_alignment(1, 0.5)
        self.label_sidebar_show.set_halign(Gtk.Align.END)
        self.label_sidebar_show.set_justify(Gtk.Justification.RIGHT)
        self.label_sidebar_show.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.label_sidebar_show.get_style_context().add_class("dim-label")
        self.label_sidebar_show.set_text(
            _("Show sidebar"))

        self.check_sidebar_show.set_halign(Gtk.Align.START)
        self.check_sidebar_show.set_valign(Gtk.Align.CENTER)

        self.label_sidebar_screenshot.set_line_wrap(True)
        self.label_sidebar_screenshot.set_alignment(1, 0.5)
        self.label_sidebar_screenshot.set_halign(Gtk.Align.END)
        self.label_sidebar_screenshot.set_justify(Gtk.Justification.RIGHT)
        self.label_sidebar_screenshot.set_line_wrap_mode(
            Pango.WrapMode.WORD_CHAR)
        self.label_sidebar_screenshot.get_style_context().add_class("dim-label")
        self.label_sidebar_screenshot.set_text(
            _("Randomize game screenshot in sidebar"))

        self.check_sidebar_screenshot.set_halign(Gtk.Align.START)
        self.check_sidebar_screenshot.set_valign(Gtk.Align.CENTER)

        self.label_sidebar_position.set_line_wrap(True)
        self.label_sidebar_position.set_alignment(1, 0.5)
        self.label_sidebar_position.set_halign(Gtk.Align.END)
        self.label_sidebar_position.set_justify(Gtk.Justification.RIGHT)
        self.label_sidebar_position.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.label_sidebar_position.get_style_context().add_class("dim-label")
        self.label_sidebar_position.set_label(
            _("Sidebar position"))

        self.model_sidebar.set_sort_column_id(0, Gtk.SortType.ASCENDING)

        self.combo_sidebar.set_model(self.model_sidebar)
        self.combo_sidebar.set_id_column(0)
        self.combo_sidebar.pack_start(self.cell_sidebar, True)
        self.combo_sidebar.add_attribute(self.cell_sidebar, "text", 0)
        self.combo_sidebar.set_size_request(300, -1)
        self.combo_sidebar.set_halign(Gtk.Align.START)
        self.combo_sidebar.set_valign(Gtk.Align.CENTER)

        # ------------------------------------
        #   Interface - Games list
        # ------------------------------------

        self.label_treeview = Gtk.Label()
        self.label_treeview_lines = Gtk.Label()

        self.model_lines = Gtk.ListStore(str)
        self.combo_lines = Gtk.ComboBox()

        self.cell_lines = Gtk.CellRendererText()

        self.label_icons = Gtk.Label()
        self.check_icons = Gtk.Switch()

        # Properties
        self.label_treeview.set_margin_top(18)
        self.label_treeview.set_hexpand(True)
        self.label_treeview.set_use_markup(True)
        self.label_treeview.set_halign(Gtk.Align.CENTER)
        self.label_treeview.set_markup("<b>%s</b>" % _("Games list"))

        self.label_treeview_lines.set_line_wrap(True)
        self.label_treeview_lines.set_alignment(1, 0.5)
        self.label_treeview_lines.set_halign(Gtk.Align.END)
        self.label_treeview_lines.set_justify(Gtk.Justification.RIGHT)
        self.label_treeview_lines.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.label_treeview_lines.get_style_context().add_class("dim-label")
        self.label_treeview_lines.set_text(
            _("Show grid lines"))

        self.model_lines.set_sort_column_id(0, Gtk.SortType.ASCENDING)

        self.combo_lines.set_model(self.model_lines)
        self.combo_lines.set_id_column(0)
        self.combo_lines.pack_start(self.cell_lines, True)
        self.combo_lines.add_attribute(self.cell_lines, "text", 0)
        self.combo_lines.set_size_request(300, -1)
        self.combo_lines.set_halign(Gtk.Align.START)
        self.combo_lines.set_valign(Gtk.Align.CENTER)

        self.label_icons.set_line_wrap(True)
        self.label_icons.set_alignment(1, 0.5)
        self.label_icons.set_halign(Gtk.Align.END)
        self.label_icons.set_justify(Gtk.Justification.RIGHT)
        self.label_icons.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.label_icons.get_style_context().add_class("dim-label")
        self.label_icons.set_label(
            _("Use translucent icons"))

        self.check_icons.set_halign(Gtk.Align.START)
        self.check_icons.set_valign(Gtk.Align.CENTER)

        # ------------------------------------
        #   Interface - Columns
        # ------------------------------------

        self.label_columns = Gtk.Label()

        self.label_play = Gtk.Label()
        self.check_play = Gtk.Switch()
        self.label_last_play = Gtk.Label()
        self.check_last_play = Gtk.Switch()
        self.label_play_time = Gtk.Label()
        self.check_play_time = Gtk.Switch()
        self.label_installed = Gtk.Label()
        self.check_installed = Gtk.Switch()
        self.label_flags = Gtk.Label()
        self.check_flags = Gtk.Switch()

        # Properties
        self.label_columns.set_margin_top(18)
        self.label_columns.set_hexpand(True)
        self.label_columns.set_use_markup(True)
        self.label_columns.set_halign(Gtk.Align.CENTER)
        self.label_columns.set_markup("<b>%s</b>" % _("Columns appearance"))

        self.label_play.set_line_wrap(True)
        self.label_play.set_alignment(1, 0.5)
        self.label_play.set_halign(Gtk.Align.END)
        self.label_play.set_justify(Gtk.Justification.RIGHT)
        self.label_play.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.label_play.get_style_context().add_class("dim-label")
        self.label_play.set_label(
            _("Launch"))

        self.check_play.set_halign(Gtk.Align.START)
        self.check_play.set_valign(Gtk.Align.CENTER)

        self.label_last_play.set_line_wrap(True)
        self.label_last_play.set_alignment(1, 0.5)
        self.label_last_play.set_halign(Gtk.Align.END)
        self.label_last_play.set_justify(Gtk.Justification.RIGHT)
        self.label_last_play.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.label_last_play.get_style_context().add_class("dim-label")
        self.label_last_play.set_label(
            _("Last launch"))

        self.check_last_play.set_halign(Gtk.Align.START)
        self.check_last_play.set_valign(Gtk.Align.CENTER)

        self.label_play_time.set_line_wrap(True)
        self.label_play_time.set_alignment(1, 0.5)
        self.label_play_time.set_halign(Gtk.Align.END)
        self.label_play_time.set_justify(Gtk.Justification.RIGHT)
        self.label_play_time.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.label_play_time.get_style_context().add_class("dim-label")
        self.label_play_time.set_label(
            _("Play time"))

        self.check_play_time.set_halign(Gtk.Align.START)
        self.check_play_time.set_valign(Gtk.Align.CENTER)

        self.label_installed.set_line_wrap(True)
        self.label_installed.set_alignment(1, 0.5)
        self.label_installed.set_halign(Gtk.Align.END)
        self.label_installed.set_justify(Gtk.Justification.RIGHT)
        self.label_installed.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.label_installed.get_style_context().add_class("dim-label")
        self.label_installed.set_label(
            _("Installed"))

        self.check_installed.set_halign(Gtk.Align.START)
        self.check_installed.set_valign(Gtk.Align.CENTER)

        self.label_flags.set_line_wrap(True)
        self.label_flags.set_alignment(1, 0.5)
        self.label_flags.set_halign(Gtk.Align.END)
        self.label_flags.set_justify(Gtk.Justification.RIGHT)
        self.label_flags.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.label_flags.get_style_context().add_class("dim-label")
        self.label_flags.set_label(
            _("Flags"))

        self.check_flags.set_halign(Gtk.Align.START)
        self.check_flags.set_valign(Gtk.Align.CENTER)

        # ------------------------------------
        #   Shortcuts
        # ------------------------------------

        self.scroll_shortcuts = Gtk.ScrolledWindow()
        self.view_shortcuts = Gtk.Viewport()

        self.label_shortcuts = Gtk.Label()

        self.scroll_shortcuts_treeview = Gtk.ScrolledWindow()

        self.model_shortcuts = Gtk.TreeStore(str, str, str, bool)
        self.treeview_shortcuts = Gtk.TreeView()

        self.column_shortcuts_name = Gtk.TreeViewColumn()
        self.column_shortcuts_key = Gtk.TreeViewColumn()

        self.cell_shortcuts_name = Gtk.CellRendererText()
        self.cell_shortcuts_keys = Gtk.CellRendererAccel()

        # Properties
        self.label_shortcuts.set_label(_("You can edit interface shortcuts for "
            "some actions. Click on a shortcut and insert wanted shortcut "
            "with your keyboard."))
        self.label_shortcuts.set_line_wrap_mode(Pango.WrapMode.WORD)
        self.label_shortcuts.set_line_wrap(True)
        self.label_shortcuts.set_halign(Gtk.Align.START)
        self.label_shortcuts.set_justify(Gtk.Justification.FILL)

        self.scroll_shortcuts_treeview.set_hexpand(True)
        self.scroll_shortcuts_treeview.set_vexpand(True)
        self.scroll_shortcuts_treeview.set_shadow_type(Gtk.ShadowType.OUT)

        self.model_shortcuts.set_sort_column_id(0, Gtk.SortType.ASCENDING)

        self.treeview_shortcuts.set_model(self.model_shortcuts)
        self.treeview_shortcuts.set_headers_clickable(False)
        self.treeview_shortcuts.set_hexpand(True)
        self.treeview_shortcuts.set_vexpand(True)

        self.column_shortcuts_name.set_expand(True)
        self.column_shortcuts_name.set_title(_("Action"))

        self.column_shortcuts_key.set_expand(True)
        self.column_shortcuts_key.set_title(_("Shortcut"))

        self.column_shortcuts_name.pack_start(
            self.cell_shortcuts_name, True)
        self.column_shortcuts_key.pack_start(
            self.cell_shortcuts_keys, True)

        self.column_shortcuts_name.add_attribute(
            self.cell_shortcuts_name, "text", 0)
        self.column_shortcuts_key.add_attribute(
            self.cell_shortcuts_keys, "text", 1)
        self.column_shortcuts_key.add_attribute(
            self.cell_shortcuts_keys, "sensitive", 3)

        self.cell_shortcuts_keys.set_property("editable", True)

        self.treeview_shortcuts.append_column(self.column_shortcuts_name)
        self.treeview_shortcuts.append_column(self.column_shortcuts_key)

        # ------------------------------------
        #   Consoles
        # ------------------------------------

        self.scroll_consoles = Gtk.ScrolledWindow()
        self.view_consoles = Gtk.Viewport()

        self.scroll_consoles_treeview = Gtk.ScrolledWindow()

        self.model_consoles = Gtk.ListStore(Pixbuf, str, str, str)
        self.treeview_consoles = Gtk.TreeView()

        self.column_consoles_name = Gtk.TreeViewColumn()

        self.cell_consoles_icon = Gtk.CellRendererPixbuf()
        self.cell_consoles_name = Gtk.CellRendererText()
        self.cell_consoles_check = Gtk.CellRendererPixbuf()

        self.image_consoles_add = Gtk.Image()
        self.button_consoles_add = Gtk.Button()

        self.image_consoles_modify = Gtk.Image()
        self.button_consoles_modify = Gtk.Button()

        self.image_consoles_remove = Gtk.Image()
        self.button_consoles_remove = Gtk.Button()

        # Properties
        self.scroll_consoles_treeview.set_hexpand(True)
        self.scroll_consoles_treeview.set_vexpand(True)
        self.scroll_consoles_treeview.set_shadow_type(Gtk.ShadowType.OUT)

        self.model_consoles.set_sort_column_id(1, Gtk.SortType.ASCENDING)

        self.treeview_consoles.set_model(self.model_consoles)
        self.treeview_consoles.set_headers_clickable(False)
        self.treeview_consoles.set_headers_visible(False)
        self.treeview_consoles.set_hexpand(True)
        self.treeview_consoles.set_vexpand(True)

        self.column_consoles_name.set_title(_("Console"))
        self.column_consoles_name.set_expand(True)
        self.column_consoles_name.set_spacing(8)

        self.column_consoles_name.pack_start(
            self.cell_consoles_icon, False)
        self.column_consoles_name.pack_start(
            self.cell_consoles_name, True)
        self.column_consoles_name.pack_start(
            self.cell_consoles_check, False)

        self.column_consoles_name.add_attribute(
            self.cell_consoles_icon, "pixbuf", 0)
        self.column_consoles_name.add_attribute(
            self.cell_consoles_name, "markup", 1)
        self.column_consoles_name.add_attribute(
            self.cell_consoles_check, "icon-name", 2)

        self.cell_consoles_icon.set_padding(6, 6)
        self.cell_consoles_name.set_padding(6, 6)
        self.cell_consoles_check.set_padding(6, 6)

        self.treeview_consoles.append_column(self.column_consoles_name)

        self.image_consoles_add.set_margin_right(4)
        self.image_consoles_add.set_from_icon_name(
            Icons.Add, Gtk.IconSize.MENU)
        self.button_consoles_add.set_image(self.image_consoles_add)
        self.button_consoles_add.set_label(_("Add"))

        self.image_consoles_modify.set_margin_right(4)
        self.image_consoles_modify.set_from_icon_name(
            Icons.Properties, Gtk.IconSize.MENU)
        self.button_consoles_modify.set_image(self.image_consoles_modify)
        self.button_consoles_modify.set_label(_("Modify"))

        self.image_consoles_remove.set_margin_right(4)
        self.image_consoles_remove.set_from_icon_name(
            Icons.Remove, Gtk.IconSize.MENU)
        self.button_consoles_remove.set_image(self.image_consoles_remove)
        self.button_consoles_remove.set_label(_("Remove"))

        # ------------------------------------
        #   Emulators
        # ------------------------------------

        self.scroll_emulators = Gtk.ScrolledWindow()
        self.view_emulators = Gtk.Viewport()

        self.scroll_emulators_treeview = Gtk.ScrolledWindow()

        self.model_emulators = Gtk.ListStore(Pixbuf, str, str, str)
        self.treeview_emulators = Gtk.TreeView()

        self.column_emulators_name = Gtk.TreeViewColumn()

        self.cell_emulators_icon = Gtk.CellRendererPixbuf()
        self.cell_emulators_name = Gtk.CellRendererText()
        self.cell_emulators_check = Gtk.CellRendererPixbuf()

        self.image_emulators_add = Gtk.Image()
        self.button_emulators_add = Gtk.Button()

        self.image_emulators_modify = Gtk.Image()
        self.button_emulators_modify = Gtk.Button()

        self.image_emulators_remove = Gtk.Image()
        self.button_emulators_remove = Gtk.Button()

        # Properties
        self.scroll_emulators_treeview.set_hexpand(True)
        self.scroll_emulators_treeview.set_vexpand(True)
        self.scroll_emulators_treeview.set_shadow_type(Gtk.ShadowType.OUT)

        self.model_emulators.set_sort_column_id(1, Gtk.SortType.ASCENDING)

        self.treeview_emulators.set_model(self.model_emulators)
        self.treeview_emulators.set_headers_clickable(False)
        self.treeview_emulators.set_headers_visible(False)
        self.treeview_emulators.set_hexpand(True)
        self.treeview_emulators.set_vexpand(True)

        self.column_emulators_name.set_title(_("Emulator"))
        self.column_emulators_name.set_expand(True)
        self.column_emulators_name.set_spacing(8)

        self.column_emulators_name.pack_start(
            self.cell_emulators_icon, False)
        self.column_emulators_name.pack_start(
            self.cell_emulators_name, True)
        self.column_emulators_name.pack_start(
            self.cell_emulators_check, False)

        self.column_emulators_name.add_attribute(
            self.cell_emulators_icon, "pixbuf", 0)
        self.column_emulators_name.add_attribute(
            self.cell_emulators_name, "markup", 1)
        self.column_emulators_name.add_attribute(
            self.cell_emulators_check, "icon-name", 2)

        self.cell_emulators_icon.set_padding(6, 6)
        self.cell_emulators_name.set_padding(6, 6)
        self.cell_emulators_check.set_padding(6, 6)

        self.treeview_emulators.append_column(self.column_emulators_name)

        self.image_emulators_add.set_margin_right(4)
        self.image_emulators_add.set_from_icon_name(
            Icons.Add, Gtk.IconSize.MENU)
        self.button_emulators_add.set_image(self.image_emulators_add)
        self.button_emulators_add.set_label(_("Add"))

        self.image_emulators_modify.set_margin_right(4)
        self.image_emulators_modify.set_from_icon_name(
            Icons.Properties, Gtk.IconSize.MENU)
        self.button_emulators_modify.set_image(self.image_emulators_modify)
        self.button_emulators_modify.set_label(_("Modify"))

        self.image_emulators_remove.set_margin_right(4)
        self.image_emulators_remove.set_from_icon_name(
            Icons.Remove, Gtk.IconSize.MENU)
        self.button_emulators_remove.set_image(self.image_emulators_remove)
        self.button_emulators_remove.set_label(_("Remove"))


    def __init_packing(self):
        """ Initialize widgets packing in main window
        """

        # Main widgets
        self.pack_start(self.notebook, True, True)

        # Notebook
        self.box_notebook_general.pack_start(
            self.image_notebook_general, False, False, 0)
        self.box_notebook_general.pack_start(
            self.label_notebook_general, True, True, 0)

        self.box_notebook_interface.pack_start(
            self.image_notebook_interface, False, False, 0)
        self.box_notebook_interface.pack_start(
            self.label_notebook_interface, True, True, 0)

        self.box_notebook_shortcuts.pack_start(
            self.image_notebook_shortcuts, False, False, 0)
        self.box_notebook_shortcuts.pack_start(
            self.label_notebook_shortcuts, True, True, 0)

        self.box_notebook_consoles.pack_start(
            self.image_notebook_consoles, False, False, 0)
        self.box_notebook_consoles.pack_start(
            self.label_notebook_consoles, True, True, 0)

        self.box_notebook_emulators.pack_start(
            self.image_notebook_emulators, False, False, 0)
        self.box_notebook_emulators.pack_start(
            self.label_notebook_emulators, True, True, 0)

        self.notebook.append_page(
            self.scroll_general, self.box_notebook_general)
        self.notebook.append_page(
            self.scroll_interface, self.box_notebook_interface)
        self.notebook.append_page(
            self.scroll_shortcuts, self.box_notebook_shortcuts)
        self.notebook.append_page(
            self.scroll_consoles, self.box_notebook_consoles)
        self.notebook.append_page(
            self.scroll_emulators, self.box_notebook_emulators)

        # General tab
        self.grid_general.pack_start(
            self.label_behavior, False, False, 0)
        self.grid_general.pack_start(
            self.grid_last_console, False, False, 0)
        self.grid_general.pack_start(
            self.grid_hide_console, False, False, 0)
        self.grid_general.pack_start(
            self.label_editor, False, False, 0)
        self.grid_general.pack_start(
            self.grid_lines, False, False, 0)
        self.grid_general.pack_start(
            self.grid_colorsheme, False, False, 0)
        self.grid_general.pack_start(
            self.grid_font, False, False, 0)
        self.grid_general.pack_start(
            self.label_viewer, False, False, 0)
        self.grid_general.pack_start(
            self.grid_viewer, False, False, 0)
        self.grid_general.pack_start(
            self.grid_binary, False, False, 0)
        self.grid_general.pack_start(
            self.grid_options, False, False, 0)

        self.grid_last_console.pack_start(
            self.label_last_console, True, True, 0)
        self.grid_last_console.pack_start(
            self.check_last_console, True, True, 0)

        self.grid_hide_console.pack_start(
            self.label_hide_console, True, True, 0)
        self.grid_hide_console.pack_start(
            self.check_hide_console, True, True, 0)

        self.grid_lines.pack_start(
            self.label_lines, True, True, 0)
        self.grid_lines.pack_start(
            self.check_lines, True, True, 0)

        self.grid_colorsheme.pack_start(
            self.label_editor_colorscheme, True, True, 0)
        self.grid_colorsheme.pack_start(
            self.combo_colorsheme, True, True, 0)

        self.grid_font.pack_start(
            self.label_editor_font, True, True, 0)
        self.grid_font.pack_start(
            self.font_editor, True, True, 0)

        self.grid_viewer.pack_start(
            self.label_native_viewer, True, True, 0)
        self.grid_viewer.pack_start(
            self.check_native_viewer, True, True, 0)

        self.grid_binary.pack_start(
            self.label_viewer_binary, True, True, 0)
        self.grid_binary.pack_start(
            self.file_viewer_binary, True, True, 0)

        self.grid_options.pack_start(
            self.label_viewer_options, True, True, 0)
        self.grid_options.pack_start(
            self.entry_viewer_options, True, True, 0)

        self.view_general.add(self.grid_general)

        self.scroll_general.add(self.view_general)

        # Interface tab
        self.grid_interface.pack_start(
            self.label_interface, False, False, 0)
        self.grid_interface.pack_start(
            self.grid_theme_classic, False, False, 0)
        self.grid_interface.pack_start(
            self.grid_theme_header, False, False, 0)
        self.grid_interface.pack_start(
            self.label_toolbar, False, False, 0)
        self.grid_interface.pack_start(
            self.grid_toolbar_icons, False, False, 0)
        self.grid_interface.pack_start(
            self.label_sidebar, False, False, 0)
        self.grid_interface.pack_start(
            self.grid_sidebar_show, False, False, 0)
        self.grid_interface.pack_start(
            self.grid_sidebar_screenshot, False, False, 0)
        self.grid_interface.pack_start(
            self.grid_sidebar_position, False, False, 0)
        self.grid_interface.pack_start(
            self.label_treeview, False, False, 0)
        self.grid_interface.pack_start(
            self.grid_games_lines, False, False, 0)
        self.grid_interface.pack_start(
            self.grid_games_icons, False, False, 0)
        self.grid_interface.pack_start(
            self.label_columns, False, False, 0)
        self.grid_interface.pack_start(
            self.grid_columns_play, False, False, 0)
        self.grid_interface.pack_start(
            self.grid_columns_last_play, False, False, 0)
        self.grid_interface.pack_start(
            self.grid_columns_play_time, False, False, 0)
        self.grid_interface.pack_start(
            self.grid_columns_installed, False, False, 0)
        self.grid_interface.pack_start(
            self.grid_columns_flags, False, False, 0)

        self.grid_theme_classic.pack_start(
            self.label_classic_theme, True, True, 0)
        self.grid_theme_classic.pack_start(
            self.check_classic_theme, True, True, 0)

        self.grid_theme_header.pack_start(
            self.label_header, True, True, 0)
        self.grid_theme_header.pack_start(
            self.check_header, True, True, 0)

        self.grid_toolbar_icons.pack_start(
            self.label_toolbar_icons, True, True, 0)
        self.grid_toolbar_icons.pack_start(
            self.combo_toolbar, True, True, 0)

        self.grid_sidebar_show.pack_start(
            self.label_sidebar_show, True, True, 0)
        self.grid_sidebar_show.pack_start(
            self.check_sidebar_show, True, True, 0)

        self.grid_sidebar_screenshot.pack_start(
            self.label_sidebar_screenshot, True, True, 0)
        self.grid_sidebar_screenshot.pack_start(
            self.check_sidebar_screenshot, True, True, 0)

        self.grid_sidebar_position.pack_start(
            self.label_sidebar_position, True, True, 0)
        self.grid_sidebar_position.pack_start(
            self.combo_sidebar, True, True, 0)

        self.grid_games_lines.pack_start(
            self.label_treeview_lines, True, True, 0)
        self.grid_games_lines.pack_start(
            self.combo_lines, True, True, 0)

        self.grid_games_icons.pack_start(
            self.label_icons, True, True, 0)
        self.grid_games_icons.pack_start(
            self.check_icons, True, True, 0)

        self.grid_columns_play.pack_start(
            self.label_play, True, True, 0)
        self.grid_columns_play.pack_start(
            self.check_play, True, True, 0)

        self.grid_columns_last_play.pack_start(
            self.label_last_play, True, True, 0)
        self.grid_columns_last_play.pack_start(
            self.check_last_play, True, True, 0)

        self.grid_columns_play_time.pack_start(
            self.label_play_time, True, True, 0)
        self.grid_columns_play_time.pack_start(
            self.check_play_time, True, True, 0)

        self.grid_columns_installed.pack_start(
            self.label_installed, True, True, 0)
        self.grid_columns_installed.pack_start(
            self.check_installed, True, True, 0)

        self.grid_columns_flags.pack_start(
            self.label_flags, True, True, 0)
        self.grid_columns_flags.pack_start(
            self.check_flags, True, True, 0)

        self.view_interface.add(self.grid_interface)

        self.scroll_interface.add(self.view_interface)

        # Shortcuts tab
        self.grid_shortcuts.attach(self.label_shortcuts, 0, 0, 1, 1)
        self.grid_shortcuts.attach(self.scroll_shortcuts_treeview, 0, 1, 1, 1)

        self.scroll_shortcuts_treeview.add(self.treeview_shortcuts)

        self.view_shortcuts.add(self.grid_shortcuts)

        self.scroll_shortcuts.add(self.view_shortcuts)

        # Consoles tab
        self.grid_consoles.attach(self.scroll_consoles_treeview, 0, 0, 1, 1)
        self.grid_consoles.attach(self.grid_consoles_buttons, 0, 1, 1, 1)

        self.grid_consoles_buttons.pack_start(
            self.button_consoles_add, False, False, 0)
        self.grid_consoles_buttons.pack_start(
            self.button_consoles_modify, False, False, 0)
        self.grid_consoles_buttons.pack_start(
            self.button_consoles_remove, False, False, 0)

        self.scroll_consoles_treeview.add(self.treeview_consoles)

        self.view_consoles.add(self.grid_consoles)

        self.scroll_consoles.add(self.view_consoles)

        # Emulators tab
        self.grid_emulators.attach(self.scroll_emulators_treeview, 0, 0, 1, 1)
        self.grid_emulators.attach(self.grid_emulators_buttons, 0, 1, 1, 1)

        self.grid_emulators_buttons.pack_start(
            self.button_emulators_add, False, False, 0)
        self.grid_emulators_buttons.pack_start(
            self.button_emulators_modify, False, False, 0)
        self.grid_emulators_buttons.pack_start(
            self.button_emulators_remove, False, False, 0)

        self.scroll_emulators_treeview.add(self.treeview_emulators)

        self.view_emulators.add(self.grid_emulators)

        self.scroll_emulators.add(self.view_emulators)


    def __init_signals(self):
        """ Initialize widgets signals
        """

        # ------------------------------------
        #   Window
        # ------------------------------------

        self.window.connect(
            "delete-event", self.__stop_interface)

        # ------------------------------------
        #   General
        # ------------------------------------

        self.entry_viewer_options.connect(
            "icon-press", on_entry_clear)

        self.check_native_viewer.connect(
            "state-set", self.__on_check_native_viewer)

        # ------------------------------------
        #   Interface
        # ------------------------------------

        self.check_sidebar_show.connect(
            "state-set", self.__on_check_sidebar)

        # ------------------------------------
        #   Shortcuts
        # ------------------------------------

        self.cell_shortcuts_keys.connect(
            "accel-edited", self.__edit_keys)
        self.cell_shortcuts_keys.connect(
            "accel-cleared", self.__clear_keys)

        # ------------------------------------
        #   Consoles
        # ------------------------------------

        self.treeview_consoles.connect(
            "button-press-event", self.__on_selected_treeview, Manager.CONSOLE)
        self.treeview_consoles.connect(
            "key-release-event", self.__on_selected_treeview, Manager.CONSOLE)

        self.button_consoles_add.connect(
            "clicked", self.__on_modify_item, Manager.CONSOLE, False)
        self.button_consoles_modify.connect(
            "clicked", self.__on_modify_item, Manager.CONSOLE, True)
        self.button_consoles_remove.connect(
            "clicked", self.__on_remove_item, Manager.CONSOLE)

        # ------------------------------------
        #   Emulators
        # ------------------------------------

        self.treeview_emulators.connect(
            "button-press-event", self.__on_selected_treeview, Manager.EMULATOR)
        self.treeview_emulators.connect(
            "key-release-event", self.__on_selected_treeview, Manager.EMULATOR)

        self.button_emulators_add.connect(
            "clicked", self.__on_modify_item, Manager.EMULATOR, False)
        self.button_emulators_modify.connect(
            "clicked", self.__on_modify_item, Manager.EMULATOR, True)
        self.button_emulators_remove.connect(
            "clicked", self.__on_remove_item, Manager.EMULATOR)


    def __start_interface(self):
        """ Load data and start interface
        """

        self.button_cancel = self.add_button(
            _("Close"), Gtk.ResponseType.CLOSE)

        self.button_save = self.add_button(
            _("Apply"), Gtk.ResponseType.APPLY, Gtk.Align.END)

        if self.parent is None:
            self.button_cancel.connect("clicked", self.__stop_interface)
            self.button_save.connect("clicked", self.__stop_interface)

        self.load_configuration()

        try:
            width, height = self.config.get(
                "windows", "preferences", fallback="800x600").split('x')

            self.window.set_default_size(int(width), int(height))
            self.window.resize(int(width), int(height))

        except ValueError as error:
            self.logger.error(
                _("Cannot resize preferences window: %s") % str(error))

            self.window.set_default_size(800, 600)

        self.window.hide()
        self.window.unrealize()

        # Update widget sensitive status
        self.__on_check_sidebar()
        self.__on_check_native_viewer()

        self.show_all()

        self.box_notebook_general.show_all()
        self.box_notebook_interface.show_all()
        self.box_notebook_shortcuts.show_all()
        self.box_notebook_consoles.show_all()
        self.box_notebook_emulators.show_all()

        # Avoid to remove console or emulator when games are launched
        if self.parent is not None and len(self.parent.threads) > 0:
            self.button_consoles_remove.set_sensitive(False)
            self.button_emulators_remove.set_sensitive(False)


    def __stop_interface(self, widget=None, event=None):
        """ Save data and stop interface

        Other Parameters
        ----------------
        widget : Gtk.Widget
            Object which receive signal (Default: None)
        event : Gdk.EventButton or Gdk.EventKey
            Event which triggered this signal (Default: None)
        """

        if self.parent is None and widget == self.button_save:
            self.save_configuration()

        self.window.hide()

        self.config.modify("windows", "preferences", "%dx%d" % self.get_size())
        self.config.update()

        if self.parent is None:
            self.destroy()


    def save_configuration(self):
        """ Load configuration files and fill widgets
        """

        # Write emulators and consoles data
        self.api.write_data()

        self.config.modify("gem", "load_console_startup",
            int(self.check_last_console.get_active()))
        self.config.modify("gem", "hide_empty_console",
            int(self.check_hide_console.get_active()))

        self.config.modify("gem", "toolbar_icons_size",
            self.toolbar[self.combo_toolbar.get_active_id()])

        self.config.modify("gem", "use_classic_theme",
            int(self.check_classic_theme.get_active()))
        self.config.modify("gem", "show_header",
            int(self.check_header.get_active()))
        self.config.modify("gem", "show_sidebar",
            int(self.check_sidebar_show.get_active()))
        self.config.modify("gem", "show_random_screenshot",
            int(self.check_sidebar_screenshot.get_active()))
        self.config.modify("gem", "sidebar_orientation",
            self.sidebar[self.combo_sidebar.get_active_id()])

        self.config.modify("gem", "use_translucent_icons",
            int(self.check_icons.get_active()))
        self.config.modify("columns", "play",
            int(self.check_play.get_active()))
        self.config.modify("columns", "last_play",
            int(self.check_last_play.get_active()))
        self.config.modify("columns", "play_time",
            int(self.check_play_time.get_active()))
        self.config.modify("columns", "installed",
            int(self.check_installed.get_active()))
        self.config.modify("columns", "flags",
            int(self.check_flags.get_active()))

        self.config.modify("gem", "games_treeview_lines",
            self.lines[self.combo_lines.get_active_id()])

        self.config.modify("viewer", "native",
            int(not self.check_native_viewer.get_active()))
        self.config.modify("viewer", "binary",
            self.file_viewer_binary.get_filename())
        self.config.modify("viewer", "options",
            self.entry_viewer_options.get_text())

        # ------------------------------------
        #   Editor
        # ------------------------------------

        if self.gtksource:
            self.config.modify("editor", "lines",
                int(self.check_lines.get_active()))
            self.config.modify("editor", "colorscheme",
                self.combo_colorsheme.get_active_id())
            self.config.modify("editor", "font",
                self.font_editor.get_font_name())

        # ------------------------------------
        #   Shortcuts
        # ------------------------------------

        root = self.model_shortcuts.get_iter_first()

        for line in self.__on_list_shortcuts(root):
            key = self.model_shortcuts.get_value(line, 2)
            value = self.model_shortcuts.get_value(line, 1)

            if key is not None and value is not None:
                self.config.modify("keys", key, value)

        # ------------------------------------
        #   Save data
        # ------------------------------------

        self.config.update()


    def load_configuration(self):
        """ Load configuration files and fill widgets
        """

        # ------------------------------------
        #   General
        # ------------------------------------

        self.check_last_console.set_active(self.config.getboolean(
            "gem", "load_console_startup", fallback=True))
        self.check_hide_console.set_active(self.config.getboolean(
            "gem", "hide_empty_console", fallback=True))

        # ------------------------------------
        #   Viewer
        # ------------------------------------

        self.check_native_viewer.set_active(not self.config.getboolean(
            "viewer", "native", fallback=True))

        self.file_viewer_binary.set_filename(
            self.config.item("viewer", "binary"))
        self.entry_viewer_options.set_text(
            self.config.item("viewer", "options"))

        # ------------------------------------
        #   Interface
        # ------------------------------------

        self.check_classic_theme.set_active(self.config.getboolean(
            "gem", "use_classic_theme", fallback=True))
        self.check_header.set_active(self.config.getboolean(
            "gem", "show_header", fallback=True))
        self.check_sidebar_show.set_active(self.config.getboolean(
            "gem", "show_sidebar", fallback=True))
        self.check_sidebar_screenshot.set_active(self.config.getboolean(
            "gem", "show_random_screenshot", fallback=True))

        item = None
        for key, value in self.toolbar.items():
            row = self.model_toolbar.append([key])

            if self.config.item(
                "gem", "toolbar_icons_size", "small-toolbar") == value:
                item = row

        if item is not None:
            self.combo_toolbar.set_active_iter(item)

        item = None
        for key, value in self.sidebar.items():
            row = self.model_sidebar.append([key])

            if self.config.item("gem", "sidebar_orientation", "none") == value:
                item = row

        if item is not None:
            self.combo_sidebar.set_active_iter(item)

        # ------------------------------------
        #   Games list
        # ------------------------------------

        item = None
        for key, value in self.lines.items():
            row = self.model_lines.append([key])

            if self.config.item("gem", "games_treeview_lines", "none") == value:
                item = row

        if item is not None:
            self.combo_lines.set_active_iter(item)

        self.check_icons.set_active(self.config.getboolean(
            "gem", "use_translucent_icons", fallback=True))

        self.check_play.set_active(self.config.getboolean(
            "columns", "play", fallback=True))

        self.check_last_play.set_active(self.config.getboolean(
            "columns", "last_play", fallback=True))

        self.check_play_time.set_active(self.config.getboolean(
            "columns", "play_time", fallback=True))

        self.check_installed.set_active(self.config.getboolean(
            "columns", "installed", fallback=True))

        self.check_flags.set_active(self.config.getboolean(
            "columns", "flags", fallback=True))

        # ------------------------------------
        #   Editor
        # ------------------------------------

        try:
            require_version("GtkSource", "3.0")

            from gi.repository.GtkSource import StyleSchemeManager

            self.check_lines.set_active(
                self.config.getboolean("editor", "lines", fallback=True))

            colorscheme = self.config.item("editor", "colorscheme", "classic")

            item = None
            for path in StyleSchemeManager().get_search_path():
                for element in sorted(glob(path_join(path, "*.xml"))):
                    filename, extension = splitext(basename(element))

                    row = self.model_colorsheme.append([filename])
                    if filename == colorscheme:
                        item = row

            if item is not None:
                self.combo_colorsheme.set_active_iter(item)

            self.font_editor.set_font_name(
                self.config.item("editor", "font", "Sans 12"))

            self.gtksource = True

        except Exception as error:
            self.gtksource = False

        # ------------------------------------
        #   Shortcuts
        # ------------------------------------

        for key in self.shortcuts.keys():
            key_iter = self.model_shortcuts.append(
                None, [key, None, None, False])

            for option, (string, default) in self.shortcuts[key].items():
                value = self.config.item("keys", option, default)

                self.model_shortcuts.append(
                    key_iter, [string, value, option, True])

        self.treeview_shortcuts.expand_all()

        # ------------------------------------
        #   Consoles
        # ------------------------------------

        self.on_load_consoles()

        # ------------------------------------
        #   Emulators
        # ------------------------------------

        self.on_load_emulators()


    def on_load_consoles(self):
        """ Load consoles into treeview
        """

        self.model_consoles.clear()

        self.selection["console"] = None

        for console in self.api.consoles.values():
            image = icon_from_data(
                console.icon, self.empty, 48, 48, subfolder="consoles")

            path = str()
            if console.path is not None:
                path = console.path

            check = str()
            if not exists(expanduser(path)):
                check = Icons.Symbolic.Warning

            self.model_consoles.append([
                image, "<b>%s</b>\n<small>%s</small>" % (
                console.name, path), check, console.id])


    def on_load_emulators(self):
        """ Load emulators into treeview
        """

        self.model_emulators.clear()

        self.selection["emulator"] = None

        for emulator in self.api.emulators.values():
            image = icon_from_data(
                emulator.icon, self.empty, 48, 48, subfolder="emulators")

            check = str()
            if not emulator.exists:
                check = Icons.Symbolic.Warning

            self.model_emulators.append([
                image, "<b>%s</b>\n<small>%s</small>" % (
                emulator.name, emulator.binary), check, emulator.id])


    def __edit_keys(self, widget, path, key, mods, hwcode):
        """ Edit a shortcut

        Parameters
        ----------
        widget : Gtk.CellRendererAccel
            Object which receive signal
        path : str
            Path identifying the row of the edited cell
        key : int
            New accelerator keyval
        mods : Gdk.ModifierType
            New acclerator modifier mask
        hwcode : int
            Keycode of the new accelerator
        """

        treeiter = self.model_shortcuts.get_iter(path)

        if self.model_shortcuts.iter_parent(treeiter) is not None:
            if Gtk.accelerator_valid(key, mods):
                self.model_shortcuts.set_value(
                    treeiter, 1, Gtk.accelerator_name(key, mods))


    def __clear_keys(self, widget, path):
        """ Clear a shortcut

        Parameters
        ----------
        widget : Gtk.CellRendererAccel
            Object which receive signal
        path : str
            Path identifying the row of the edited cell
        """

        treeiter = self.model_shortcuts.get_iter(path)

        if self.model_shortcuts.iter_parent(treeiter) is not None:
            self.model_shortcuts.set_value(treeiter, 1, None)


    def __on_list_shortcuts(self, treeiter):
        """ List treeiter from shortcuts treestore

        Parameters
        ----------
        treeiter : Gtk.TreeIter
            Current iter

        Returns
        -------
        list
            Treeiter list
        """

        results = list()

        while treeiter is not None:
            results.append(treeiter)

            # Check if current iter has child
            if self.model_shortcuts.iter_has_child(treeiter):
                childiter = self.model_shortcuts.iter_children(treeiter)

                results.extend(self.__on_list_shortcuts(childiter))

            treeiter = self.model_shortcuts.iter_next(treeiter)

        return results


    def __on_selected_treeview(self, treeview, event, manager):
        """ Select a console in consoles treeview

        Parameters
        ----------
        treeview : Gtk.Widget
            Object which receive signal
        event : Gdk.EventButton or Gdk.EventKey
            Event which triggered this signal
        manager : preferences.Manager
            Treeview widget which receive signal
        """

        self.selection[manager] = None

        edit = False

        # Keyboard
        if event.type == EventType.KEY_RELEASE:
            model, treeiter = treeview.get_selection().get_selected()

            if treeiter is not None:
                self.selection[manager] = model.get_value(treeiter, 1)

                if event.keyval == Gdk.KEY_Return:
                    edit = True

        # Mouse
        elif (event.type in [EventType.BUTTON_PRESS, EventType._2BUTTON_PRESS]) \
            and (event.button == 1 or event.button == 3):

            selection = treeview.get_path_at_pos(int(event.x), int(event.y))
            if selection is not None:
                model = treeview.get_model()

                treeiter = model.get_iter(selection[0])
                self.selection[manager] = model.get_value(treeiter, 1)

                if event.button == 1 and event.type == EventType._2BUTTON_PRESS:
                    edit = True

        if edit:
            self.__on_modify_item(None, manager, True)


    def __on_check_native_viewer(self, widget=None, state=None):
        """ Update native viewer widget from checkbutton state

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        status = self.check_native_viewer.get_active()

        self.label_viewer_binary.set_sensitive(status)
        self.file_viewer_binary.set_sensitive(status)

        self.label_viewer_options.set_sensitive(status)
        self.entry_viewer_options.set_sensitive(status)


    def __on_check_sidebar(self, widget=None, state=None):
        """ Update sidebar widget from checkbutton state

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        status = self.check_sidebar_show.get_active()

        self.label_sidebar_screenshot.set_sensitive(status)
        self.check_sidebar_screenshot.set_sensitive(status)
        self.label_sidebar_position.set_sensitive(status)
        self.combo_sidebar.set_sensitive(status)


    def __on_modify_item(self, widget, manager, modification):
        """ Append or modify an item in the treeview

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        manager : preferences.Manager
            Treeview widget which receive signal
        modification : bool
            Use edit mode instead of append mode
        """

        self.selection = {
            "console": None,
            "emulator": None }

        # Select current treeview
        if manager == Manager.CONSOLE:
            treeview = self.treeview_consoles
        elif manager == Manager.EMULATOR:
            treeview = self.treeview_emulators

        model, treeiter = treeview.get_selection().get_selected()

        identifier = None
        if treeiter is not None:
            identifier = model.get_value(treeiter, 3)

        if modification and identifier is None:
            return False

        if manager == Manager.CONSOLE:
            console = self.api.get_console(identifier)

            if modification:
                self.selection["console"] = console

            PreferencesConsole(self, console, modification)

        elif manager == Manager.EMULATOR:
            emulator = self.api.get_emulator(identifier)

            if modification:
                self.selection["emulator"] = emulator

            PreferencesEmulator(self, emulator, modification)

        return True


    def __on_remove_item(self, widget, manager):
        """ Remove an item in the treeview

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        manager : preferences.Manager
            Treeview widget which receive signal
        """

        data = None
        identifier = None

        # Select current treeview
        if manager == Manager.CONSOLE:
            treeview = self.treeview_consoles
        elif manager == Manager.EMULATOR:
            treeview = self.treeview_emulators

        model, treeiter = treeview.get_selection().get_selected()
        if treeiter is not None:
            identifier = model.get_value(treeiter, 3)

        # ----------------------------
        #   Game selected
        # ----------------------------

        need_reload = False

        # Get correct data from identifier
        if identifier is not None:
            if manager == Manager.CONSOLE:
                data = self.api.get_console(identifier)
            elif manager == Manager.EMULATOR:
                data = self.api.get_emulator(identifier)

        if data is not None:
            dialog = Question(self, data.name,
                _("Would you really want to remove this entry ?"))

            if dialog.run() == Gtk.ResponseType.YES:
                if manager == Manager.CONSOLE:
                    self.api.delete_console(data.id)
                elif manager == Manager.EMULATOR:
                    self.api.delete_emulator(data.id)

                model.remove(treeiter)

                need_reload = True

            dialog.destroy()

        if need_reload:
            if manager == Manager.CONSOLE:
                self.on_load_consoles()
            elif manager == Manager.EMULATOR:
                self.on_load_emulators()


class PreferencesConsole(CommonWindow):

    def __init__(self, parent, console, modify):
        """ Constructor

        Parameters
        ----------
        parent : Gtk.Window
            Parent object (Default: None)
        console : gem.api.Console
            Console object
        modify : bool
            Use edit mode instead of append mode
        """

        CommonWindow.__init__(self, parent, _("Console"), Icons.Gaming,
            parent.use_classic_theme)

        # ------------------------------------
        #   Initialize variables
        # ------------------------------------

        # GEM API instance
        self.api = parent.api
        # Console object
        self.console = console

        self.path = None

        self.error = False
        self.file_error = False
        self.emulator_error = False

        self.interface = parent
        self.modify = modify

        # Empty Pixbuf icon
        self.empty = parent.empty

        self.help_data = {
            "order": [
                "Description",
                "Extensions",
                _("Extensions examples"),
                "Expressions"
            ],
            "Description": [
                _("A console represent a games library. You can specify a "
                "default emulator which is used by this console and extensions "
                "which is readable by this emulator.")
            ],
            "Extensions": [
                _("Most of the time, extensions are common between differents "
                "emulators and represent the console acronym name (example: "
                "Nintendo NES -> nes)."),
                _("Extensions are split by spaces and must not having the "
                "first dot (using \"nes\" than \".nes\").")
            ],
            _("Extensions examples"): {
                "Nintendo NES": "nes",
                "Sega Megadrive": "md smd bin 32x md cue"
            },
            "Expressions": [
                _("It's possible to hide specific files from the games list "
                "with regular expressions.")
            ]
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


    def __init_widgets(self):
        """ Initialize interface widgets
        """

        self.set_size(640, -1)

        self.set_resizable(True)

        # ------------------------------------
        #   Grids
        # ------------------------------------

        self.grid_preferences = Gtk.Grid()

        self.grid_ignores = Gtk.Box()
        self.grid_ignores_buttons = Gtk.Box()

        # Properties
        self.grid_preferences.set_row_spacing(6)
        self.grid_preferences.set_column_spacing(12)
        self.grid_preferences.set_column_homogeneous(False)

        self.grid_ignores.set_spacing(12)
        self.grid_ignores.set_homogeneous(False)

        Gtk.StyleContext.add_class(
            self.grid_ignores_buttons.get_style_context(), "linked")
        self.grid_ignores_buttons.set_spacing(-1)
        self.grid_ignores_buttons.set_orientation(Gtk.Orientation.VERTICAL)

        # ------------------------------------
        #   Console options
        # ------------------------------------

        self.label_name = Gtk.Label()
        self.entry_name = Gtk.Entry()

        self.label_folder = Gtk.Label()
        self.file_folder = Gtk.FileChooserButton()

        self.button_console = Gtk.Button()
        self.image_console = Gtk.Image()

        self.label_recursive = Gtk.Label()
        self.switch_recursive = Gtk.Switch()

        # Properties
        self.label_name.set_alignment(1, 0.5)
        self.label_name.set_halign(Gtk.Align.END)
        self.label_name.set_justify(Gtk.Justification.RIGHT)
        self.label_name.get_style_context().add_class("dim-label")
        self.label_name.set_text(_("Name"))

        self.entry_name.set_hexpand(True)
        self.entry_name.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, Icons.Symbolic.Clear)

        self.label_folder.set_alignment(1, 0.5)
        self.label_folder.set_halign(Gtk.Align.END)
        self.label_folder.set_justify(Gtk.Justification.RIGHT)
        self.label_folder.get_style_context().add_class("dim-label")
        self.label_folder.set_text(_("Games folder"))

        self.file_folder.set_action(Gtk.FileChooserAction.SELECT_FOLDER)
        self.file_folder.set_hexpand(True)

        self.button_console.set_size_request(64, 64)
        self.image_console.set_size_request(64, 64)

        self.label_recursive.set_margin_top(12)
        self.label_recursive.set_label(_("Recursive"))
        self.label_recursive.set_halign(Gtk.Align.END)
        self.label_recursive.set_valign(Gtk.Align.CENTER)
        self.label_recursive.get_style_context().add_class("dim-label")

        self.switch_recursive.set_margin_top(12)
        self.switch_recursive.set_halign(Gtk.Align.START)

        # ------------------------------------
        #   Emulator options
        # ------------------------------------

        self.label_emulator = Gtk.Label()

        self.label_default = Gtk.Label()

        self.model_emulators = Gtk.ListStore(Pixbuf, str, Pixbuf)
        self.combo_emulators = Gtk.ComboBox()

        cell_emulators_icon = Gtk.CellRendererPixbuf()
        cell_emulators_name = Gtk.CellRendererText()
        cell_emulators_warning = Gtk.CellRendererPixbuf()

        self.label_extensions = Gtk.Label()
        self.entry_extensions = Gtk.Entry()

        # Properties
        self.label_emulator.set_margin_top(18)
        self.label_emulator.set_hexpand(True)
        self.label_emulator.set_use_markup(True)
        self.label_emulator.set_halign(Gtk.Align.CENTER)
        self.label_emulator.set_markup("<b>%s</b>" % _("Default emulator"))

        self.label_default.set_alignment(1, 0.5)
        self.label_default.set_halign(Gtk.Align.END)
        self.label_default.set_justify(Gtk.Justification.RIGHT)
        self.label_default.get_style_context().add_class("dim-label")
        self.label_default.set_text(_("Emulator"))

        self.model_emulators.set_sort_column_id(1, Gtk.SortType.ASCENDING)

        self.combo_emulators.set_hexpand(True)
        self.combo_emulators.set_model(self.model_emulators)
        self.combo_emulators.set_id_column(1)
        self.combo_emulators.pack_start(cell_emulators_icon, False)
        self.combo_emulators.add_attribute(cell_emulators_icon, "pixbuf", 0)
        self.combo_emulators.pack_start(cell_emulators_name, True)
        self.combo_emulators.add_attribute(cell_emulators_name, "text", 1)
        self.combo_emulators.pack_start(cell_emulators_warning, False)
        self.combo_emulators.add_attribute(cell_emulators_warning, "pixbuf", 2)

        cell_emulators_icon.set_padding(4, 0)

        self.label_extensions.set_alignment(1, 0.5)
        self.label_extensions.set_halign(Gtk.Align.END)
        self.label_extensions.set_justify(Gtk.Justification.RIGHT)
        self.label_extensions.get_style_context().add_class("dim-label")
        self.label_extensions.set_text(_("Extensions"))

        self.entry_extensions.set_hexpand(True)
        self.entry_extensions.set_tooltip_text(
            _("Use space to separate extensions"))
        self.entry_extensions.set_placeholder_text(
            _("Use space to separate extensions"))
        self.entry_extensions.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, Icons.Symbolic.Clear)

        # ------------------------------------
        #   Ignores options
        # ------------------------------------

        self.scroll_ignores = Gtk.ScrolledWindow()

        self.viewport_ignores = Gtk.Viewport()

        self.label_ignores = Gtk.Label()

        self.image_ignores_add = Gtk.Image()
        self.button_ignores_add = Gtk.Button()

        self.image_ignores_remove = Gtk.Image()
        self.button_ignores_remove = Gtk.Button()

        self.model_ignores = Gtk.ListStore(str)
        self.treeview_ignores = Gtk.TreeView()
        self.column_ignores = Gtk.TreeViewColumn()
        self.cell_ignores = Gtk.CellRendererText()

        # Properties
        self.scroll_ignores.add(self.viewport_ignores)
        self.scroll_ignores.set_size_request(-1, 200)

        self.label_ignores.set_margin_top(18)
        self.label_ignores.set_hexpand(True)
        self.label_ignores.set_use_markup(True)
        self.label_ignores.set_halign(Gtk.Align.CENTER)
        self.label_ignores.set_markup(
            "<b>%s</b>" % _("Regular expressions for ignored files"))

        self.image_ignores_add.set_from_icon_name(
            Icons.Symbolic.Add, Gtk.IconSize.BUTTON)
        self.image_ignores_remove.set_from_icon_name(
            Icons.Symbolic.Remove, Gtk.IconSize.BUTTON)

        self.treeview_ignores.set_vexpand(True)
        self.treeview_ignores.set_model(self.model_ignores)
        self.treeview_ignores.set_headers_visible(False)
        self.treeview_ignores.set_grid_lines(Gtk.TreeViewGridLines.HORIZONTAL)

        self.column_ignores.pack_start(self.cell_ignores, True)
        self.column_ignores.add_attribute(self.cell_ignores, "text", 0)

        self.cell_ignores.set_padding(12, 6)
        self.cell_ignores.set_property("editable", True)
        self.cell_ignores.set_property("placeholder_text",
            _("Write your regex here..."))
        self.cell_ignores.set_property("ellipsize", Pango.EllipsizeMode.END)


    def __init_packing(self):
        """ Initialize widgets packing in main window
        """

        # Main widgets
        self.pack_start(self.grid_preferences, True, True)

        # Console grid
        self.grid_preferences.attach(self.label_name, 0, 0, 1, 1)
        self.grid_preferences.attach(self.entry_name, 1, 0, 1, 1)

        self.grid_preferences.attach(self.label_folder, 0, 1, 1, 1)
        self.grid_preferences.attach(self.file_folder, 1, 1, 1, 1)

        self.grid_preferences.attach(self.button_console, 2, 0, 1, 2)

        self.grid_preferences.attach(self.label_recursive, 0, 2, 1, 1)
        self.grid_preferences.attach(self.switch_recursive, 1, 2, 2, 1)

        self.grid_preferences.attach(self.label_emulator, 0, 3, 3, 1)

        self.grid_preferences.attach(self.label_default, 0, 4, 1, 1)
        self.grid_preferences.attach(self.combo_emulators, 1, 4, 2, 1)

        self.grid_preferences.attach(self.label_extensions, 0, 5, 1, 1)
        self.grid_preferences.attach(self.entry_extensions, 1, 5, 2, 1)

        self.grid_preferences.attach(self.label_ignores, 0, 6, 3, 1)
        self.grid_preferences.attach(self.grid_ignores, 0, 7, 3, 1)

        # Console options
        self.button_console.set_image(self.image_console)

        # Ignores
        self.button_ignores_add.add(self.image_ignores_add)
        self.button_ignores_remove.add(self.image_ignores_remove)

        self.treeview_ignores.append_column(self.column_ignores)

        self.grid_ignores_buttons.pack_start(
            self.button_ignores_add, False, False, 0)
        self.grid_ignores_buttons.pack_start(
            self.button_ignores_remove, False, False, 0)

        self.grid_ignores.pack_start(
            self.grid_ignores_buttons, False, False, 0)
        self.grid_ignores.pack_start(
            self.scroll_ignores, True, True, 0)

        self.viewport_ignores.add(self.treeview_ignores)


    def __init_signals(self):
        """ Initialize widgets signals
        """

        self.entry_name.connect("changed", self.__update_dialog)
        self.entry_name.connect("icon-press", on_entry_clear)

        self.file_folder.connect("file-set", self.__update_dialog)

        self.entry_extensions.connect("icon-press", on_entry_clear)

        self.button_console.connect("clicked", self.__on_select_icon)

        self.combo_emulators.connect("changed", self.__update_dialog)

        self.cell_ignores.connect("edited", self.__on_edited_cell)

        self.button_ignores_add.connect("clicked", self.__on_append_item)
        self.button_ignores_remove.connect("clicked", self.__on_remove_item)


    def __start_interface(self):
        """ Load data and start interface
        """

        self.add_button(_("Close"), Gtk.ResponseType.CLOSE)
        self.add_button(_("Apply"), Gtk.ResponseType.APPLY, Gtk.Align.END)

        self.add_help(self.help_data)

        self.set_response_sensitive(Gtk.ResponseType.APPLY, False)

        emulators_rows = dict()

        for emulator in self.api.emulators.values():
            icon = icon_from_data(
                emulator.icon, self.empty, 24, 24, "emulators")

            warning = self.empty
            if not emulator.exists:
                warning = icon_load(Icons.Warning, 24, self.empty)

            emulators_rows[emulator.id] = self.model_emulators.append(
                [icon, emulator.name, warning])

        self.combo_emulators.set_wrap_width(int(len(self.model_emulators) / 10))

        # ------------------------------------
        #   Init data
        # ------------------------------------

        if self.modify:
            self.entry_name.set_text(self.console.name)

            # Folder
            folder = self.console.path
            if folder is not None and exists(folder):
                self.file_folder.set_current_folder(folder)

            # Recursive status
            self.switch_recursive.set_active(self.console.recursive)

            # Extensions
            self.entry_extensions.set_text(' '.join(self.console.extensions))

            # Icon
            self.path = self.console.icon
            self.image_console.set_from_pixbuf(
                icon_from_data(self.path, self.empty, 64, 64, "consoles"))

            # Ignores
            for ignore in self.console.ignores:
                self.model_ignores.append([ ignore ])

            # Emulator
            emulator = self.console.emulator
            if emulator is not None and emulator.id in emulators_rows:
                self.combo_emulators.set_active_id(emulator.name)

            self.set_response_sensitive(Gtk.ResponseType.APPLY, True)

        # ------------------------------------
        #   Start dialog
        # ------------------------------------

        need_reload = False

        response = self.run()

        # Save console
        if response == Gtk.ResponseType.APPLY:
            self.__on_save_data()

            if self.data is not None:
                if self.modify:
                    self.api.delete_console(self.console.id)

                # Append a new console
                self.api.add_console(self.data)

            need_reload = True

        self.destroy()

        if need_reload:
            self.interface.on_load_consoles()


    def __on_save_data(self):
        """ Return all the data from interface
        """

        self.section = self.entry_name.get_text()

        identifier = None
        if len(self.section) > 0:
            identifier = generate_identifier(self.section)

        path = self.file_folder.get_filename()
        if path is None or not exists(path):
            path = self.console.path

        icon = self.path
        if icon is not None and path_join(
            get_data("icons"), basename(icon)) == icon:

            icon = splitext(basename(icon))[0]

        extensions = list()
        if len(self.entry_extensions.get_text()) > 0:
            extensions = self.entry_extensions.get_text().split()

        ignores = list()
        for row in self.model_ignores:
            data = self.model_ignores.get_value(row.iter, 0)

            if data is not None and len(data) > 0:
                ignores.append(data)

        self.data = {
            "id": identifier,
            "name": self.section,
            "path": path,
            "icon": icon,
            "ignores": ignores,
            "extensions": extensions,
            "recursive": self.switch_recursive.get_active(),
            "emulator": self.api.get_emulator(
                self.combo_emulators.get_active_id())
        }


    def __on_select_icon(self, widget):
        """ Select a new icon

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        dialog = IconViewer(self, _("Choose an icon"), self.path, "consoles")

        if dialog.new_path is not None:
            self.image_console.set_from_pixbuf(
                icon_from_data(dialog.new_path, self.empty, 64, 64, "consoles"))

            self.path = dialog.new_path

        dialog.destroy()


    def __on_append_item(self, widget):
        """ Append a new row in treeview

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        self.model_ignores.append([ str() ])


    def __on_remove_item(self, widget):
        """ Remove a row in treeview

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        model, treeiter = self.treeview_ignores.get_selection().get_selected()
        if treeiter is not None:
            self.model_ignores.remove(treeiter)


    def __on_edited_cell(self, widget, path, text):
        """ Update treerow when a cell has been edited

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        path : str
            Path identifying the edited cell
        text : str
            New text
        """

        self.model_ignores[path][0] = str(text)


    def __update_dialog(self, widget):
        """ Update dialog response sensitive status

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        status = True
        icon, tooltip = None, None

        # ------------------------------------
        #   Console name
        # ------------------------------------

        name = self.entry_name.get_text()

        if len(name) == 0:
            status = False

        else:
            # Always check identifier to avoid NES != NeS
            identifier = generate_identifier(name)

            if identifier in self.api.consoles and (not self.modify or (
                self.modify and not name == self.console.name)):

                status = False

                icon = Icons.Error
                tooltip = _(
                    "This console already exist, please, choose another name")

        self.entry_name.set_icon_from_icon_name(
            Gtk.EntryIconPosition.PRIMARY, icon)
        self.entry_name.set_tooltip_text(tooltip)

        # ------------------------------------
        #   Console roms folder
        # ------------------------------------

        path = self.file_folder.get_filename()

        if path is None or not exists(expanduser(path)):
            status = False

        # ------------------------------------
        #   Console emulator
        # ------------------------------------

        # emulator = self.api.get_emulator(self.combo_emulators.get_active_id())

        # Allow to validate dialog if selected emulator binary exist
        # if emulator is None or emulator.binary is None or not emulator.exists:
            # status = False

        # ------------------------------------
        #   Start dialog
        # ------------------------------------

        self.set_response_sensitive(Gtk.ResponseType.APPLY, status)


class PreferencesEmulator(CommonWindow):

    def __init__(self, parent, emulator, modify):
        """ Constructor

        Parameters
        ----------
        parent : Gtk.Window
            Parent object (Default: None)
        emulator : gem.api.Emulator
            Emulator object
        modify : bool
            Use edit mode instead of append mode
        """

        CommonWindow.__init__(self, parent, _("Emulator"), Icons.Desktop,
            parent.use_classic_theme)

        # ------------------------------------
        #   Initialize variables
        # ------------------------------------

        # GEM API instance
        self.api = parent.api
        # Emulator object
        self.emulator = emulator

        self.path = None

        self.error = False

        self.interface = parent
        self.modify = modify

        # Empty Pixbuf icon
        self.empty = parent.empty

        self.help_data = {
            "order": [
                _("Description"),
                _("Parameters"),
            ],
            _("Description"): [
                _("To facilitate file detection with every emulators, some "
                    "custom parameters have been created."),
                _("This parameters are used in \"Default options\", \"Save\" "
                    "and \"Snapshots\" entries."),
            ],
            _("Parameters"): {
                "<key>": _("Use game key"),
                "<name>": _("Use ROM filename"),
                "<lname>": _("Use ROM lowercase filename"),
                "<rom_path>": _("Use ROM folder path"),
                "<rom_file>": _("Use ROM file path"),
                "<conf_path>": _("Use emulator configuration file path"),
            }
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


    def __init_widgets(self):
        """ Initialize interface widgets
        """

        self.set_size(640, -1)

        self.set_resizable(True)

        # ------------------------------------
        #   Grids
        # ------------------------------------

        self.grid_preferences = Gtk.Grid()

        self.grid_binary = Gtk.Box()

        # Properties
        self.grid_preferences.set_row_spacing(6)
        self.grid_preferences.set_column_spacing(12)
        self.grid_preferences.set_column_homogeneous(False)

        Gtk.StyleContext.add_class(
            self.grid_binary.get_style_context(), "linked")

        # ------------------------------------
        #   Emulator
        # ------------------------------------

        self.label_name = Gtk.Label()
        self.entry_name = Gtk.Entry()

        self.label_binary = Gtk.Label()
        self.entry_binary = Gtk.Entry()

        self.button_binary = Gtk.Button()
        self.image_binary = Gtk.Image()

        self.button_emulator = Gtk.Button()
        self.image_emulator = Gtk.Image()

        # Properties
        self.label_name.set_alignment(1, 0.5)
        self.label_name.set_halign(Gtk.Align.END)
        self.label_name.set_justify(Gtk.Justification.RIGHT)
        self.label_name.get_style_context().add_class("dim-label")
        self.label_name.set_text(
            _("Name"))

        self.entry_name.set_hexpand(True)
        self.entry_name.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, Icons.Symbolic.Clear)

        self.label_binary.set_alignment(1, 0.5)
        self.label_binary.set_halign(Gtk.Align.END)
        self.label_binary.set_justify(Gtk.Justification.RIGHT)
        self.label_binary.get_style_context().add_class("dim-label")
        self.label_binary.set_text(
            _("Binary"))

        self.entry_binary.set_hexpand(True)
        self.entry_binary.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, Icons.Symbolic.Clear)

        self.image_binary.set_from_icon_name(
            Icons.Symbolic.Open, Gtk.IconSize.MENU)

        self.button_emulator.set_size_request(64, 64)
        self.image_emulator.set_size_request(64, 64)

        # ------------------------------------
        #   Emulator - Configuration
        # ------------------------------------

        self.label_configuration = Gtk.Label()

        self.file_configuration = Gtk.FileChooserButton()

        # Properties
        self.label_configuration.set_alignment(1, 0.5)
        self.label_configuration.set_halign(Gtk.Align.END)
        self.label_configuration.set_justify(Gtk.Justification.RIGHT)
        self.label_configuration.get_style_context().add_class("dim-label")
        self.label_configuration.set_text(
            _("Configuration file"))

        self.file_configuration.set_hexpand(True)

        # ------------------------------------
        #   Emulator - Arguments
        # ------------------------------------

        self.label_arguments = Gtk.Label()

        self.label_launch = Gtk.Label()
        self.entry_launch = Gtk.Entry()

        self.label_windowed = Gtk.Label()
        self.entry_windowed = Gtk.Entry()

        self.label_fullscreen = Gtk.Label()
        self.entry_fullscreen = Gtk.Entry()

        # Properties
        self.label_arguments.set_margin_top(18)
        self.label_arguments.set_hexpand(True)
        self.label_arguments.set_use_markup(True)
        self.label_arguments.set_halign(Gtk.Align.CENTER)
        self.label_arguments.set_markup(
            "<b>%s</b>" % _("Emulator arguments"))

        self.label_launch.set_alignment(1, 0.5)
        self.label_launch.set_halign(Gtk.Align.END)
        self.label_launch.set_justify(Gtk.Justification.RIGHT)
        self.label_launch.get_style_context().add_class("dim-label")
        self.label_launch.set_label(
            _("Default options"))

        self.entry_launch.set_hexpand(True)
        self.entry_launch.set_placeholder_text(
            _("Default arguments to add when launch emulator"))
        self.entry_launch.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, Icons.Symbolic.Clear)

        self.label_windowed.set_alignment(1, 0.5)
        self.label_windowed.set_halign(Gtk.Align.END)
        self.label_windowed.set_justify(Gtk.Justification.RIGHT)
        self.label_windowed.get_style_context().add_class("dim-label")
        self.label_windowed.set_label(
            _("Windowed"))

        self.entry_windowed.set_placeholder_text(
            _("Argument which activate windowded mode"))
        self.entry_windowed.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, Icons.Symbolic.Clear)

        self.label_fullscreen.set_alignment(1, 0.5)
        self.label_fullscreen.set_halign(Gtk.Align.END)
        self.label_fullscreen.set_justify(Gtk.Justification.RIGHT)
        self.label_fullscreen.get_style_context().add_class("dim-label")
        self.label_fullscreen.set_label(
            _("Fullscreen"))

        self.entry_fullscreen.set_hexpand(True)
        self.entry_fullscreen.set_placeholder_text(
            _("Argument which activate fullscreen mode"))
        self.entry_fullscreen.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, Icons.Symbolic.Clear)

        # ------------------------------------
        #   Emulator - Files pattern
        # ------------------------------------

        self.label_files = Gtk.Label()

        self.label_save = Gtk.Label()
        self.entry_save = Gtk.Entry()

        self.label_screenshots = Gtk.Label()
        self.entry_screenshots = Gtk.Entry()

        self.label_joker = Gtk.Label()

        # Properties
        self.label_files.set_margin_top(18)
        self.label_files.set_hexpand(True)
        self.label_files.set_use_markup(True)
        self.label_files.set_halign(Gtk.Align.CENTER)
        self.label_files.set_markup(
            "<b>%s</b>" % _("Files patterns"))

        self.label_save.set_alignment(1, 0.5)
        self.label_save.set_halign(Gtk.Align.END)
        self.label_save.set_justify(Gtk.Justification.RIGHT)
        self.label_save.get_style_context().add_class("dim-label")
        self.label_save.set_label(
            _("Save"))

        self.entry_save.set_hexpand(True)
        self.entry_save.set_placeholder_text(
            _("Pattern to detect savestates files"))
        self.entry_save.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, Icons.Symbolic.Clear)

        self.label_screenshots.set_alignment(1, 0.5)
        self.label_screenshots.set_halign(Gtk.Align.END)
        self.label_screenshots.set_justify(Gtk.Justification.RIGHT)
        self.label_screenshots.get_style_context().add_class("dim-label")
        self.label_screenshots.set_label(
            _("Snapshots"))

        self.entry_screenshots.set_hexpand(True)
        self.entry_screenshots.set_placeholder_text(
            _("Pattern to detect screenshots files"))
        self.entry_screenshots.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, Icons.Symbolic.Clear)

        self.label_joker.set_use_markup(True)
        self.label_joker.set_alignment(1, 0.5)
        self.label_joker.set_halign(Gtk.Align.END)
        self.label_joker.set_justify(Gtk.Justification.RIGHT)
        self.label_joker.get_style_context().add_class("dim-label")
        self.label_joker.set_markup(
            "<i>%s</i>" % _("* can be used as joker"))


    def __init_packing(self):
        """ Initialize widgets packing in main window
        """

        # Main widgets
        self.pack_start(self.grid_preferences, True, True)

        # Emulator grid
        self.grid_preferences.attach(self.label_name, 0, 0, 1, 1)
        self.grid_preferences.attach(self.entry_name, 1, 0, 1, 1)

        self.grid_preferences.attach(self.label_binary, 0, 1, 1, 1)
        self.grid_preferences.attach(self.grid_binary, 1, 1, 1, 1)

        self.grid_preferences.attach(self.button_emulator, 2, 0, 1, 2)

        self.grid_preferences.attach(self.label_configuration, 0, 2, 1, 1)
        self.grid_preferences.attach(self.file_configuration, 1, 2, 2, 1)

        self.grid_preferences.attach(self.label_arguments, 0, 4, 3, 1)

        self.grid_preferences.attach(self.label_launch, 0, 5, 1, 1)
        self.grid_preferences.attach(self.entry_launch, 1, 5, 2, 1)

        self.grid_preferences.attach(self.label_windowed, 0, 6, 1, 1)
        self.grid_preferences.attach(self.entry_windowed, 1, 6, 2, 1)
        self.grid_preferences.attach(self.label_fullscreen, 0, 7, 1, 1)
        self.grid_preferences.attach(self.entry_fullscreen, 1, 7, 2, 1)

        self.grid_preferences.attach(self.label_files, 0, 8, 3, 1)

        self.grid_preferences.attach(self.label_save, 0, 9, 1, 1)
        self.grid_preferences.attach(self.entry_save, 1, 9, 2, 1)
        self.grid_preferences.attach(self.label_screenshots, 0, 10, 1, 1)
        self.grid_preferences.attach(self.entry_screenshots, 1, 10, 2, 1)

        self.grid_preferences.attach(self.label_joker, 0, 11, 3, 1)

        # Emulator options
        self.button_binary.set_image(self.image_binary)

        self.button_emulator.set_image(self.image_emulator)

        # Emulator binary
        self.grid_binary.pack_start(self.entry_binary, True, True, 0)
        self.grid_binary.pack_start(self.button_binary, False, False, 0)


    def __init_signals(self):
        """ Initialize widgets signals
        """

        self.entry_name.connect("changed", self.__on_entry_update)
        self.entry_name.connect("icon-press", on_entry_clear)

        self.entry_binary.connect("changed", self.__on_entry_update)
        self.entry_binary.connect("icon-press", on_entry_clear)

        self.entry_launch.connect("icon-press", on_entry_clear)
        self.entry_windowed.connect("icon-press", on_entry_clear)
        self.entry_fullscreen.connect("icon-press", on_entry_clear)

        self.entry_save.connect("icon-press", on_entry_clear)
        self.entry_screenshots.connect("icon-press", on_entry_clear)

        self.button_emulator.connect("clicked", self.__on_select_icon)
        self.button_binary.connect("clicked", self.__on_file_set)


    def __start_interface(self):
        """ Load data and start interface
        """

        self.add_button(_("Close"), Gtk.ResponseType.CLOSE)
        self.add_button(_("Apply"), Gtk.ResponseType.APPLY, Gtk.Align.END)

        self.add_help(self.help_data)

        self.set_response_sensitive(Gtk.ResponseType.APPLY, False)

        # ------------------------------------
        #   Init data
        # ------------------------------------

        if self.modify:
            self.entry_name.set_text(self.emulator.name)

            # Binary
            self.entry_binary.set_text(self.emulator.binary)

            # Configuration
            folder = self.emulator.configuration
            if folder is not None and exists(folder):
                self.file_configuration.set_filename(folder)

            # Icon
            self.path = self.emulator.icon
            self.image_emulator.set_from_pixbuf(
                icon_from_data(self.path, self.empty, 64, 64, "emulators"))

            # Regex
            if self.emulator.savestates is not None:
                self.entry_save.set_text(self.emulator.savestates)
            if self.emulator.screenshots is not None:
                self.entry_screenshots.set_text(self.emulator.screenshots)

            # Arguments
            if self.emulator.default is not None:
                self.entry_launch.set_text(self.emulator.default)
            if self.emulator.windowed is not None:
                self.entry_windowed.set_text(self.emulator.windowed)
            if self.emulator.fullscreen is not None:
                self.entry_fullscreen.set_text(self.emulator.fullscreen)

            self.set_response_sensitive(Gtk.ResponseType.APPLY, True)

        # ------------------------------------
        #   Start dialog
        # ------------------------------------

        need_reload = False

        response = self.run()

        # Save emulator
        if response == Gtk.ResponseType.APPLY:
            self.__on_save_data()

            if self.data is not None:
                if self.modify:
                    # Store identifier for rename function
                    previous_identifier = self.emulator.id

                    self.api.delete_emulator(self.emulator.id)

                # Append a new emulator
                self.api.add_emulator(self.data)

                # This emulator has been renamed
                if self.modify and not self.data["id"] == previous_identifier:
                    self.api.rename_emulator(
                        previous_identifier, self.data["id"])

            need_reload = True

        self.destroy()

        if need_reload:
            self.interface.on_load_emulators()


    def __on_save_data(self):
        """ Return all the data from interface
        """

        self.section = self.entry_name.get_text()

        identifier = None
        if len(self.section) > 0:
            identifier = generate_identifier(self.section)

        binary = self.entry_binary.get_text()
        if binary is None:
            binary = str()

        icon = self.path
        if icon is not None and path_join(
            get_data("icons"), basename(icon)) == icon:

            icon = splitext(basename(icon))[0]

        configuration = self.file_configuration.get_filename()
        if configuration is None or not exists(configuration):
            configuration = None

        savestates = self.entry_save.get_text()
        if len(savestates) == 0:
            savestates = None

        screenshots = self.entry_screenshots.get_text()
        if len(screenshots) == 0:
            screenshots = None

        default = self.entry_launch.get_text()
        if len(default) == 0:
            default = None

        windowed = self.entry_windowed.get_text()
        if len(windowed) == 0:
            windowed = None

        fullscreen = self.entry_fullscreen.get_text()
        if len(fullscreen) == 0:
            fullscreen = None

        self.data = {
            "id": identifier,
            "name": self.section,
            "binary": binary,
            "icon": icon,
            "configuration": configuration,
            "savestates": savestates,
            "screenshots": screenshots,
            "default": default,
            "windowed": windowed,
            "fullscreen": fullscreen
        }


    def __on_entry_update(self, widget):
        """ Check if a value is not already used

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        self.error = False

        # ------------------------------------
        #   Emulator name
        # ------------------------------------

        icon = None
        tooltip = None

        name = self.entry_name.get_text()

        if name is None or len(name) == 0:
            self.error = True

        else:
            # Always check identifier to avoid NES != NeS
            identifier = generate_identifier(name)

            if identifier in self.api.emulators and (not self.modify or (
                self.modify and not name == self.emulator.name)):

                status = False

                icon = Icons.Error
                tooltip = _(
                    "This emulator already exist, please, choose another name")

        if widget == self.entry_name:
            self.entry_name.set_icon_from_icon_name(
                Gtk.EntryIconPosition.PRIMARY, icon)
            self.entry_name.set_tooltip_text(tooltip)

        # ------------------------------------
        #   Emulator binary
        # ------------------------------------

        icon = None
        tooltip = None

        path = self.entry_binary.get_text()

        if path is None or len(path) == 0:
            self.error = True

        elif len(get_binary_path(path)) == 0:
            self.error = True

            icon = Icons.Error
            tooltip = _("This binary not exist, please, check the path")

        if widget == self.entry_binary:
            self.entry_binary.set_icon_from_icon_name(
                Gtk.EntryIconPosition.PRIMARY, icon)
            self.entry_binary.set_tooltip_text(tooltip)

        # ------------------------------------
        #   Manage error
        # ------------------------------------

        if not self.error:
            self.set_response_sensitive(Gtk.ResponseType.APPLY, True)

        else:
            self.set_response_sensitive(Gtk.ResponseType.APPLY, False)


    def __on_file_set(self, widget):
        """ Change response button state when user set a file

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        dialog = Gtk.FileChooserDialog(_("Select a binary"),
            self.interface.window, Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK),
            use_header_bar=not self.use_classic_theme)

        if dialog.run() == Gtk.ResponseType.OK:
            self.entry_binary.set_text(dialog.get_filename())

        dialog.destroy()


    def __on_select_icon(self, widget):
        """ Select a new icon
        """

        dialog = IconViewer(self, _("Choose an icon"), self.path, "emulators")

        if dialog.new_path is not None:
            self.image_emulator.set_from_pixbuf(icon_from_data(
                dialog.new_path, self.empty, 64, 64, "emulators"))

            self.path = dialog.new_path

        dialog.destroy()


class IconViewer(CommonWindow):

    def __init__(self, parent, title, path, folder):
        """ Constructor

        Parameters
        ----------
        parent : Gtk.Window
            Parent object
        title : str
            Window title
        path : str
            Selected icon path
        folder : str
            Icons folder
        """

        CommonWindow.__init__(self, parent, title, Icons.Image,
            parent.use_classic_theme)

        # ------------------------------------
        #   Variables
        # ------------------------------------

        self.path = path
        self.new_path = None

        self.folder = folder

        if parent is None:
            self.empty = Pixbuf(Colorspace.RGB, True, 8, 24, 24)
            self.empty.fill(0x00000000)
        else:
            self.empty = parent.empty

        # ------------------------------------
        #   Initialization
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

        self.set_size(800, 600)

        self.set_spacing(6)
        self.set_border_width(6)

        # ------------------------------------
        #   Grid
        # ------------------------------------

        self.stack = Gtk.Stack()
        self.stack_switcher = Gtk.StackSwitcher()

        # Properties
        self.stack.set_transition_type(Gtk.StackTransitionType.NONE)

        self.stack_switcher.set_stack(self.stack)
        self.stack_switcher.set_halign(Gtk.Align.CENTER)

        # ------------------------------------
        #   Custom
        # ------------------------------------

        self.frame_icons = Gtk.Frame()

        self.file_icons = Gtk.FileChooserWidget.new(Gtk.FileChooserAction.OPEN)

        # Properties
        self.frame_icons.set_shadow_type(Gtk.ShadowType.OUT)

        self.file_icons.set_hexpand(True)
        self.file_icons.set_vexpand(True)
        self.file_icons.set_current_folder(expanduser('~'))

        # ------------------------------------
        #   Icons
        # ------------------------------------

        self.view_icons = Gtk.IconView()
        self.model_icons = Gtk.ListStore(Pixbuf, str)

        self.scroll_icons = Gtk.ScrolledWindow()

        # Properties
        self.view_icons.set_model(self.model_icons)
        self.view_icons.set_pixbuf_column(0)
        self.view_icons.set_tooltip_column(1)
        # self.view_icons.set_item_width(96)
        self.view_icons.set_selection_mode(Gtk.SelectionMode.SINGLE)

        self.model_icons.set_sort_column_id(1, Gtk.SortType.ASCENDING)

        self.scroll_icons.set_hexpand(True)
        self.scroll_icons.set_vexpand(True)
        self.scroll_icons.set_shadow_type(Gtk.ShadowType.OUT)
        self.scroll_icons.set_policy(
            Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        # ------------------------------------
        #   Add widgets into interface
        # ------------------------------------

        self.stack.add_titled(self.scroll_icons, "library", _("Library"))

        self.scroll_icons.add(self.view_icons)

        self.stack.add_titled(self.frame_icons, "file", _("File"))

        self.frame_icons.add(self.file_icons)

        self.pack_start(self.stack_switcher, False, False)
        self.pack_start(self.stack, True, True)


    def __init_signals(self):
        """ Initialize widgets signals
        """

        self.file_icons.connect("file-activated", self.__on_selected_icon)

        self.view_icons.connect("item-activated", self.__on_selected_icon)


    def __start_interface(self):
        """ Load data and start interface
        """

        self.add_button(_("Close"), Gtk.ResponseType.CLOSE)
        self.add_button(_("Apply"), Gtk.ResponseType.APPLY, Gtk.Align.END)

        self.load_interface()

        response = self.run()

        if response == Gtk.ResponseType.APPLY:
            self.save_interface()


    def __on_selected_icon(self, widget, path=None):
        """ Select an icon in treeview

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal

        Others Parameters
        -----------------
        path : Gtk.TreePath
            Path to be activated
        """

        self.emit_response(None, Gtk.ResponseType.APPLY)


    def load_interface(self):
        """ Insert data into interface's widgets
        """

        self.icons_data = dict()

        # Fill icons view
        for icon in \
            glob(path_join(GEM.Local, "icons", self.folder, "*.png")):
            name = splitext(basename(icon))[0]

            self.icons_data[name] = self.model_icons.append([
                icon_from_data(icon, self.empty, 72, 72, self.folder), name])

        # Set filechooser or icons view selected item
        if self.path is not None:

            # Check if current path is a gem icons
            data = path_join(
                GEM.Local, "icons", self.folder, self.path + ".png")

            if data is not None and exists(data):
                self.view_icons.select_path(
                    self.model_icons.get_path(self.icons_data[self.path]))

            else:
                self.frame_icons.show()
                self.stack.set_visible_child(self.frame_icons)

                self.file_icons.set_filename(self.path)


    def save_interface(self):
        """ Return all the data from interface
        """

        if self.stack.get_visible_child_name() == "library":
            selection = self.view_icons.get_selected_items()[0]

            path = self.model_icons.get_value(
                self.model_icons.get_iter(selection), 1)

        else:
            path = self.file_icons.get_filename()

        if not path == self.path:
            self.new_path = path
