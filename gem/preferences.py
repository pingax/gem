# ------------------------------------------------------------------
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
# ------------------------------------------------------------------

# ------------------------------------------------------------------
#   Modules
# ------------------------------------------------------------------

# Path
from os.path import exists
from os.path import basename
from os.path import splitext
from os.path import expanduser
from os.path import join as path_join

from glob import glob

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

    from gi.repository.GdkPixbuf import Pixbuf
    from gi.repository.GdkPixbuf import Colorspace

except ImportError as error:
    sys_exit("Import error with python3-gobject module: %s" % str(error))

# ------------------------------------------------------------------
#   Modules - GEM
# ------------------------------------------------------------------

try:
    from gem import *
    from gem.utils import *
    from gem.windows import *
    from gem.configuration import Configuration

except ImportError as error:
    sys_exit("Import error with gem module: %s" % str(error))

# ------------------------------------------------------------------
#   Translation
# ------------------------------------------------------------------

bindtextdomain("gem", get_data("i18n"))
textdomain("gem")

# ------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------

class Manager(object):
    CONSOLE  = 0
    EMULATOR = 1


class Preferences(object):

    def __init__(self, parent=None, logger=None):
        """ Constructor

        Other Parameters
        ----------------
        parent : Gtk.Window
            Parent object (Default: None)
        logger : logging.Logger
            Output logger (Default: None)
        """

        # ------------------------------------
        #   Initialize variables
        # ------------------------------------

        self.interface = parent

        self.shortcuts = {
            _("Interface"): {
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
                "snapshots": [
                    _("Show game snapshots"), "F5"],
                "log": [
                    _("Open game log"), "F6"],
                "notes": [
                    _("Open game notes"), "F7"] },
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

        self.selection = {
            "console": None,
            "emulator": None }

        # ------------------------------------
        #   Initialize configuration files
        # ------------------------------------

        if self.interface is not None:
            self.config = self.interface.config
            self.consoles = self.interface.consoles
            self.emulators = self.interface.emulators

            # Get user icon theme
            self.icons_theme = self.interface.icons_theme

            self.empty = self.interface.empty

        else:
            self.config = Configuration(
                expanduser(path_join(Path.User, "gem.conf")))
            self.consoles = Configuration(
                expanduser(path_join(Path.User, "consoles.conf")))
            self.emulators = Configuration(
                expanduser(path_join(Path.User, "emulators.conf")))

            # Get user icon theme
            self.icons_theme = Gtk.IconTheme.get_default()

            self.icons_theme.append_search_path(
                get_data(path_join("icons", "ui")))

            # HACK: Create an empty image to avoid g_object_set_qdata warning
            self.empty = Pixbuf.new(Colorspace.RGB, True, 8, 24, 24)
            self.empty.fill(0x00000000)

            # Set light/dark theme
            on_change_theme(self.config.getboolean(
                "gem", "dark_theme", fallback=False))

        # ------------------------------------
        #   Initialize logger
        # ------------------------------------

        self.logger = logger

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

        # ------------------------------------
        #   Main window
        # ------------------------------------

        # Gtk.Window
        if self.interface is None:
            self.window = Gtk.Window()

            self.grid = Gtk.Box()

            # Packing
            self.window.add(self.grid)

        # Gtk.Dialog
        else:
            self.window = Gtk.Dialog()

            self.grid = self.window.get_content_area()

            # Properties
            self.window.set_modal(True)
            self.window.set_destroy_with_parent(True)

            self.window.set_transient_for(self.interface)

        # Properties
        self.window.set_title(_("Preferences"))

        self.window.set_default_icon_name(Icons.Desktop)

        self.window.set_can_focus(True)
        self.window.set_keep_above(True)

        self.grid.set_border_width(0)
        self.grid.set_orientation(Gtk.Orientation.VERTICAL)

        try:
            width, height = self.config.get(
                "windows", "preferences", fallback="800x600").split('x')

            self.window.set_default_size(int(width), int(height))
            self.window.resize(int(width), int(height))

        except ValueError as error:
            self.logger.error(
                _("Cannot resize preferences window: %s") % str(error))

            self.window.set_default_size(800, 600)

        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.set_type_hint(Gdk.WindowTypeHint.DIALOG)

        # ------------------------------------
        #   Grids
        # ------------------------------------

        self.grid_buttons = Gtk.ButtonBox()

        self.box_notebook_general = Gtk.Box()
        self.box_notebook_interface = Gtk.Box()
        self.box_notebook_shortcuts = Gtk.Box()
        self.box_notebook_consoles = Gtk.Box()
        self.box_notebook_emulators = Gtk.Box()

        self.grid_general = Gtk.Grid()
        self.grid_interface = Gtk.Grid()
        self.grid_shortcuts = Gtk.Grid()
        self.grid_consoles = Gtk.Grid()
        self.grid_emulators = Gtk.Grid()

        self.grid_consoles_buttons = Gtk.ButtonBox()
        self.grid_emulators_buttons = Gtk.ButtonBox()

        # Properties
        self.grid_buttons.set_spacing(8)
        self.grid_buttons.set_border_width(8)
        self.grid_buttons.set_layout(Gtk.ButtonBoxStyle.END)

        self.box_notebook_general.set_spacing(8)
        self.box_notebook_interface.set_spacing(8)
        self.box_notebook_shortcuts.set_spacing(8)
        self.box_notebook_consoles.set_spacing(8)
        self.box_notebook_emulators.set_spacing(8)

        self.grid_general.set_row_spacing(8)
        self.grid_general.set_column_spacing(8)
        self.grid_general.set_border_width(16)
        self.grid_general.set_column_homogeneous(False)

        self.grid_interface.set_row_spacing(8)
        self.grid_interface.set_column_spacing(8)
        self.grid_interface.set_border_width(16)
        self.grid_interface.set_column_homogeneous(False)

        self.grid_shortcuts.set_row_spacing(8)
        self.grid_shortcuts.set_column_spacing(8)
        self.grid_shortcuts.set_border_width(16)
        self.grid_shortcuts.set_column_homogeneous(False)

        self.grid_consoles.set_row_spacing(8)
        self.grid_consoles.set_column_spacing(8)
        self.grid_consoles.set_border_width(16)
        self.grid_consoles.set_column_homogeneous(False)

        self.grid_emulators.set_row_spacing(8)
        self.grid_emulators.set_column_spacing(8)
        self.grid_emulators.set_border_width(16)
        self.grid_emulators.set_column_homogeneous(False)

        self.grid_consoles_buttons.set_spacing(4)
        self.grid_consoles_buttons.set_layout(Gtk.ButtonBoxStyle.CENTER)

        self.grid_emulators_buttons.set_spacing(4)
        self.grid_emulators_buttons.set_layout(Gtk.ButtonBoxStyle.CENTER)

        # ------------------------------------
        #   Headerbar
        # ------------------------------------

        self.headerbar = Gtk.HeaderBar()

        # Properties
        self.headerbar.set_title(_("Preferences"))
        self.headerbar.set_show_close_button(True)

        if self.interface is None:
            self.headerbar.set_subtitle(
                "%s - %s (%s)" % (Gem.Name, Gem.Version, Gem.CodeName))

        # ------------------------------------
        #   Header
        # ------------------------------------

        self.image_header = Gtk.Image()

        # Properties
        self.image_header.set_from_icon_name(Icons.Desktop, Gtk.IconSize.DND)

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

        self.check_last_console = Gtk.CheckButton()
        self.check_hide_console = Gtk.CheckButton()

        # Properties
        self.label_behavior.set_markup("<b>%s</b>" % _("Behavior"))
        self.label_behavior.set_use_markup(True)
        self.label_behavior.set_alignment(0, .5)

        self.check_last_console.set_hexpand(True)
        self.check_last_console.set_margin_left(32)
        self.check_last_console.set_label(
            _("Load the last chosen console during startup"))
        self.check_hide_console.set_hexpand(True)
        self.check_hide_console.set_margin_left(32)
        self.check_hide_console.set_label(_("Hide consoles whitout any game"))

        # ------------------------------------
        #   General - Viewer
        # ------------------------------------

        self.label_viewer = Gtk.Label()

        self.label_viewer_binary = Gtk.Label()
        self.label_viewer_options = Gtk.Label()

        self.check_native_viewer = Gtk.CheckButton()

        self.file_viewer_binary = Gtk.FileChooserButton()

        self.entry_viewer_options = Gtk.Entry()

        self.separator_viewer = Gtk.Separator()

        # Properties
        self.label_viewer.set_markup("<b>%s</b>" % _("Viewer"))
        self.label_viewer.set_use_markup(True)
        self.label_viewer.set_alignment(0, .5)

        self.label_viewer_binary.set_label(_("Binary"))
        self.label_viewer_binary.set_alignment(0, .5)
        self.label_viewer_binary.set_margin_left(32)
        self.label_viewer_options.set_label(_("Default options"))
        self.label_viewer_options.set_alignment(0, .5)
        self.label_viewer_options.set_margin_left(32)

        self.check_native_viewer.set_label(_("Use native viewer"))
        self.check_native_viewer.set_hexpand(True)
        self.check_native_viewer.set_margin_left(32)

        self.file_viewer_binary.set_hexpand(True)

        self.entry_viewer_options.set_hexpand(True)
        self.entry_viewer_options.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, Icons.Clear)

        self.separator_viewer.set_margin_left(32)

        # ------------------------------------
        #   Interface
        # ------------------------------------

        self.scroll_interface = Gtk.ScrolledWindow()
        self.view_interface = Gtk.Viewport()

        self.label_interface = Gtk.Label()

        self.check_classic_theme = Gtk.CheckButton()
        self.check_header = Gtk.CheckButton()
        self.check_icons = Gtk.CheckButton()

        # Properties
        self.label_interface.set_markup("<b>%s</b>" % _("Interface"))
        self.label_interface.set_use_markup(True)
        self.label_interface.set_alignment(0, .5)

        self.check_classic_theme.set_label(
            _("Use classic theme (Need to reboot GEM)"))
        self.check_classic_theme.set_hexpand(True)
        self.check_classic_theme.set_margin_left(32)
        self.check_header.set_label(
            _("Show close buttons in header bar"))
        self.check_header.set_hexpand(True)
        self.check_header.set_margin_left(32)
        self.check_icons.set_label(
            _("use translucent icons in games list instead of empty ones"))
        self.check_icons.set_hexpand(True)
        self.check_icons.set_margin_left(32)

        # ------------------------------------
        #   Interface - Games list
        # ------------------------------------

        self.label_treeview = Gtk.Label()
        self.label_treeview_lines = Gtk.Label()

        self.model_lines = Gtk.ListStore(str)
        self.combo_lines = Gtk.ComboBox()

        self.cell_lines = Gtk.CellRendererText()

        self.check_play = Gtk.CheckButton()
        self.check_last_play = Gtk.CheckButton()
        self.check_play_time = Gtk.CheckButton()
        self.check_installed = Gtk.CheckButton()
        self.check_flags = Gtk.CheckButton()

        self.separator_interface_game = Gtk.Separator()

        # Properties
        self.label_treeview.set_markup("<b>%s</b>" % _("Games list"))
        self.label_treeview.set_use_markup(True)
        self.label_treeview.set_alignment(0, .5)

        self.label_treeview_lines.set_label(_("Show lines in games list"))
        self.label_treeview_lines.set_hexpand(True)
        self.label_treeview_lines.set_margin_left(32)
        self.label_treeview_lines.set_alignment(0, .5)

        self.model_lines.set_sort_column_id(0, Gtk.SortType.ASCENDING)

        self.combo_lines.set_model(self.model_lines)
        self.combo_lines.set_id_column(0)
        self.combo_lines.pack_start(self.cell_lines, True)
        self.combo_lines.add_attribute(self.cell_lines, "text", 0)

        self.check_play.set_label(_("Show \"Launch\" column"))
        self.check_play.set_hexpand(True)
        self.check_play.set_margin_left(32)
        self.check_last_play.set_label(_("Show \"Last launch\" column"))
        self.check_last_play.set_hexpand(True)
        self.check_last_play.set_margin_left(32)
        self.check_play_time.set_label(_("Show \"Play time\" column"))
        self.check_play_time.set_hexpand(True)
        self.check_play_time.set_margin_left(32)
        self.check_installed.set_label(_("Show \"Installed\" column"))
        self.check_installed.set_hexpand(True)
        self.check_installed.set_margin_left(32)
        self.check_flags.set_label(_("Show \"Flags\" column"))
        self.check_flags.set_hexpand(True)
        self.check_flags.set_margin_left(32)

        self.separator_interface_game.set_hexpand(True)
        self.separator_interface_game.set_margin_left(32)

        # ------------------------------------
        #   Interface - Editor
        # ------------------------------------

        self.label_editor = Gtk.Label()
        self.label_editor_colorscheme = Gtk.Label()
        self.label_editor_font = Gtk.Label()

        self.check_lines = Gtk.CheckButton()

        self.model_colorsheme = Gtk.ListStore(str)
        self.combo_colorsheme = Gtk.ComboBox()

        self.cell_colorsheme = Gtk.CellRendererText()

        self.font_editor = Gtk.FontButton()
        self.separator_interface_editor = Gtk.Separator()

        # Properties
        self.label_editor.set_markup("<b>%s</b>" % _("Editor"))
        self.label_editor.set_use_markup(True)
        self.label_editor.set_alignment(0, .5)

        self.label_editor_colorscheme.set_label(_("Colorscheme"))
        self.label_editor_colorscheme.set_margin_left(32)
        self.label_editor_colorscheme.set_alignment(0, .5)

        self.label_editor_font.set_label(_("Font"))
        self.label_editor_font.set_margin_left(32)
        self.label_editor_font.set_alignment(0, .5)

        self.check_lines.set_label(_("Show line numbers"))
        self.check_lines.set_hexpand(True)
        self.check_lines.set_margin_left(32)

        self.combo_colorsheme.set_model(self.model_colorsheme)
        self.combo_colorsheme.set_id_column(0)
        self.combo_colorsheme.pack_start(self.cell_colorsheme, True)
        self.combo_colorsheme.add_attribute(self.cell_colorsheme, "text", 0)
        self.combo_colorsheme.set_hexpand(True)

        self.font_editor.set_hexpand(True)

        self.separator_interface_editor.set_hexpand(True)
        self.separator_interface_editor.set_margin_left(32)

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
        self.label_shortcuts.set_alignment(0, .5)

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

        self.cell_shortcuts_keys.set_property("editable", True)

        self.treeview_shortcuts.append_column(self.column_shortcuts_name)
        self.treeview_shortcuts.append_column(self.column_shortcuts_key)

        # ------------------------------------
        #   Consoles
        # ------------------------------------

        self.scroll_consoles = Gtk.ScrolledWindow()
        self.view_consoles = Gtk.Viewport()

        self.scroll_consoles_treeview = Gtk.ScrolledWindow()

        self.model_consoles = Gtk.ListStore(Pixbuf, str, str, Pixbuf)
        self.treeview_consoles = Gtk.TreeView()

        self.column_consoles_name = Gtk.TreeViewColumn()
        self.column_consoles_emulator = Gtk.TreeViewColumn()

        self.cell_consoles_icon = Gtk.CellRendererPixbuf()
        self.cell_consoles_name = Gtk.CellRendererText()
        self.cell_consoles_emulator = Gtk.CellRendererText()
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
        self.treeview_consoles.set_hexpand(True)
        self.treeview_consoles.set_vexpand(True)

        self.column_consoles_name.set_title(_("Console"))
        self.column_consoles_name.set_expand(True)
        self.column_consoles_name.set_spacing(8)

        self.column_consoles_emulator.set_title(_("ROMs path"))
        self.column_consoles_emulator.set_expand(True)
        self.column_consoles_emulator.set_spacing(8)

        self.column_consoles_name.pack_start(
            self.cell_consoles_icon, False)
        self.column_consoles_name.pack_start(
            self.cell_consoles_name, True)
        self.column_consoles_emulator.pack_start(
            self.cell_consoles_emulator, True)
        self.column_consoles_emulator.pack_start(
            self.cell_consoles_check, False)

        self.column_consoles_name.add_attribute(
            self.cell_consoles_icon, "pixbuf", 0)
        self.column_consoles_name.add_attribute(
            self.cell_consoles_name, "text", 1)
        self.column_consoles_emulator.add_attribute(
            self.cell_consoles_emulator, "text", 2)
        self.column_consoles_emulator.add_attribute(
            self.cell_consoles_check, "pixbuf", 3)

        self.treeview_consoles.append_column(self.column_consoles_name)
        self.treeview_consoles.append_column(self.column_consoles_emulator)

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

        self.model_emulators = Gtk.ListStore(
            Pixbuf, str, str, Pixbuf, Pango.Style)
        self.treeview_emulators = Gtk.TreeView()

        self.column_emulators_name = Gtk.TreeViewColumn()
        self.column_emulators_binary = Gtk.TreeViewColumn()

        self.cell_emulators_icon = Gtk.CellRendererPixbuf()
        self.cell_emulators_name = Gtk.CellRendererText()
        self.cell_emulators_binary = Gtk.CellRendererText()
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
        self.treeview_emulators.set_hexpand(True)
        self.treeview_emulators.set_vexpand(True)

        self.column_emulators_name.set_title(_("Emulator"))
        self.column_emulators_name.set_expand(True)
        self.column_emulators_name.set_spacing(8)

        self.column_emulators_binary.set_title(_("Binary"))
        self.column_emulators_binary.set_expand(True)
        self.column_emulators_binary.set_spacing(8)

        self.column_emulators_name.pack_start(
            self.cell_emulators_icon, False)
        self.column_emulators_name.pack_start(
            self.cell_emulators_name, True)
        self.column_emulators_binary.pack_start(
            self.cell_emulators_binary, True)
        self.column_emulators_binary.pack_start(
            self.cell_emulators_check, False)

        self.column_emulators_name.add_attribute(
            self.cell_emulators_icon, "pixbuf", 0)
        self.column_emulators_name.add_attribute(
            self.cell_emulators_name, "text", 1)
        self.column_emulators_binary.add_attribute(
            self.cell_emulators_binary, "text", 2)
        self.column_emulators_binary.add_attribute(
            self.cell_emulators_check, "pixbuf", 3)

        self.treeview_emulators.append_column(self.column_emulators_name)
        self.treeview_emulators.append_column(self.column_emulators_binary)

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

        # ------------------------------------
        #   Buttons
        # ------------------------------------

        self.image_cancel = Gtk.Image()
        self.button_cancel = Gtk.Button()

        self.image_save = Gtk.Image()
        self.button_save = Gtk.Button()

        # Properties
        self.image_cancel.set_margin_right(4)
        self.image_cancel.set_from_icon_name(
            Icons.Stop, Gtk.IconSize.BUTTON)
        self.button_cancel.set_image(self.image_cancel)
        self.button_cancel.set_label(_("Cancel"))

        self.image_save.set_margin_right(4)
        self.image_save.set_from_icon_name(
            Icons.Save, Gtk.IconSize.BUTTON)
        self.button_save.set_image(self.image_save)
        self.button_save.set_label(_("Save"))


    def __init_packing(self):
        """ Initialize widgets packing in main window
        """

        self.window.set_titlebar(self.headerbar)

        # Main widgets
        self.grid.pack_start(self.notebook, True, True, 0)
        self.grid.pack_start(self.grid_buttons, False, False, 0)

        # Headerbar
        self.headerbar.pack_start(self.image_header)

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
        self.grid_general.attach(self.label_behavior, 0, 0, 2, 1)
        self.grid_general.attach(self.check_last_console, 0, 1, 2, 1)
        self.grid_general.attach(self.check_hide_console, 0, 2, 2, 1)

        self.grid_general.attach(self.label_viewer, 0, 4, 2, 1)
        self.grid_general.attach(self.check_native_viewer, 0, 5, 2, 1)
        self.grid_general.attach(self.separator_viewer, 0, 6, 2, 1)
        self.grid_general.attach(self.label_viewer_binary, 0, 7, 1, 1)
        self.grid_general.attach(self.file_viewer_binary, 1, 7, 1, 1)
        self.grid_general.attach(self.label_viewer_options, 0, 8, 1, 1)
        self.grid_general.attach(self.entry_viewer_options, 1, 8, 1, 1)

        self.view_general.add(self.grid_general)

        self.scroll_general.add(self.view_general)

        # Interface tab
        self.grid_interface.attach(self.label_interface, 0, 0, 3, 1)
        self.grid_interface.attach(self.check_classic_theme, 0, 1, 3, 1)
        self.grid_interface.attach(self.check_header, 0, 2, 3, 1)
        self.grid_interface.attach(self.check_icons, 0, 3, 3, 1)

        self.grid_interface.attach(self.label_treeview, 0, 5, 3, 1)
        self.grid_interface.attach(self.label_treeview_lines, 0, 6, 2, 1)
        self.grid_interface.attach(self.combo_lines, 2, 6, 1, 1)
        self.grid_interface.attach(self.separator_interface_game, 0, 7, 3, 1)
        self.grid_interface.attach(self.check_play, 0, 8, 3, 1)
        self.grid_interface.attach(self.check_last_play, 0, 9, 3, 1)
        self.grid_interface.attach(self.check_play_time, 0, 10, 3, 1)
        self.grid_interface.attach(self.check_installed, 0, 11, 3, 1)
        self.grid_interface.attach(self.check_flags, 0, 12, 3, 1)

        self.grid_interface.attach(self.label_editor, 0, 14, 3, 1)
        self.grid_interface.attach(self.check_lines, 0, 15, 3, 1)
        self.grid_interface.attach(self.separator_interface_editor, 0, 16, 3, 1)
        self.grid_interface.attach(self.label_editor_colorscheme, 0, 17, 1, 1)
        self.grid_interface.attach(self.combo_colorsheme, 1, 17, 2, 1)
        self.grid_interface.attach(self.label_editor_font, 0, 18, 1, 1)
        self.grid_interface.attach(self.font_editor, 1, 18, 2, 1)

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

        self.grid_consoles_buttons.pack_end(
            self.button_consoles_add, False, False, 0)
        self.grid_consoles_buttons.pack_end(
            self.button_consoles_modify, False, False, 0)
        self.grid_consoles_buttons.pack_end(
            self.button_consoles_remove, False, False, 0)

        self.scroll_consoles_treeview.add(self.treeview_consoles)

        self.view_consoles.add(self.grid_consoles)

        self.scroll_consoles.add(self.view_consoles)

        # Emulators tab
        self.grid_emulators.attach(self.scroll_emulators_treeview, 0, 0, 1, 1)
        self.grid_emulators.attach(self.grid_emulators_buttons, 0, 1, 1, 1)

        self.grid_emulators_buttons.pack_end(
            self.button_emulators_add, False, False, 0)
        self.grid_emulators_buttons.pack_end(
            self.button_emulators_modify, False, False, 0)
        self.grid_emulators_buttons.pack_end(
            self.button_emulators_remove, False, False, 0)

        self.scroll_emulators_treeview.add(self.treeview_emulators)

        self.view_emulators.add(self.grid_emulators)

        self.scroll_emulators.add(self.view_emulators)

        # Buttons
        self.grid_buttons.pack_end(self.button_cancel, False, False, 0)
        self.grid_buttons.pack_end(self.button_save, False, False, 0)


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

        self.check_native_viewer.connect("toggled",
            self.__on_check_native_viewer)

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

        # ------------------------------------
        #   Buttons
        # ------------------------------------

        self.button_cancel.connect(
            "clicked", self.__stop_interface)
        self.button_save.connect(
            "clicked", self.__stop_interface)


    def __start_interface(self):
        """ Load data and start interface
        """

        self.load_configuration()

        self.window.hide()
        self.window.unrealize()


    def start(self):
        """ Start interface
        """

        self.window.show_all()

        self.box_notebook_general.show_all()
        self.box_notebook_interface.show_all()
        self.box_notebook_shortcuts.show_all()
        self.box_notebook_consoles.show_all()
        self.box_notebook_emulators.show_all()

        if self.interface is None:
            Gtk.main()

        else:
            self.window.run()


    def __stop_interface(self, widget=None, event=None):
        """ Save data and stop interface

        Other Parameters
        ----------------
        widget : Gtk.Widget
            Object which receive signal (Default: None)
        event : Gdk.EventButton or Gdk.EventKey
            Event which triggered this signal (Default: None)
        """

        if widget == self.button_save:

            self.config.modify("gem", "use_classic_theme",
                int(self.check_classic_theme.get_active()))
            self.config.modify("gem", "load_console_startup",
                int(self.check_last_console.get_active()))
            self.config.modify("gem", "hide_empty_console",
                int(self.check_hide_console.get_active()))

            self.config.modify("gem", "show_header",
                int(self.check_header.get_active()))
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
                int(self.check_native_viewer.get_active()))
            self.config.modify("viewer", "binary",
                self.file_viewer_binary.get_filename())
            self.config.modify("viewer", "options",
                self.entry_viewer_options.get_text())

            if self.gtksource:
                self.config.modify("editor", "lines",
                    int(self.check_lines.get_active()))
                self.config.modify("editor", "colorscheme",
                    self.combo_colorsheme.get_active_id())
                self.config.modify("editor", "font",
                    self.font_editor.get_font_name())

            for text, value, option, sensitive in self.model_shortcuts:
                if value is not None and option is not None:
                    self.config.modify("keys", option, value)

            self.config.update()

            if self.interface is not None:
                self.interface.load_interface()

        self.window.hide()

        self.config.modify(
            "windows", "preferences", "%dx%d" % self.window.get_size())
        self.config.update()

        if self.interface is None:
            Gtk.main_quit()

        else:
            self.window.response(Gtk.ResponseType.CANCEL)
            self.window.destroy()


    def load_configuration(self):
        """ Load configuration files and fill widgets
        """

        # ------------------------------------
        #   Interface
        # ------------------------------------

        self.check_classic_theme.set_active(self.config.getboolean(
            "gem", "use_classic_theme", fallback=True))
        self.check_last_console.set_active(self.config.getboolean(
            "gem", "load_console_startup", fallback=True))
        self.check_hide_console.set_active(self.config.getboolean(
            "gem", "hide_empty_console", fallback=True))

        # ------------------------------------
        #   Viewer
        # ------------------------------------

        self.check_native_viewer.set_active(self.config.getboolean(
            "viewer", "native", fallback=True))

        self.file_viewer_binary.set_filename(
            self.config.item("viewer", "binary"))
        self.entry_viewer_options.set_text(
            self.config.item("viewer", "options"))

        # ------------------------------------
        #   Interface
        # ------------------------------------

        self.check_header.set_active(self.config.getboolean(
            "gem", "show_header", fallback=True))
        self.check_icons.set_active(self.config.getboolean(
            "gem", "use_translucent_icons", fallback=True))

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

        for name in self.consoles.sections():
            image = icon_from_data(self.consoles.item(name, "icon"),
                self.empty, subfolder="consoles")

            path = self.consoles.item(name, "roms")

            if path is not None:
                path = path.replace(expanduser('~'), '~')
            else:
                path = str()

            check = self.empty
            if not exists(expanduser(path)):
                check = icon_load(Icons.Warning, 24, self.empty)

            self.model_consoles.append([image, name, path, check])


    def on_load_emulators(self):
        """ Load emulators into treeview
        """

        self.model_emulators.clear()

        self.selection["emulator"] = None

        for name in self.emulators.sections():
            image = icon_from_data(self.emulators.item(name, "icon"),
                self.empty, subfolder="emulators")

            binary = self.emulators.item(name, "binary")

            check, font = self.empty, Pango.Style.NORMAL
            if len(get_binary_path(binary)) == 0:
                check = icon_load(Icons.Warning, 24, self.empty)
                font = Pango.Style.OBLIQUE

            self.model_emulators.append([image, name, binary, check, font])


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
        kwcode : int
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


    def __on_check_native_viewer(self, widget):
        """ Update native viewer widget from checkbutton state

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        status = not self.check_native_viewer.get_active()

        self.label_viewer_binary.set_sensitive(status)
        self.file_viewer_binary.set_sensitive(status)
        self.label_viewer_options.set_sensitive(status)
        self.entry_viewer_options.set_sensitive(status)


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

        if manager == Manager.CONSOLE:
            config, treeview = self.consoles, self.treeview_consoles

        elif manager == Manager.EMULATOR:
            config, treeview = self.emulators, self.treeview_emulators

        model, treeiter = treeview.get_selection().get_selected()

        name = None
        if treeiter is not None:
            name = model.get_value(treeiter, 1)

        if modification and name is None:
            return False

        if manager == Manager.CONSOLE:
            if modification:
                self.selection["console"] = name

            Console(self, modification)

        elif manager == Manager.EMULATOR:
            if modification:
                self.selection["emulator"] = name

            Emulator(self, modification)

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

        name = None

        if manager == Manager.CONSOLE:
            config, treeview = self.consoles, self.treeview_consoles

        elif manager == Manager.EMULATOR:
            config, treeview = self.emulators, self.treeview_emulators

        model, treeiter = treeview.get_selection().get_selected()
        if treeiter is not None:
            name = model.get_value(treeiter, 1)

        # ----------------------------
        #   Game selected
        # ----------------------------

        need_reload = False

        if name is not None:
            dialog = Question(self.interface, name,
                _("Would you really want to remove this entry ?"))

            if dialog.run() == Gtk.ResponseType.YES:
                config.remove(name)
                config.update()

                model.remove(treeiter)

                need_reload = True

            dialog.destroy()

        if need_reload:
            if manager == Manager.CONSOLE:
                self.on_load_consoles()
            elif manager == Manager.EMULATOR:
                self.on_load_emulators()


class Console(Dialog):

    def __init__(self, parent, modify):
        """ Constructor

        Parameters
        ----------
        parent : Gtk.Window
            Parent object (Default: None)
        modify : bool
            Use edit mode instead of append mode
        """

        Dialog.__init__(self, parent.window, _("Console"), Icons.Gaming)

        # ------------------------------------
        #   Initialize variables
        # ------------------------------------

        self.path = None

        self.error = False
        self.file_error = False
        self.emulator_error = False

        self.interface = parent
        self.modify = modify

        self.empty = parent.empty
        self.consoles = parent.consoles
        self.emulators = parent.emulators
        self.selection = parent.selection

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

        # ------------------------------------
        #   Main window
        # ------------------------------------

        # Properties
        self.set_transient_for(self.interface.window)

        self.set_size(640, 250)
        self.set_resizable(True)

        self.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_APPLY, Gtk.ResponseType.APPLY)

        self.set_response_sensitive(Gtk.ResponseType.APPLY, False)

        # ------------------------------------
        #   Main scrolling
        # ------------------------------------

        self.scroll = Gtk.ScrolledWindow()

        self.viewport = Gtk.Viewport()

        # Properties
        self.scroll.add(self.viewport)

        # ------------------------------------
        #   Grids
        # ------------------------------------

        self.grid = Gtk.Grid()

        # Properties
        self.grid.set_row_spacing(8)
        self.grid.set_column_spacing(8)
        self.grid.set_column_homogeneous(False)

        # ------------------------------------
        #   Console options
        # ------------------------------------

        self.label_name = Gtk.Label()
        self.entry_name = Gtk.Entry()

        self.label_folder = Gtk.Label()
        self.file_folder = Gtk.FileChooserButton()

        self.label_extensions = Gtk.Label()
        self.entry_extensions = Gtk.Entry()

        self.button_console = Gtk.Button()
        self.image_console = Gtk.Image()

        self.label_emulator = Gtk.Label()
        self.model_emulators = Gtk.ListStore(Pixbuf, str, Pixbuf)
        self.combo_emulators = Gtk.ComboBox()

        cell_emulators_icon = Gtk.CellRendererPixbuf()
        cell_emulators_name = Gtk.CellRendererText()
        cell_emulators_warning = Gtk.CellRendererPixbuf()

        # Properties
        self.label_name.set_markup("<b>%s</b>" % _("Name"))
        self.label_name.set_use_markup(True)
        self.label_name.set_alignment(0, .5)
        self.entry_name.set_hexpand(True)
        self.entry_name.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, Icons.Clear)

        self.label_folder.set_markup("<b>%s</b>" % _("Choose the ROMs folder"))
        self.label_folder.set_use_markup(True)
        self.label_folder.set_alignment(0, .5)
        self.file_folder.set_action(Gtk.FileChooserAction.SELECT_FOLDER)
        self.file_folder.set_hexpand(True)

        self.label_extensions.set_markup("<b>%s</b>" % _("ROM's extensions"))
        self.label_extensions.set_use_markup(True)
        self.label_extensions.set_alignment(0, .5)
        self.entry_extensions.set_hexpand(True)
        self.entry_extensions.set_tooltip_text(
            _("Use ; to separate extensions"))
        self.entry_extensions.set_placeholder_text(
            _("Use ; to separate extensions"))
        self.entry_extensions.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, Icons.Clear)

        self.button_console.set_size_request(64, 64)
        self.image_console.set_size_request(64, 64)

        self.label_emulator.set_markup("<b>%s</b>" % _("Emulator"))
        self.label_emulator.set_use_markup(True)
        self.label_emulator.set_alignment(0, .5)

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


    def __init_packing(self):
        """ Initialize widgets packing in main window
        """

        # Main widgets
        self.dialog_box.pack_start(self.scroll, True, True, 8)

        self.viewport.add(self.grid)

        # Console grid
        self.grid.attach(self.label_name, 0, 0, 1, 1)
        self.grid.attach(self.entry_name, 1, 0, 1, 1)

        self.grid.attach(self.label_folder, 0, 1, 1, 1)
        self.grid.attach(self.file_folder, 1, 1, 1, 1)

        self.grid.attach(Gtk.Separator(), 2, 0, 1, 2)

        self.grid.attach(self.button_console, 3, 0, 1, 2)

        self.grid.attach(self.label_extensions, 0, 2, 1, 1)
        self.grid.attach(self.entry_extensions, 1, 2, 3, 1)

        self.grid.attach(Gtk.Separator(), 0, 3, 4, 1)

        self.grid.attach(self.label_emulator, 0, 4, 1, 1)
        self.grid.attach(self.combo_emulators, 1, 4, 3, 1)

        # Console options
        self.button_console.set_image(self.image_console)


    def __init_signals(self):
        """ Initialize widgets signals
        """

        self.entry_name.connect("changed", self.__update_dialog)
        self.entry_name.connect("icon-press", on_entry_clear)

        self.file_folder.connect("file-set", self.__update_dialog)

        self.entry_extensions.connect("icon-press", on_entry_clear)

        self.button_console.connect("clicked", self.__on_select_icon)

        self.combo_emulators.connect("changed", self.__update_dialog)


    def __start_interface(self):
        """ Load data and start interface
        """

        emulators_rows = dict()

        for emulator in self.emulators.sections():
            icon = icon_from_data(self.emulators.item(emulator, "icon"),
                self.empty, 24, 24, "emulators")

            path = self.emulators.item(emulator, "binary")

            warning = self.empty
            if len(get_binary_path(path)) == 0:
                warning = icon_load(Icons.Warning, 24, self.empty)

            emulators_rows[emulator] = self.model_emulators.append(
                [icon, emulator, warning])

        # ------------------------------------
        #   Init data
        # ------------------------------------

        self.console = self.selection["console"]

        if self.modify:
            self.entry_name.set_text(self.console)

            # Folder
            folder = expanduser(self.consoles.item(self.console, "roms", str()))
            if exists(folder):
                self.file_folder.set_current_folder(folder)

            # Extensions
            self.entry_extensions.set_text(
                self.consoles.item(self.console, "exts", str()))

            # Icon
            self.path = self.consoles.item(self.console, "icon")
            self.image_console.set_from_pixbuf(
                icon_from_data(self.path, self.empty, 64, 64, "consoles"))

            # Emulator
            if self.consoles.item(self.console, "emulator", str()) in \
                self.emulators.sections():

                self.combo_emulators.set_active_id(
                    self.consoles.item(self.console, "emulator", str()))

            self.set_response_sensitive(Gtk.ResponseType.APPLY, True)

        # ------------------------------------
        #   Start dialog
        # ------------------------------------

        need_reload = False

        self.show_all()

        response = self.run()

        # Save console
        if response == Gtk.ResponseType.APPLY:
            self.__on_save_data()

            if self.data is not None:
                if not self.section == self.console:
                    self.consoles.remove(self.console)

                self.consoles.remove(self.section)

                for (option, value) in self.data.items():
                    if value is None:
                        value = str()

                    if len(str(value)) > 0:
                        self.consoles.modify(self.section, option, str(value))

                self.consoles.update()

            need_reload = True

        self.destroy()

        if need_reload:
            self.interface.on_load_consoles()


    def __on_save_data(self):
        """ Return all the data from interface
        """

        self.data = dict()

        self.section = self.entry_name.get_text()

        path_roms = self.file_folder.get_filename()
        if path_roms is None or not exists(path_roms):
            path_roms = expanduser(
                self.consoles.item(self.console, "roms", str()))

        path_icon = self.path
        if path_icon is not None and \
            path_join(get_data("icons"), basename(path_icon)) == path_icon:
            path_icon = splitext(basename(path_icon))[0]

        self.data["roms"] = path_roms
        self.data["icon"] = path_icon
        self.data["exts"] = self.entry_extensions.get_text()
        self.data["emulator"] = self.combo_emulators.get_active_id()


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

        elif self.consoles.has_section(name):
            if not self.modify or (self.modify and not name == self.console):
                status = False

                icon, tooltip = Icons.Error, _(
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

        path = self.interface.emulators.item(
            self.combo_emulators.get_active_id(), "binary")

        # Allow to validate dialog if selected emulator binary exist
        if path is None or len(get_binary_path(path)) == 0:
            status = False

        # ------------------------------------
        #   Start dialog
        # ------------------------------------

        self.set_response_sensitive(Gtk.ResponseType.APPLY, status)


class Emulator(Dialog):

    def __init__(self, parent, modify):
        """ Constructor

        Parameters
        ----------
        parent : Gtk.Window
            Parent object (Default: None)
        modify : bool
            Use edit mode instead of append mode
        """

        Dialog.__init__(self, parent.window, _("Emulator"), Icons.Desktop)

        # ------------------------------------
        #   Initialize variables
        # ------------------------------------

        self.path = None

        self.error = False

        self.interface = parent
        self.modify = modify

        self.empty = parent.empty
        self.consoles = parent.consoles
        self.emulators = parent.emulators
        self.selection = parent.selection

        self.help_data = {
            "order": [
                _("Description"),
                _("Parameters"),
            ],
            _("Description"): [
                _("To facilitate files detection with every emulators, some "
                    "custom parameters has been created."),
                _("This parameters are used in \"Default options\", \"Save\" "
                    "and \"Snapshots\" entries."),
            ],
            _("Parameters"): {
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

        # ------------------------------------
        #   Main window
        # ------------------------------------

        # Properties
        self.set_transient_for(self.interface.window)

        self.set_size(640, 530)
        self.set_resizable(True)

        self.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_APPLY, Gtk.ResponseType.APPLY)

        self.set_response_sensitive(Gtk.ResponseType.APPLY, False)

        self.set_help(self.interface.window, self.help_data)

        # ------------------------------------
        #   Main scrolling
        # ------------------------------------

        self.scroll = Gtk.ScrolledWindow()

        self.viewport = Gtk.Viewport()

        # Properties
        self.scroll.add(self.viewport)

        # ------------------------------------
        #   Grids
        # ------------------------------------

        self.grid = Gtk.Grid()
        self.grid_misc = Gtk.Grid()

        self.grid_configuration = Gtk.Box()
        self.grid_arguments = Gtk.Box()
        self.grid_files = Gtk.Box()

        self.grid_binary = Gtk.Box()

        # Properties
        self.grid.set_row_spacing(8)
        self.grid.set_column_spacing(8)
        self.grid.set_column_homogeneous(False)

        self.grid_misc.set_row_spacing(8)
        self.grid_misc.set_column_spacing(8)
        self.grid_misc.set_column_homogeneous(False)

        Gtk.StyleContext.add_class(
            self.grid_binary.get_style_context(), "linked")

        # ------------------------------------
        #   Emulator options
        # ------------------------------------

        self.label_name = Gtk.Label()
        self.entry_name = Gtk.Entry()

        self.label_binary = Gtk.Label()
        self.entry_binary = Gtk.Entry()

        self.button_binary = Gtk.Button()
        self.image_binary = Gtk.Image()

        self.image_configuration = Gtk.Image()
        self.label_configuration = Gtk.Label()
        self.file_configuration = Gtk.FileChooserButton()

        self.button_emulator = Gtk.Button()
        self.image_emulator = Gtk.Image()

        self.image_arguments = Gtk.Image()
        self.label_arguments = Gtk.Label()

        self.label_launch = Gtk.Label()
        self.entry_launch = Gtk.Entry()

        self.label_windowed = Gtk.Label()
        self.entry_windowed = Gtk.Entry()

        self.label_fullscreen = Gtk.Label()
        self.entry_fullscreen = Gtk.Entry()

        self.image_files = Gtk.Image()
        self.label_files = Gtk.Label()

        self.label_save = Gtk.Label()
        self.entry_save = Gtk.Entry()

        self.label_screenshots = Gtk.Label()
        self.entry_screenshots = Gtk.Entry()

        # Properties
        self.label_name.set_markup(
            "<b>%s</b>" % _("Name"))
        self.label_name.set_use_markup(True)
        self.label_name.set_alignment(0, .5)
        self.entry_name.set_hexpand(True)
        self.entry_name.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, Icons.Clear)

        self.label_binary.set_markup(
            "<b>%s</b>" % _("Binary"))
        self.label_binary.set_use_markup(True)
        self.label_binary.set_alignment(0, .5)
        self.entry_binary.set_hexpand(True)
        self.entry_binary.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, Icons.Clear)

        self.image_binary.set_from_icon_name(
            Icons.Open, Gtk.IconSize.MENU)

        self.button_emulator.set_size_request(64, 64)
        self.image_emulator.set_size_request(64, 64)

        self.image_configuration.set_from_icon_name(
            Icons.Document, Gtk.IconSize.MENU)
        self.label_configuration.set_markup(
            "<b>%s</b>" % _("Configuration file"))
        self.label_configuration.set_use_markup(True)
        self.label_configuration.set_alignment(0, .5)
        self.file_configuration.set_margin_left(32)

        self.image_arguments.set_from_icon_name(
            Icons.Terminal, Gtk.IconSize.MENU)
        self.label_arguments.set_markup(
            "<b>%s</b>" % _("Emulator arguments"))
        self.label_arguments.set_use_markup(True)
        self.label_arguments.set_alignment(0, .5)

        self.label_launch.set_label(_("Default options"))
        self.label_launch.set_alignment(0, .5)
        self.label_launch.set_margin_left(32)
        self.entry_launch.set_hexpand(True)
        self.entry_launch.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, Icons.Clear)

        self.label_windowed.set_label(_("Windowed"))
        self.label_windowed.set_alignment(0, .5)
        self.label_windowed.set_margin_left(32)
        self.entry_windowed.set_hexpand(True)
        self.entry_windowed.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, Icons.Clear)

        self.label_fullscreen.set_label(_("Fullscreen"))
        self.label_fullscreen.set_alignment(0, .5)
        self.label_fullscreen.set_margin_left(32)
        self.entry_fullscreen.set_hexpand(True)
        self.entry_fullscreen.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, Icons.Clear)

        self.image_files.set_from_icon_name(
            Icons.Folder, Gtk.IconSize.MENU)
        self.label_files.set_markup(
            "<b>%s</b>" % _("Regular expressions for files"))
        self.label_files.set_use_markup(True)
        self.label_files.set_alignment(0, .5)

        self.label_save.set_label(_("Save"))
        self.label_save.set_alignment(0, .5)
        self.label_save.set_margin_left(32)
        self.entry_save.set_hexpand(True)
        self.entry_save.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, Icons.Clear)

        self.label_screenshots.set_label(_("Snapshots"))
        self.label_screenshots.set_alignment(0, .5)
        self.label_screenshots.set_margin_left(32)
        self.entry_screenshots.set_hexpand(True)
        self.entry_screenshots.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, Icons.Clear)


    def __init_packing(self):
        """ Initialize widgets packing in main window
        """

        # Main widgets
        self.dialog_box.pack_start(self.scroll, True, True, 8)

        self.viewport.add(self.grid)

        # Emulator grid
        self.grid.attach(self.label_name, 0, 0, 1, 1)
        self.grid.attach(self.entry_name, 1, 0, 1, 1)

        self.grid.attach(self.label_binary, 0, 1, 1, 1)
        self.grid.attach(self.grid_binary, 1, 1, 1, 1)

        self.grid.attach(Gtk.Separator(), 2, 0, 1, 2)

        self.grid.attach(self.button_emulator, 3, 0, 1, 2)

        self.grid.attach(Gtk.Separator(), 0, 2, 4, 1)

        self.grid.attach(self.grid_configuration, 0, 3, 4, 1)
        self.grid.attach(self.file_configuration, 0, 4, 4, 1)

        self.grid.attach(Gtk.Separator(), 0, 5, 4, 1)

        self.grid.attach(self.grid_misc, 0, 6, 4, 1)

        self.grid_misc.attach(self.grid_arguments, 0, 0, 2, 1)
        self.grid_misc.attach(self.label_launch, 0, 1, 1, 1)
        self.grid_misc.attach(self.entry_launch, 1, 1, 1, 1)
        self.grid_misc.attach(Gtk.Separator(), 1, 2, 1, 1)
        self.grid_misc.attach(self.label_windowed, 0, 3, 1, 1)
        self.grid_misc.attach(self.entry_windowed, 1, 3, 1, 1)
        self.grid_misc.attach(self.label_fullscreen, 0, 4, 1, 1)
        self.grid_misc.attach(self.entry_fullscreen, 1, 4, 1, 1)

        self.grid_misc.attach(Gtk.Separator(), 0, 5, 2, 1)

        self.grid_misc.attach(self.grid_files, 0, 6, 2, 1)
        self.grid_misc.attach(self.label_save, 0, 7, 1, 1)
        self.grid_misc.attach(self.entry_save, 1, 7, 1, 1)
        self.grid_misc.attach(self.label_screenshots, 0, 8, 1, 1)
        self.grid_misc.attach(self.entry_screenshots, 1, 8, 1, 1)

        # Emulator options
        self.button_binary.set_image(self.image_binary)

        self.button_emulator.set_image(self.image_emulator)

        # Emulator binary
        self.grid_binary.pack_start(self.entry_binary, True, True, 0)
        self.grid_binary.pack_start(self.button_binary, False, False, 0)

        # Emulator configuration
        self.grid_configuration.pack_start(
            self.image_configuration, False, False, 0)
        self.grid_configuration.pack_start(
            self.label_configuration, True, True, 8)

        # Emulator arguments
        self.grid_arguments.pack_start(
            self.image_arguments, False, False, 0)
        self.grid_arguments.pack_start(
            self.label_arguments, True, True, 8)

        # Emulator files
        self.grid_files.pack_start(
            self.image_files, False, False, 0)
        self.grid_files.pack_start(
            self.label_files, True, True, 8)


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

        # ------------------------------------
        #   Init data
        # ------------------------------------

        self.emulator = self.selection["emulator"]

        if self.modify:
            self.entry_name.set_text(self.emulator)

            # Binary
            folder = expanduser(
                self.emulators.item(self.emulator, "binary", str()))
            self.entry_binary.set_text(folder)

            # Configuration
            folder = expanduser(
                self.emulators.item(self.emulator, "configuration", str()))
            if exists(folder):
                self.file_configuration.set_filename(folder)

            # Icon
            self.path = self.emulators.item(self.emulator, "icon")
            self.image_emulator.set_from_pixbuf(
                icon_from_data(self.path, self.empty, 64, 64, "emulators"))

            # Regex
            self.entry_save.set_text(
                self.emulators.item(self.emulator, "save", str()))
            self.entry_screenshots.set_text(
                self.emulators.item(self.emulator, "snaps", str()))

            # Arguments
            self.entry_launch.set_text(
                self.emulators.item(self.emulator, "default", str()))
            self.entry_windowed.set_text(
                self.emulators.item(self.emulator, "windowed", str()))
            self.entry_fullscreen.set_text(
                self.emulators.item(self.emulator, "fullscreen", str()))

            self.set_response_sensitive(Gtk.ResponseType.APPLY, True)

        # ------------------------------------
        #   Start dialog
        # ------------------------------------

        need_reload = False

        self.show_all()

        response = self.run()

        # Save emulator
        if response == Gtk.ResponseType.APPLY:
            self.__on_save_data()

            if self.data is not None:
                if self.modify:
                    if not self.section == self.emulator:
                        self.emulators.remove(self.emulator)

                    self.emulators.remove(self.section)

                for (option, value) in self.data.items():
                    if value is None:
                        value = str()

                    if len(str(value)) > 0:
                        self.emulators.modify(self.section, option, str(value))

                self.emulators.update()

            need_reload = True

        self.destroy()

        if need_reload:
            self.interface.on_load_emulators()


    def __on_save_data(self):
        """ Return all the data from interface
        """

        self.data = dict()

        self.section = self.entry_name.get_text()

        path_binary = self.entry_binary.get_text()
        if path_binary is None:
            path_binary = expanduser(
                self.emulators.item(self.emulator, "binary", str()))

        path_configuration = self.file_configuration.get_filename()
        if path_configuration is None or not exists(path_configuration):
            path_configuration = expanduser(
                self.emulators.item(self.emulator, "configuration", str()))

        path_icon = self.path
        if path_icon is not None and \
            path_join(get_data("icons"), basename(path_icon)) == path_icon:
            path_icon = splitext(basename(path_icon))[0]

        self.data["binary"] = path_binary
        self.data["configuration"] = path_configuration
        self.data["icon"] = path_icon
        self.data["save"] = self.entry_save.get_text()
        self.data["snaps"] = self.entry_screenshots.get_text()
        self.data["default"] = self.entry_launch.get_text()
        self.data["windowed"] = self.entry_windowed.get_text()
        self.data["fullscreen"] = self.entry_fullscreen.get_text()


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

        icon, tooltip = None, None

        name = self.entry_name.get_text()

        if name is None or len(name) == 0:
            self.error = True

        elif self.emulators.has_section(name):

            if not self.modify or (self.modify and not name == self.emulator):
                self.error = True

                icon = "dialog-error"
                tooltip = _(
                    "This emulator already exist, please, choose another name")

            else:
                icon, tooltip = None, None

        if widget == self.entry_name:
            self.entry_name.set_icon_from_icon_name(
                Gtk.EntryIconPosition.PRIMARY, icon)
            self.entry_name.set_tooltip_text(tooltip)

        # ------------------------------------
        #   Emulator binary
        # ------------------------------------

        icon, tooltip = None, None

        path = self.entry_binary.get_text()

        if path is None or len(path) == 0:
            self.error = True

        elif len(get_binary_path(path)) == 0:
            self.error = True

            icon = "dialog-error"
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

        dialog = Gtk.FileChooserDialog(_("Select a binary"), self,
            Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

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


class IconViewer(Dialog):

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

        Dialog.__init__(self, parent, title, Icons.Image)

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

        # ------------------------------------
        #   Interface
        # ------------------------------------

        self.set_size(800, 600)

        self.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK)

        # ------------------------------------
        #   Grid
        # ------------------------------------

        scrollview = Gtk.ScrolledWindow()
        view = Gtk.Viewport()

        box = Gtk.Grid()
        box_switch = Gtk.Box()

        # Properties
        scrollview.set_border_width(4)
        scrollview.set_policy(
            Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        view.set_shadow_type(Gtk.ShadowType.NONE)

        box.set_row_spacing(4)
        box.set_column_spacing(8)
        box.set_column_homogeneous(False)

        box_switch.set_spacing(0)

        # ------------------------------------
        #   Option
        # ------------------------------------

        label_option = Gtk.Label()

        self.model_option = Gtk.ListStore(str)
        self.combo_option = Gtk.ComboBox()

        cell_option = Gtk.CellRendererText()

        # Properties
        label_option.set_alignment(1, .5)
        label_option.set_label(_("Select icon from"))

        self.combo_option.set_model(self.model_option)
        self.combo_option.set_id_column(0)
        self.combo_option.pack_start(cell_option, True)
        self.combo_option.add_attribute(cell_option, "text", 0)

        # ------------------------------------
        #   Custom
        # ------------------------------------

        self.frame_icons = Gtk.Frame()

        self.file_icons = Gtk.FileChooserWidget()

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

        self.dialog_box.pack_start(scrollview, True, True, 0)

        scrollview.add(view)
        view.add(box)

        box.attach(label_option, 0, 0, 1, 1)
        box.attach(self.combo_option, 1, 0, 1, 1)
        box.attach(box_switch, 0, 1, 2, 1)

        box_switch.pack_start(self.frame_icons, True, True, 0)
        box_switch.pack_start(self.scroll_icons, True, True, 0)

        self.frame_icons.add(self.file_icons)
        self.scroll_icons.add(self.view_icons)


    def __init_signals(self):
        """ Initialize widgets signals
        """

        self.combo_option.connect("changed", self.set_widgets_sensitive)

        self.view_icons.connect("item_activated", self.__on_selected_icon)


    def __start_interface(self):
        """ Load data and start interface
        """

        self.load_interface()

        self.show_all()

        self.set_widgets_sensitive()

        response = self.run()

        if response == Gtk.ResponseType.OK:
            self.save_interface()


    def __on_selected_icon(self, widget, path):
        """ Select an icon in treeview

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        path : Gtk.TreePath
            Path to be activated
        """

        self.response(Gtk.ResponseType.OK)


    def load_interface(self):
        """ Insert data into interface's widgets
        """

        # Fill options combobox
        self.model_option.append([_("All icons")])
        self.model_option.append([_("Image file")])

        self.frame_icons.set_visible(False)
        self.scroll_icons.set_visible(True)

        self.icons_data = dict()

        # Fill icons view
        for icon in \
            glob(path_join(Path.Icons, self.folder, "*.%s" % Icons.Ext)):
            name = splitext(basename(icon))[0]

            self.icons_data[name] = self.model_icons.append([
                icon_from_data(icon, self.empty, 72, 72, self.folder), name])

        # Set filechooser or icons view selected item
        if self.path is not None:

            # Check if current path is a gem icons
            data = path_join(Path.Icons, self.folder,
                "%s.%s" % (self.path, Icons.Ext))

            if data is not None and exists(data):
                self.view_icons.select_path(
                    self.model_icons.get_path(self.icons_data[self.path]))

            else:
                self.file_icons.set_filename(self.path)

        self.combo_option.set_active_id(_("All icons"))


    def save_interface(self):
        """ Return all the data from interface
        """

        if self.combo_option.get_active_id() == _("All icons"):
            selection = self.view_icons.get_selected_items()[0]

            path = self.model_icons.get_value(
                self.model_icons.get_iter(selection), 1)

        else:
            path = self.file_icons.get_filename()

        if not path == self.path:
            self.new_path = path


    def set_widgets_sensitive(self, widget=None):
        """ Change sensitive state between radio children

        Others Parameters
        -----------------
        widget : Gtk.Widget
            Object which receive signal (Default: None)
        """

        if self.combo_option.get_active_id() == _("All icons"):
            self.frame_icons.set_visible(False)
            self.scroll_icons.set_visible(True)

        else:
            self.frame_icons.set_visible(True)
            self.scroll_icons.set_visible(False)
