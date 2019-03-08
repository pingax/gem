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

# Filesystem
from pathlib import Path

# GEM
from gem.engine.api import GEM
from gem.engine.lib.configuration import Configuration

from gem.ui.data import Icons
from gem.ui.data import Folders
from gem.ui.utils import on_entry_clear
from gem.ui.dialog.question import QuestionDialog
from gem.ui.widgets.window import CommonWindow
from gem.ui.widgets.widgets import PreferencesItem
from gem.ui.preferences.console import ConsolePreferences
from gem.ui.preferences.emulator import EmulatorPreferences

# GObject
try:
    from gi import require_version

    require_version("Gtk", "3.0")

    from gi.repository import Gtk
    from gi.repository import Gdk
    from gi.repository import GdkPixbuf
    from gi.repository import Pango

except ImportError as error:
    from sys import exit

    exit("Cannot found python3-gobject module: %s" % str(error))

# Translation
from gettext import gettext as _

# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class Manager(object):
    CONSOLE  = 0
    EMULATOR = 1


class PreferencesWindow(CommonWindow):

    def __init__(self, api, parent):
        """ Constructor

        Parameters
        ----------
        api : gem.engine.api.GEM
            GEM API instance
        parent : Gtk.Window or None, optional
            Parent window for transient mode (default: None)

        Raises
        ------
        TypeError
            if api type is not gem.engine.api.GEM
        """

        if type(api) is not GEM:
            raise TypeError("Wrong type for api, expected gem.engine.api.GEM")

        CommonWindow.__init__(self, parent, _("Preferences"),
            Icons.Symbolic.PREFERENCES, parent.use_classic_theme)

        # ------------------------------------
        #   Initialize variables
        # ------------------------------------

        # API instance
        self.api = parent.api

        self.icons = parent.icons

        self.interface = parent

        self.shortcuts = {
            _("Interface"): {
                "fullscreen": [
                    _("Switch between fullscreen modes"), "F11"],
                "sidebar": [
                    _("Show sidebar"), "F9"],
                "statusbar": [
                    _("Show statusbar"), "<Control>F9"],
                "gem": [
                    _("Open main log"), "<Control>L"],
                "preferences": [
                    _("Open preferences"), "<Control>P"],
                "quit": [
                    _("Quit application"), "<Control>Q"]
            },
            _("Game"): {
                "start": [
                    _("Launch a game"), "<Control>Return"],
                "favorite": [
                    _("Mark a game as favorite"), "F3"],
                "multiplayer": [
                    _("Mark a game as multiplayer"), "F4"],
                "finish": [
                    _("Mark a game as finish"), "<Control>F3"],
                "snapshots": [
                    _("Show a game screenshots"), "F5"],
                "log": [
                    _("Open a game log"), "F6"],
                "notes": [
                    _("Open a game notes"), "F7"],
                "memory": [
                    _("Generate a backup memory file"), "F8"]
            },
            _("Score"): {
                "score-up": [
                    _("Increase selected game score"), "<Control>Page_Up"],
                "score-down": [
                    _("Decrease selected game score"), "<Control>Page_Down"],
                "score-0": [
                    _("Set selected game score as 0"), "<Primary>0"],
                "score-1": [
                    _("Set selected game score as 1"), "<Primary>1"],
                "score-2": [
                    _("Set selected game score as 2"), "<Primary>2"],
                "score-3": [
                    _("Set selected game score as 3"), "<Primary>3"],
                "score-4": [
                    _("Set selected game score as 4"), "<Primary>4"],
                "score-5": [
                    _("Set selected game score as 5"), "<Primary>5"]
            },
            _("Edit"): {
                "maintenance": [
                    _("Open a game maintenance dialog"), "<Control>D"],
                "delete": [
                    _("Remove a game from disk"), "<Control>Delete"],
                "rename": [
                    _("Rename a game"), "F2"],
                "duplicate": [
                    _("Duplicate a game"), "<Control>U"],
                "cover": [
                    _("Set a game cover"), "<Control>I"],
                "exceptions": [
                    _("Set specific arguments for a game"), "F12"],
                "open": [
                    _("Open selected game directory"), "<Control>O"],
                "copy": [
                    _("Copy selected game path"), "<Control>C"],
                "desktop": [
                    _("Generate desktop entry for a game"), "<Control>G"]
            }
        }

        self.lines = {
            _("None"): "none",
            _("Horizontal"): "horizontal",
            _("Vertical"): "vertical",
            _("Both"): "both"
        }

        self.sidebar = {
            _("Right"): "horizontal",
            _("Bottom"): "vertical"
        }

        self.toolbar = {
            _("Menu"): "menu",
            _("Small Toolbar"): "small-toolbar",
            _("Large Toolbar"): "large-toolbar",
            _("Button"): "button",
            _("Drag and Drop"): "dnd",
            _("Dialog"): "dialog"
        }

        self.tooltips = {
            _("Show screenshot or cover"): "both",
            _("Show screenshot only"): "screenshot",
            _("Show cover only"): "cover",
            _("Hide"): "none"
        }

        self.selection = {
            "console": None,
            "emulator": None
        }

        # ------------------------------------
        #   Initialize configuration files
        # ------------------------------------

        self.config = Configuration(Folders.CONFIG.joinpath("gem.conf"))

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

        self.set_border_width(6)
        self.set_spacing(6)

        self.button_cancel = self.add_button(
            _("Close"), Gtk.ResponseType.CLOSE)

        self.button_save = self.add_button(
            _("Accept"), Gtk.ResponseType.APPLY, Gtk.Align.END)

        # ------------------------------------
        #   Grids
        # ------------------------------------

        self.box_stack = Gtk.Box()

        self.grid_general = Gtk.Box()
        self.grid_interface = Gtk.Box()
        self.grid_games = Gtk.Box()
        self.grid_shortcuts = Gtk.Grid()
        self.grid_consoles = Gtk.Box()
        self.grid_emulators = Gtk.Box()

        self.grid_consoles_buttons = Gtk.ButtonBox()
        self.grid_emulators_buttons = Gtk.ButtonBox()

        # Properties
        self.box_stack.set_orientation(Gtk.Orientation.HORIZONTAL)

        self.grid_general.set_spacing(6)
        self.grid_general.set_border_width(18)
        self.grid_general.set_halign(Gtk.Align.FILL)
        self.grid_general.set_orientation(Gtk.Orientation.VERTICAL)

        self.grid_interface.set_spacing(6)
        self.grid_interface.set_border_width(18)
        self.grid_interface.set_halign(Gtk.Align.FILL)
        self.grid_interface.set_orientation(Gtk.Orientation.VERTICAL)

        self.grid_games.set_spacing(6)
        self.grid_games.set_border_width(18)
        self.grid_games.set_halign(Gtk.Align.FILL)
        self.grid_games.set_orientation(Gtk.Orientation.VERTICAL)

        self.grid_shortcuts.set_row_spacing(6)
        self.grid_shortcuts.set_column_spacing(12)
        self.grid_shortcuts.set_border_width(18)
        self.grid_shortcuts.set_column_homogeneous(False)

        self.grid_consoles.set_spacing(6)
        self.grid_consoles.set_border_width(18)
        self.grid_consoles.set_orientation(Gtk.Orientation.VERTICAL)

        self.grid_emulators.set_spacing(6)
        self.grid_emulators.set_border_width(18)
        self.grid_emulators.set_orientation(Gtk.Orientation.VERTICAL)

        Gtk.StyleContext.add_class(
            self.grid_consoles_buttons.get_style_context(), "linked")
        self.grid_consoles_buttons.set_spacing(-1)
        self.grid_consoles_buttons.set_homogeneous(True)
        self.grid_consoles_buttons.set_halign(Gtk.Align.CENTER)
        self.grid_consoles_buttons.set_valign(Gtk.Align.CENTER)

        Gtk.StyleContext.add_class(
            self.grid_emulators_buttons.get_style_context(), "linked")
        self.grid_emulators_buttons.set_spacing(-1)
        self.grid_emulators_buttons.set_homogeneous(True)
        self.grid_emulators_buttons.set_halign(Gtk.Align.CENTER)
        self.grid_emulators_buttons.set_valign(Gtk.Align.CENTER)

        # ------------------------------------
        #   Stack
        # ------------------------------------

        self.stack = Gtk.Stack()

        self.sidebar_stack = Gtk.StackSidebar()

        self.frame_stack = Gtk.Frame()

        # Properties
        self.stack.set_transition_type(Gtk.StackTransitionType.NONE)

        self.sidebar_stack.set_stack(self.stack)

        # ------------------------------------
        #   General
        # ------------------------------------

        self.scroll_general = Gtk.ScrolledWindow()
        self.view_general = Gtk.Viewport()

        # ------------------------------------
        #   General - Behavior
        # ------------------------------------

        self.label_general_behavior = Gtk.Label()

        self.frame_general_behavior = Gtk.Frame()
        self.listbox_general_behavior = Gtk.ListBox()

        self.widget_behavior_last_console = PreferencesItem()
        self.switch_general_behavior_last_console = Gtk.Switch()

        self.widget_behavior_last_column = PreferencesItem()
        self.switch_general_behavior_last_column = Gtk.Switch()

        self.widget_behavior_hide_consoles = PreferencesItem()
        self.switch_general_behavior_hide_consoles = Gtk.Switch()

        # Properties
        self.label_general_behavior.set_hexpand(True)
        self.label_general_behavior.set_use_markup(True)
        self.label_general_behavior.set_halign(Gtk.Align.CENTER)
        self.label_general_behavior.set_markup(
            "<b>%s</b>" % _("Behavior"))

        self.frame_general_behavior.set_margin_bottom(12)

        self.listbox_general_behavior.set_activate_on_single_click(True)
        self.listbox_general_behavior.set_selection_mode(
            Gtk.SelectionMode.NONE)

        self.widget_behavior_last_console.set_widget(
            self.switch_general_behavior_last_console)
        self.widget_behavior_last_console.set_option_label(
            _("Restore last console"))
        self.widget_behavior_last_console.set_description_label(
            _("Restore the last selected console when application is opened"))

        self.widget_behavior_last_column.set_widget(
            self.switch_general_behavior_last_column)
        self.widget_behavior_last_column.set_option_label(
            _("Restore sorted column"))
        self.widget_behavior_last_column.set_description_label(
            _("Restore the last sorted column when application is opened"))

        self.widget_behavior_hide_consoles.set_widget(
            self.switch_general_behavior_hide_consoles)
        self.widget_behavior_hide_consoles.set_option_label(
            _("Disable empty consoles"))
        self.widget_behavior_hide_consoles.set_description_label(
            _("Disable consoles without games"))

        # ------------------------------------
        #   General - Editor
        # ------------------------------------

        self.label_general_editor = Gtk.Label()

        self.frame_general_editor = Gtk.Frame()
        self.listbox_general_editor = Gtk.ListBox()

        self.widget_editor_lines_visible = PreferencesItem()
        self.switch_general_editor_lines_visible = Gtk.Switch()

        self.widget_editor_tab_width = PreferencesItem()
        self.spin_general_editor_tab_width = Gtk.SpinButton()

        self.widget_editor_colorscheme = PreferencesItem()
        self.model_general_colorscheme = Gtk.ListStore(str)
        self.combo_general_colorscheme = Gtk.ComboBox()
        self.cell_general_colorscheme = Gtk.CellRendererText()

        self.widget_editor_font = PreferencesItem()
        self.font_general_editor_font = Gtk.FontButton()

        # Properties
        self.label_general_editor.set_hexpand(True)
        self.label_general_editor.set_use_markup(True)
        self.label_general_editor.set_halign(Gtk.Align.CENTER)
        self.label_general_editor.set_markup(
            "<b>%s</b>" % _("Editor"))

        self.frame_general_editor.set_margin_bottom(12)

        self.listbox_general_editor.set_activate_on_single_click(True)
        self.listbox_general_editor.set_selection_mode(
            Gtk.SelectionMode.NONE)

        self.widget_editor_lines_visible.set_widget(
            self.switch_general_editor_lines_visible)
        self.widget_editor_lines_visible.set_option_label(
            _("Line numbers"))
        self.widget_editor_lines_visible.set_description_label(
            _("Show line number at beginning of each line"))

        self.widget_editor_tab_width.set_widget(
            self.spin_general_editor_tab_width)
        self.widget_editor_tab_width.set_option_label(
            _("Tab width"))
        self.widget_editor_tab_width.set_description_label(
            _("Width of a tab character in spaces"))

        self.spin_general_editor_tab_width.set_range(1.0, 40.0)
        self.spin_general_editor_tab_width.set_increments(1, 4)
        self.spin_general_editor_tab_width.set_numeric(True)
        self.spin_general_editor_tab_width.set_digits(0)

        self.widget_editor_colorscheme.set_widget(
            self.combo_general_colorscheme)
        self.widget_editor_colorscheme.set_option_label(
            _("Color scheme"))

        self.model_general_colorscheme.set_sort_column_id(
            0, Gtk.SortType.ASCENDING)

        self.combo_general_colorscheme.set_model(
            self.model_general_colorscheme)
        self.combo_general_colorscheme.set_id_column(0)
        self.combo_general_colorscheme.pack_start(
            self.cell_general_colorscheme, True)
        self.combo_general_colorscheme.add_attribute(
            self.cell_general_colorscheme, "text", 0)

        self.widget_editor_font.set_widget(
            self.font_general_editor_font)
        self.widget_editor_font.set_option_label(
            _("Editor font"))

        # HACK: Set an ellipsize mode for the label inside FontButton
        for child in self.font_general_editor_font.get_child():
            if type(child) == Gtk.Label:
                child.set_ellipsize(Pango.EllipsizeMode.END)

        # ------------------------------------
        #   General - Viewer
        # ------------------------------------

        self.label_general_viewer = Gtk.Label()

        self.frame_general_viewer = Gtk.Frame()
        self.listbox_general_viewer = Gtk.ListBox()

        self.widget_viewer_alternative_viewer = PreferencesItem()
        self.switch_general_viewer_alternative_viewer = Gtk.Switch()

        self.widget_viewer_binary = PreferencesItem()
        self.file_general_viewer_binary = Gtk.FileChooserButton()

        self.widget_viewer_options = PreferencesItem()
        self.entry_general_viewer_options = Gtk.Entry()

        # Properties
        self.label_general_viewer.set_hexpand(True)
        self.label_general_viewer.set_use_markup(True)
        self.label_general_viewer.set_halign(Gtk.Align.CENTER)
        self.label_general_viewer.set_markup(
            "<b>%s</b>" % _("Screenshots viewer"))

        self.frame_general_viewer.set_margin_bottom(12)

        self.listbox_general_viewer.set_activate_on_single_click(True)
        self.listbox_general_viewer.set_selection_mode(
            Gtk.SelectionMode.NONE)

        self.widget_viewer_alternative_viewer.set_widget(
            self.switch_general_viewer_alternative_viewer)
        self.widget_viewer_alternative_viewer.set_option_label(
            _("Enable alternative application"))
        self.widget_viewer_alternative_viewer.set_description_label(
            _("Allow to use an alternative screenshots viewer"))

        self.widget_viewer_binary.set_widget(
            self.file_general_viewer_binary)
        self.widget_viewer_binary.set_option_label(
            _("Executable"))

        self.widget_viewer_options.set_widget(
            self.entry_general_viewer_options)
        self.widget_viewer_options.set_option_label(
            _("Parameters"))

        self.entry_general_viewer_options.set_icon_from_icon_name(
            Gtk.EntryIconPosition.PRIMARY, Icons.Symbolic.TERMINAL)
        self.entry_general_viewer_options.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, Icons.Symbolic.CLEAR)

        # ------------------------------------
        #   Interface
        # ------------------------------------

        self.scroll_interface = Gtk.ScrolledWindow()
        self.view_interface = Gtk.Viewport()

        # ------------------------------------
        #   Interface - Appearance
        # ------------------------------------

        self.label_interface_appearance = Gtk.Label()

        self.frame_interface_appearance = Gtk.Frame()
        self.listbox_interface_appearance = Gtk.ListBox()

        self.widget_appearance_classic_theme = PreferencesItem()
        self.switch_interface_appearance_classic_theme = Gtk.Switch()

        self.widget_appearance_header_button = PreferencesItem()
        self.switch_interface_appearance_header_buttons = Gtk.Switch()

        # Properties
        self.label_interface_appearance.set_hexpand(True)
        self.label_interface_appearance.set_use_markup(True)
        self.label_interface_appearance.set_halign(Gtk.Align.CENTER)
        self.label_interface_appearance.set_markup(
            "<b>%s</b>" % _("Appearance"))

        self.frame_interface_appearance.set_margin_bottom(12)

        self.listbox_interface_appearance.set_activate_on_single_click(True)
        self.listbox_interface_appearance.set_selection_mode(
            Gtk.SelectionMode.NONE)

        self.widget_appearance_classic_theme.set_widget(
            self.switch_interface_appearance_classic_theme)
        self.widget_appearance_classic_theme.set_option_label(
            _("Enable classic theme"))
        self.widget_appearance_classic_theme.set_description_label(
            _("Use a GTK+2 like appearance (Restart application is needed)"))

        self.widget_appearance_header_button.set_widget(
            self.switch_interface_appearance_header_buttons)
        self.widget_appearance_header_button.set_option_label(
            _("Enable close buttons"))
        self.widget_appearance_header_button.set_description_label(
            _("Enable close buttons in headerbar"))

        # ------------------------------------
        #   Interface - Toolbar
        # ------------------------------------

        self.label_interface_toolbar = Gtk.Label()

        self.frame_interface_toolbar = Gtk.Frame()
        self.listbox_interface_toolbar = Gtk.ListBox()

        self.widget_toolbar_size = PreferencesItem()
        self.model_interface_toolbar_size = Gtk.ListStore(str, str)
        self.combo_interface_toolbar_size = Gtk.ComboBox()
        self.cell_interface_toolbar_size = Gtk.CellRendererText()

        # Properties
        self.label_interface_toolbar.set_hexpand(True)
        self.label_interface_toolbar.set_use_markup(True)
        self.label_interface_toolbar.set_halign(Gtk.Align.CENTER)
        self.label_interface_toolbar.set_markup(
            "<b>%s</b>" % _("Toolbar"))

        self.frame_interface_toolbar.set_margin_bottom(12)

        self.listbox_interface_toolbar.set_activate_on_single_click(True)
        self.listbox_interface_toolbar.set_selection_mode(
            Gtk.SelectionMode.NONE)

        self.widget_toolbar_size.set_widget(self.combo_interface_toolbar_size)
        self.widget_toolbar_size.set_option_label(
            _("Icons size"))
        self.widget_toolbar_size.set_description_label(
            _("The size of icons in toolbar"))

        self.combo_interface_toolbar_size.set_model(
            self.model_interface_toolbar_size)
        self.combo_interface_toolbar_size.set_id_column(0)
        self.combo_interface_toolbar_size.pack_start(
            self.cell_interface_toolbar_size, True)
        self.combo_interface_toolbar_size.add_attribute(
            self.cell_interface_toolbar_size, "text", 1)

        # ------------------------------------
        #   Interface - Sidebar
        # ------------------------------------

        self.label_interface_sidebar = Gtk.Label()

        self.frame_interface_sidebar = Gtk.Frame()
        self.listbox_interface_sidebar = Gtk.ListBox()

        self.widget_sidebar_visible = PreferencesItem()
        self.switch_interface_sidebar_visible = Gtk.Switch()

        self.widget_sidebar_position = PreferencesItem()
        self.model_interface_sidebar_position = Gtk.ListStore(str, str)
        self.combo_interface_sidebar_position = Gtk.ComboBox()
        self.cell_interface_sidebar_position = Gtk.CellRendererText()

        self.widget_sidebar_random_screenshot = PreferencesItem()
        self.switch_interface_random_screenshot = Gtk.Switch()

        self.widget_sidebar_ellipsize = PreferencesItem()
        self.switch_interface_ellipsize = Gtk.Switch()

        # Properties
        self.label_interface_sidebar.set_hexpand(True)
        self.label_interface_sidebar.set_use_markup(True)
        self.label_interface_sidebar.set_halign(Gtk.Align.CENTER)
        self.label_interface_sidebar.set_markup(
            "<b>%s</b>" % _("Sidebar"))

        self.listbox_interface_sidebar.set_activate_on_single_click(True)
        self.listbox_interface_sidebar.set_selection_mode(
            Gtk.SelectionMode.NONE)

        self.widget_sidebar_visible.set_widget(
            self.switch_interface_sidebar_visible)
        self.widget_sidebar_visible.set_option_label(
            _("Enable sidebar"))
        self.widget_sidebar_visible.set_description_label(
            _("Enable sidebar next to games view"))

        self.widget_sidebar_position.set_widget(
            self.combo_interface_sidebar_position)
        self.widget_sidebar_position.set_option_label(
            _("Position"))
        self.widget_sidebar_position.set_description_label(
            _("Set sidebar position as for games view"))

        self.combo_interface_sidebar_position.set_model(
            self.model_interface_sidebar_position)
        self.combo_interface_sidebar_position.set_id_column(0)
        self.combo_interface_sidebar_position.pack_start(
            self.cell_interface_sidebar_position, True)
        self.combo_interface_sidebar_position.add_attribute(
            self.cell_interface_sidebar_position, "text", 1)

        self.widget_sidebar_random_screenshot.set_widget(
            self.switch_interface_random_screenshot)
        self.widget_sidebar_random_screenshot.set_option_label(
            _("Enable randomize screenshot"))
        self.widget_sidebar_random_screenshot.set_description_label(
            _("Use a random game screenshot instead of latest"))

        self.widget_sidebar_ellipsize.set_widget(
            self.switch_interface_ellipsize)
        self.widget_sidebar_ellipsize.set_option_label(
            _("Enable ellipsize title mode"))
        self.widget_sidebar_ellipsize.set_description_label(
            _("Add an ellipsis to title when there is not enough space"))

        # ------------------------------------
        #   Games
        # ------------------------------------

        self.scroll_games = Gtk.ScrolledWindow()
        self.view_games = Gtk.Viewport()

        # ------------------------------------
        #   Games - Views
        # ------------------------------------

        self.label_games_view = Gtk.Label()

        self.frame_games_view = Gtk.Frame()
        self.listbox_games_view = Gtk.ListBox()

        self.widget_view_grid_lines = PreferencesItem()
        self.model_games_view_grid_lines = Gtk.ListStore(str, str)
        self.combo_games_view_grid_lines = Gtk.ComboBox()
        self.cell_games_view_grid_lines = Gtk.CellRendererText()

        self.widget_view_tooltip_icon = PreferencesItem()
        self.model_games_view_tooltip_icon = Gtk.ListStore(str, str)
        self.combo_games_view_tooltip_icon = Gtk.ComboBox()
        self.cell_games_view_tooltip_icon = Gtk.CellRendererText()

        self.widget_view_icons = PreferencesItem()
        self.switch_games_view_icons = Gtk.Switch()

        # Properties
        self.label_games_view.set_hexpand(True)
        self.label_games_view.set_use_markup(True)
        self.label_games_view.set_halign(Gtk.Align.CENTER)
        self.label_games_view.set_markup(
            "<b>%s</b>" % _("List view"))

        self.frame_games_view.set_margin_bottom(12)

        self.listbox_games_view.set_activate_on_single_click(True)
        self.listbox_games_view.set_selection_mode(
            Gtk.SelectionMode.NONE)

        self.widget_view_grid_lines.set_widget(
            self.combo_games_view_grid_lines)
        self.widget_view_grid_lines.set_option_label(
            _("Grid lines"))
        self.widget_view_grid_lines.set_description_label(
            _("Display lines in games list view"))

        self.combo_games_view_grid_lines.set_model(
            self.model_games_view_grid_lines)
        self.combo_games_view_grid_lines.set_id_column(0)
        self.combo_games_view_grid_lines.pack_start(
            self.cell_games_view_grid_lines, True)
        self.combo_games_view_grid_lines.add_attribute(
            self.cell_games_view_grid_lines, "text", 1)

        self.widget_view_tooltip_icon.set_widget(
            self.combo_games_view_tooltip_icon)
        self.widget_view_tooltip_icon.set_option_label(
            _("Tooltip image"))
        self.widget_view_tooltip_icon.set_description_label(
            _("Display a specific image in game tooltip"))

        self.combo_games_view_tooltip_icon.set_model(
            self.model_games_view_tooltip_icon)
        self.combo_games_view_tooltip_icon.set_id_column(0)
        self.combo_games_view_tooltip_icon.pack_start(
            self.cell_games_view_tooltip_icon, True)
        self.combo_games_view_tooltip_icon.add_attribute(
            self.cell_games_view_tooltip_icon, "text", 1)

        self.widget_view_icons.set_widget(
            self.switch_games_view_icons)
        self.widget_view_icons.set_option_label(
            _("Enable translucent icons"))
        self.widget_view_icons.set_description_label(
            _("Display translucent icons in games views instead of empty ones"))

        # ------------------------------------
        #   Interface - Columns
        # ------------------------------------

        self.label_games_column = Gtk.Label()

        self.frame_games_column = Gtk.Frame()
        self.listbox_games_column = Gtk.ListBox()

        self.widget_column_favorite = PreferencesItem()
        self.switch_games_column_favorite = Gtk.Switch()

        self.widget_column_multiplayer = PreferencesItem()
        self.switch_games_column_multiplayer = Gtk.Switch()

        self.widget_column_finish = PreferencesItem()
        self.switch_games_column_finish = Gtk.Switch()

        self.widget_column_play = PreferencesItem()
        self.switch_games_column_play = Gtk.Switch()

        self.widget_column_last_launch = PreferencesItem()
        self.switch_games_column_last_launch = Gtk.Switch()

        self.widget_column_play_time = PreferencesItem()
        self.switch_games_column_play_time = Gtk.Switch()

        self.widget_column_score = PreferencesItem()
        self.switch_games_column_score = Gtk.Switch()

        self.widget_column_installed = PreferencesItem()
        self.switch_games_column_installed = Gtk.Switch()

        self.widget_column_flags = PreferencesItem()
        self.switch_games_column_flags = Gtk.Switch()

        # Properties
        self.label_games_column.set_hexpand(True)
        self.label_games_column.set_use_markup(True)
        self.label_games_column.set_halign(Gtk.Align.CENTER)
        self.label_games_column.set_markup(
            "<b>%s</b>" % _("Columns"))

        self.frame_games_column.set_margin_bottom(12)

        self.listbox_games_column.set_activate_on_single_click(True)
        self.listbox_games_column.set_selection_mode(
            Gtk.SelectionMode.NONE)

        self.widget_column_favorite.set_widget(
            self.switch_games_column_favorite)
        self.widget_column_favorite.set_option_label(
            _("Favorite"))

        self.widget_column_multiplayer.set_widget(
            self.switch_games_column_multiplayer)
        self.widget_column_multiplayer.set_option_label(
            _("Multiplayer"))

        self.widget_column_finish.set_widget(
            self.switch_games_column_finish)
        self.widget_column_finish.set_option_label(
            _("Finish"))

        self.widget_column_play.set_widget(
            self.switch_games_column_play)
        self.widget_column_play.set_option_label(
            _("Launch"))

        self.widget_column_last_launch.set_widget(
            self.switch_games_column_last_launch)
        self.widget_column_last_launch.set_option_label(
            _("Last launch"))

        self.widget_column_play_time.set_widget(
            self.switch_games_column_play_time)
        self.widget_column_play_time.set_option_label(
            _("Play time"))

        self.widget_column_score.set_widget(
            self.switch_games_column_score)
        self.widget_column_score.set_option_label(
            _("Score"))

        self.widget_column_installed.set_widget(
            self.switch_games_column_installed)
        self.widget_column_installed.set_option_label(
            _("Installed"))

        self.widget_column_flags.set_widget(
            self.switch_games_column_flags)
        self.widget_column_flags.set_option_label(
            _("Flags"))

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

        self.model_consoles = Gtk.ListStore(GdkPixbuf.Pixbuf, str, str, str)
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

        self.image_consoles_add.set_margin_end(6)
        self.image_consoles_add.set_from_icon_name(
            Icons.Symbolic.ADD, Gtk.IconSize.BUTTON)

        self.button_consoles_add.set_image(self.image_consoles_add)
        self.button_consoles_add.set_label(_("Add"))
        self.button_consoles_add.set_tooltip_text(
            _("Add a new console"))

        self.image_consoles_modify.set_margin_end(6)
        self.image_consoles_modify.set_from_icon_name(
            Icons.Symbolic.EDIT, Gtk.IconSize.BUTTON)

        self.button_consoles_modify.set_image(self.image_consoles_modify)
        self.button_consoles_modify.set_label(_("Modify"))
        self.button_consoles_modify.set_tooltip_text(
            _("Modify selected console"))

        self.image_consoles_remove.set_margin_end(6)
        self.image_consoles_remove.set_from_icon_name(
            Icons.Symbolic.REMOVE, Gtk.IconSize.BUTTON)

        self.button_consoles_remove.set_image(self.image_consoles_remove)
        self.button_consoles_remove.set_label(_("Remove"))
        self.button_consoles_remove.set_tooltip_text(
            _("Remove selected console"))

        # ------------------------------------
        #   Emulators
        # ------------------------------------

        self.scroll_emulators = Gtk.ScrolledWindow()
        self.view_emulators = Gtk.Viewport()

        self.scroll_emulators_treeview = Gtk.ScrolledWindow()

        self.model_emulators = Gtk.ListStore(GdkPixbuf.Pixbuf, str, str, str)
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

        self.image_emulators_add.set_margin_end(6)
        self.image_emulators_add.set_from_icon_name(
            Icons.Symbolic.ADD, Gtk.IconSize.BUTTON)

        self.button_emulators_add.set_image(self.image_emulators_add)
        self.button_emulators_add.set_label(_("Add"))
        self.button_emulators_add.set_tooltip_text(
            _("Add a new emulator"))

        self.image_emulators_modify.set_margin_end(6)
        self.image_emulators_modify.set_from_icon_name(
            Icons.Symbolic.EDIT, Gtk.IconSize.BUTTON)

        self.button_emulators_modify.set_image(self.image_emulators_modify)
        self.button_emulators_modify.set_label(_("Modify"))
        self.button_emulators_modify.set_tooltip_text(
            _("Modify selected emulator"))

        self.image_emulators_remove.set_margin_end(6)
        self.image_emulators_remove.set_from_icon_name(
            Icons.Symbolic.REMOVE, Gtk.IconSize.BUTTON)

        self.button_emulators_remove.set_image(self.image_emulators_remove)
        self.button_emulators_remove.set_label(_("Remove"))
        self.button_emulators_remove.set_tooltip_text(
            _("Remove selected emulator"))


    def __init_packing(self):
        """ Initialize widgets packing in main window
        """

        # Main widgets
        self.pack_start(self.frame_stack, True, True)

        self.frame_stack.add(self.box_stack)

        self.box_stack.pack_start(self.sidebar_stack, False, False, 0)
        self.box_stack.pack_start(self.stack, True, True, 0)

        # ------------------------------------
        #   General
        # ------------------------------------

        self.stack.add_titled(
            self.scroll_general, "general", _("General"))

        self.frame_general_behavior.add(self.listbox_general_behavior)
        self.frame_general_editor.add(self.listbox_general_editor)

        self.listbox_general_behavior.add(self.widget_behavior_last_console)
        self.listbox_general_behavior.add(self.widget_behavior_last_column)
        self.listbox_general_behavior.add(self.widget_behavior_hide_consoles)

        self.listbox_general_editor.add(self.widget_editor_lines_visible)
        self.listbox_general_editor.add(self.widget_editor_tab_width)
        self.listbox_general_editor.add(self.widget_editor_colorscheme)
        self.listbox_general_editor.add(self.widget_editor_font)

        self.frame_general_viewer.add(self.listbox_general_viewer)

        self.listbox_general_viewer.add(self.widget_viewer_alternative_viewer)
        self.listbox_general_viewer.add(self.widget_viewer_binary)
        self.listbox_general_viewer.add(self.widget_viewer_options)

        self.grid_general.pack_start(
            self.label_general_behavior, False, False, 0)
        self.grid_general.pack_start(
            self.frame_general_behavior, False, False, 0)
        self.grid_general.pack_start(
            self.label_general_editor, False, False, 0)
        self.grid_general.pack_start(
            self.frame_general_editor, False, False, 0)
        self.grid_general.pack_start(
            self.label_general_viewer, False, False, 0)
        self.grid_general.pack_start(
            self.frame_general_viewer, False, False, 0)

        self.view_general.add(self.grid_general)
        self.scroll_general.add(self.view_general)

        # ------------------------------------
        #   Interface
        # ------------------------------------

        self.stack.add_titled(
            self.scroll_interface, "interface", _("Interface"))

        self.frame_interface_appearance.add(self.listbox_interface_appearance)
        self.frame_interface_toolbar.add(self.listbox_interface_toolbar)
        self.frame_interface_sidebar.add(self.listbox_interface_sidebar)

        self.listbox_interface_appearance.add(
            self.widget_appearance_classic_theme)
        self.listbox_interface_appearance.add(
            self.widget_appearance_header_button)

        self.listbox_interface_toolbar.add(self.widget_toolbar_size)

        self.listbox_interface_sidebar.add(self.widget_sidebar_visible)
        self.listbox_interface_sidebar.add(self.widget_sidebar_position)
        self.listbox_interface_sidebar.add(
            self.widget_sidebar_random_screenshot)
        self.listbox_interface_sidebar.add(self.widget_sidebar_ellipsize)

        self.grid_interface.pack_start(
            self.label_interface_appearance, False, False, 0)
        self.grid_interface.pack_start(
            self.frame_interface_appearance, False, False, 0)
        self.grid_interface.pack_start(
            self.label_interface_toolbar, False, False, 0)
        self.grid_interface.pack_start(
            self.frame_interface_toolbar, False, False, 0)
        self.grid_interface.pack_start(
            self.label_interface_sidebar, False, False, 0)
        self.grid_interface.pack_start(
            self.frame_interface_sidebar, False, False, 0)

        self.view_interface.add(self.grid_interface)
        self.scroll_interface.add(self.view_interface)

        # ------------------------------------
        #   Games
        # ------------------------------------

        self.stack.add_titled(
            self.scroll_games, "games-list", _("Games"))

        self.frame_games_view.add(self.listbox_games_view)

        self.listbox_games_view.add(self.widget_view_grid_lines)
        self.listbox_games_view.add(self.widget_view_tooltip_icon)
        self.listbox_games_view.add(self.widget_view_icons)

        self.frame_games_column.add(self.listbox_games_column)

        self.listbox_games_column.add(self.widget_column_favorite)
        self.listbox_games_column.add(self.widget_column_multiplayer)
        self.listbox_games_column.add(self.widget_column_finish)
        self.listbox_games_column.add(self.widget_column_play)
        self.listbox_games_column.add(self.widget_column_last_launch)
        self.listbox_games_column.add(self.widget_column_play_time)
        self.listbox_games_column.add(self.widget_column_score)
        self.listbox_games_column.add(self.widget_column_installed)
        self.listbox_games_column.add(self.widget_column_flags)

        self.grid_games.pack_start(
            self.label_games_view, False, False, 0)
        self.grid_games.pack_start(
            self.frame_games_view, False, False, 0)
        self.grid_games.pack_start(
            self.label_games_column, False, False, 0)
        self.grid_games.pack_start(
            self.frame_games_column, False, False, 0)

        self.view_games.add(self.grid_games)
        self.scroll_games.add(self.view_games)

        # ------------------------------------
        #   Shortcuts
        # ------------------------------------

        self.stack.add_titled(
            self.scroll_shortcuts, "shortcuts", _("Shortcuts"))

        self.grid_shortcuts.attach(self.label_shortcuts, 0, 0, 1, 1)
        self.grid_shortcuts.attach(self.scroll_shortcuts_treeview, 0, 1, 1, 1)

        self.scroll_shortcuts_treeview.add(self.treeview_shortcuts)

        self.view_shortcuts.add(self.grid_shortcuts)
        self.scroll_shortcuts.add(self.view_shortcuts)

        # ------------------------------------
        #   Consoles
        # ------------------------------------

        self.stack.add_titled(
            self.scroll_consoles, "consoles", _("Consoles"))

        self.grid_consoles.pack_start(
            self.grid_consoles_buttons, False, False, 0)
        self.grid_consoles.pack_start(
            self.scroll_consoles_treeview, True, True, 0)

        self.grid_consoles_buttons.pack_start(
            self.button_consoles_add, False, False, 0)
        self.grid_consoles_buttons.pack_start(
            self.button_consoles_modify, False, False, 0)
        self.grid_consoles_buttons.pack_start(
            self.button_consoles_remove, False, False, 0)

        self.scroll_consoles_treeview.add(self.treeview_consoles)

        self.view_consoles.add(self.grid_consoles)
        self.scroll_consoles.add(self.view_consoles)

        # ------------------------------------
        #   Emulators
        # ------------------------------------

        self.stack.add_titled(
            self.scroll_emulators, "emulators", _("Emulators"))

        self.grid_emulators.pack_start(
            self.grid_emulators_buttons, False, False, 0)
        self.grid_emulators.pack_start(
            self.scroll_emulators_treeview, True, True, 0)

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

        self.button_cancel.connect("clicked", self.__stop_interface)
        self.button_save.connect("clicked", self.__stop_interface)

        # ------------------------------------
        #   General
        # ------------------------------------

        self.listbox_general_behavior.connect(
            "row-activated", self.on_activate_listboxrow)
        self.listbox_general_editor.connect(
            "row-activated", self.on_activate_listboxrow)
        self.listbox_general_viewer.connect(
            "row-activated", self.on_activate_listboxrow)

        self.entry_general_viewer_options.connect(
            "icon-press", on_entry_clear)

        self.switch_general_viewer_alternative_viewer.connect(
            "state-set", self.__on_check_native_viewer)

        # ------------------------------------
        #   Interface
        # ------------------------------------

        self.listbox_interface_appearance.connect(
            "row-activated", self.on_activate_listboxrow)
        self.listbox_interface_toolbar.connect(
            "row-activated", self.on_activate_listboxrow)
        self.listbox_interface_sidebar.connect(
            "row-activated", self.on_activate_listboxrow)

        self.switch_interface_sidebar_visible.connect(
            "state-set", self.__on_check_sidebar)

        # ------------------------------------
        #   Games
        # ------------------------------------

        self.listbox_games_view.connect(
            "row-activated", self.on_activate_listboxrow)
        self.listbox_games_column.connect(
            "row-activated", self.on_activate_listboxrow)

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

        self.widgets = {

            # ------------------------------------
            #   General - Behavior
            # ------------------------------------

            self.widget_behavior_last_console: {
                "type": Gtk.Switch,
                "section": "gem",
                "option": "load_console_startup",
                "fallback": True
            },
            self.widget_behavior_last_column: {
                "type": Gtk.Switch,
                "section": "gem",
                "option": "load_sort_column_startup",
                "fallback": True
            },
            self.widget_behavior_hide_consoles: {
                "type": Gtk.Switch,
                "section": "gem",
                "option": "hide_empty_console",
                "fallback": False
            },

            # ------------------------------------
            #   General - Editor
            # ------------------------------------

            self.widget_editor_lines_visible: {
                "type": Gtk.Switch,
                "section": "editor",
                "option": "lines",
                "fallback": True
            },
            self.widget_editor_tab_width: {
                "type": Gtk.SpinButton,
                "section": "editor",
                "option": "tab",
                "fallback": 4
            },
            self.widget_editor_colorscheme: {
                "type": Gtk.ComboBox,
                "section": "editor",
                "option": "colorscheme",
                "fallback": "classic"
            },
            self.widget_editor_font: {
                "type": Gtk.FontButton,
                "section": "editor",
                "option": "font",
                "fallback": "Sans 12"
            },

            # ------------------------------------
            #   General - Viewer
            # ------------------------------------

            self.widget_viewer_alternative_viewer: {
                "type": Gtk.Switch,
                "section": "viewer",
                "option": "native",
                "fallback": True,
                "reverse": True
            },
            self.widget_viewer_binary: {
                "type": Gtk.FileChooserButton,
                "section": "viewer",
                "option": "binary",
                "fallback": "/usr/bin/feh"
            },
            self.widget_viewer_options: {
                "type": Gtk.Entry,
                "section": "viewer",
                "option": "options",
                "fallback": "-x -d --force-aliasing -Z -q -g 700x600 -B black"
            },

            # ------------------------------------
            #   Interface - Appearance
            # ------------------------------------

            self.widget_appearance_classic_theme: {
                "type": Gtk.Switch,
                "section": "gem",
                "option": "use_classic_theme",
                "fallback": True
            },
            self.widget_appearance_header_button: {
                "type": Gtk.Switch,
                "section": "gem",
                "option": "show_header",
                "fallback": True
            },

            # ------------------------------------
            #   Interface - Toolbar
            # ------------------------------------

            self.widget_toolbar_size: {
                "type": Gtk.ComboBox,
                "section": "gem",
                "option": "toolbar_icons_size",
                "fallback": "small-toolbar"
            },

            # ------------------------------------
            #   Interface - Sidebar
            # ------------------------------------

            self.widget_sidebar_visible: {
                "type": Gtk.Switch,
                "section": "gem",
                "option": "show_sidebar",
                "fallback": True
            },
            self.widget_sidebar_position: {
                "type": Gtk.ComboBox,
                "section": "gem",
                "option": "sidebar_orientation",
                "fallback": "vertical"
            },
            self.widget_sidebar_random_screenshot: {
                "type": Gtk.Switch,
                "section": "gem",
                "option": "show_random_screenshot",
                "fallback": True
            },
            self.widget_sidebar_ellipsize: {
                "type": Gtk.Switch,
                "section": "gem",
                "option": "sidebar_title_ellipsize",
                "fallback": True
            },

            # ------------------------------------
            #   Games - List view
            # ------------------------------------

            self.widget_view_grid_lines: {
                "type": Gtk.ComboBox,
                "section": "gem",
                "option": "games_treeview_lines",
                "fallback": "none"
            },
            self.widget_view_tooltip_icon: {
                "type": Gtk.ComboBox,
                "section": "gem",
                "option": "tooltip_image_type",
                "fallback": "screenshot"
            },
            self.widget_view_icons: {
                "type": Gtk.Switch,
                "section": "gem",
                "option": "use_translucent_icons",
                "fallback": True
            },

            # ------------------------------------
            #   Games - Columns
            # ------------------------------------

            self.widget_column_favorite: {
                "type": Gtk.Switch,
                "section": "columns",
                "option": "favorite",
                "fallback": True
            },
            self.widget_column_multiplayer: {
                "type": Gtk.Switch,
                "section": "columns",
                "option": "multiplayer",
                "fallback": True
            },
            self.widget_column_finish: {
                "type": Gtk.Switch,
                "section": "columns",
                "option": "finish",
                "fallback": True
            },
            self.widget_column_play: {
                "type": Gtk.Switch,
                "section": "columns",
                "option": "play",
                "fallback": True
            },
            self.widget_column_last_launch: {
                "type": Gtk.Switch,
                "section": "columns",
                "option": "last_play",
                "fallback": True
            },
            self.widget_column_play_time: {
                "type": Gtk.Switch,
                "section": "columns",
                "option": "play_time",
                "fallback": True
            },
            self.widget_column_score: {
                "type": Gtk.Switch,
                "section": "columns",
                "option": "score",
                "fallback": True
            },
            self.widget_column_installed: {
                "type": Gtk.Switch,
                "section": "columns",
                "option": "installed",
                "fallback": True
            },
            self.widget_column_flags: {
                "type": Gtk.Switch,
                "section": "columns",
                "option": "flags",
                "fallback": True
            }
        }

        self.load_configuration()

        # ------------------------------------
        #   Window size
        # ------------------------------------

        window_size = Gdk.Geometry()
        window_size.min_width = 640
        window_size.min_height = 480
        window_size.base_width = 800
        window_size.base_height = 600

        try:
            width, height = self.config.get(
                "windows", "preferences", fallback="800x600").split('x')

            window_size.base_width = int(width)
            window_size.base_height = int(height)

            self.window.resize(int(width), int(height))

        except ValueError as error:
            self.logger.error(
                _("Cannot resize preferences window: %s") % str(error))

        self.window.set_geometry_hints(self.window, window_size,
            Gdk.WindowHints.MIN_SIZE | Gdk.WindowHints.BASE_SIZE)

        self.set_size(window_size.base_width, window_size.base_height)

        # ------------------------------------
        #   Widgets
        # ------------------------------------

        self.show_all()

        # Update widget sensitive status
        self.__on_check_sidebar()
        self.__on_check_native_viewer()

        # Avoid to remove console or emulator when games are launched
        if self.parent is not None and len(self.parent.threads) > 0:
            self.button_consoles_remove.set_sensitive(False)
            self.button_emulators_remove.set_sensitive(False)


    def __stop_interface(self, widget=None, *args):
        """ Save data and stop interface

        Other Parameters
        ----------------
        widget : Gtk.Widget, optional
            Object which receive signal (Default: None)
        """

        self.window.hide()

        self.config.modify("windows", "preferences", "%dx%d" % self.get_size())
        self.config.update()


    def save_configuration(self):
        """ Load configuration files and fill widgets
        """

        # Write emulators and consoles data
        self.api.write_data(GEM.Consoles, GEM.Emulators, GEM.Environment)

        for row, data in self.widgets.items():
            widget = row.get_widget()

            if data["type"] == Gtk.ComboBox:
                value = widget.get_active_id()

            elif data["type"] == Gtk.Entry:
                value = widget.get_text()

            elif data["type"] == Gtk.FileChooserButton:
                value = widget.get_filename()

            elif data["type"] == Gtk.FontButton:
                value = widget.get_font()

            elif data["type"] == Gtk.SpinButton:
                value = int(widget.get_value())

            elif data["type"] == Gtk.Switch:
                value = widget.get_active()

                if "reverse" in data and data["reverse"]:
                    value = not value

            self.config.modify(data["section"], data["option"], value)

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

        # Fill toolbar size combobox
        for key, value in self.toolbar.items():
            self.model_interface_toolbar_size.append([value, key])

        # Fill sidebar position combobox
        for key, value in self.sidebar.items():
            self.model_interface_sidebar_position.append([value, key])

        # Fill combobox
        for key, value in self.lines.items():
            self.model_games_view_grid_lines.append([value, key])

        # Fill combobox
        for key, value in self.tooltips.items():
            self.model_games_view_tooltip_icon.append([value, key])

        # ------------------------------------
        #   Editor
        # ------------------------------------

        try:
            require_version("GtkSource", "3.0")

            from gi.repository.GtkSource import StyleSchemeManager

            for path in StyleSchemeManager().get_search_path():
                scheme_path = Path(path).expanduser().resolve()

                for element in sorted(scheme_path.glob("*.xml")):
                    self.model_general_colorscheme.append([element.stem])

        except ImportError:
            self.logger.warning(_("Cannot found GtkSource module"))

            self.widget_editor_tab_width.set_visible(False)
            self.widget_editor_colorscheme.set_visible(False)
            self.widget_editor_lines_visible.set_visible(False)

        except Exception as error:
            self.logger.exception(_("Cannot retrieve style schemes"))

        # ------------------------------------
        #   Configuration file
        # ------------------------------------

        for row, data in self.widgets.items():
            widget = row.get_widget()

            if data["type"] == Gtk.ComboBox:
                widget.set_active_id(self.config.get(
                    data["section"], data["option"], fallback=data["fallback"]))

            elif data["type"] == Gtk.Entry:
                widget.set_text(self.config.get(
                    data["section"], data["option"], fallback=data["fallback"]))

            elif data["type"] == Gtk.FileChooserButton:
                widget.set_filename(self.config.get(
                    data["section"], data["option"], fallback=data["fallback"]))

            elif data["type"] == Gtk.FontButton:
                widget.set_font(self.config.get(
                    data["section"], data["option"], fallback=data["fallback"]))

            elif data["type"] == Gtk.SpinButton:
                widget.set_value(self.config.getint(
                    data["section"], data["option"], fallback=data["fallback"]))

            elif data["type"] == Gtk.Switch:
                value = self.config.getboolean(
                    data["section"], data["option"], fallback=data["fallback"])

                if "reverse" in data and data["reverse"]:
                    value = not value

                widget.set_active(value)

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

            icon = self.parent.get_pixbuf_from_cache(
                "consoles", 48, console.id, console.icon)

            if icon is None:
                icon = self.icons.blank(48)

            check = str()
            if not console.path.exists():
                check = Icons.Symbolic.WARNING

            self.model_consoles.append([
                icon, "<b>%s</b>\n<small>%s</small>" % (
                console.name, console.path), check, console.id])


    def on_load_emulators(self):
        """ Load emulators into treeview
        """

        self.model_emulators.clear()

        self.selection["emulator"] = None

        for emulator in self.api.emulators.values():

            icon = self.parent.get_pixbuf_from_cache(
                "emulators", 48, emulator.id, emulator.icon)

            if icon is None:
                icon = self.icons.blank(48)

            check = str()
            if not emulator.exists:
                check = Icons.Symbolic.WARNING

            self.model_emulators.append([
                icon, "<b>%s</b>\n<small>%s</small>" % (
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
        if event.type == Gdk.EventType.KEY_RELEASE:
            model, treeiter = treeview.get_selection().get_selected()

            if treeiter is not None:
                self.selection[manager] = model.get_value(treeiter, 1)

                if event.keyval == Gdk.KEY_Return:
                    edit = True

        # Mouse
        elif event.type in [Gdk.EventType.BUTTON_PRESS,
            Gdk.EventType._2BUTTON_PRESS] and event.button in (1, 3):

            selection = treeview.get_path_at_pos(int(event.x), int(event.y))
            if selection is not None:
                model = treeview.get_model()

                treeiter = model.get_iter(selection[0])
                self.selection[manager] = model.get_value(treeiter, 1)

                if event.button == 1 and \
                    event.type == Gdk.EventType._2BUTTON_PRESS:
                    edit = True

        if edit:
            self.__on_modify_item(None, manager, True)


    def __on_check_native_viewer(self, widget=None, state=None):
        """ Update native viewer widget from checkbutton state

        Parameters
        ----------
        widget : Gtk.Widget, optional
            Object which receive signal (Default: None)
        state : bool or None, optional
            New status for current widget (Default: None)
        """

        status = self.switch_general_viewer_alternative_viewer.get_active()

        self.widget_viewer_binary.set_sensitive(status)
        self.widget_viewer_options.set_sensitive(status)


    def __on_check_sidebar(self, widget=None, state=None):
        """ Update sidebar widget from checkbutton state

        Parameters
        ----------
        widget : Gtk.Widget, optional
            Object which receive signal (Default: None)
        state : bool or None, optional
            New status for current widget (Default: None)
        """

        status = self.switch_interface_sidebar_visible.get_active()

        self.widget_sidebar_position.set_sensitive(status)
        self.widget_sidebar_random_screenshot.set_sensitive(status)
        self.widget_sidebar_ellipsize.set_sensitive(status)


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

        dialog = None

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

            dialog = ConsolePreferences(self, console, modification)

        elif manager == Manager.EMULATOR:
            emulator = self.api.get_emulator(identifier)

            if modification:
                self.selection["emulator"] = emulator

            dialog = EmulatorPreferences(self, emulator, modification)

        if dialog is not None:

            if dialog.run() == Gtk.ResponseType.APPLY:
                dialog.save()

                if manager == Manager.CONSOLE:
                    self.on_load_consoles()

                elif manager == Manager.EMULATOR:
                    self.on_load_emulators()

            dialog.destroy()

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
            dialog = QuestionDialog(self, data.name,
                _("Would you really want to remove this entry ?"))

            if dialog.run() == Gtk.ResponseType.YES:

                if manager == Manager.CONSOLE:
                    self.api.delete_console(data.id)

                    for size in ("24x24", "48x48"):
                        path = self.parent.get_icon_from_cache(
                            "consoles", size, "%s.png" % data.id)

                        if path.exists():
                            path.unlink()

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
