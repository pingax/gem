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
from gem.engine.utils import parse_timedelta

from gem.ui.data import Icons
from gem.ui.utils import replace_for_markup
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

# System
from os import environ

# Translation
from gettext import gettext as _


# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class ParametersDialog(CommonWindow):

    def __init__(self, parent, game):
        """ Constructor

        Parameters
        ----------
        parent : Gtk.Window
            Parent object
        game : gem.engine.game.Game
            Game object
        """

        classic_theme = False
        if parent is not None:
            classic_theme = parent.use_classic_theme

        CommonWindow.__init__(self,
                              parent,
                              _("Game properties"),
                              Icons.Symbolic.GAMING,
                              classic_theme)

        # ------------------------------------
        #   Initialize variables
        # ------------------------------------

        self.interface = parent

        self.api = parent.api
        self.icons = parent.icons

        self.game = game

        self.help_data = {
            "order": [
                _("Description"),
                _("Parameters"),
            ],
            _("Description"): [
                _("Emulator default arguments can use custom parameters to "
                    "facilitate file detection."),
                _("Nintendo console titles are identified by a 6 character "
                    "identifier known as a GameID. This GameID is only used "
                    "with some emulators like Dolphin-emu. For more "
                    "informations, consult emulators documentation."),
                _("Tags are split by commas.")
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

        # Init signals
        self.__init_signals()

        # Start interface
        self.__start_interface()

    def __init_widgets(self):
        """ Initialize interface widgets
        """

        self.set_size(640, -1)

        self.set_spacing(6)

        self.set_resizable(True)

        # ------------------------------------
        #   Stack
        # ------------------------------------

        self.stack = Gtk.Stack()

        self.sidebar_stack = Gtk.StackSwitcher()

        # Properties
        self.stack.set_margin_top(12)
        self.stack.set_transition_type(Gtk.StackTransitionType.NONE)

        self.sidebar_stack.set_margin_top(12)
        self.sidebar_stack.set_stack(self.stack)
        self.sidebar_stack.set_halign(Gtk.Align.CENTER)

        # ------------------------------------
        #   Grids
        # ------------------------------------

        self.grid_content = Gtk.Box()

        grid_parameters = Gtk.Box()

        grid_environment = Gtk.Box()
        grid_environment_buttons = Gtk.Box()

        grid_statistic = Gtk.Box()
        grid_statistic_total = Gtk.Box()
        grid_statistic_average = Gtk.Box()

        # Properties
        self.grid_content.set_spacing(6)
        self.grid_content.set_orientation(Gtk.Orientation.VERTICAL)

        grid_parameters.set_spacing(6)
        grid_parameters.set_homogeneous(False)
        grid_parameters.set_orientation(Gtk.Orientation.VERTICAL)

        grid_environment.set_spacing(12)
        grid_environment.set_homogeneous(False)

        Gtk.StyleContext.add_class(
            grid_environment_buttons.get_style_context(), "linked")
        grid_environment_buttons.set_spacing(-1)
        grid_environment_buttons.set_orientation(Gtk.Orientation.VERTICAL)

        grid_statistic.set_spacing(6)
        grid_statistic.set_homogeneous(False)
        grid_statistic.set_orientation(Gtk.Orientation.VERTICAL)

        grid_statistic_total.set_spacing(12)
        grid_statistic_total.set_homogeneous(True)

        grid_statistic_average.set_spacing(12)
        grid_statistic_average.set_homogeneous(True)

        # ------------------------------------
        #   Title
        # ------------------------------------

        self.label_title = Gtk.Label()

        # Properties
        self.label_title.set_markup(
            "<span weight='bold' size='large'>%s</span>" % (
                replace_for_markup(self.game.name)))
        self.label_title.set_use_markup(True)
        self.label_title.set_halign(Gtk.Align.CENTER)
        self.label_title.set_ellipsize(Pango.EllipsizeMode.END)

        # ------------------------------------
        #   Emulators
        # ------------------------------------

        label_emulator = Gtk.Label()

        self.model = Gtk.ListStore(GdkPixbuf.Pixbuf, str)
        self.combo = Gtk.ComboBox()

        cell_icon = Gtk.CellRendererPixbuf()
        cell_name = Gtk.CellRendererText()

        # Properties
        label_emulator.set_use_markup(True)
        label_emulator.set_halign(Gtk.Align.CENTER)
        label_emulator.set_markup("<b>%s</b>" % _("Alternative emulator"))

        self.model.set_sort_column_id(1, Gtk.SortType.ASCENDING)

        self.combo.set_model(self.model)
        self.combo.set_id_column(1)
        self.combo.pack_start(cell_icon, False)
        self.combo.add_attribute(cell_icon, "pixbuf", 0)
        self.combo.pack_start(cell_name, True)
        self.combo.add_attribute(cell_name, "text", 1)

        cell_icon.set_padding(4, 0)

        # ------------------------------------
        #   Arguments
        # ------------------------------------

        self.entry_arguments = Gtk.Entry()

        # Properties
        self.entry_arguments.set_icon_from_icon_name(
            Gtk.EntryIconPosition.PRIMARY, Icons.Symbolic.TERMINAL)
        self.entry_arguments.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, Icons.Symbolic.CLEAR)

        # ------------------------------------
        #   Key
        # ------------------------------------

        label_key = Gtk.Label()

        self.entry_key = Gtk.Entry()

        # Properties
        label_key.set_margin_top(12)
        label_key.set_halign(Gtk.Align.CENTER)
        label_key.set_use_markup(True)
        label_key.set_markup("<b>%s</b>" % _("GameID"))

        self.entry_key.set_placeholder_text(_("No default value"))
        self.entry_key.set_icon_from_icon_name(
            Gtk.EntryIconPosition.PRIMARY, Icons.Symbolic.PASSWORD)
        self.entry_key.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, Icons.Symbolic.CLEAR)

        # ------------------------------------
        #   Tags
        # ------------------------------------

        label_tags = Gtk.Label()

        self.entry_tags = Gtk.Entry()
        self.completion_tags = Gtk.EntryCompletion()

        self.store_tags = Gtk.ListStore(str)

        # Properties
        label_tags.set_margin_top(12)
        label_tags.set_halign(Gtk.Align.CENTER)
        label_tags.set_use_markup(True)
        label_tags.set_markup("<b>%s</b>" % _("Tags"))

        self.entry_tags.set_tooltip_text(
            _("Use comma to separate tags"))
        self.entry_tags.set_placeholder_text(
            _("Use comma to separate tags"))
        self.entry_tags.set_completion(self.completion_tags)
        self.entry_tags.set_icon_from_icon_name(
            Gtk.EntryIconPosition.PRIMARY, Icons.Symbolic.ADD_TEXT)
        self.entry_tags.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, Icons.Symbolic.CLEAR)

        self.completion_tags.set_model(self.store_tags)
        self.completion_tags.set_popup_single_match(True)
        self.completion_tags.set_popup_completion(True)
        self.completion_tags.set_text_column(0)
        self.completion_tags.set_match_func(self.__on_entry_match_tag)

        # ------------------------------------
        #   Statistics
        # ------------------------------------

        scroll_statistic = Gtk.ScrolledWindow()
        viewport_statistic = Gtk.Viewport()

        label_statistic_total = Gtk.Label()
        self.label_statistic_total_value = Gtk.Label()

        label_statistic_average = Gtk.Label()
        self.label_statistic_average_value = Gtk.Label()

        # Properties
        label_statistic_total.set_label(_("Total play time"))
        label_statistic_total.set_halign(Gtk.Align.END)
        label_statistic_total.set_valign(Gtk.Align.CENTER)
        label_statistic_total.get_style_context().add_class("dim-label")

        self.label_statistic_total_value.set_label(_("No data"))
        self.label_statistic_total_value.set_halign(Gtk.Align.START)
        self.label_statistic_total_value.set_valign(Gtk.Align.CENTER)
        self.label_statistic_total_value.set_use_markup(True)

        label_statistic_average.set_label(_("Average play time"))
        label_statistic_average.set_halign(Gtk.Align.END)
        label_statistic_average.set_valign(Gtk.Align.CENTER)
        label_statistic_average.get_style_context().add_class("dim-label")

        self.label_statistic_average_value.set_label(_("No data"))
        self.label_statistic_average_value.set_halign(Gtk.Align.START)
        self.label_statistic_average_value.set_valign(Gtk.Align.CENTER)
        self.label_statistic_average_value.set_use_markup(True)

        # ------------------------------------
        #   Environment variables
        # ------------------------------------

        scroll_environment = Gtk.ScrolledWindow()
        viewport_environment = Gtk.Viewport()

        image_environment_add = Gtk.Image()
        self.button_environment_add = Gtk.Button()

        image_environment_remove = Gtk.Image()
        self.button_environment_remove = Gtk.Button()

        self.store_environment_keys = Gtk.ListStore(str)

        self.store_environment = Gtk.ListStore(str, str)
        self.treeview_environment = Gtk.TreeView()

        treeview_column_environment = Gtk.TreeViewColumn()

        self.treeview_cell_environment_key = Gtk.CellRendererCombo()
        self.treeview_cell_environment_value = Gtk.CellRendererText()

        # Properties
        scroll_environment.set_shadow_type(Gtk.ShadowType.OUT)

        image_environment_add.set_from_icon_name(
            Icons.Symbolic.ADD, Gtk.IconSize.BUTTON)
        image_environment_remove.set_from_icon_name(
            Icons.Symbolic.REMOVE, Gtk.IconSize.BUTTON)

        self.treeview_environment.set_model(self.store_environment)
        self.treeview_environment.set_headers_clickable(False)
        self.treeview_environment.set_headers_visible(False)

        treeview_column_environment.pack_start(
            self.treeview_cell_environment_key, True)
        treeview_column_environment.pack_start(
            self.treeview_cell_environment_value, True)

        treeview_column_environment.add_attribute(
            self.treeview_cell_environment_key, "text", 0)
        treeview_column_environment.add_attribute(
            self.treeview_cell_environment_value, "text", 1)

        self.treeview_cell_environment_key.set_padding(12, 6)
        self.treeview_cell_environment_key.set_property("text-column", 0)
        self.treeview_cell_environment_key.set_property("editable", True)
        self.treeview_cell_environment_key.set_property("has-entry", True)
        self.treeview_cell_environment_key.set_property(
            "model", self.store_environment_keys)
        self.treeview_cell_environment_key.set_property(
            "placeholder_text", _("Key"))
        self.treeview_cell_environment_key.set_property(
            "ellipsize", Pango.EllipsizeMode.END)

        self.treeview_cell_environment_value.set_padding(12, 6)
        self.treeview_cell_environment_value.set_property("editable", True)
        self.treeview_cell_environment_value.set_property(
            "placeholder_text", _("Value"))
        self.treeview_cell_environment_value.set_property(
            "ellipsize", Pango.EllipsizeMode.END)

        self.treeview_environment.append_column(
            treeview_column_environment)

        # ------------------------------------
        #   Integrate widgets
        # ------------------------------------

        self.stack.add_titled(grid_parameters, "parameters", _("Parameters"))

        grid_parameters.pack_start(label_emulator, False, False, 0)
        grid_parameters.pack_start(self.combo, False, False, 0)
        grid_parameters.pack_start(self.entry_arguments, False, False, 0)
        grid_parameters.pack_start(label_key, False, False, 0)
        grid_parameters.pack_start(self.entry_key, False, False, 0)
        grid_parameters.pack_start(label_tags, False, False, 0)
        grid_parameters.pack_start(self.entry_tags, False, False, 0)

        self.stack.add_titled(scroll_statistic, "statistic", _("Statistic"))

        scroll_statistic.add(viewport_statistic)
        viewport_statistic.add(grid_statistic)

        grid_statistic.pack_start(grid_statistic_total, False, False, 0)
        grid_statistic.pack_start(grid_statistic_average, False, False, 0)

        grid_statistic_total.pack_start(
            label_statistic_total, True, True, 0)
        grid_statistic_total.pack_start(
            self.label_statistic_total_value, True, True, 0)

        grid_statistic_average.pack_start(
            label_statistic_average, True, True, 0)
        grid_statistic_average.pack_start(
            self.label_statistic_average_value, True, True, 0)

        self.stack.add_titled(
            grid_environment, "environment", _("Environment"))

        scroll_environment.add(viewport_environment)
        viewport_environment.add(self.treeview_environment)

        self.button_environment_add.add(image_environment_add)
        self.button_environment_remove.add(image_environment_remove)

        grid_environment_buttons.pack_start(
            self.button_environment_add, False, False, 0)
        grid_environment_buttons.pack_start(
            self.button_environment_remove, False, False, 0)

        grid_environment.pack_start(grid_environment_buttons, False, False, 0)
        grid_environment.pack_start(scroll_environment, True, True, 0)

        self.grid_content.pack_start(self.sidebar_stack, False, False, 0)
        self.grid_content.pack_start(self.stack, True, True, 0)

        self.pack_start(self.label_title, False, False)
        self.pack_start(self.grid_content)

    def __init_signals(self):
        """ Initialize widgets signals
        """

        self.combo.connect(
            "changed", self.__on_selected_emulator)

        self.entry_arguments.connect(
            "icon-press", self.__on_entry_clear)
        self.entry_tags.connect(
            "icon-press", self.__on_entry_clear)
        self.entry_key.connect(
            "icon-press", self.__on_entry_clear)

        self.completion_tags.connect(
            "match-selected", self.__on_entry_write_tag)

        self.treeview_cell_environment_key.connect(
            "edited", self.__on_edited_cell)
        self.treeview_cell_environment_value.connect(
            "edited", self.__on_edited_cell)

        self.button_environment_add.connect(
            "clicked", self.__on_append_item)
        self.button_environment_remove.connect(
            "clicked", self.__on_remove_item)

    def __start_interface(self):
        """ Load data and start interface
        """

        self.add_button(_("Close"), Gtk.ResponseType.CLOSE)
        self.add_button(_("Accept"), Gtk.ResponseType.APPLY, Gtk.Align.END)

        self.add_help(self.help_data)

        for emulator in self.interface.api.emulators.values():

            if emulator.exists:

                icon = self.parent.get_pixbuf_from_cache(
                    "emulators", 22, emulator.id, emulator.icon)

                if icon is None:
                    icon = self.icons.blank(22)

                row = self.model.append([icon, emulator.name])

                if self.game.emulator is not None \
                   and emulator.name == self.game.emulator.name:
                    self.combo.set_active_iter(row)

        self.combo.set_wrap_width(int(len(self.model) / 6))

        # Emulator parameters
        if len(self.game.default) > 0:
            self.entry_arguments.set_text(self.game.default)

        # Game ID
        if self.game.key is not None:
            self.entry_key.set_text(self.game.key)

        # Game tags
        if len(self.game.tags) > 0:
            self.entry_tags.set_text(', '.join(self.game.tags))

        for tag in self.interface.api.get_game_tags():
            self.store_tags.append([tag])

        # Game statistics
        if not parse_timedelta(self.game.play_time) == "00:00:00":
            self.label_statistic_total_value.set_label(
                parse_timedelta(self.game.play_time))

            if self.game.played > 0:
                self.label_statistic_average_value.set_label(
                    parse_timedelta(self.game.play_time / self.game.played))

        # Environment variables
        for key in sorted(self.game.environment.keys()):
            self.store_environment.append([key, self.game.environment[key]])

        for key in sorted(environ.copy().keys()):
            self.store_environment_keys.append([key])

        self.combo.grab_focus()

    def __on_selected_emulator(self, widget=None):
        """ Select an emulator in combobox and update parameters placeholder

        Other Parameters
        ----------------
        widget : Gtk.Widget
            Object which receive signal (Default: None)
        """

        emulator = self.interface.api.get_emulator(self.combo.get_active_id())

        self.entry_arguments.set_placeholder_text(_("No default value"))
        self.set_response_sensitive(Gtk.ResponseType.APPLY, False)

        if emulator is not None:

            if len(emulator.default) > 0:
                self.entry_arguments.set_placeholder_text(emulator.default)

            # Allow to validate dialog if selected emulator binary exist
            if emulator.exists:
                self.set_response_sensitive(Gtk.ResponseType.APPLY, True)

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

        if widget == self.treeview_cell_environment_key:
            self.store_environment[path][0] = str(text)

        elif widget == self.treeview_cell_environment_value:
            self.store_environment[path][1] = str(text)

    def __on_append_item(self, widget):
        """ Append a new row in treeview

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        self.store_environment.append([str(), str()])

    def __on_remove_item(self, widget):
        """ Remove a row in treeview

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        model, treeiter = \
            self.treeview_environment.get_selection().get_selected()

        if treeiter is not None:
            self.store_environment.remove(treeiter)

    def __on_entry_clear(self, widget, pos, event):
        """ Reset an entry widget when secondary icon is clicked

        Parameters
        ----------
        widget : Gtk.Entry
            Entry widget
        pos : Gtk.EntryIconPosition
            Position of the clicked icon
        event : Gdk.EventButton or Gdk.EventKey
            Event which triggered this signal

        Returns
        -------
        bool
            Function state
        """

        if type(widget) is not Gtk.Entry:
            return False

        if pos == Gtk.EntryIconPosition.SECONDARY \
           and len(widget.get_text()) > 0:
            widget.set_text(str())

            return True

        return False

    def __on_entry_match_tag(self, widget, key, treeiter):
        """ Check if current entry match an entry from completion

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        key : str
            String to match
        treeiter : Gtk.Treeiter
            Row to match

        Returns
        -------
        bool
            Match item status
        """

        text = self.entry_tags.get_text()

        # Retrieve tag from model
        tag = self.store_tags.get_value(treeiter, 0)

        if ',' in text:

            # Retrieve current cursor position
            position = self.entry_tags.get_position()

            # Retrieve commas position
            left_comma = text.rfind(',', 0, position)
            right_comma = text.find(',', position)

            if left_comma == -1 and right_comma == -1:
                text = text

            elif left_comma == -1:
                text = text[:right_comma]

            elif right_comma == -1:
                text = text[left_comma + 1:]

            else:
                text = text[left_comma + 1:right_comma]

        # Avoid to retrieve all the tag when the specified text is empty
        if len(text.strip()) == 0:
            return False

        # Avoid to show the tag when the user already complete it
        if text.strip() == tag:
            return False

        # Check if the tag start with the specified text
        return tag.startswith(text.strip())

    def __on_entry_write_tag(self, widget, model, treeiter):
        """ Write the specified completion item to entry

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        model : Gtk.TreeModel
            Model which contains data
        treeiter : Gtk.Treeiter
            Selected entry from model

        Returns
        -------
        bool
            Handled signal
        """

        text = self.entry_tags.get_text()

        # Retrieve tag from model
        tag = model.get_value(treeiter, 0)

        if len(text) > 0:

            # Retrieve current cursor position
            position = self.entry_tags.get_position()

            # Retrieve commas position
            left_comma = text.rfind(',', 0, position)
            right_comma = text.find(',', position)

            left_text = str()
            if not left_comma == -1:
                left_text = text[:left_comma + 1] + ' '

            right_text = str()
            if not right_comma == -1:
                right_text = text[right_comma:]

            self.entry_tags.set_text(left_text + tag + right_text)
            self.entry_tags.set_position(len(left_text + tag))

        return True
