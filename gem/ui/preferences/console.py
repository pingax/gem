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
from gem.engine.utils import generate_identifier

from gem.ui.data import Icons
from gem.ui.data import Folders
from gem.ui.utils import on_entry_clear
from gem.ui.utils import magic_from_file
from gem.ui.dialog.icons import IconsDialog
from gem.ui.widgets.window import CommonWindow

# GObject
try:
    from gi import require_version

    require_version("Gtk", "3.0")

    from gi.repository import Gtk
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

class ConsolePreferences(CommonWindow):

    def __init__(self, parent, console, consoles, emulators):
        """ Constructor

        Parameters
        ----------
        parent : Gtk.Window
            Parent object (Default: None)
        console : gem.engine.console.Console
            Console object
        emulators : list
            Emulator objects storage
        """

        CommonWindow.__init__(self,
                              parent,
                              _("Console"),
                              Icons.Symbolic.GAMING,
                              parent.use_classic_theme)

        # ------------------------------------
        #   Initialize variables
        # ------------------------------------

        # GEM API instance
        self.api = parent.api
        # Console object
        self.console = console

        # Consoles storage
        self.consoles = consoles
        # Emulators storage
        self.emulators = emulators

        # GEM config
        self.config = parent.config

        self.path = None

        self.error = False
        self.file_error = False
        self.emulator_error = False

        if getattr(parent, "interface", None) is not None:
            self.interface = parent.interface

        else:
            self.interface = parent

        # Empty Pixbuf icon
        self.icons = parent.icons

        self.help_data = {
            "order": [
                "Description",
                "Extensions",
                _("Extensions examples"),
                "Expressions"
            ],
            "Description": [
                _("A console represent a games library. You can specify a "
                  "default emulator which is used by this console and "
                  "extensions which is readable by this emulator.")
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

        self.label_icon = Gtk.Label()
        self.entry_icon = Gtk.Entry()

        self.label_folder = Gtk.Label()
        self.file_folder = Gtk.FileChooserButton()

        self.button_console = Gtk.Button()
        self.image_console = Gtk.Image()

        self.label_favorite = Gtk.Label()
        self.switch_favorite = Gtk.Switch()

        self.label_recursive = Gtk.Label()
        self.switch_recursive = Gtk.Switch()

        # Properties
        self.label_name.set_halign(Gtk.Align.END)
        self.label_name.set_valign(Gtk.Align.CENTER)
        self.label_name.set_justify(Gtk.Justification.RIGHT)
        self.label_name.get_style_context().add_class("dim-label")
        self.label_name.set_text(_("Name"))

        self.entry_name.set_hexpand(True)
        self.entry_name.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, Icons.Symbolic.CLEAR)

        self.label_icon.set_halign(Gtk.Align.END)
        self.label_icon.set_valign(Gtk.Align.CENTER)
        self.label_icon.set_justify(Gtk.Justification.RIGHT)
        self.label_icon.get_style_context().add_class("dim-label")
        self.label_icon.set_text(_("Icon"))

        self.entry_icon.set_hexpand(True)
        self.entry_icon.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, Icons.Symbolic.CLEAR)

        self.label_folder.set_halign(Gtk.Align.END)
        self.label_folder.set_valign(Gtk.Align.CENTER)
        self.label_folder.set_justify(Gtk.Justification.RIGHT)
        self.label_folder.get_style_context().add_class("dim-label")
        self.label_folder.set_text(_("Games folder"))

        self.file_folder.set_action(Gtk.FileChooserAction.SELECT_FOLDER)
        self.file_folder.set_hexpand(True)

        self.button_console.set_size_request(64, 64)
        self.image_console.set_size_request(64, 64)

        self.label_favorite.set_margin_top(12)
        self.label_favorite.set_label(_("Favorite"))
        self.label_favorite.set_halign(Gtk.Align.END)
        self.label_favorite.set_valign(Gtk.Align.CENTER)
        self.label_favorite.get_style_context().add_class("dim-label")

        self.switch_favorite.set_margin_top(12)
        self.switch_favorite.set_halign(Gtk.Align.START)

        self.label_recursive.set_margin_top(12)
        self.label_recursive.set_no_show_all(True)
        self.label_recursive.set_label(_("Recursive"))
        self.label_recursive.set_halign(Gtk.Align.END)
        self.label_recursive.set_valign(Gtk.Align.CENTER)
        self.label_recursive.get_style_context().add_class("dim-label")

        self.switch_recursive.set_margin_top(12)
        self.switch_recursive.set_no_show_all(True)
        self.switch_recursive.set_halign(Gtk.Align.START)

        # ------------------------------------
        #   Emulator options
        # ------------------------------------

        self.label_emulator = Gtk.Label()

        self.label_default = Gtk.Label()

        self.model_emulators = Gtk.ListStore(GdkPixbuf.Pixbuf, str, str)
        self.combo_emulators = Gtk.ComboBox()

        cell_emulators_icon = Gtk.CellRendererPixbuf()
        cell_emulators_name = Gtk.CellRendererText()

        self.label_extensions = Gtk.Label()
        self.entry_extensions = Gtk.Entry()

        # Properties
        self.label_emulator.set_margin_top(18)
        self.label_emulator.set_hexpand(True)
        self.label_emulator.set_use_markup(True)
        self.label_emulator.set_halign(Gtk.Align.CENTER)
        self.label_emulator.set_markup("<b>%s</b>" % _("Default emulator"))

        self.label_default.set_halign(Gtk.Align.END)
        self.label_default.set_valign(Gtk.Align.CENTER)
        self.label_default.set_justify(Gtk.Justification.RIGHT)
        self.label_default.get_style_context().add_class("dim-label")
        self.label_default.set_text(_("Emulator"))

        self.model_emulators.set_sort_column_id(1, Gtk.SortType.ASCENDING)

        self.combo_emulators.set_hexpand(True)
        self.combo_emulators.set_model(self.model_emulators)
        self.combo_emulators.set_id_column(2)
        self.combo_emulators.pack_start(cell_emulators_icon, False)
        self.combo_emulators.add_attribute(cell_emulators_icon, "pixbuf", 0)
        self.combo_emulators.pack_start(cell_emulators_name, True)
        self.combo_emulators.add_attribute(cell_emulators_name, "text", 1)

        cell_emulators_icon.set_padding(4, 0)

        self.label_extensions.set_halign(Gtk.Align.END)
        self.label_extensions.set_valign(Gtk.Align.CENTER)
        self.label_extensions.set_justify(Gtk.Justification.RIGHT)
        self.label_extensions.get_style_context().add_class("dim-label")
        self.label_extensions.set_text(_("Extensions"))

        self.entry_extensions.set_hexpand(True)
        self.entry_extensions.set_tooltip_text(
            _("Use space to separate extensions"))
        self.entry_extensions.set_placeholder_text(
            _("Use space to separate extensions"))
        self.entry_extensions.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, Icons.Symbolic.CLEAR)

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
        self.scroll_ignores.set_shadow_type(Gtk.ShadowType.OUT)
        self.scroll_ignores.add(self.viewport_ignores)
        self.scroll_ignores.set_size_request(-1, 200)
        self.scroll_ignores.set_no_show_all(True)

        self.label_ignores.set_margin_top(18)
        self.label_ignores.set_hexpand(True)
        self.label_ignores.set_use_markup(True)
        self.label_ignores.set_no_show_all(True)
        self.label_ignores.set_halign(Gtk.Align.CENTER)
        self.label_ignores.set_markup(
            "<b>%s</b>" % _("Regular expressions for ignored files"))

        self.image_ignores_add.set_from_icon_name(
            Icons.Symbolic.ADD, Gtk.IconSize.BUTTON)
        self.image_ignores_remove.set_from_icon_name(
            Icons.Symbolic.REMOVE, Gtk.IconSize.BUTTON)

        self.button_ignores_add.set_no_show_all(True)
        self.button_ignores_remove.set_no_show_all(True)

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

        # ------------------------------------
        #   Advanced mode
        # ------------------------------------

        self.check_advanced = Gtk.CheckButton()

        # Properties
        self.check_advanced.set_label(_("Advanced mode"))

    def __init_packing(self):
        """ Initialize widgets packing in main window
        """

        # Main widgets
        self.pack_start(self.grid_preferences, True, True)
        self.pack_start(self.check_advanced, False, False)

        # Console grid
        self.grid_preferences.attach(self.label_name, 0, 0, 1, 1)
        self.grid_preferences.attach(self.entry_name, 1, 0, 1, 1)

        self.grid_preferences.attach(self.label_icon, 0, 1, 1, 1)
        self.grid_preferences.attach(self.entry_icon, 1, 1, 1, 1)

        self.grid_preferences.attach(self.label_folder, 0, 2, 1, 1)
        self.grid_preferences.attach(self.file_folder, 1, 2, 2, 1)

        self.grid_preferences.attach(self.button_console, 2, 0, 1, 2)

        self.grid_preferences.attach(self.label_favorite, 0, 3, 1, 1)
        self.grid_preferences.attach(self.switch_favorite, 1, 3, 2, 1)

        self.grid_preferences.attach(self.label_recursive, 0, 4, 1, 1)
        self.grid_preferences.attach(self.switch_recursive, 1, 4, 2, 1)

        self.grid_preferences.attach(self.label_emulator, 0, 5, 3, 1)

        self.grid_preferences.attach(self.label_default, 0, 6, 1, 1)
        self.grid_preferences.attach(self.combo_emulators, 1, 6, 2, 1)

        self.grid_preferences.attach(self.label_extensions, 0, 7, 1, 1)
        self.grid_preferences.attach(self.entry_extensions, 1, 7, 2, 1)

        self.grid_preferences.attach(self.label_ignores, 0, 8, 3, 1)
        self.grid_preferences.attach(self.grid_ignores, 0, 9, 3, 1)

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

        self.entry_name.connect("changed", self.__on_entry_update)
        self.entry_name.connect("icon-press", on_entry_clear)

        self.entry_icon.connect("changed", self.__on_icon_update)
        self.entry_icon.connect("icon-press", on_entry_clear)

        self.file_folder.connect("file-set", self.__on_entry_update)

        self.entry_extensions.connect("changed", self.__on_entry_update)
        self.entry_extensions.connect("icon-press", on_entry_clear)

        self.button_console.connect("clicked", self.__on_select_icon)

        self.combo_emulators.connect("changed", self.__on_entry_update)

        self.cell_ignores.connect("edited", self.__on_edited_cell)

        self.button_ignores_add.connect("clicked", self.__on_append_item)
        self.button_ignores_remove.connect("clicked", self.__on_remove_item)

        self.check_advanced.connect("toggled", self.__on_check_advanced_mode)

    def __start_interface(self):
        """ Load data and start interface
        """

        self.add_button(_("Close"), Gtk.ResponseType.CLOSE)
        self.add_button(_("Accept"), Gtk.ResponseType.APPLY, Gtk.Align.END)

        self.add_help(self.help_data)

        self.set_response_sensitive(Gtk.ResponseType.APPLY, False)

        emulators_rows = dict()

        for emulator in self.emulators.values():

            if emulator.exists:

                icon = self.interface.get_pixbuf_from_cache(
                    "emulators",
                    22,
                    emulator.id,
                    emulator.icon,
                    use_cache=False)

                if icon is None:
                    icon = self.icons.blank(22)

                emulators_rows[emulator.id] = self.model_emulators.append(
                    [icon, emulator.name, emulator.id])

        self.combo_emulators.set_wrap_width(int(len(self.model_emulators) / 6))

        # ------------------------------------
        #   Init data
        # ------------------------------------

        if self.console is not None and len(self.console.id) > 0:
            self.entry_name.set_text(self.console.name)

            # Folder
            folder = self.console.path
            if folder is not None and folder.exists():
                self.file_folder.set_current_folder(str(folder))

            # Favorite status
            self.switch_favorite.set_active(self.console.favorite)

            # Recursive status
            self.switch_recursive.set_active(self.console.recursive)

            # Extensions
            self.entry_extensions.set_text(' '.join(self.console.extensions))

            # Icon
            self.path = self.console.icon

            if self.path is not None:
                self.entry_icon.set_text(str(self.path))

                icon = self.interface.get_pixbuf_from_cache(
                    "consoles", 64, self.console.id, self.console.icon)

                if icon is None:
                    icon = self.icons.blank(64)

                self.image_console.set_from_pixbuf(icon)

            # Ignores
            for ignore in self.console.ignores:
                self.model_ignores.append([ignore])

            # Emulator
            emulator = self.console.emulator
            if emulator is not None and emulator.id in emulators_rows:
                self.combo_emulators.set_active_id(emulator.id)

            self.__on_entry_update()

        # ------------------------------------
        #   Advanded mode
        # ------------------------------------

        self.check_advanced.set_active(
            self.config.getboolean("advanced", "console", fallback=False))

        self.__on_check_advanced_mode()

    def save(self):
        """ Save modification
        """

        self.section = self.entry_name.get_text().strip()

        if len(self.section) == 0:
            return None

        data = {
            "id": generate_identifier(self.section),
            "name": self.section
        }

        value = self.file_folder.get_filename()
        if value is not None and len(value) > 0:
            data["path"] = Path(value).expanduser()

        value = self.entry_icon.get_text().strip()
        if len(value) > 0:
            data["icon"] = Path(value).expanduser()

        value = self.entry_extensions.get_text().strip()
        if len(value) > 0:
            data["extensions"] = value.split()

        data["ignores"] = list()
        for row in self.model_ignores:
            element = self.model_ignores.get_value(row.iter, 0)

            if element is not None and len(element) > 0:
                data["ignores"].append(element)

        data["favorite"] = self.switch_favorite.get_active()
        data["recursive"] = self.switch_recursive.get_active()

        data["emulator"] = self.api.get_emulator(
            self.combo_emulators.get_active_id())

        # Avanced view status
        status = self.config.getboolean("advanced", "console", fallback=False)

        if not self.check_advanced.get_active() == status:
            self.config.modify(
                "advanced", "console", self.check_advanced.get_active())
            self.config.update()

        return data

    def __on_entry_update(self, widget=None):
        """ Update dialog response sensitive status

        Parameters
        ----------
        widget : Gtk.Widget, optional
            Object which receive signal
        """

        self.error = False

        # ------------------------------------
        #   Console name
        # ------------------------------------

        icon = None
        tooltip = None

        name = self.entry_name.get_text()

        if len(name) > 0:

            # Always check identifier to avoid NES != NeS
            name = generate_identifier(name)

            # Check if current console exists in database
            if name in self.consoles.keys():

                if self.console is None:
                    self.error = True

                # Avoid to use a name which already exists in database
                elif not self.console.id == name:
                    self.error = True

                if self.error:
                    icon = Icons.ERROR
                    tooltip = _("This console already exist, please, "
                                "choose another name")

        else:
            self.error = True

        self.entry_name.set_icon_from_icon_name(
            Gtk.EntryIconPosition.PRIMARY, icon)
        self.entry_name.set_tooltip_text(tooltip)

        # ------------------------------------
        #   Console roms folder
        # ------------------------------------

        path = self.file_folder.get_filename()

        if path is None or not Path(path).expanduser().exists():
            self.error = True

        # ------------------------------------
        #   Console roms extensions
        # ------------------------------------

        extensions = self.entry_extensions.get_text().strip()

        if len(extensions) == 0:
            self.error = True

        # ------------------------------------
        #   Console emulator
        # ------------------------------------

        if self.combo_emulators.get_active_id() is None:
            self.error = True

        # ------------------------------------
        #   Start dialog
        # ------------------------------------

        self.set_response_sensitive(Gtk.ResponseType.APPLY, not self.error)

    def __on_icon_update(self, widget):
        """ Update icon thumbnail when the icon entry is update

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        value = widget.get_text()

        self.path = None
        if len(value) > 0:
            self.path = Path(value).expanduser()

        self.set_icon(self.image_console, self.path)

    def __on_select_icon(self, widget):
        """ Select a new icon

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        dialog = IconsDialog(self, _("Choose an icon"), self.path, "consoles")

        if dialog.new_path is not None:
            self.path = Path(dialog.new_path).expanduser()

            # Update icon thumbnail
            self.set_icon(self.image_console, self.path)

            # Update icon entry
            self.entry_icon.set_text(dialog.new_path)

        dialog.destroy()

    def __on_append_item(self, widget):
        """ Append a new row in treeview

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        self.model_ignores.append([str()])

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

    def __on_check_advanced_mode(self, *args):
        """ Check advanced checkbutton status and update widgets sensitivity
        """

        status = self.check_advanced.get_active()

        self.label_recursive.set_visible(status)
        self.switch_recursive.set_visible(status)

        self.label_ignores.set_visible(status)
        self.grid_ignores.set_visible(status)
        self.scroll_ignores.set_visible(status)
        self.viewport_ignores.set_visible(status)
        self.treeview_ignores.set_visible(status)
        self.image_ignores_add.set_visible(status)
        self.button_ignores_add.set_visible(status)
        self.image_ignores_remove.set_visible(status)
        self.button_ignores_remove.set_visible(status)

    def set_icon(self, widget, path, size=64):
        """ Set thumbnail icon from a specific path

        Parameters
        ----------
        widget : Gtk.Widget
            Icon widget to update
        path : pathlib.Path
            Icon path
        size : int, optional
            Icon size in pixels (Default: 64)
        """

        # Retrieve an empty icon
        icon = self.icons.blank(size)

        if path is not None:

            # Check icon from icons theme
            if not path.exists():
                collection_path = Folders.LOCAL.joinpath(
                    "icons", "%s.png" % path)

                # Retrieve icon from collection
                if collection_path.exists() and collection_path.is_file():

                    # Check the file mime-type to avoid non-image file
                    if magic_from_file(collection_path,
                                       mime=True).startswith("image/"):

                        icon = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                            str(collection_path), size, size, True)

            # Retrieve icon from file
            elif path.is_file():

                # Check the file mime-type to avoid non-image file
                if magic_from_file(path, mime=True).startswith("image/"):
                    icon = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                        str(path), size, size, True)

        widget.set_from_pixbuf(icon)
