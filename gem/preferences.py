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
    sys_exit("Cannot found python3-gobject module: %s" % str(error))

# ------------------------------------------------------------------
#   Modules - GEM
# ------------------------------------------------------------------

try:
    from gem import *
    from gem.utils import *
    from gem.windows import *
    from gem.configuration import Configuration

except ImportError as error:
    sys_exit("Cannot found gem module: %s" % str(error))

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


class Preferences(Gtk.Builder):

    def __init__(self, widget=None, parent=None, logger=None):
        """
        Constructor
        """

        Gtk.Builder.__init__(self)

        # Load glade file
        try:
            self.add_from_file(get_data(path_join("ui", "preferences.glade")))

        except OSError as error:
            sys_exit(_("Cannot open interface: %s" % error))

        # ------------------------------------
        #   Initialize variables
        # ------------------------------------

        self.interface = parent

        self.shortcuts = {
            _("Interface"): {
                "gem": [_("Open main log"), "<Control>L"],
                "preferences": [_("Open preferences"), "<Control>P"],
                "quit": [_("Quit application"), "<Control>Q"] },
            _("Game"): {
                "start": [_("Launch a game"), "Return"],
                "favorite": [_("Mark a game as favorite"), "F3"],
                "multiplayer": [_("Mark a game as multiplayer"), "F4"],
                "snapshots": [_("Show game snapshots"), "F5"],
                "log": [_("Open game log"), "F6"],
                "notes": [_("Open game notes"), "F7"] },
            _("Edit"): {
                "remove": [_("Remove a game from database"), "Delete"],
                "delete": [_("Remove a game from disk"), "<Control>Delete"],
                "rename": [_("Rename a game"), "F2"],
                "exceptions": [_("Set specific arguments for a game"), "F12"],
                "open": [_("Open selected game directory"), "<Control>O"],
                "copy": [_("Copy selected game path"), "<Control>C"],
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
                get_data(path_join("ui", "icons")))

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

        # Init signals
        self.__init_signals()

        # Start interface
        self.__start_interface()


    def __init_widgets(self):
        """
        Initialize interface widgets
        """

        # ------------------------------------
        #   Main window
        # ------------------------------------

        self.window = self.get_object("window_preferences")

        # Properties
        self.window.set_title("%s - %s (%s) - %s" % (
            Gem.Name, Gem.Version, Gem.CodeName, _("Preferences")))

        if self.interface is not None:
            self.window.set_transient_for(self.interface.window)

        self.window.set_default_icon_name("gtk-preferences")

        # ------------------------------------
        #   Header
        # ------------------------------------

        label_header_preferences = self.get_object("label_header_preferences")

        # Properties
        label_header_preferences.set_label(_("Preferences"))

        # ------------------------------------
        #   Notebook
        # ------------------------------------

        label_notebook_general = self.get_object("label_notebook_general")
        label_notebook_interface = self.get_object("label_notebook_interface")
        label_notebook_shortcuts = self.get_object("label_notebook_shortcuts")
        label_notebook_consoles = self.get_object("label_notebook_consoles")
        label_notebook_emulators = self.get_object("label_notebook_emulators")

        # Properties
        label_notebook_general.set_label(_("General"))
        label_notebook_interface.set_label(_("Interface"))
        label_notebook_shortcuts.set_label(_("Shortcuts"))
        label_notebook_consoles.set_label(_("Consoles"))
        label_notebook_emulators.set_label(_("Emulators"))

        # ------------------------------------
        #   General - Behavior
        # ------------------------------------

        label_behavior = self.get_object("label_behavior")

        self.check_last_console = self.get_object("check_behavior_last_console")

        # Properties
        label_behavior.set_label(_("Behavior"))

        self.check_last_console.set_label(
            _("Load the last chosen console during startup"))

        # ------------------------------------
        #   General - Viewer
        # ------------------------------------

        label_viewer = self.get_object("label_viewer")
        label_viewer_binary = self.get_object("label_viewer_binary")
        label_viewer_options = self.get_object("label_viewer_options")

        self.check_native_viewer = self.get_object("check_behavior_native")

        self.file_viewer_binary = self.get_object("file_viewer_binary")

        self.entry_viewer_options = self.get_object("entry_viewer_options")

        # Properties
        label_viewer.set_label(_("Viewer"))
        label_viewer_binary.set_label(_("Binary"))
        label_viewer_options.set_label(_("Default options"))

        self.check_native_viewer.set_label(_("Use native viewer"))

        # ------------------------------------
        #   Interface
        # ------------------------------------

        label_interface = self.get_object("label_interface")

        self.check_header = self.get_object("check_header")
        self.check_icons = self.get_object("check_translucent_icons")

        # Properties
        label_interface.set_label(_("Interface"))

        self.check_header.set_label(_("Show close buttons in header bar"))
        self.check_icons.set_label(
            _("use translucent icons in games list instead of empty ones"))

        # ------------------------------------
        #   Interface - Games list
        # ------------------------------------

        label_treeview = self.get_object("label_treeview")
        label_treeview_lines = self.get_object("label_treeview_lines")

        self.model_lines = Gtk.ListStore(str)
        self.combo_lines = self.get_object("combo_treeview_lines")

        cell_lines = Gtk.CellRendererText()

        self.check_play = self.get_object("check_treeview_play")
        self.check_last_play = self.get_object("check_treeview_last_play")
        self.check_play_time = self.get_object("check_treeview_play_time")
        self.check_installed = self.get_object("check_treeview_installed")
        self.check_flags = self.get_object("check_treeview_flags")

        # Properties
        label_treeview.set_label(_("Games list"))
        label_treeview_lines.set_label(_("Show lines in games list"))

        self.model_lines.set_sort_column_id(0, Gtk.SortType.ASCENDING)

        self.combo_lines.set_model(self.model_lines)
        self.combo_lines.set_id_column(0)
        self.combo_lines.pack_start(cell_lines, True)
        self.combo_lines.add_attribute(cell_lines, "text", 0)

        self.check_play.set_label(_("Show \"Launch\" column"))
        self.check_last_play.set_label(_("Show \"Last launch\" column"))
        self.check_play_time.set_label(_("Show \"Play time\" column"))
        self.check_installed.set_label(_("Show \"Installed\" column"))
        self.check_flags.set_label(_("Show \"Flags\" column"))

        # ------------------------------------
        #   Interface - Editor
        # ------------------------------------

        label_editor = self.get_object("label_editor")
        label_editor_colorscheme = self.get_object("label_editor_colorscheme")
        label_editor_font = self.get_object("label_editor_font")

        self.check_lines = self.get_object("check_editor_lines")

        self.model_colorsheme = Gtk.ListStore(str)
        self.combo_colorsheme = self.get_object("combo_colorsheme")

        cell_colorsheme = Gtk.CellRendererText()

        self.font_editor = self.get_object("font_editor")

        # Properties
        label_editor.set_label(_("Editor"))
        label_editor_colorscheme.set_label(_("Colorscheme"))
        label_editor_font.set_label(_("Font"))

        self.check_lines.set_label(_("Show line numbers"))

        self.combo_colorsheme.set_model(self.model_colorsheme)
        self.combo_colorsheme.set_id_column(0)
        self.combo_colorsheme.pack_start(cell_colorsheme, True)
        self.combo_colorsheme.add_attribute(cell_colorsheme, "text", 0)

        # ------------------------------------
        #   Shortcuts
        # ------------------------------------

        label_shortcuts = self.get_object("label_shortcuts")

        self.model_shortcuts = self.get_object("store_shortcuts")
        self.treeview_shortcuts = self.get_object("treeview_shortcuts")

        column_shortcuts_name = self.get_object("column_shortcuts_name")
        column_shortcuts_key = self.get_object("column_shortcuts_key")

        self.cell_shortcuts_keys = self.get_object("cell_shortcuts_key")

        # Properties
        label_shortcuts.set_label(_("You can edit interface shortcuts for "
            "some actions. Click on a shortcut and insert wanted shortcut "
            "with your keyboard."))

        self.model_shortcuts.set_sort_column_id(0, Gtk.SortType.ASCENDING)

        column_shortcuts_name.set_expand(True)
        column_shortcuts_name.set_title(_("Action"))

        column_shortcuts_key.set_expand(True)
        column_shortcuts_key.set_title(_("Shortcut"))

        self.cell_shortcuts_keys.set_property("editable", True)

        # ------------------------------------
        #   Consoles
        # ------------------------------------

        self.model_consoles = self.get_object("store_consoles")
        self.treeview_consoles = self.get_object("treeview_consoles")

        column_consoles_name = self.get_object("column_consoles_name")
        column_consoles_emulator = self.get_object("column_consoles_emulator")

        self.button_console_add = self.get_object("button_console_add")
        self.button_console_modify = self.get_object("button_console_modify")
        self.button_console_remove = self.get_object("button_console_remove")

        # Properties
        self.model_consoles.set_sort_column_id(1, Gtk.SortType.ASCENDING)

        column_consoles_name.set_expand(True)
        column_consoles_name.set_title(_("Console"))

        column_consoles_emulator.set_expand(True)
        column_consoles_emulator.set_title(_("ROMs path"))

        # ------------------------------------
        #   Emulators
        # ------------------------------------

        self.model_emulators = self.get_object("store_emulators")
        self.treeview_emulators = self.get_object("treeview_emulators")

        column_emulators_name = self.get_object("column_emulators_name")
        column_emulators_binary = self.get_object("column_emulators_binary")

        self.button_emulator_add = self.get_object("button_emulator_add")
        self.button_emulator_modify = self.get_object("button_emulator_modify")
        self.button_emulator_remove = self.get_object("button_emulator_remove")

        # Properties
        self.model_emulators.set_sort_column_id(1, Gtk.SortType.ASCENDING)

        column_emulators_name.set_expand(True)
        column_emulators_name.set_title(_("Emulator"))

        column_emulators_binary.set_expand(True)
        column_emulators_binary.set_title(_("Binary"))

        # ------------------------------------
        #   Buttons
        # ------------------------------------

        self.button_cancel = self.get_object("button_cancel")
        self.button_save = self.get_object("button_save")


    def __init_signals(self):
        """
        Initialize widgets signals
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

        self.button_console_add.connect(
            "clicked", self.__on_modify_item, Manager.CONSOLE, False)
        self.button_console_modify.connect(
            "clicked", self.__on_modify_item, Manager.CONSOLE, True)
        self.button_console_remove.connect(
            "clicked", self.__on_remove_item, Manager.CONSOLE)

        # ------------------------------------
        #   Emulators
        # ------------------------------------

        self.treeview_emulators.connect(
            "button-press-event", self.__on_selected_treeview, Manager.EMULATOR)
        self.treeview_emulators.connect(
            "key-release-event", self.__on_selected_treeview, Manager.EMULATOR)

        self.button_emulator_add.connect(
            "clicked", self.__on_modify_item, Manager.EMULATOR, False)
        self.button_emulator_modify.connect(
            "clicked", self.__on_modify_item, Manager.EMULATOR, True)
        self.button_emulator_remove.connect(
            "clicked", self.__on_remove_item, Manager.EMULATOR)

        # ------------------------------------
        #   Buttons
        # ------------------------------------

        self.button_cancel.connect(
            "clicked", self.__stop_interface)
        self.button_save.connect(
            "clicked", self.__stop_interface)


    def __start_interface(self):
        """
        Load data and start interface
        """

        self.load_configuration()

        self.window.show_all()

        if self.interface is None:
            Gtk.main()


    def __stop_interface(self, widget=None, event=None):
        """
        Save data and stop interface
        """

        if widget == self.button_save:

            self.config.modify("gem", "load_console_startup",
                int(self.check_last_console.get_active()))

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
                # self.config.modify("editor", "font",
                    # self.font_editor.get_font_name())

            for text, value, option, sensitive in self.model_shortcuts:
                if value is not None and option is not None:
                    self.config.modify("keys", option, value)

            self.config.update()

            if self.interface is not None:
                self.interface.load_interface()

        self.window.hide()

        if self.interface is None:
            Gtk.main_quit()


    def load_configuration(self):
        """
        Load configuration files and fill widgets
        """

        # ------------------------------------
        #   Interface
        # ------------------------------------

        self.check_last_console.set_active(self.config.getboolean(
            "gem", "load_console_startup", fallback=True))

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

            # self.font_editor.set_font_name(
                # self.config.item("editor", "font", "Sans 12"))

            self.gtksource = True

        except ImportError as error:
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
        """
        Load consoles into treeview
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
                path = ""

            check = self.empty
            if not exists(expanduser(path)):
                check = icon_load("dialog-warning", 16, self.empty)

            self.model_consoles.append([image, name, path, check])


    def on_load_emulators(self):
        """
        Load emulators into treeview
        """

        self.model_emulators.clear()

        self.selection["emulator"] = None

        for name in self.emulators.sections():
            image = icon_from_data(self.emulators.item(name, "icon"),
                self.empty, subfolder="emulators")

            binary = self.emulators.item(name, "binary")

            check, font = self.empty, Pango.Style.NORMAL
            if len(get_binary_path(binary)) == 0:
                check = icon_load("dialog-warning", 16, self.empty)
                font = Pango.Style.OBLIQUE

            self.model_emulators.append([image, name, binary, check, font])


    def __edit_keys(self, widget, path, key, mods, hwcode):
        """
        Edit a shortcut
        """

        treeiter = self.model_shortcuts.get_iter(path)

        if self.model_shortcuts.iter_parent(treeiter) is not None:
            if Gtk.accelerator_valid(key, mods):
                self.model_shortcuts.set_value(
                    treeiter, 1, Gtk.accelerator_name(key, mods))


    def __clear_keys(self, widget, path):
        """
        Clear a shortcut
        """

        treeiter = self.model_shortcuts.get_iter(path)

        if self.model_shortcuts.iter_parent(treeiter) is not None:
            self.model_shortcuts.set_value(treeiter, 1, None)


    def __on_selected_treeview(self, treeview, event, manager):
        """
        Select a console in consoles treeview
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


    def __on_modify_item(self, widget, manager, modification):
        """
        Append or modify an item in the treeview
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
        """
        Remove an item in the treeview
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
            dialog = Question(self, name,
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


class Console(Gtk.Builder):

    def __init__(self, parent, modify):
        """
        Constructor
        """

        Gtk.Builder.__init__(self)

        # Load glade file
        try:
            self.add_from_file(get_data(
                path_join("ui", "preferences_dialogs.glade")))

        except OSError as error:
            raise IOError(_("Cannot open interface: %s" % error))

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
        """
        Initialize interface widgets
        """

        self.window = self.get_object("dialog_console")

        # Properties
        self.window.set_transient_for(self.interface.window)

        self.window.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_APPLY, Gtk.ResponseType.APPLY)

        self.window.set_response_sensitive(Gtk.ResponseType.APPLY, False)

        # ------------------------------------
        #   Init localization
        # ------------------------------------

        label_header = self.get_object("label_header_console")
        label_name = self.get_object("label_console_name")
        label_folder = self.get_object("label_console_folder")
        label_extensions = self.get_object("label_console_extensions")
        label_separator = self.get_object("label_console_separator")
        label_emulator = self.get_object("label_console_emulator")

        # Properties
        label_header.set_label(_("Console"))
        label_name.set_label(_("Name"))
        label_folder.set_label(_("Choose the ROMs folder"))
        label_extensions.set_label(_("ROM's extensions"))
        label_separator.set_label(_("Use ; to separate extensions"))
        label_emulator.set_label(_("Emulator"))

        # ------------------------------------
        #   Init widgets
        # ------------------------------------

        self.entry_name = self.get_object("entry_console_name")
        self.file_folder = self.get_object("file_console_folder")
        self.entry_extensions = self.get_object("entry_console_extensions")

        self.button_console = self.get_object("button_console_image")
        self.image_console = self.get_object("image_console")

        self.model_emulators = Gtk.ListStore(Pixbuf, str)
        self.combo_emulators = self.get_object("combo_emulators")

        cell_emulators_icon = Gtk.CellRendererPixbuf()
        cell_emulators_name = Gtk.CellRendererText()

        # Properties
        self.model_emulators.set_sort_column_id(1, Gtk.SortType.ASCENDING)

        self.combo_emulators.set_model(self.model_emulators)
        self.combo_emulators.set_id_column(1)
        self.combo_emulators.pack_start(cell_emulators_icon, False)
        self.combo_emulators.add_attribute(cell_emulators_icon, "pixbuf", 0)
        self.combo_emulators.pack_start(cell_emulators_name, True)
        self.combo_emulators.add_attribute(cell_emulators_name, "text", 1)

        cell_emulators_icon.set_padding(4, 0)


    def __init_signals(self):
        """
        Initialize widgets signals
        """

        self.entry_name.connect("changed", self.__on_entry_update)
        self.entry_name.connect("icon-press", on_entry_clear)

        self.file_folder.connect("file-set", self.__on_file_set)

        self.entry_extensions.connect("icon-press", on_entry_clear)

        self.button_console.connect("clicked", self.__on_select_icon)


    def __start_interface(self):
        """
        Load data and start interface
        """

        emulators_rows = dict()

        for emulator in self.emulators.sections():
            icon = icon_from_data(self.emulators.item(emulator, "icon"),
                self.empty, 24, 24, "emulators")

            emulators_rows[emulator] = self.model_emulators.append(
                [icon, emulator])

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

            self.window.set_response_sensitive(Gtk.ResponseType.APPLY, True)

        # ------------------------------------
        #   Start dialog
        # ------------------------------------

        need_reload = False

        self.window.show_all()

        response = self.window.run()

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

        self.window.destroy()

        if need_reload:
            self.interface.on_load_consoles()


    def __on_save_data(self):
        """
        Return all the data from interface
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


    def __on_entry_update(self, widget, pos=None, event=None):
        """
        Check if a value is not already used
        """

        name = widget.get_text()

        path = self.file_folder.get_filename()
        if path is None or not exists(expanduser(path)):
            path = None

        self.error = False
        icon, tooltip = None, None

        if len(name) == 0:
            self.error = True

        elif self.consoles.has_section(name):
            icon, tooltip = "dialog-error", _(
                "This console already exist, please, choose another name")

            if not self.modify:
                self.error = True

            elif self.modify and not name == self.console:
                self.error = True

            else:
                icon, tooltip = None, None

        widget.set_icon_from_icon_name(Gtk.EntryIconPosition.PRIMARY, icon)
        widget.set_tooltip_text(tooltip)

        if not self.error and path is not None:
            self.window.set_response_sensitive(Gtk.ResponseType.APPLY, True)
        else:
            self.window.set_response_sensitive(Gtk.ResponseType.APPLY, False)


    def __on_file_set(self, widget):
        """
        Change response button state when user set a file
        """

        path = widget.get_filename()

        if path is None or not exists(expanduser(path)):
            self.window.set_response_sensitive(Gtk.ResponseType.APPLY, False)

        elif len(self.entry_name.get_text()) > 0 and not self.error:
            self.window.set_response_sensitive(Gtk.ResponseType.APPLY, True)


    def __on_select_icon(self, widget):
        """
        Select a new icon
        """

        dialog = IconViewer(self, _("Choose an icon"), self.path, "consoles")

        if dialog.new_path is not None:
            self.image_console.set_from_pixbuf(
                icon_from_data(dialog.new_path, self.empty, 64, 64, "consoles"))

            self.path = dialog.new_path

        dialog.destroy()


class Emulator(Gtk.Builder):

    def __init__(self, parent, modify):
        """
        Constructor
        """

        Gtk.Builder.__init__(self)

        # Load glade file
        try:
            self.add_from_file(get_data(
                path_join("ui", "preferences_dialogs.glade")))

        except OSError as error:
            raise IOError(_("Cannot open interface: %s" % error))

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
        """
        Initialize interface widgets
        """

        self.window = self.get_object("dialog_emulator")

        # Properties
        self.window.set_transient_for(self.interface.window)

        self.window.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_APPLY, Gtk.ResponseType.APPLY)

        self.window.set_response_sensitive(Gtk.ResponseType.APPLY, False)

        # ------------------------------------
        #   Init localization
        # ------------------------------------

        label_header = self.get_object("label_header_emulator")
        label_name = self.get_object("label_emulator_name")
        label_binary = self.get_object("label_emulator_binary")
        label_configuration = self.get_object("label_emulator_configuration")

        label_arguments = self.get_object("label_arguments")
        label_launch = self.get_object("label_emulator_launch")
        label_windowed = self.get_object("label_emulator_windowed")
        label_fullscreen = self.get_object("label_emulator_fullscreen")

        label_files = self.get_object("label_emulator_files")
        label_save = self.get_object("label_emulator_save")
        label_screenshots = self.get_object("label_emulator_screenshots")
        label_regex = self.get_object("label_emulator_regex")

        # Properties
        label_header.set_label(_("Emulator"))
        label_name.set_label(_("Name"))
        label_binary.set_label(_("Binary"))
        label_configuration.set_label(_("Configuration file"))

        label_arguments.set_label(_("Emulator arguments"))
        label_launch.set_label(_("Default options"))
        label_windowed.set_label(_("Windowed"))
        label_fullscreen.set_label(_("Fullscreen"))

        label_files.set_label(_("Regular expressions for files"))
        label_save.set_label(_("Save"))
        label_screenshots.set_label(_("Snapshots"))
        label_regex.set_markup("<i>%s</i>" % (
            _("<name> = ROM filename, <lname> = ROM lowercase filename\n"
            "<rom_path> = ROM folder").replace('>', "&gt;").replace('<', "&lt;")))

        # ------------------------------------
        #   Init widgets
        # ------------------------------------

        self.entry_name = self.get_object("entry_emulator_name")
        self.entry_binary = self.get_object("entry_emulator_binary")
        self.button_binary = self.get_object("button_emulator_binary")
        self.file_configuration = self.get_object("file_emulator_configuration")

        self.button_emulator = self.get_object("button_emulator_image")
        self.image_emulator = self.get_object("image_emulator")

        self.entry_launch = self.get_object("entry_emulator_launch")
        self.entry_windowed = self.get_object("entry_emulator_windowed")
        self.entry_fullscreen = self.get_object("entry_emulator_fullscreen")

        self.entry_save = self.get_object("entry_emulator_save")
        self.entry_screenshots = self.get_object("entry_emulator_screenshots")


    def __init_signals(self):
        """
        Initialize widgets signals
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
        """
        Load data and start interface
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

            self.window.set_response_sensitive(Gtk.ResponseType.APPLY, True)

        # ------------------------------------
        #   Start dialog
        # ------------------------------------

        need_reload = False

        self.window.show_all()

        response = self.window.run()

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

        self.window.destroy()

        if need_reload:
            self.interface.on_load_emulators()


    def __on_save_data(self):
        """
        Return all the data from interface
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


    def __on_entry_update(self, widget, pos=None, event=None):
        """
        Check if a value is not already used
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
            self.window.set_response_sensitive(Gtk.ResponseType.APPLY, True)

        else:
            self.window.set_response_sensitive(Gtk.ResponseType.APPLY, False)


    def __on_file_set(self, widget):
        """
        Change response button state when user set a file
        """

        dialog = Gtk.FileChooserDialog(_("Select a binary"), self.window,
            Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

        if dialog.run() == Gtk.ResponseType.OK:
            self.entry_binary.set_text(dialog.get_filename())

        dialog.destroy()


    def __on_select_icon(self, widget):
        """
        Select a new icon
        """

        dialog = IconViewer(self, _("Choose an icon"), self.path, "emulators")

        if dialog.new_path is not None:
            self.image_emulator.set_from_pixbuf(
                icon_from_data(
                    dialog.new_path, self.empty, 64, 64, "emulators"))

            self.path = dialog.new_path

        dialog.destroy()


class IconViewer(Dialog):

    def __init__(self, parent, title, path, folder):
        """
        Constructor
        """

        Dialog.__init__(self, parent, title, "image-x-generic")

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
        """
        Initialize interface widgets
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

        box = Gtk.Table()

        # Properties
        scrollview.set_border_width(4)
        scrollview.set_policy(
            Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        view.set_shadow_type(Gtk.ShadowType.NONE)

        box.set_border_width(4)
        box.set_row_spacings(8)
        box.set_col_spacings(8)
        box.set_homogeneous(False)

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

        self.file_icon = Gtk.FileChooserWidget()

        # Properties
        self.file_icon.set_current_folder(expanduser('~'))

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

        self.scroll_icons.set_policy(
            Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        # ------------------------------------
        #   Add widgets into interface
        # ------------------------------------

        view.add(box)
        scrollview.add(view)

        self.scroll_icons.add(self.view_icons)

        box.attach(label_option, 0, 1, 0, 1, Gtk.Align.FILL, Gtk.Align.FILL)
        box.attach(self.combo_option, 1, 2, 0, 1, yoptions=Gtk.Align.FILL)
        box.attach(self.file_icon, 0, 2, 1, 2)
        box.attach(self.scroll_icons, 0, 2, 2, 3)

        self.dialog_box.pack_start(scrollview, True, True, 0)


    def __init_signals(self):
        """
        Initialize widgets signals
        """

        self.combo_option.connect(
            "changed", self.set_widgets_sensitive)

        self.view_icons.connect(
            "item_activated", self.__on_selected_icon)


    def __start_interface(self):
        """
        Load data and start interface
        """

        self.load_interface()

        self.show_all()

        self.set_widgets_sensitive()

        response = self.run()

        if response == Gtk.ResponseType.OK:
            self.save_interface()


    def __on_selected_icon(self, iconview, path):
        """
        Select an icon in treeview
        """

        self.response(Gtk.ResponseType.OK)


    def load_interface(self):
        """
        Insert data into interface's widgets
        """

        # Fill options combobox
        self.model_option.append([_("All icons")])
        self.model_option.append([_("Image file")])

        self.file_icon.set_visible(False)
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
                self.file_icon.set_filename(self.path)

        self.combo_option.set_active_id(_("All icons"))


    def save_interface(self):
        """
        Return all the data from interface
        """

        if self.combo_option.get_active_id() == _("All icons"):
            selection = self.view_icons.get_selected_items()[0]

            path = self.model_icons.get_value(
                self.model_icons.get_iter(selection), 1)

        else:
            path = self.file_icon.get_filename()

        if not path == self.path:
            self.new_path = path


    def set_widgets_sensitive(self, widget=None):
        """
        Change sensitive state between radio children
        """

        if self.combo_option.get_active_id() == _("All icons"):
            self.file_icon.set_visible(False)
            self.scroll_icons.set_visible(True)

        else:
            self.file_icon.set_visible(True)
            self.scroll_icons.set_visible(False)
