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
from gem.engine.utils import *

from gem.ui import *
from gem.ui.data import *
from gem.ui.utils import *

from gem.ui.widgets.window import CommonWindow

# Translation
from gettext import gettext as _

# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class ParametersDialog(CommonWindow):

    def __init__(self, parent, game, emulator):
        """ Constructor

        Parameters
        ----------
        parent : Gtk.Window
            Parent object
        game : gem.api.Game
            Game object
        emulator : dict
            Emulator data
        """

        classic_theme = False
        if parent is not None:
            classic_theme = parent.use_classic_theme

        CommonWindow.__init__(self, parent,
            _("Game properties"), Icons.Symbolic.Gaming, classic_theme)

        # ------------------------------------
        #   Initialize variables
        # ------------------------------------

        self.interface = parent

        self.api = parent.api

        self.game = game
        self.emulator = emulator

        # HACK: Create an empty image to avoid g_object_set_qdata warning
        self.empty = Pixbuf.new(Colorspace.RGB, True, 8, 24, 24)
        self.empty.fill(0x00000000)

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
                _("Tags are split by spaces.")
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
        grid_tags = Gtk.Box()
        self.grid_tags_popover = Gtk.Box()

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

        Gtk.StyleContext.add_class(
            grid_tags.get_style_context(), "linked")
        grid_tags.set_spacing(-1)
        grid_tags.set_orientation(Gtk.Orientation.HORIZONTAL)

        self.grid_tags_popover.set_spacing(12)
        self.grid_tags_popover.set_border_width(12)
        self.grid_tags_popover.set_homogeneous(False)
        self.grid_tags_popover.set_orientation(Gtk.Orientation.VERTICAL)

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
            "<span weight='bold' size='large'>%s</span>" % \
            replace_for_markup(self.game.name))
        self.label_title.set_use_markup(True)
        self.label_title.set_halign(Gtk.Align.CENTER)
        self.label_title.set_ellipsize(Pango.EllipsizeMode.END)

        # ------------------------------------
        #   Emulators
        # ------------------------------------

        label_emulator = Gtk.Label()

        self.model = Gtk.ListStore(Pixbuf, str, Pixbuf)
        self.combo = Gtk.ComboBox()

        cell_icon = Gtk.CellRendererPixbuf()
        cell_name = Gtk.CellRendererText()
        cell_warning = Gtk.CellRendererPixbuf()

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
        self.combo.pack_start(cell_warning, False)
        self.combo.add_attribute(cell_warning, "pixbuf", 2)

        cell_icon.set_padding(4, 0)

        # ------------------------------------
        #   Arguments
        # ------------------------------------

        self.entry_arguments = Gtk.Entry()

        # Properties
        self.entry_arguments.set_icon_from_icon_name(
            Gtk.EntryIconPosition.PRIMARY, Icons.Symbolic.Terminal)
        self.entry_arguments.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, Icons.Symbolic.Clear)

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
            Gtk.EntryIconPosition.PRIMARY, Icons.Symbolic.Password)
        self.entry_key.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, Icons.Symbolic.Clear)

        # ------------------------------------
        #   Tags
        # ------------------------------------

        label_tags = Gtk.Label()

        self.entry_tags = Gtk.Entry()

        self.image_tags = Gtk.Image()
        self.button_tags = Gtk.MenuButton()

        self.popover_tags = Gtk.Popover()
        self.popover_tags_frame = Gtk.Frame()
        self.popover_tags_scroll = Gtk.ScrolledWindow()
        self.popover_tags_filter = Gtk.SearchEntry()
        self.popover_tags_listbox = Gtk.ListBox()
        self.popover_tags_placeholder = Gtk.Label()

        # Properties
        label_tags.set_margin_top(12)
        label_tags.set_halign(Gtk.Align.CENTER)
        label_tags.set_use_markup(True)
        label_tags.set_markup("<b>%s</b>" % _("Tags"))

        self.entry_tags.set_tooltip_text(
            _("Use space to separate tags"))
        self.entry_tags.set_placeholder_text(
            _("Use space to separate tags"))
        self.entry_tags.set_icon_from_icon_name(
            Gtk.EntryIconPosition.PRIMARY, Icons.Symbolic.AddText)
        self.entry_tags.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, Icons.Symbolic.Clear)

        self.image_tags.set_from_icon_name(
            Icons.Symbolic.Add, Gtk.IconSize.SMALL_TOOLBAR)

        self.button_tags.set_popover(self.popover_tags)
        self.button_tags.set_image(self.image_tags)
        self.button_tags.set_use_popover(True)

        self.popover_tags_scroll.set_size_request(-1, 180)

        self.popover_tags_listbox.set_placeholder(self.popover_tags_placeholder)
        self.popover_tags_listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.popover_tags_listbox.set_filter_func(self.__on_filter_tag)
        self.popover_tags_listbox.set_activate_on_single_click(False)

        self.popover_tags_placeholder.get_style_context().add_class("dim-label")
        self.popover_tags_placeholder.set_label(_("Empty"))
        self.popover_tags_placeholder.set_margin_bottom(6)
        self.popover_tags_placeholder.set_margin_right(6)
        self.popover_tags_placeholder.set_margin_left(6)
        self.popover_tags_placeholder.set_margin_top(6)

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
            Icons.Symbolic.Add, Gtk.IconSize.BUTTON)
        image_environment_remove.set_from_icon_name(
            Icons.Symbolic.Remove, Gtk.IconSize.BUTTON)

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
        grid_parameters.pack_start(grid_tags, False, False, 0)

        grid_tags.pack_start(self.entry_tags, True, True, 0)
        grid_tags.pack_start(self.button_tags, False, False, 0)

        self.popover_tags.add(self.grid_tags_popover)

        self.grid_tags_popover.pack_start(
            self.popover_tags_filter, False, False, 0)
        self.grid_tags_popover.pack_start(
            self.popover_tags_frame, True, True, 0)

        self.popover_tags_frame.add(self.popover_tags_scroll)
        self.popover_tags_scroll.add(self.popover_tags_listbox)

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

        self.stack.add_titled(grid_environment, "environment", _("Environment"))

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

        self.popover_tags_filter.connect(
            "changed", self.__on_filters_update)

        self.popover_tags_listbox.connect(
            "row-activated", self.__on_filter_activate)

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
            icon = emulator.icon

            if not exists(expanduser(icon)):
                icon = self.api.get_local(
                    "icons", "emulators", "%s.%s" % (icon, Icons.Ext))

            icon = icon_from_data(icon, self.empty, 24, 24)

            warning = self.empty
            if not emulator.exists:
                warning = self.interface.icons["warning"]

            row = self.model.append([icon, emulator.name, warning])

            if self.emulator["rom"] is not None:
                if emulator.name == self.emulator["rom"].name:
                    self.combo.set_active_iter(row)

            elif self.emulator["console"] is not None:
                if emulator.name == self.emulator["console"].name:
                    self.combo.set_active_iter(row)

        self.combo.set_wrap_width(int(len(self.model) / 10))

        # Emulator parameters
        if self.emulator["parameters"] is not None:
            self.entry_arguments.set_text(self.emulator["parameters"])

        # Game ID
        if self.game.key is not None:
            self.entry_key.set_text(self.game.key)

        # Game tags
        if len(self.game.tags) > 0:
            self.entry_tags.set_text(' '.join(self.game.tags))

        for tag in self.interface.api.get_game_tags():
            label = Gtk.Label()
            label.set_label(tag)
            label.set_margin_top(6)
            label.set_margin_left(6)
            label.set_margin_right(6)
            label.set_margin_bottom(6)

            row = Gtk.ListBoxRow()
            row.add(label)

            self.popover_tags_listbox.add(row)

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

        self.grid_tags_popover.show_all()
        self.popover_tags_placeholder.show()

        self.combo.grab_focus()


    def __on_selected_emulator(self, widget=None):
        """ Select an emulator in combobox and update parameters placeholder

        Other Parameters
        ----------------
        widget : Gtk.Widget
            Object which receive signal (Default: None)
        """

        default = _("No default value")

        emulator = self.interface.api.get_emulator(self.combo.get_active_id())

        if emulator is not None:
            if emulator.default is not None:
                default = emulator.default

        # Allow to validate dialog if selected emulator binary exist
        if emulator is not None and emulator.exists:
            self.set_response_sensitive(Gtk.ResponseType.APPLY, True)

        else:
            self.set_response_sensitive(Gtk.ResponseType.APPLY, False)

        self.entry_arguments.set_placeholder_text(default)


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

        self.store_environment.append([ str(), str() ])


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


    def __on_filters_update(self, widget, status=None):
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

        self.popover_tags_listbox.invalidate_filter()


    def __on_filter_tag(self, widget, *args):
        """ Update treeview rows

        This function update tag listbox with filter entry content. A row is
        visible if the content match the filter.

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        # Retrieve row label text
        text = widget.get_children()[0].get_label()

        try:
            filter_text = self.popover_tags_filter.get_text().strip()

            if len(filter_text) == 0:
                return True

            return filter_text in text

        except:
            return False


    def __on_filter_activate(self, widget, row):
        """ Add a new filter to list

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        row : Gtk.ListBoxRow
            Activated row
        """

        # Retrieve row label text
        text = row.get_children()[0].get_label()

        filter_text = self.entry_tags.get_text().strip()

        if len(filter_text) > 0:
            text = "%s %s" % (self.entry_tags.get_text(), text)

        self.entry_tags.set_text(text)


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

        if pos == Gtk.EntryIconPosition.SECONDARY and \
            len(widget.get_text()) > 0:
            widget.set_text(str())

            return True

        return False
