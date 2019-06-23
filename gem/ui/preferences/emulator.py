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
from gem.engine.utils import get_binary_path
from gem.engine.utils import generate_identifier

from gem.ui.data import Icons
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

except ImportError as error:
    from sys import exit

    exit("Cannot found python3-gobject module: %s" % str(error))

# Translation
from gettext import gettext as _


# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class EmulatorPreferences(CommonWindow):

    def __init__(self, parent, emulator, emulators):
        """ Constructor

        Parameters
        ----------
        parent : Gtk.Window
            Parent object
        emulator : gem.engine.emulator.Emulator
            Emulator object
        modify : bool
            Use edit mode instead of append mode
        """

        CommonWindow.__init__(self,
                              parent,
                              _("Emulator"),
                              Icons.Symbolic.PROPERTIES,
                              parent.use_classic_theme)

        # ------------------------------------
        #   Initialize variables
        # ------------------------------------

        # GEM API instance
        self.api = parent.api
        # Emulator object
        self.emulator = emulator

        # Consoles storage
        self.emulators = emulators

        # GEM config
        self.config = parent.config

        self.path = None

        self.error = False

        if getattr(parent, "interface", None) is not None:
            self.interface = parent.interface

        else:
            self.interface = parent

        # Empty Pixbuf icon
        self.icons = parent.icons

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
        self.grid_configuration = Gtk.Box()

        # Properties
        self.grid_preferences.set_row_spacing(6)
        self.grid_preferences.set_column_spacing(12)
        self.grid_preferences.set_column_homogeneous(False)

        Gtk.StyleContext.add_class(
            self.grid_binary.get_style_context(), "linked")

        Gtk.StyleContext.add_class(
            self.grid_configuration.get_style_context(), "linked")

        # ------------------------------------
        #   Emulator
        # ------------------------------------

        self.label_name = Gtk.Label()
        self.entry_name = Gtk.Entry()

        self.label_icon = Gtk.Label()
        self.entry_icon = Gtk.Entry()

        self.label_binary = Gtk.Label()
        self.entry_binary = Gtk.Entry()

        self.button_binary = Gtk.Button()
        self.image_binary = Gtk.Image()

        self.button_emulator = Gtk.Button()
        self.image_emulator = Gtk.Image()

        # Properties
        self.label_name.set_halign(Gtk.Align.END)
        self.label_name.set_valign(Gtk.Align.CENTER)
        self.label_name.set_justify(Gtk.Justification.RIGHT)
        self.label_name.get_style_context().add_class("dim-label")
        self.label_name.set_text(
            _("Name"))

        self.entry_name.set_hexpand(True)
        self.entry_name.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, Icons.Symbolic.CLEAR)

        self.label_icon.set_halign(Gtk.Align.END)
        self.label_icon.set_valign(Gtk.Align.CENTER)
        self.label_icon.set_justify(Gtk.Justification.RIGHT)
        self.label_icon.get_style_context().add_class("dim-label")
        self.label_icon.set_text(
            _("Icon"))

        self.entry_icon.set_hexpand(True)
        self.entry_icon.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, Icons.Symbolic.CLEAR)

        self.label_binary.set_halign(Gtk.Align.END)
        self.label_binary.set_valign(Gtk.Align.CENTER)
        self.label_binary.set_justify(Gtk.Justification.RIGHT)
        self.label_binary.get_style_context().add_class("dim-label")
        self.label_binary.set_text(
            _("Binary"))

        self.entry_binary.set_hexpand(True)
        self.entry_binary.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, Icons.Symbolic.CLEAR)

        self.image_binary.set_from_icon_name(
            Icons.Symbolic.OPEN, Gtk.IconSize.MENU)

        self.button_emulator.set_size_request(64, 64)
        self.image_emulator.set_size_request(64, 64)

        # ------------------------------------
        #   Emulator - Configuration
        # ------------------------------------

        self.label_configuration = Gtk.Label()
        self.entry_configuration = Gtk.Entry()

        self.button_configuration = Gtk.Button()
        self.image_configuration = Gtk.Image()

        # Properties
        self.label_configuration.set_halign(Gtk.Align.END)
        self.label_configuration.set_justify(Gtk.Justification.RIGHT)
        self.label_configuration.get_style_context().add_class("dim-label")
        self.label_configuration.set_text(
            _("Configuration file"))

        self.entry_configuration.set_hexpand(True)
        self.entry_configuration.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, Icons.Symbolic.CLEAR)

        self.image_configuration.set_from_icon_name(
            Icons.Symbolic.OPEN, Gtk.IconSize.MENU)

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
        self.label_arguments.set_no_show_all(True)
        self.label_arguments.set_halign(Gtk.Align.CENTER)
        self.label_arguments.set_markup(
            "<b>%s</b>" % _("Emulator arguments"))

        self.label_launch.set_halign(Gtk.Align.END)
        self.label_launch.set_valign(Gtk.Align.CENTER)
        self.label_launch.set_no_show_all(True)
        self.label_launch.set_justify(Gtk.Justification.RIGHT)
        self.label_launch.get_style_context().add_class("dim-label")
        self.label_launch.set_label(
            _("Default options"))

        self.entry_launch.set_hexpand(True)
        self.entry_launch.set_no_show_all(True)
        self.entry_launch.set_placeholder_text(
            _("Default arguments to add when launch emulator"))
        self.entry_launch.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, Icons.Symbolic.CLEAR)

        self.label_windowed.set_no_show_all(True)
        self.label_windowed.set_halign(Gtk.Align.END)
        self.label_windowed.set_valign(Gtk.Align.CENTER)
        self.label_windowed.set_justify(Gtk.Justification.RIGHT)
        self.label_windowed.get_style_context().add_class("dim-label")
        self.label_windowed.set_label(
            _("Windowed"))

        self.entry_windowed.set_no_show_all(True)
        self.entry_windowed.set_placeholder_text(
            _("Argument which activate windowded mode"))
        self.entry_windowed.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, Icons.Symbolic.CLEAR)

        self.label_fullscreen.set_no_show_all(True)
        self.label_fullscreen.set_halign(Gtk.Align.END)
        self.label_fullscreen.set_valign(Gtk.Align.CENTER)
        self.label_fullscreen.set_justify(Gtk.Justification.RIGHT)
        self.label_fullscreen.get_style_context().add_class("dim-label")
        self.label_fullscreen.set_label(
            _("Fullscreen"))

        self.entry_fullscreen.set_hexpand(True)
        self.entry_fullscreen.set_no_show_all(True)
        self.entry_fullscreen.set_placeholder_text(
            _("Argument which activate fullscreen mode"))
        self.entry_fullscreen.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, Icons.Symbolic.CLEAR)

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
        self.label_files.set_no_show_all(True)
        self.label_files.set_halign(Gtk.Align.CENTER)
        self.label_files.set_markup(
            "<b>%s</b>" % _("Files patterns"))

        self.label_save.set_no_show_all(True)
        self.label_save.set_halign(Gtk.Align.END)
        self.label_save.set_valign(Gtk.Align.CENTER)
        self.label_save.set_justify(Gtk.Justification.RIGHT)
        self.label_save.get_style_context().add_class("dim-label")
        self.label_save.set_label(
            _("Save"))

        self.entry_save.set_hexpand(True)
        self.entry_save.set_no_show_all(True)
        self.entry_save.set_placeholder_text(
            _("Pattern to detect savestates files"))
        self.entry_save.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, Icons.Symbolic.CLEAR)

        self.label_screenshots.set_no_show_all(True)
        self.label_screenshots.set_halign(Gtk.Align.END)
        self.label_screenshots.set_valign(Gtk.Align.CENTER)
        self.label_screenshots.set_justify(Gtk.Justification.RIGHT)
        self.label_screenshots.get_style_context().add_class("dim-label")
        self.label_screenshots.set_label(
            _("Snapshots"))

        self.entry_screenshots.set_hexpand(True)
        self.entry_screenshots.set_no_show_all(True)
        self.entry_screenshots.set_placeholder_text(
            _("Pattern to detect screenshots files"))
        self.entry_screenshots.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, Icons.Symbolic.CLEAR)

        self.label_joker.set_use_markup(True)
        self.label_joker.set_no_show_all(True)
        self.label_joker.set_halign(Gtk.Align.END)
        self.label_joker.set_valign(Gtk.Align.CENTER)
        self.label_joker.set_justify(Gtk.Justification.RIGHT)
        self.label_joker.get_style_context().add_class("dim-label")
        self.label_joker.set_markup(
            "<i>%s</i>" % _("* can be used as joker"))

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

        # Emulator grid
        self.grid_preferences.attach(self.label_name, 0, 0, 1, 1)
        self.grid_preferences.attach(self.entry_name, 1, 0, 1, 1)

        self.grid_preferences.attach(self.label_icon, 0, 1, 1, 1)
        self.grid_preferences.attach(self.entry_icon, 1, 1, 1, 1)

        self.grid_preferences.attach(self.label_binary, 0, 2, 1, 1)
        self.grid_preferences.attach(self.grid_binary, 1, 2, 2, 1)

        self.grid_preferences.attach(self.button_emulator, 2, 0, 1, 2)

        self.grid_preferences.attach(self.label_configuration, 0, 3, 1, 1)
        self.grid_preferences.attach(self.grid_configuration, 1, 3, 2, 1)

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

        # Emulator icon
        self.button_emulator.set_image(self.image_emulator)

        # Emulator binary
        self.button_binary.set_image(self.image_binary)

        self.grid_binary.pack_start(self.entry_binary, True, True, 0)
        self.grid_binary.pack_start(self.button_binary, False, False, 0)

        # Emulator configuration
        self.button_configuration.set_image(self.image_configuration)

        self.grid_configuration.pack_start(
            self.entry_configuration, True, True, 0)
        self.grid_configuration.pack_start(
            self.button_configuration, False, False, 0)

    def __init_signals(self):
        """ Initialize widgets signals
        """

        self.entry_name.connect("changed", self.__on_entry_update)
        self.entry_name.connect("icon-press", on_entry_clear)

        self.entry_icon.connect("changed", self.__on_icon_update)
        self.entry_icon.connect("icon-press", on_entry_clear)

        self.entry_binary.connect("changed", self.__on_entry_update)
        self.entry_binary.connect("icon-press", on_entry_clear)

        self.entry_configuration.connect("icon-press", on_entry_clear)

        self.entry_launch.connect("icon-press", on_entry_clear)
        self.entry_windowed.connect("icon-press", on_entry_clear)
        self.entry_fullscreen.connect("icon-press", on_entry_clear)

        self.entry_save.connect("icon-press", on_entry_clear)
        self.entry_screenshots.connect("icon-press", on_entry_clear)

        self.button_emulator.connect("clicked", self.__on_select_icon)
        self.button_configuration.connect("clicked", self.__on_file_set)
        self.button_binary.connect("clicked", self.__on_file_set)

        self.check_advanced.connect("toggled", self.__on_check_advanced_mode)

    def __start_interface(self):
        """ Load data and start interface
        """

        self.add_button(_("Close"), Gtk.ResponseType.CLOSE)
        self.add_button(_("Accept"), Gtk.ResponseType.APPLY, Gtk.Align.END)

        self.add_help(self.help_data)

        self.set_response_sensitive(Gtk.ResponseType.APPLY, False)

        # ------------------------------------
        #   Init data
        # ------------------------------------

        if self.emulator is not None and len(self.emulator.id) > 0:
            self.entry_name.set_text(self.emulator.name)

            # Binary
            self.entry_binary.set_text(str(self.emulator.binary))

            # Configuration
            folder = self.emulator.configuration
            if folder is not None and folder.exists():
                self.entry_configuration.set_text(str(folder))

            # Icon
            self.path = self.emulator.icon

            if self.path is not None:
                self.entry_icon.set_text(str(self.path))

                icon = self.interface.get_pixbuf_from_cache(
                    "emulators", 64, self.emulator.id, self.emulator.icon)

                if icon is None:
                    icon = self.icons.blank(64)

                self.image_emulator.set_from_pixbuf(icon)

            # Regex
            if self.emulator.savestates is not None:
                self.entry_save.set_text(str(self.emulator.savestates))
            if self.emulator.screenshots is not None:
                self.entry_screenshots.set_text(str(self.emulator.screenshots))

            # Arguments
            if self.emulator.default is not None:
                self.entry_launch.set_text(self.emulator.default)
            if self.emulator.windowed is not None:
                self.entry_windowed.set_text(self.emulator.windowed)
            if self.emulator.fullscreen is not None:
                self.entry_fullscreen.set_text(self.emulator.fullscreen)

            self.set_response_sensitive(Gtk.ResponseType.APPLY, True)

        # ------------------------------------
        #   Advanded mode
        # ------------------------------------

        self.check_advanced.set_active(
            self.config.getboolean("advanced", "emulator", fallback=False))

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

        value = self.entry_binary.get_text().strip()
        if len(value) > 0:
            data["binary"] = Path(value).expanduser()

        value = self.entry_icon.get_text().strip()
        if len(value) > 0:
            data["icon"] = Path(value).expanduser()

        value = self.entry_configuration.get_text().strip()
        if len(value) > 0:
            data["configuration"] = Path(value).expanduser()

        value = self.entry_save.get_text().strip()
        if len(value) > 0:
            data["savestates"] = str(Path(value).expanduser())

        value = self.entry_screenshots.get_text().strip()
        if len(value) > 0:
            data["screenshots"] = str(Path(value).expanduser())

        value = self.entry_launch.get_text().strip()
        if len(value) > 0:
            data["default"] = value

        value = self.entry_windowed.get_text().strip()
        if len(value) > 0:
            data["windowed"] = value

        value = self.entry_fullscreen.get_text().strip()
        if len(value) > 0:
            data["fullscreen"] = value

        # Avanced view status
        status = self.config.getboolean("advanced", "emulator", fallback=False)

        if not self.check_advanced.get_active() == status:
            self.config.modify(
                "advanced", "emulator", self.check_advanced.get_active())
            self.config.update()

        return data

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

        if len(name) > 0:

            # Always check identifier to avoid NES != NeS
            name = generate_identifier(name)

            # Check if current emulator exists in database
            if name in self.emulators:

                if self.emulator is None:
                    self.error = True

                # Avoid to use a name which already exists in database
                elif not self.emulator.id == name:
                    self.error = True

                if self.error:
                    icon = Icons.ERROR
                    tooltip = _("This emulator already exist, please, "
                                "choose another name")

        else:
            self.error = True

        self.entry_name.set_icon_from_icon_name(
            Gtk.EntryIconPosition.PRIMARY, icon)
        self.entry_name.set_tooltip_text(tooltip)

        # ------------------------------------
        #   Emulator binary
        # ------------------------------------

        icon = None
        tooltip = None

        binary_path = self.entry_binary.get_text()

        # No binary available in entry
        if len(binary_path) == 0:
            self.error = True

        # Binary not exists in available $PATH variable
        elif len(get_binary_path(binary_path)) == 0:
            self.error = True

            icon = Icons.ERROR
            tooltip = _("This binary not exist, please, check the path")

        if widget == self.entry_binary:
            self.entry_binary.set_icon_from_icon_name(
                Gtk.EntryIconPosition.PRIMARY, icon)
            self.entry_binary.set_tooltip_text(tooltip)

        # ------------------------------------
        #   Manage error
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

        self.set_icon(self.image_emulator, self.path)

    def __on_file_set(self, widget):
        """ Change response button state when user set a file

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        if widget == self.button_binary:
            title = _("Select a binary")

            filename = self.entry_binary.get_text().strip()

        elif widget == self.button_configuration:
            title = _("Select a configuration file")

            filename = self.entry_configuration.get_text().strip()

        path = None
        if len(filename) > 0:
            path = Path(filename).expanduser()

            if widget == self.button_binary and not path.exists():
                paths = get_binary_path(filename)

                if len(paths) > 0:
                    path = Path(paths[0]).expanduser()

        # ------------------------------------
        #   Open dialog
        # ------------------------------------

        dialog = Gtk.FileChooserDialog(
            title=title,
            action=Gtk.FileChooserAction.OPEN,
            transient_for=self.interface,
            use_header_bar=not self.use_classic_theme)

        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK)

        if path is not None:
            dialog.set_filename(str(path))

        if dialog.run() == Gtk.ResponseType.OK:

            if widget == self.button_binary:
                self.entry_binary.set_text(dialog.get_filename())

            elif widget == self.button_configuration:
                self.entry_configuration.set_text(dialog.get_filename())

        dialog.destroy()

    def __on_select_icon(self, widget):
        """ Select a new icon

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        dialog = IconsDialog(self, _("Choose an icon"), self.path, "emulators")

        if dialog.new_path is not None:
            self.path = Path(dialog.new_path).expanduser()

            # Update icon thumbnail
            self.set_icon(self.image_emulator, self.path)

            # Update icon entry
            self.entry_icon.set_text(dialog.new_path)

        dialog.destroy()

    def __on_check_advanced_mode(self, *args):
        """ Check advanced checkbutton status and update widgets sensitivity
        """

        status = self.check_advanced.get_active()

        self.label_arguments.set_visible(status)
        self.label_launch.set_visible(status)
        self.entry_launch.set_visible(status)
        self.label_windowed.set_visible(status)
        self.entry_windowed.set_visible(status)
        self.label_fullscreen.set_visible(status)
        self.entry_fullscreen.set_visible(status)
        self.label_files.set_visible(status)
        self.label_save.set_visible(status)
        self.entry_save.set_visible(status)
        self.label_screenshots.set_visible(status)
        self.entry_screenshots.set_visible(status)
        self.label_joker.set_visible(status)

    def set_icon(self, widget, path, size=64):
        """ Set thumbnail icon from a specific path

        Parameters
        ----------
        widget : Gtk.Widget
            Icon widget to update
        path : str
            Icon path
        size : int, optional
            Icon size in pixels (Default: 64)
        """

        # Retrieve an empty icon
        icon = self.icons.blank(size)

        if path is not None:

            # Check icon from icons theme
            if not path.exists():

                # Retrieve icon from collection
                if self.icons.theme.has_icon(str(path)):
                    icon = self.icons.theme.load_icon(
                        str(path), size, Gtk.IconLookupFlags.FORCE_SIZE)

            # Retrieve icon from file
            elif path.is_file():

                # Check the file mime-type to avoid non-image file
                if magic_from_file(path, mime=True).startswith("image/"):
                    icon = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                        str(path), size, size, True)

        widget.set_from_pixbuf(icon)
