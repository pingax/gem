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

# Collections
from collections import OrderedDict

# Filesystem
from os.path import exists
from os.path import expanduser

# System
from os import environ

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

    from gi.repository.GLib import idle_add

    from gi.repository.GdkPixbuf import Pixbuf
    from gi.repository.GdkPixbuf import Colorspace
    from gi.repository.GdkPixbuf import InterpType

except ImportError as error:
    sys_exit("Import error with python3-gobject module: %s" % str(error))

# ------------------------------------------------------------------------------
#   Modules - GEM
# ------------------------------------------------------------------------------

try:
    from gem.api import GEM

    from gem.utils import *

    from gem.gtk import *

    from gem.gtk.widgets import CommonWindow

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

class Message(CommonWindow):

    def __init__(self, parent, title, message, icon=Icons.Information,
        center=True):
        """ Constructor

        Parameters
        ----------
        parent : Gtk.Window
            Parent object
        title : str
            Dialog title
        message : str
            Dialog message
        icon : str, optional
            Default icon name (Default: dialog-information)
        center : bool, optional
            If False, use justify text insted of center (Default: True)
        """

        classic_theme = False
        if parent is not None:
            classic_theme = parent.use_classic_theme

        CommonWindow.__init__(self, parent, title, icon, classic_theme)

        # ------------------------------------
        #   Initialize variables
        # ------------------------------------

        self.message = message

        self.center = center

        # ------------------------------------
        #   Prepare interface
        # ------------------------------------

        # Init widgets
        self.__init_widgets()


    def __init_widgets(self):
        """ Initialize interface widgets
        """

        self.set_size(500, -1)

        # ------------------------------------
        #   Message
        # ------------------------------------

        text = Gtk.Label()

        # Properties
        text.set_line_wrap(True)
        text.set_use_markup(True)
        text.set_max_width_chars(10)
        text.set_markup(self.message)
        text.set_line_wrap_mode(Pango.WrapMode.WORD)

        if(self.center):
            text.set_alignment(.5, .5)
            text.set_justify(Gtk.Justification.CENTER)
        else:
            text.set_alignment(0, .5)
            text.set_justify(Gtk.Justification.FILL)

        # ------------------------------------
        #   Integrate widgets
        # ------------------------------------

        self.pack_start(text, False, False)


class Question(CommonWindow):

    def __init__(self, parent, title, message, icon=Icons.Question):
        """ Constructor

        Parameters
        ----------
        parent : Gtk.Window
            Parent object
        title : str
            Dialog title
        message : str
            Dialog message
        icon : str, optional
            Default icon name (Default: dialog-question)
        """

        classic_theme = False
        if parent is not None:
            classic_theme = parent.use_classic_theme

        CommonWindow.__init__(self, parent, title, icon, classic_theme)

        # ------------------------------------
        #   Variables
        # ------------------------------------

        self.message = message

        # ------------------------------------
        #   Prepare interface
        # ------------------------------------

        # Init widgets
        self.__init_widgets()

        # Start interface
        self.__start_interface()


    def __init_widgets(self):
        """ Initialize interface widgets
        """

        self.set_size(400, -1)

        # ------------------------------------
        #   Label
        # ------------------------------------

        self.label = Gtk.Label()

        # Properties
        self.label.set_line_wrap(True)
        self.label.set_use_markup(True)
        self.label.set_max_width_chars(10)
        self.label.set_line_wrap_mode(Pango.WrapMode.WORD)

        # ------------------------------------
        #   Integrate widgets
        # ------------------------------------

        self.pack_start(self.label, False, True)


    def __start_interface(self):
        """ Load data and start interface
        """

        self.add_button(_("No"), Gtk.ResponseType.NO)
        self.add_button(_("Yes"), Gtk.ResponseType.YES, Gtk.Align.END)

        self.label.set_markup(self.message)


class DialogEditor(CommonWindow):

    def __init__(self, parent, title, file_path, size, editable=True,
        icon=Icons.Editor):
        """ Constructor

        Parameters
        ----------
        parent : Gtk.Window
            Parent object
        title : str
            Dialog title
        file_path : str
            File path
        size : (int, int)
            Dialog size
        editable : bool, optional
            If True, allow to modify and save text buffer to file_path
            (Default: True)
        icon : str, optional
            Default icon name (Default: gtk-file)
        """

        classic_theme = False
        if parent is not None:
            classic_theme = parent.use_classic_theme

        CommonWindow.__init__(self, parent, title, icon, classic_theme)

        # ------------------------------------
        #   Initialize variables
        # ------------------------------------

        if type(editable) is not bool:
            raise TypeError("Wrong type for editable, expected bool")

        self.path = file_path
        self.editable = editable
        self.__width, self.__height = size

        self.founded_iter = list()
        self.current_index = int()
        self.previous_search = str()

        self.modified_buffer = False
        self.refresh_buffer = True

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

        self.set_resizable(True)

        self.set_spacing(6)
        self.set_border_width(6)

        # ------------------------------------
        #   Grid
        # ------------------------------------

        grid_tools = Gtk.Box()
        grid_search = Gtk.Box()

        self.grid_menu_options = Gtk.Grid()

        # Properties
        grid_tools.set_spacing(12)

        Gtk.StyleContext.add_class(grid_search.get_style_context(), "linked")

        self.grid_menu_options.set_border_width(12)
        self.grid_menu_options.set_row_spacing(6)
        self.grid_menu_options.set_column_spacing(12)

        # ------------------------------------
        #   Path
        # ------------------------------------

        self.entry_path = Gtk.Entry()

        # Properties
        self.entry_path.set_editable(False)
        self.entry_path.set_icon_from_icon_name(
            Gtk.EntryIconPosition.PRIMARY, Icons.Symbolic.Text)
        self.entry_path.set_icon_activatable(
            Gtk.EntryIconPosition.PRIMARY, False)

        if not self.editable:
            self.entry_path.set_icon_from_icon_name(
                Gtk.EntryIconPosition.SECONDARY, Icons.Symbolic.Refresh)

        # ------------------------------------
        #   Menu
        # ------------------------------------

        self.image_menu = Gtk.Image()
        self.button_menu = Gtk.MenuButton()

        self.popover_menu = Gtk.Popover()

        self.item_menu_label_line = Gtk.Label()
        self.item_menu_switch_line = Gtk.Switch()

        # Properties
        self.image_menu.set_from_icon_name(
            Icons.Symbolic.Menu, Gtk.IconSize.BUTTON)

        self.button_menu.add(self.image_menu)
        self.button_menu.set_use_popover(True)
        self.button_menu.set_popover(self.popover_menu)

        self.popover_menu.add(self.grid_menu_options)
        self.popover_menu.set_modal(True)

        self.item_menu_label_line.set_label(_("Auto line break"))
        self.item_menu_label_line.set_halign(Gtk.Align.END)
        self.item_menu_label_line.set_valign(Gtk.Align.CENTER)
        self.item_menu_label_line.get_style_context().add_class("dim-label")

        self.item_menu_switch_line.set_halign(Gtk.Align.START)
        self.item_menu_switch_line.set_valign(Gtk.Align.CENTER)

        # ------------------------------------
        #   Editor
        # ------------------------------------

        scroll_editor = Gtk.ScrolledWindow()

        if self.editable:
            try:
                require_version("GtkSource", "3.0")

                from gi.repository import GtkSource

                self.text_editor = GtkSource.View()
                self.buffer_editor = GtkSource.Buffer()

                self.language_editor = GtkSource.LanguageManager()
                self.style_editor = GtkSource.StyleSchemeManager()

                # Properties
                self.text_editor.set_insert_spaces_instead_of_tabs(True)

                self.buffer_editor.set_language(
                    self.language_editor.guess_language(self.path))

                if self.parent is not None:
                    self.text_editor.set_tab_width(self.parent.config.getint(
                        "editor", "tab", fallback=4))
                    self.text_editor.set_show_line_numbers(
                        self.parent.config.getboolean(
                        "editor", "lines", fallback=False))

                    self.buffer_editor.set_style_scheme(
                        self.style_editor.get_scheme(self.parent.config.item(
                        "editor", "colorscheme", "classic")))

            except Exception as error:
                self.text_editor = Gtk.TextView()
                self.buffer_editor = Gtk.TextBuffer()

        else:
            self.text_editor = Gtk.TextView()
            self.buffer_editor = Gtk.TextBuffer()

        # Properties
        scroll_editor.set_shadow_type(Gtk.ShadowType.OUT)

        self.text_editor.set_editable(self.editable)
        self.text_editor.set_monospace(True)
        self.text_editor.set_top_margin(4)
        self.text_editor.set_left_margin(4)
        self.text_editor.set_right_margin(4)
        self.text_editor.set_bottom_margin(4)
        self.text_editor.set_buffer(self.buffer_editor)

        self.tag_found = self.buffer_editor.create_tag("found",
            background="yellow", foreground="black")
        self.tag_current = self.buffer_editor.create_tag("current",
            background="cyan", foreground="black")

        # ------------------------------------
        #   Search
        # ------------------------------------

        self.entry_search = Gtk.Entry()

        self.image_up = Gtk.Image()
        self.button_up = Gtk.Button()

        self.image_bottom = Gtk.Image()
        self.button_bottom = Gtk.Button()

        # Properties
        self.entry_search.set_placeholder_text(_("Search"))
        self.entry_search.set_icon_from_icon_name(
            Gtk.EntryIconPosition.PRIMARY, Icons.Symbolic.Find)
        self.entry_search.set_icon_activatable(
            Gtk.EntryIconPosition.PRIMARY, False)
        self.entry_search.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, Icons.Symbolic.Clear)

        self.image_up.set_from_icon_name(
            Icons.Symbolic.Previous, Gtk.IconSize.BUTTON)

        self.button_up.set_label(str())
        self.button_up.set_image(self.image_up)

        self.image_bottom.set_from_icon_name(
            Icons.Symbolic.Next, Gtk.IconSize.BUTTON)

        self.button_bottom.set_label(str())
        self.button_bottom.set_image(self.image_bottom)

        # ------------------------------------
        #   Integrate widgets
        # ------------------------------------

        grid_tools.pack_start(self.entry_path, True, True, 0)
        grid_tools.pack_start(grid_search, False, False, 0)
        grid_tools.pack_start(self.button_menu, False, False, 0)

        self.pack_start(grid_tools, False, False)
        self.pack_start(scroll_editor, True, True)

        scroll_editor.add(self.text_editor)

        grid_search.pack_start(self.entry_search, False, True, 0)
        grid_search.pack_start(self.button_up, False, True, 0)
        grid_search.pack_start(self.button_bottom, False, True, 0)

        self.grid_menu_options.attach(self.item_menu_label_line, 0, 0, 1, 1)
        self.grid_menu_options.attach(self.item_menu_switch_line, 1, 0, 1, 1)


    def __init_signals(self):
        """ Initialize widgets signals
        """

        self.buffer_editor.connect("changed", self.__on_buffer_modified)

        self.item_menu_switch_line.connect("state-set", self.__on_break_line)

        self.entry_search.connect("activate", self.__on_entry_update)
        self.entry_search.connect("icon-press", on_entry_clear)

        self.button_bottom.connect("clicked", self.__on_move_search)
        self.button_up.connect("clicked", self.__on_move_search, True)

        if not self.editable:
            self.entry_path.connect("icon-press", self.__on_refresh_buffer)

            self.window.connect("key-press-event", self.__on_manage_keys)


    def __start_interface(self):
        """ Load data and start interface
        """

        if self.editable:
            self.add_button(_("Cancel"), Gtk.ResponseType.CLOSE)
            self.add_button(_("Save"), Gtk.ResponseType.APPLY, Gtk.Align.END)

        elif self.use_classic_theme:
            self.add_button(_("Close"), Gtk.ResponseType.CLOSE)

        self.entry_path.set_text(self.path)

        self.set_size(int(self.__width), int(self.__height))

        self.show_all()
        self.grid_menu_options.show_all()

        self.text_editor.grab_focus()

        self.__on_refresh_buffer()


    def __on_refresh_buffer(self, widget=None, pos=None, event=None):
        """ Load buffer text into editor area

        Parameters
        ----------
        widget : Gtk.Entry, optional
            Entry widget (Default: None)
        pos : Gtk.EntryIconPosition, optional
            Position of the clicked icon (Default: None)
        event : Gdk.EventButton or Gdk.EventKey, optional
            Event which triggered this signal (Default: None)
        """

        if self.refresh_buffer:
            self.refresh_buffer = False

            self.text_editor.set_sensitive(False)

            self.buffer_editor.delete(self.buffer_editor.get_start_iter(),
                self.buffer_editor.get_end_iter())

            loader = self.__on_load_file()
            self.buffer_thread = idle_add(loader.__next__)


    def __on_load_file(self):
        """ Load file content into textbuffer
        """

        yield True

        if exists(expanduser(self.path)):
            with open(self.path, 'r', errors="replace") as pipe:
                lines = pipe.readlines()

                for index in range(0, len(lines)):
                    self.buffer_editor.insert(
                        self.buffer_editor.get_end_iter(), lines[index])

                    self.entry_path.set_progress_fraction(
                        float(index / len(lines)))

                    yield True

            self.entry_path.set_progress_fraction(0.0)

        # Remove undo stack from GtkSource.Buffer
        if type(self.buffer_editor) is not Gtk.TextBuffer:
            self.buffer_editor.set_undo_manager(None)

        self.text_editor.set_sensitive(True)

        self.refresh_buffer = True

        yield False


    def __on_manage_keys(self, widget, event):
        """ Manage widgets for specific keymaps

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        event : Gdk.EventButton or Gdk.EventKey
            Event which triggered this signal
        """

        # Refresh buffer
        if event.keyval == Gdk.KEY_F5:
            self.__on_refresh_buffer()


    def __on_break_line(self, widget, status=None):
        """ Set break line mode for textview

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

        if status:
            self.text_editor.set_wrap_mode(Gtk.WrapMode.WORD)

        else:
            self.text_editor.set_wrap_mode(Gtk.WrapMode.NONE)


    def __init_search(self, text):
        """ Initialize search from search entry

        Parameters
        ----------
        text : str
            Text to match in text buffer
        """

        self.founded_iter = list()

        if len(text) > 0:
            # Remove previous tags from buffer
            self.buffer_editor.remove_all_tags(
                self.buffer_editor.get_start_iter(),
                self.buffer_editor.get_end_iter())

            # Match tags from text in buffer
            self.__on_search_and_mark(text, self.buffer_editor.get_start_iter())

            if len(self.founded_iter) > 0:
                match = self.founded_iter[self.current_index]

                self.buffer_editor.apply_tag(
                    self.tag_current, match[0], match[1])

                self.text_editor.scroll_to_iter(match[0], .25, False, .0, .0)

                # Avoid to do the same search twice
                self.previous_search = text


    def __on_move_search(self, widget=None, backward=False):
        """ Move between search results

        Parameters
        ----------
        widget : Gtk.Widget, optional
            Object which receive signal (Default: None)
        backward : bool, optional
            If True, use backward search instead of forward (Default: False)
        """

        if self.modified_buffer:
            text = self.entry_search.get_text()

            # Reset cursor position if different search
            if not text == self.previous_search:
                self.current_index = int()

            self.__init_search(text)

            self.previous_search = str()
            self.modified_buffer = False

        if len(self.founded_iter) > 0:
            # Avoid to check an index which not exist anymore
            if not self.current_index in range(len(self.founded_iter) - 1):
                self.current_index = int()

            match = self.founded_iter[self.current_index]

            self.buffer_editor.remove_tag(self.tag_current, match[0], match[1])
            self.buffer_editor.apply_tag(self.tag_found, match[0], match[1])

            if backward:
                self.current_index -= 1

                if self.current_index == -1:
                    self.current_index = len(self.founded_iter) - 1

            else:
                self.current_index += 1

                if self.current_index == len(self.founded_iter):
                    self.current_index = 0

            match = self.founded_iter[self.current_index]

            self.buffer_editor.apply_tag(self.tag_current, match[0], match[1])

            self.text_editor.scroll_to_iter(match[0], .25, False, .0, .0)


    def __on_entry_update(self, widget):
        """ Search entry value in text buffer

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        text = widget.get_text()

        if not text == self.previous_search:
            self.current_index = int()

            self.__init_search(text)

        else:
            self.__on_move_search()


    def __on_search_and_mark(self, text, start):
        """ Search a text and mark it

        Parameters
        ----------
        text : str
            Text to match in text buffer
        start : Gtk.TextIter
            Start position in text buffer
        """

        match = start.forward_search(text, 0, self.buffer_editor.get_end_iter())

        while match is not None:
            self.founded_iter.append(match)

            self.buffer_editor.apply_tag(self.tag_found, match[0], match[1])

            match = match[1].forward_search(
                text, 0, self.buffer_editor.get_end_iter())


    def __on_buffer_modified(self, textbuffer):
        """ Check buffer modification

        Parameters
        ----------
        textbuffer : Gtk.TextBuffer
            Modified buffer
        """

        self.modified_buffer = True


class DialogParameters(CommonWindow):

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

        CommonWindow.__init__(self, parent, _("Game properties"), Icons.Gaming,
            classic_theme)
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

        self.set_size(520, -1)

        # ------------------------------------
        #   Grids
        # ------------------------------------

        stack = Gtk.Stack()
        stack_switcher = Gtk.StackSwitcher()

        grid_parameters = Gtk.Box()
        grid_tags = Gtk.Box()
        self.grid_tags_popover = Gtk.Box()

        grid_environment = Gtk.Box()
        grid_environment_buttons = Gtk.Box()

        grid_statistic = Gtk.Box()
        grid_statistic_total = Gtk.Box()
        grid_statistic_average = Gtk.Box()

        # Properties
        stack.set_transition_type(Gtk.StackTransitionType.NONE)

        stack_switcher.set_stack(stack)
        stack_switcher.set_margin_bottom(6)
        stack_switcher.set_halign(Gtk.Align.CENTER)

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

        stack.add_titled(grid_parameters, "parameters", _("Parameters"))

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

        stack.add_titled(scroll_statistic, "statistic", _("Statistic"))

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

        stack.add_titled(grid_environment, "environment", _("Environment"))

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

        self.pack_start(stack_switcher, False, False)
        self.pack_start(stack, False, False)


    def __init_signals(self):
        """ Initialize widgets signals
        """

        self.combo.connect(
            "changed", self.__on_selected_emulator)

        self.entry_arguments.connect(
            "icon-press", on_entry_clear)
        self.entry_tags.connect(
            "icon-press", on_entry_clear)
        self.entry_key.connect(
            "icon-press", on_entry_clear)

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


class DialogRemove(CommonWindow):

    def __init__(self, parent, game):
        """ Constructor

        Parameters
        ----------
        parent : Gtk.Window
            Parent object
        game : gem.api.Game
            Game object
        """

        classic_theme = False
        if parent is not None:
            classic_theme = parent.use_classic_theme

        CommonWindow.__init__(self, parent, _("Remove a game"), Icons.Delete,
            classic_theme)

        # ------------------------------------
        #   Variables
        # ------------------------------------

        self.game = game

        # ------------------------------------
        #   Prepare interface
        # ------------------------------------

        # Init widgets
        self.__init_widgets()

        # Start interface
        self.__start_interface()


    def __init_widgets(self):
        """ Initialize interface widgets
        """

        self.set_size(520, -1)

        self.set_spacing(6)

        # ------------------------------------
        #   Description
        # ------------------------------------

        label = Gtk.Label()
        label_game = Gtk.Label()

        # Properties
        label.set_text(_("The following game going to be removed from your "
            "harddrive. This action is irreversible !"))
        label.set_line_wrap(True)
        label.set_max_width_chars(8)
        label.set_single_line_mode(False)
        label.set_justify(Gtk.Justification.FILL)
        label.set_line_wrap_mode(Pango.WrapMode.WORD)

        label_game.set_text(self.game.name)
        label_game.set_margin_top(12)
        label_game.set_single_line_mode(True)
        label_game.set_ellipsize(Pango.EllipsizeMode.END)
        label_game.get_style_context().add_class("dim-label")

        # ------------------------------------
        #   Options
        # ------------------------------------

        self.check_database = Gtk.CheckButton()

        self.check_save_state = Gtk.CheckButton()

        self.check_screenshots = Gtk.CheckButton()

        # Properties
        self.check_database.set_margin_top(6)
        self.check_database.set_label(_("Remove game's data from database"))

        self.check_save_state.set_margin_top(6)
        self.check_save_state.set_label(_("Remove game save files"))

        self.check_screenshots.set_label(_("Remove game screenshots"))

        # ------------------------------------
        #   Integrate widgets
        # ------------------------------------

        self.pack_start(label, False, True)
        self.pack_start(label_game, False, True)
        self.pack_start(self.check_database, False, True)
        self.pack_start(self.check_save_state, False, True)
        self.pack_start(self.check_screenshots, False, True)


    def __start_interface(self):
        """ Load data and start interface
        """

        self.add_button(_("No"), Gtk.ResponseType.NO)
        self.add_button(_("Yes"), Gtk.ResponseType.YES, Gtk.Align.END)

        self.check_database.set_active(True)


class DialogViewer(CommonWindow):

    def __init__(self, parent, title, size, screenshots_path):
        """ Constructor

        Parameters
        ----------
        parent : Gtk.Window
            Parent object
        title : str
            Dialog title
        size : (int, int)
            Dialog size
        screenshots_path : list
            Screnshots path list
        """

        classic_theme = False
        if parent is not None:
            classic_theme = parent.use_classic_theme

        CommonWindow.__init__(self, parent, title, Icons.Image, classic_theme)

        # ------------------------------------
        #   Initialize variables
        # ------------------------------------

        self.index = 0

        self.zoom_fit = True

        self.zoom_min = 10
        self.zoom_max = 400
        self.zoom_step = 5
        self.zoom_page_step = 10
        self.zoom_actual = 100

        # Allow the picture to autosize (with zoom_fit) when resize dialog
        self.auto_resize = parent.config.getboolean(
            "viewer", "auto_resize", fallback=False)

        self.screenshots = screenshots_path

        self.current_path = None
        self.current_pixbuf = None
        self.current_pixbuf_zoom = None
        self.current_pixbuf_size = tuple()

        self.targets = parent.targets

        self.__width, self.__height = size

        # ------------------------------------
        #   Manage monitor geometry
        # ------------------------------------

        self.__default_size = 800

        # Get default display
        display = Gdk.DisplayManager.get().get_default_display()

        if display is not None:
            # Retrieve default display screen
            screen = display.get_default_screen()
            # Retrieve default monitor geometry
            geometry = screen.get_monitor_geometry(screen.get_primary_monitor())

            self.__default_size = min(
                int(geometry.width / 2), int(geometry.height / 2))

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

        self.set_resizable(True)

        self.set_spacing(0)
        self.set_border_width(0)

        self.grid_tools.set_border_width(6)

        # ------------------------------------
        #   Overlay
        # ------------------------------------

        self.overlay = Gtk.Overlay()

        # ------------------------------------
        #   Image
        # ------------------------------------

        self.scroll_image = Gtk.ScrolledWindow()
        self.view_image = Gtk.Viewport()

        self.image = Gtk.Image()

        # Properties
        self.view_image.drag_source_set(
            Gdk.ModifierType.BUTTON1_MASK, self.targets, Gdk.DragAction.COPY)

        # ------------------------------------
        #   Resize buttons
        # ------------------------------------

        self.grid_resize_buttons = Gtk.Box()

        self.image_fit = Gtk.Image()
        self.button_fit = Gtk.Button()

        self.image_original = Gtk.Image()
        self.button_original = Gtk.Button()

        # Properties
        Gtk.StyleContext.add_class(
            self.grid_resize_buttons.get_style_context(), "linked")
        self.grid_resize_buttons.set_spacing(-1)
        self.grid_resize_buttons.set_orientation(Gtk.Orientation.HORIZONTAL)

        self.image_fit.set_from_icon_name(
            Icons.Symbolic.ZoomFit, Gtk.IconSize.BUTTON)

        self.button_fit.set_image(self.image_fit)

        self.image_original.set_from_icon_name(
            Icons.Symbolic.Zoom, Gtk.IconSize.BUTTON)

        self.button_original.set_image(self.image_original)

        # ------------------------------------
        #   Move buttons
        # ------------------------------------

        self.grid_move_buttons = Gtk.Box()

        self.image_first = Gtk.Image()
        self.button_first = Gtk.Button()

        self.image_previous = Gtk.Image()
        self.button_previous = Gtk.Button()

        self.image_next = Gtk.Image()
        self.button_next = Gtk.Button()

        self.image_last = Gtk.Image()
        self.button_last = Gtk.Button()

        # Properties
        Gtk.StyleContext.add_class(
            self.grid_move_buttons.get_style_context(), "linked")
        self.grid_move_buttons.set_spacing(-1)
        self.grid_move_buttons.set_orientation(Gtk.Orientation.HORIZONTAL)

        self.image_first.set_from_icon_name(
            Icons.Symbolic.First, Gtk.IconSize.BUTTON)

        self.button_first.set_image(self.image_first)

        self.image_previous.set_from_icon_name(
            Icons.Symbolic.Previous, Gtk.IconSize.BUTTON)

        self.button_previous.set_image(self.image_previous)

        self.image_next.set_from_icon_name(
            Icons.Symbolic.Next, Gtk.IconSize.BUTTON)

        self.button_next.set_image(self.image_next)

        self.image_last.set_from_icon_name(
            Icons.Symbolic.Last, Gtk.IconSize.BUTTON)

        self.button_last.set_image(self.image_last)

        # ------------------------------------
        #   Zoom buttons
        # ------------------------------------

        self.grid_zoom_buttons = Gtk.Box()

        self.image_zoom_minus = Gtk.Image()
        self.button_zoom_minus = Gtk.Button()

        self.image_zoom_plus = Gtk.Image()
        self.button_zoom_plus = Gtk.Button()

        self.adjustment_zoom = Gtk.Adjustment()

        self.scale_zoom = Gtk.Scale()

        # Properties
        Gtk.StyleContext.add_class(
            self.grid_zoom_buttons.get_style_context(), "linked")
        self.grid_zoom_buttons.set_spacing(-1)
        self.grid_zoom_buttons.set_orientation(Gtk.Orientation.HORIZONTAL)

        self.image_zoom_minus.set_from_icon_name(
            Icons.Symbolic.ZoomOut, Gtk.IconSize.BUTTON)

        self.button_zoom_minus.set_image(self.image_zoom_minus)

        self.image_zoom_plus.set_from_icon_name(
            Icons.Symbolic.ZoomIn, Gtk.IconSize.BUTTON)

        self.button_zoom_plus.set_image(self.image_zoom_plus)

        self.adjustment_zoom.set_lower(self.zoom_min)
        self.adjustment_zoom.set_upper(self.zoom_max)
        self.adjustment_zoom.set_step_increment(self.zoom_step)
        self.adjustment_zoom.set_page_increment(self.zoom_page_step)

        self.scale_zoom.set_draw_value(False)
        self.scale_zoom.set_size_request(150, -1)
        self.scale_zoom.set_adjustment(self.adjustment_zoom)
        self.scale_zoom.add_mark(self.zoom_min, Gtk.PositionType.BOTTOM, None)
        self.scale_zoom.add_mark(200, Gtk.PositionType.BOTTOM, None)
        self.scale_zoom.add_mark(self.zoom_max, Gtk.PositionType.BOTTOM, None)

        # ------------------------------------
        #   Overlay move buttons
        # ------------------------------------

        self.image_previous = Gtk.Image()
        self.button_overlay_previous = Gtk.Button()

        self.image_next = Gtk.Image()
        self.button_overlay_next = Gtk.Button()

        # Properties
        self.image_previous.set_from_icon_name(
            Icons.Symbolic.Previous, Gtk.IconSize.BUTTON)

        self.button_overlay_previous.get_style_context().add_class("osd")
        self.button_overlay_previous.set_image(self.image_previous)
        self.button_overlay_previous.set_valign(Gtk.Align.CENTER)
        self.button_overlay_previous.set_halign(Gtk.Align.START)
        self.button_overlay_previous.set_no_show_all(True)
        self.button_overlay_previous.set_margin_bottom(6)
        self.button_overlay_previous.set_margin_right(6)
        self.button_overlay_previous.set_margin_left(6)
        self.button_overlay_previous.set_margin_top(6)

        self.image_next.set_from_icon_name(
            Icons.Symbolic.Next, Gtk.IconSize.BUTTON)

        self.button_overlay_next.get_style_context().add_class("osd")
        self.button_overlay_next.set_image(self.image_next)
        self.button_overlay_next.set_valign(Gtk.Align.CENTER)
        self.button_overlay_next.set_halign(Gtk.Align.END)
        self.button_overlay_next.set_no_show_all(True)
        self.button_overlay_next.set_margin_bottom(6)
        self.button_overlay_next.set_margin_right(6)
        self.button_overlay_next.set_margin_left(6)
        self.button_overlay_next.set_margin_top(6)

        # ------------------------------------
        #   Integrate widgets
        # ------------------------------------

        self.scroll_image.add(self.view_image)
        self.view_image.add(self.image)

        self.grid_move_buttons.pack_start(
            self.button_first, False, False, 0)
        self.grid_move_buttons.pack_start(
            self.button_previous, False, False, 0)
        self.grid_move_buttons.pack_start(
            self.button_next, False, False, 0)
        self.grid_move_buttons.pack_start(
            self.button_last, False, False, 0)

        # self.grid_zoom_buttons.pack_start(
            # self.button_zoom_minus, False, False, 0)
        self.grid_zoom_buttons.pack_start(
            self.button_original, False, False, 0)
        self.grid_zoom_buttons.pack_start(
            self.button_fit, False, False, 0)
        # self.grid_zoom_buttons.pack_start(
            # self.button_zoom_plus, False, False, 0)

        self.overlay.add(self.scroll_image)
        self.overlay.add_overlay(self.button_overlay_previous)
        self.overlay.add_overlay(self.button_overlay_next)

        self.pack_start(self.overlay, True, True, 0)


    def __init_signals(self):
        """ Initialize widgets signals
        """

        if self.auto_resize:
            self.window.connect("size-allocate", self.update_screenshot)

        self.window.connect("key-press-event", self.change_screenshot)

        self.button_first.connect("clicked", self.change_screenshot)
        self.button_previous.connect("clicked", self.change_screenshot)
        self.button_next.connect("clicked", self.change_screenshot)
        self.button_last.connect("clicked", self.change_screenshot)

        self.button_zoom_minus.connect("clicked", self.change_screenshot)
        self.button_original.connect("clicked", self.change_screenshot)
        self.button_fit.connect("clicked", self.change_screenshot)
        self.button_zoom_plus.connect("clicked", self.change_screenshot)

        self.button_overlay_previous.connect("clicked", self.change_screenshot)
        self.button_overlay_next.connect("clicked", self.change_screenshot)

        self.view_image.connect("drag-data-get", self.__on_dnd_send_data)

        self.scale_zoom.connect("change_value", self.update_adjustment)


    def __start_interface(self):
        """ Load data and start interface
        """

        self.add_widget(self.grid_move_buttons)
        self.add_widget(self.grid_zoom_buttons, Gtk.Align.END)
        self.add_widget(self.scale_zoom, Gtk.Align.END)

        self.set_size(int(self.__width), int(self.__height))

        self.window.show_all()

        self.set_widgets_sensitive()
        self.update_screenshot()


    def __on_dnd_send_data(self, widget, context, data, info, time):
        """ Set screenshot file path uri

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

        if exists(self.current_path):
            data.set_uris(["file://%s" % self.current_path])


    def change_screenshot(self, widget=None, event=None):
        """ Change current screenshot

        Parameters
        ----------
        widget : Gtk.Widget, optional
            Object which receive signal (Default: None)
        event : Gdk.EventButton or Gdk.EventKey, optional
            Event which triggered this signal (Default: None)
        """

        # Keyboard
        if widget is self.window:
            if event.keyval == Gdk.KEY_Left:
                self.index -= 1

            elif event.keyval == Gdk.KEY_Right:
                self.index += 1

            elif event.keyval == Gdk.KEY_KP_Subtract:
                self.zoom_fit = False
                self.zoom_actual -= self.zoom_step

            elif event.keyval == Gdk.KEY_KP_Add:
                self.zoom_fit = False
                self.zoom_actual += self.zoom_step

        # Zoom
        elif widget == self.button_zoom_minus:
            self.zoom_fit = False
            self.zoom_actual -= self.zoom_step

        elif widget == self.button_original:
            self.zoom_fit = False
            self.zoom_actual = None

        elif widget == self.button_fit:
            self.zoom_fit = True

        elif widget == self.button_zoom_plus:
            self.zoom_fit = False
            self.zoom_actual += self.zoom_step

        # Move
        elif widget == self.button_first:
            self.index = 0

        elif widget in (self.button_overlay_previous, self.button_previous):
            self.index -= 1

        elif widget in (self.button_overlay_next, self.button_next):
            self.index += 1

        elif widget == self.button_last:
            self.index = len(self.screenshots) - 1

        #Fixes
        if self.index < 0:
            self.index = 0

        elif self.index > len(self.screenshots) - 1:
            self.index = len(self.screenshots) - 1

        if self.zoom_actual is not None and type(self.zoom_actual) is int:
            if self.zoom_actual < self.zoom_min:
                self.zoom_actual = self.zoom_min

            elif self.zoom_actual > self.zoom_max:
                self.zoom_actual = self.zoom_max

        self.update_screenshot()
        self.set_widgets_sensitive()


    def set_widgets_sensitive(self):
        """ Refresh interface's widgets
        """

        self.button_first.set_sensitive(True)
        self.button_previous.set_sensitive(True)
        self.button_next.set_sensitive(True)
        self.button_last.set_sensitive(True)

        if self.index == 0:
            self.button_first.set_sensitive(False)
            self.button_previous.set_sensitive(False)

            self.button_overlay_previous.hide()

        else:
            self.button_overlay_previous.show()

        if self.index == len(self.screenshots) - 1:
            self.button_last.set_sensitive(False)
            self.button_next.set_sensitive(False)

            self.button_overlay_next.hide()

        else:
            self.button_overlay_next.show()


    def update_adjustment(self, widget, scroll, value):
        """ Change current screenshot size

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        scroll : Gtk.ScrollType
            Type of scroll action that was performed
        value : float
            New value resulting from the scroll action
        """

        if int(value) >= self.zoom_min and int(value) <= self.zoom_max:
            self.zoom_fit = False
            self.zoom_actual = int(value)

            self.update_screenshot()


    def update_screenshot(self, widget=None, event=None):
        """ Change current screenshot size

        Parameters
        ----------
        widget : Gtk.Widget, optional
            Object which receive signal (Default: None)
        event : Gdk.EventButton or Gdk.EventKey, optional
            Event which triggered this signal (Default: None)
        """

        # Get the current screenshot path
        path = expanduser(self.screenshots[self.index])

        # Avoid to recreate a pixbuf for the same file
        if not path == self.current_path:
            self.current_path = path

            # Set headerbar subtitle with current screenshot path
            self.set_subtitle(self.current_path)

            # Generate a Pixbuf from current screenshot
            self.current_pixbuf = Pixbuf.new_from_file(self.current_path)

            self.current_pixbuf_size = (
                self.current_pixbuf.get_width(),
                self.current_pixbuf.get_height())

            self.current_pixbuf_zoom = None

        # Check if pixbuf has been generate correctly
        if self.current_pixbuf is not None:

            # Restore original image size
            width, height = self.current_pixbuf_size

            if width > height:
                screen_height = int((height * self.__default_size) / width)
                screen_width = self.__default_size

            else:
                screen_width = int((width * self.__default_size) / height)
                screen_height = self.__default_size

            # ------------------------------------
            #   Check zoom features
            # ------------------------------------

            # Zoom to original size
            if self.zoom_actual is None:
                ratio_x = float(width / screen_width)
                ratio_y = float(height / screen_height)

                self.zoom_actual = int(min(ratio_x, ratio_y) * 100)

            # Zoom to fit current window
            elif self.zoom_fit:
                allocation = self.scroll_image.get_allocation()

                ratio_x = float(allocation.width / screen_width)
                ratio_y = float(allocation.height / screen_height)

                self.zoom_actual = int(min(ratio_x, ratio_y) * 100)

            # ------------------------------------
            #   Reload pixbuf
            # ------------------------------------

            # Avoid to have a zoom above maximum allowed
            if self.zoom_actual > self.zoom_max:
                self.zoom_actual = self.zoom_max
            # Avoid to have a zoom under minimum allowed
            if self.zoom_actual < self.zoom_min:
                self.zoom_actual = self.zoom_min

            if not self.current_pixbuf_zoom == self.zoom_actual:
                self.current_pixbuf_zoom = self.zoom_actual

                # Calc ratio from current zoom percent
                ratio_width = int((self.zoom_actual * screen_width) / 100)
                ratio_height = int((self.zoom_actual * screen_height) / 100)

                # Update scale adjustment
                self.adjustment_zoom.set_value(float(self.zoom_actual))

                self.image.set_from_pixbuf(self.current_pixbuf.scale_simple(
                    ratio_width, ratio_height, InterpType.TILES))


class DialogConsoles(CommonWindow):

    def __init__(self, parent, filename, consoles, previous=None):
        """ Constructor

        Parameters
        ----------
        parent : Gtk.Window
            Parent object
        filename : str
            File name
        consoles : list
            Consoles list
        previous : str or None, optional
            Previous selected console (Default: None)
        """

        classic_theme = False
        if parent is not None:
            classic_theme = parent.use_classic_theme

        CommonWindow.__init__(self, parent, _("Drag & Drop"), Icons.Gaming,
            classic_theme)

        # ------------------------------------
        #   Initialize variables
        # ------------------------------------

        self.current = None

        self.api = parent.api

        self.filename = filename

        self.consoles = consoles
        self.previous = previous

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

        self.set_size(640, 480)

        self.set_spacing(0)

        # ------------------------------------
        #   Grids
        # ------------------------------------

        grid = Gtk.Box()

        grid_checkbutton = Gtk.Box()

        # Properties
        grid.set_spacing(6)
        grid.set_homogeneous(False)
        grid.set_orientation(Gtk.Orientation.VERTICAL)

        grid_checkbutton.set_spacing(12)
        grid_checkbutton.set_margin_top(12)
        grid_checkbutton.set_homogeneous(False)
        grid_checkbutton.set_orientation(Gtk.Orientation.HORIZONTAL)

        # ------------------------------------
        #   Scroll
        # ------------------------------------

        self.scroll_consoles = Gtk.ScrolledWindow()
        self.view_consoles = Gtk.Viewport()

        # ------------------------------------
        #   Description
        # ------------------------------------

        self.label_description = Gtk.Label()
        self.label_game = Gtk.Label()

        # Properties
        self.label_description.set_label(_("The following game can be "
            "installed on multiple consoles. Select the console where to "
            "install this game:"))
        self.label_description.set_line_wrap(True)
        self.label_description.set_max_width_chars(8)
        self.label_description.set_single_line_mode(False)
        self.label_description.set_justify(Gtk.Justification.FILL)
        self.label_description.set_line_wrap_mode(Pango.WrapMode.WORD)

        self.label_game.set_label(self.filename)
        self.label_game.set_margin_bottom(12)
        self.label_game.set_single_line_mode(True)
        self.label_game.set_ellipsize(Pango.EllipsizeMode.END)
        self.label_game.get_style_context().add_class("dim-label")

        # ------------------------------------
        #   Consoles
        # ------------------------------------

        self.model_consoles = Gtk.ListStore(bool, Pixbuf, str)
        self.treeview_consoles = Gtk.TreeView()

        self.column_consoles = Gtk.TreeViewColumn()

        self.cell_consoles_status = Gtk.CellRendererToggle()
        self.cell_consoles_icon = Gtk.CellRendererPixbuf()
        self.cell_consoles_name = Gtk.CellRendererText()

        # Properties
        self.model_consoles.set_sort_column_id(2, Gtk.SortType.ASCENDING)

        self.treeview_consoles.set_model(self.model_consoles)
        self.treeview_consoles.set_headers_visible(False)

        self.column_consoles.set_expand(True)
        self.column_consoles.pack_start(self.cell_consoles_status, False)
        self.column_consoles.pack_start(self.cell_consoles_icon, False)
        self.column_consoles.pack_start(self.cell_consoles_name, True)

        self.column_consoles.add_attribute(
            self.cell_consoles_status, "active", 0)
        self.column_consoles.add_attribute(
            self.cell_consoles_icon, "pixbuf", 1)
        self.column_consoles.add_attribute(
            self.cell_consoles_name, "text", 2)

        self.cell_consoles_status.set_padding(6, 6)
        self.cell_consoles_status.set_activatable(True)
        self.cell_consoles_status.set_radio(True)

        self.cell_consoles_icon.set_padding(6, 6)
        self.cell_consoles_icon.set_alignment(0, .5)

        self.cell_consoles_name.set_padding(6, 6)
        self.cell_consoles_name.set_alignment(0, .5)

        self.treeview_consoles.append_column(self.column_consoles)

        # ------------------------------------
        #   CheckButton
        # ------------------------------------

        self.switch = Gtk.Switch()

        self.label_checkbutton = Gtk.Label()
        self.label_explanation = Gtk.Label()

        # Properties
        self.label_checkbutton.set_label(
            _("Keep this selection for every games in queue"))
        self.label_checkbutton.set_line_wrap(True)
        self.label_checkbutton.set_single_line_mode(False)
        self.label_checkbutton.set_halign(Gtk.Align.START)
        self.label_checkbutton.set_justify(Gtk.Justification.FILL)
        self.label_checkbutton.set_line_wrap_mode(Pango.WrapMode.WORD)

        self.label_explanation.set_label(
            _("Be careful, this option cannot be undo during the process."))
        self.label_explanation.set_line_wrap(True)
        self.label_explanation.set_single_line_mode(False)
        self.label_explanation.set_halign(Gtk.Align.START)
        self.label_explanation.set_justify(Gtk.Justification.FILL)
        self.label_explanation.set_line_wrap_mode(Pango.WrapMode.WORD)
        self.label_explanation.get_style_context().add_class("dim-label")

        # ------------------------------------
        #   Integrate widgets
        # ------------------------------------

        self.scroll_consoles.add(self.view_consoles)
        self.view_consoles.add(self.treeview_consoles)

        grid.pack_start(self.label_description, False, False, 0)
        grid.pack_start(self.label_game, False, False, 0)
        grid.pack_start(self.scroll_consoles, True, True, 0)
        grid.pack_start(grid_checkbutton, False, False, 0)
        grid.pack_start(self.label_explanation, False, False, 0)

        grid_checkbutton.pack_start(self.label_checkbutton, True, True, 0)
        grid_checkbutton.pack_start(self.switch, False, False, 0)

        self.pack_start(grid, True, True)


    def __init_signals(self):
        """ Initialize widgets signals
        """

        self.cell_consoles_status.connect("toggled", self.on_cell_toggled)


    def __start_interface(self):
        """ Load data and start interface
        """

        self.add_button(_("Cancel"), Gtk.ResponseType.CLOSE)
        self.add_button(_("Accept"), Gtk.ResponseType.APPLY, Gtk.Align.END)

        self.set_response_sensitive(Gtk.ResponseType.APPLY, False)

        self.window.show_all()

        for console in self.consoles:
            status = False
            if self.previous is not None and self.previous.name == console.name:
                status = True

                self.current = console
                self.set_response_sensitive(Gtk.ResponseType.APPLY, True)

            icon = console.icon

            if not exists(expanduser(icon)):
                icon = self.api.get_local(
                    "icons", "consoles", "%s.%s" % (icon, Icons.Ext))

            # Get console icon
            icon = icon_from_data(icon, self.parent.empty)

            self.model_consoles.append([status, icon, console.name])


    def on_cell_toggled(self, widget, path):
        """ Toggled a radio cell in treeview

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        path : Gtk.TreePath
            Path to be activated
        """

        self.set_response_sensitive(Gtk.ResponseType.APPLY, True)

        selected_path = Gtk.TreePath(path)

        treeiter = self.model_consoles.get_iter(selected_path)
        self.current = self.model_consoles.get_value(treeiter, 2)

        for row in self.model_consoles:
            row[0] = (row.path == selected_path)


# ------------------------------------------------------------------------------
#   Misc functions
# ------------------------------------------------------------------------------

def icon_from_data(path, fallback=None, width=24, height=24):
    """ Load an icon from path

    This function search if an icon is available in GEM icons folder and return
    a generate Pixbuf from the icon path. If no icon was found, return an empty
    generate Pixbuf.

    Parameters
    ----------
    path : str
        Absolute or relative icon path
    fallback : GdkPixbuf.Pixbuf, optional
        Fallback icon to return instead of empty (Default: None)
    width : int, optional
        Icon width in pixels (Default: 24)
    height : int, optional
        Icon height in pixels (Default: 24)

    Returns
    -------
    GdkPixbuf.Pixbuf
        Pixbuf icon object
    """

    if path is not None and exists(expanduser(path)):

        try:
            return Pixbuf.new_from_file_at_size(expanduser(path), width, height)
        except:
            pass

    # Return an empty icon
    if fallback is None:
        fallback = Pixbuf.new(Colorspace.RGB, True, 8, width, height)
        fallback.fill(0x00000000)

    return fallback


def icon_load(name, size=16, fallback=Icons.Missing):
    """ Load an icon from IconTheme

    This function search an icon in current user icons theme. If founded, return
    a generate Pixbuf from the icon name, else, return a generate Pixbuf from
    the fallback icon name.

    Parameters
    ----------
    icon : str
        Icon name
    width : int, optional
        Icon width in pixels (Default: 16)
    fallback : str or GdkPixbuf.Pixbuf, optional
        Fallback icon to return instead of empty (Default: image-missing)

    Returns
    -------
    GdkPixbuf.Pixbuf
        Pixbuf icon object
    """

    icons_theme = Gtk.IconTheme.get_default()

    # Check if specific icon name is in icons theme
    if icons_theme.has_icon(name):
        try:
            return icons_theme.load_icon(
                name, size, Gtk.IconLookupFlags.FORCE_SVG)

        except:
            if type(fallback) == Pixbuf:
                return fallback

            return icons_theme.load_icon(
                fallback, size, Gtk.IconLookupFlags.FORCE_SVG)

    # Return fallback icon (in the case where is a Pixbuf)
    if type(fallback) == Pixbuf:
        return fallback

    # Find fallback icon in icons theme
    if icons_theme.has_icon(fallback):
        return icons_theme.load_icon(
            fallback, size, Gtk.IconLookupFlags.FORCE_SVG)

    # Instead, return default image
    return icons_theme.load_icon(
        Icons.Missing, size, Gtk.IconLookupFlags.FORCE_SVG)


def set_pixbuf_opacity(pixbuf, opacity):
    """ Changes the opacity of pixbuf

    This function generate a new Pixbuf from another one and change his opacity
    by combining the two Pixbufs.

    Thanks to Rick Spencer:
    https://theravingrick.blogspot.fr/2011/01/changing-opacity-of-gtkpixbuf.html

    Parameters
    ----------
    pixbuf : GdkPixbuf.Pixbuf
        Original Pixbuf
    opacity : int
        The degree of desired opacity (between 0 and 255)

    Returns
    -------
    GdkPixbuf.Pixbuf
        Pixbuf icon object
    """

    width, height = pixbuf.get_width(), pixbuf.get_height()

    new_pixbuf = Pixbuf.new(Colorspace.RGB, True, 8, width, height)
    new_pixbuf.fill(0x00000000)

    try:
        pixbuf.composite(new_pixbuf, 0, 0, width, height, 0, 0, 1, 1,
            InterpType.NEAREST, opacity)
    except:
        pass

    return new_pixbuf


def on_change_theme(status=False):
    """ Change dark status of interface theme

    Parameters
    ----------
    status : bool, optional
        Use dark theme (Default: False)
    """

    Gtk.Settings.get_default().set_property(
        "gtk-application-prefer-dark-theme", status)


def on_entry_clear(widget, pos, event):
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

    if pos == Gtk.EntryIconPosition.SECONDARY and len(widget.get_text()) > 0:
        widget.set_text(str())

        return True

    return False


class DialogCover(CommonWindow):

    def __init__(self, parent, game):
        """ Constructor

        Parameters
        ----------
        parent : Gtk.Window
            Parent object
        game : gem.api.Game
            Game object instance
        """

        classic_theme = False
        if parent is not None:
            classic_theme = parent.use_classic_theme

        CommonWindow.__init__(
            self, parent, _("Game cover"), Icons.Image, classic_theme)

        # ------------------------------------
        #   Initialize variables
        # ------------------------------------

        self.game = game

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

        self.set_size(640, 480)

        self.set_spacing(0)

        # ------------------------------------
        #   Grid
        # ------------------------------------

        self.grid_content = Gtk.Grid()

        # Properties
        self.grid_content.set_column_spacing(12)
        self.grid_content.set_row_spacing(12)

        # ------------------------------------
        #   Image selector
        # ------------------------------------

        self.label_image_selector = Gtk.Label()

        self.filter_image_selector = Gtk.FileFilter.new()

        self.dialog_image_selector = Gtk.FileChooserDialog(
            use_header_bar=not self.use_classic_theme)

        self.file_image_selector = Gtk.FileChooserButton.new_with_dialog(
            self.dialog_image_selector)

        # Properties
        self.label_image_selector.set_halign(Gtk.Align.END)
        self.label_image_selector.set_justify(Gtk.Justification.RIGHT)
        self.label_image_selector.get_style_context().add_class("dim-label")
        self.label_image_selector.set_text(_("Cover image"))

        for pattern in [ "png", "jpg", "jpeg", "svg" ]:
            self.filter_image_selector.add_pattern("*.%s" % pattern)

        self.dialog_image_selector.add_button(
            _("Cancel"), Gtk.ResponseType.CANCEL)
        self.dialog_image_selector.add_button(
            _("Accept"), Gtk.ResponseType.ACCEPT)
        self.dialog_image_selector.set_filter(self.filter_image_selector)
        self.dialog_image_selector.set_action(Gtk.FileChooserAction.OPEN)
        self.dialog_image_selector.set_create_folders(False)
        self.dialog_image_selector.set_local_only(True)

        self.file_image_selector.set_hexpand(True)

        # ------------------------------------
        #   Image preview
        # ------------------------------------

        self.image_preview = Gtk.Image()

        # Properties
        self.image_preview.set_halign(Gtk.Align.CENTER)
        self.image_preview.set_valign(Gtk.Align.CENTER)
        self.image_preview.set_hexpand(True)
        self.image_preview.set_vexpand(True)

        # ------------------------------------
        #   Integrate widgets
        # ------------------------------------

        self.grid_content.attach(self.label_image_selector, 0, 0, 1, 1)
        self.grid_content.attach(self.file_image_selector, 1, 0, 1, 1)
        self.grid_content.attach(self.image_preview, 0, 1, 2, 1)

        self.pack_start(self.grid_content)


    def __init_signals(self):
        """ Initialize widgets signals
        """

        self.file_image_selector.connect("file-set", self.__update_preview)


    def __start_interface(self):
        """ Load data and start interface
        """

        self.add_button(_("Reset"), Gtk.ResponseType.REJECT)
        self.add_button(_("Accept"), Gtk.ResponseType.APPLY, Gtk.Align.END)

        if self.game.cover is not None and exists(self.game.cover):
            self.file_image_selector.set_filename(self.game.cover)

        self.__update_preview()


    def __update_preview(self, *args):
        """ Update image preview
        """

        self.__on_set_preview(self.file_image_selector.get_filename())


    def __on_set_preview(self, path):
        """ Set a new preview from selector filepath

        Parameters
        ----------
        path : str
            Image file path
        """

        try:
            pixbuf = Pixbuf.new_from_file(path)

            if pixbuf.get_width() >= pixbuf.get_height():
                self.image_preview.set_from_pixbuf(
                    Pixbuf.new_from_file_at_scale(path, 400, -1, True))

            else:
                self.image_preview.set_from_pixbuf(
                    Pixbuf.new_from_file_at_scale(path, -1, 236, True))

        except:
            self.file_image_selector.unselect_all()

            self.image_preview.set_from_icon_name(
                Icons.Missing, Gtk.IconSize.DND)
