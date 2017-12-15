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

    from gem.gtk.widgets import Dialog
    from gem.gtk.widgets import TemplateDialog

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

class Message(TemplateDialog):

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

        Other Parameters
        ----------------
        icon : str
            Default icon name (Default: dialog-information)
        center : bool
            If False, use justify text insted of center (Default: True)
        """

        TemplateDialog.__init__(self, parent, title, message, icon, center)


class Question(Dialog):

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

        Other Parameters
        ----------------
        icon : str
            Default icon name (Default: dialog-question)
        """

        Dialog.__init__(self, parent, title, icon, True)

        # ------------------------------------
        #   Variables
        # ------------------------------------

        self.message = message

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

        self.set_size(400, -1)

        self.headerbar.set_show_close_button(False)

        self.dialog_box.set_spacing(0)

        # ------------------------------------
        #   Action buttons
        # ------------------------------------

        self.button_close = Gtk.Button()

        self.button_accept = Gtk.Button()

        # Properties
        self.button_close.set_label(_("No"))

        self.button_accept.set_label(_("Yes"))
        self.button_accept.get_style_context().add_class("destructive-action")

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

        self.headerbar.pack_start(self.button_close)
        self.headerbar.pack_end(self.button_accept)

        self.dialog_box.pack_start(self.label, False, True, 0)


    def __init_signals(self):
        """ Initialize widgets signals
        """

        self.button_close.connect("clicked", self.__on_cancel_clicked)
        self.button_accept.connect("clicked", self.__on_accept_clicked)


    def __start_interface(self):
        """ Load data and start interface
        """

        self.show_all()

        self.label.set_markup(self.message)


    def __on_cancel_clicked(self, widget):
        """ Click on close button

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        self.response(Gtk.ResponseType.NO)


    def __on_accept_clicked(self, widget):
        """ Click on accept button

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        self.response(Gtk.ResponseType.YES)


class DialogEditor(Dialog):

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

        Other Parameters
        ----------------
        editable : bool
            If True, allow to modify and save text buffer to file_path
            (Default: True)
        icon : str
            Default icon name (Default: gtk-file)
        """

        Dialog.__init__(self, parent, title, icon, editable)

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

        if self.editable:
            self.headerbar.set_show_close_button(False)

        # ------------------------------------
        #   Grid
        # ------------------------------------

        grid_header = Gtk.Box()
        grid_search = Gtk.Box()

        self.grid_infobar = Gtk.Box()

        self.grid_menu_options = Gtk.Grid()

        # Properties
        self.dialog_box.set_spacing(0)
        self.dialog_box.set_border_width(6)

        grid_header.set_spacing(8)
        grid_header.set_orientation(Gtk.Orientation.HORIZONTAL)

        Gtk.StyleContext.add_class(grid_search.get_style_context(), "linked")

        self.grid_infobar.set_margin_bottom(8)
        self.grid_infobar.set_orientation(Gtk.Orientation.VERTICAL)

        self.grid_menu_options.set_border_width(12)
        self.grid_menu_options.set_row_spacing(6)
        self.grid_menu_options.set_column_spacing(12)

        # ------------------------------------
        #   Action buttons
        # ------------------------------------

        self.button_close = Gtk.Button()

        self.button_accept = Gtk.Button()

        # Properties
        self.button_close.set_label(_("Cancel"))

        self.button_accept.set_label(_("Save"))
        self.button_accept.get_style_context().add_class("suggested-action")

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
        #   Infobar
        # ------------------------------------

        self.infobar = Gtk.InfoBar()

        self.label_infobar = Gtk.Label()

        # Properties
        self.infobar.set_show_close_button(False)

        self.label_infobar.set_use_markup(True)

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

                self.text_editor.set_tab_width(self.interface.config.getint(
                    "editor", "tab", fallback=4))
                self.text_editor.set_show_line_numbers(
                    self.interface.config.getboolean(
                    "editor", "lines", fallback=False))

                self.buffer_editor.set_language(
                    self.language_editor.guess_language(self.path))
                self.buffer_editor.set_style_scheme(
                    self.style_editor.get_scheme(self.interface.config.item(
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

        if self.editable:
            self.headerbar.pack_start(self.button_close)
            self.headerbar.pack_end(self.button_accept)

        scroll_editor.add(self.text_editor)

        grid_header.pack_start(self.entry_path, True, True, 0)
        grid_header.pack_start(Gtk.Separator(), False, True, 0)
        grid_header.pack_start(grid_search, False, True, 0)
        grid_header.pack_start(Gtk.Separator(), False, True, 0)
        grid_header.pack_start(self.button_menu, False, True, 0)

        grid_search.pack_start(self.entry_search, False, True, 0)
        grid_search.pack_start(self.button_up, False, True, 0)
        grid_search.pack_start(self.button_bottom, False, True, 0)

        self.dialog_box.pack_start(grid_header, False, True, 0)
        self.dialog_box.pack_start(self.grid_infobar, False, False, 0)
        self.dialog_box.pack_start(scroll_editor, True, True, 0)

        self.grid_menu_options.attach(self.item_menu_label_line, 0, 0, 1, 1)
        self.grid_menu_options.attach(self.item_menu_switch_line, 1, 0, 1, 1)

        self.infobar.get_content_area().pack_start(
            self.label_infobar, True, True, 4)


    def __init_signals(self):
        """ Initialize widgets signals
        """

        self.button_close.connect("clicked", self.__on_cancel_clicked)
        self.button_accept.connect("clicked", self.__on_accept_clicked)

        self.buffer_editor.connect("changed", self.__on_buffer_modified)

        self.item_menu_switch_line.connect("state-set", self.__on_break_line)

        self.entry_search.connect("activate", self.__on_entry_update)
        self.entry_search.connect("icon-press", on_entry_clear)

        self.button_bottom.connect("clicked", self.__on_move_search)
        self.button_up.connect("clicked", self.__on_move_search, True)

        if not self.editable:
            self.entry_path.connect("icon-press", self.__on_refresh_buffer)

            self.connect("key-press-event", self.__on_manage_keys)


    def __start_interface(self):
        """ Load data and start interface
        """

        self.entry_path.set_text(self.path)

        self.set_size(int(self.__width), int(self.__height))

        self.hide()
        self.unrealize()

        self.show_all()

        self.grid_menu_options.show_all()

        self.infobar.show_all()
        self.infobar.get_content_area().show_all()

        self.text_editor.grab_focus()

        self.__on_refresh_buffer()


    def __on_refresh_buffer(self, widget=None, pos=None, event=None):
        """ Load buffer text into editor area

        Others Parameters
        -----------------
        widget : Gtk.Entry
            Entry widget
        pos : Gtk.EntryIconPosition
            Position of the clicked icon
        event : Gdk.EventButton or Gdk.EventKey
            Event which triggered this signal
        """

        if self.refresh_buffer:
            self.refresh_buffer = False

            self.set_infobar(_("Load file..."))
            self.text_editor.set_sensitive(False)

            loader = self.__on_load_file()
            self.buffer_thread = idle_add(loader.__next__)


    def __on_cancel_clicked(self, widget):
        """ Click on close button

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        self.response(Gtk.ResponseType.CLOSE)


    def __on_accept_clicked(self, widget):
        """ Click on accept button

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        self.response(Gtk.ResponseType.APPLY)


    def __on_load_file(self):
        """ Load file content into textbuffer
        """

        yield True

        if exists(expanduser(self.path)):
            with open(self.path, 'r', errors="replace") as pipe:
                self.buffer_editor.set_text(''.join(pipe.readlines()))

        # Remove undo stack from GtkSource.Buffer
        if type(self.buffer_editor) is not Gtk.TextBuffer:
            self.buffer_editor.set_undo_manager(None)

        self.set_infobar()
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

        Other Parameters
        ----------------
        status : bool or None
            New status for current widget

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

        Other Parameters
        ----------------
        widget : Gtk.Widget
            Object which receive signal (Default: None)
        backward : bool
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


    def set_infobar(self, text=str(), message_type=Gtk.MessageType.INFO):
        """ Set infobar content

        This function set the infobar widget to inform user for specific things

        Others Parameters
        -----------------
        text : str
            Message text (Default: None)
        message_type : Gtk.MessageType
            Message type (Default: Gtk.MessageType.INFO)
        """

        self.infobar.set_message_type(message_type)

        # Set infobar visibility
        if len(text) > 0:
            if len(self.grid_infobar.get_children()) == 0:
                self.infobar.set_margin_top(8)
                self.grid_infobar.pack_start(self.infobar, True, True, 0)

        elif len(self.grid_infobar.get_children()) > 0:
            self.grid_infobar.remove(self.infobar)

        self.label_infobar.set_markup(text)


class DialogParameters(Dialog):

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

        Dialog.__init__(self, parent, _("Game properties"), Icons.Gaming, True)

        # ------------------------------------
        #   Initialize variables
        # ------------------------------------

        self.interface = parent

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

        self.dialog_box.set_spacing(0)

        self.headerbar.set_show_close_button(False)

        # ------------------------------------
        #   Grids
        # ------------------------------------

        stack = Gtk.Stack()
        stack_switcher = Gtk.StackSwitcher()

        grid_parameters = Gtk.Box()

        grid_environment = Gtk.Box()
        grid_environment_buttons = Gtk.Box()

        # Properties
        stack.set_transition_type(Gtk.StackTransitionType.NONE)

        stack_switcher.set_stack(stack)
        stack_switcher.set_margin_bottom(18)
        stack_switcher.set_halign(Gtk.Align.CENTER)

        grid_parameters.set_spacing(6)
        grid_parameters.set_homogeneous(False)
        grid_parameters.set_orientation(Gtk.Orientation.VERTICAL)

        grid_environment.set_spacing(12)
        grid_environment.set_homogeneous(False)

        Gtk.StyleContext.add_class(
            grid_environment_buttons.get_style_context(), "linked")
        grid_environment_buttons.set_spacing(-1)
        grid_environment_buttons.set_orientation(Gtk.Orientation.VERTICAL)

        # ------------------------------------
        #   Action buttons
        # ------------------------------------

        self.button_close = Gtk.Button()

        self.button_accept = Gtk.Button()

        # Properties
        self.button_close.set_label(_("Close"))

        self.button_accept.set_label(_("Apply"))
        self.button_accept.get_style_context().add_class("suggested-action")

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

        # ------------------------------------
        #   Statistics
        # ------------------------------------

        scroll_statistic = Gtk.ScrolledWindow()
        viewport_statistic = Gtk.Viewport()

        self.label_statistic = Gtk.Label()

        # Properties
        self.label_statistic.set_line_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.label_statistic.set_justify(Gtk.Justification.LEFT)
        self.label_statistic.set_halign(Gtk.Align.START)
        self.label_statistic.set_valign(Gtk.Align.START)
        self.label_statistic.set_single_line_mode(False)
        self.label_statistic.set_use_markup(True)
        self.label_statistic.set_line_wrap(True)
        self.label_statistic.set_xalign(0)
        self.label_statistic.set_yalign(0)
        self.label_statistic.set_lines(-1)

        # ------------------------------------
        #   Environment variables
        # ------------------------------------

        scroll_environment = Gtk.ScrolledWindow()
        viewport_environment = Gtk.Viewport()

        image_environment_add = Gtk.Image()
        self.button_environment_add = Gtk.Button()

        image_environment_remove = Gtk.Image()
        self.button_environment_remove = Gtk.Button()

        self.store_environment = Gtk.ListStore(str, str)
        self.treeview_environment = Gtk.TreeView()

        treeview_column_environment = Gtk.TreeViewColumn()

        treeview_cell_environment_key = Gtk.CellRendererText()
        treeview_cell_environment_value = Gtk.CellRendererText()

        # Properties
        image_environment_add.set_from_icon_name(
            Icons.Symbolic.Add, Gtk.IconSize.BUTTON)
        image_environment_remove.set_from_icon_name(
            Icons.Symbolic.Remove, Gtk.IconSize.BUTTON)

        self.treeview_environment.set_model(self.store_environment)
        self.treeview_environment.set_headers_clickable(False)
        self.treeview_environment.set_headers_visible(False)

        treeview_column_environment.pack_start(
            treeview_cell_environment_key, True)
        treeview_column_environment.pack_start(
            treeview_cell_environment_value, True)

        treeview_column_environment.add_attribute(
            treeview_cell_environment_key, "text", 0)
        treeview_column_environment.add_attribute(
            treeview_cell_environment_value, "text", 1)

        self.treeview_environment.append_column(
            treeview_column_environment)

        # ------------------------------------
        #   Integrate widgets
        # ------------------------------------

        self.headerbar.pack_start(self.button_close)
        self.headerbar.pack_end(self.button_accept)

        stack.add_titled(grid_parameters, "parameters", _("Parameters"))

        grid_parameters.pack_start(label_emulator, False, False, 0)
        grid_parameters.pack_start(self.combo, False, False, 0)
        grid_parameters.pack_start(self.entry_arguments, False, False, 0)
        grid_parameters.pack_start(label_key, False, False, 0)
        grid_parameters.pack_start(self.entry_key, False, False, 0)
        grid_parameters.pack_start(label_tags, False, False, 0)
        grid_parameters.pack_start(self.entry_tags, False, False, 0)

        stack.add_titled(scroll_statistic, "statistic", _("Statistic"))

        scroll_statistic.add(viewport_statistic)
        viewport_statistic.add(self.label_statistic)

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

        self.dialog_box.pack_start(stack_switcher, False, False, 0)
        self.dialog_box.pack_start(stack, False, False, 0)


    def __init_signals(self):
        """ Initialize widgets signals
        """

        self.button_close.connect("clicked", self.__on_cancel_clicked)
        self.button_accept.connect("clicked", self.__on_accept_clicked)

        self.combo.connect("changed", self.__on_selected_emulator)

        self.entry_arguments.connect("icon-press", on_entry_clear)
        self.entry_tags.connect("icon-press", on_entry_clear)
        self.entry_key.connect("icon-press", on_entry_clear)


    def __start_interface(self):
        """ Load data and start interface
        """

        self.set_help(self.interface, self.help_data)

        self.show_all()

        for emulator in self.interface.api.emulators.values():
            icon = icon_from_data(
                emulator.icon, self.empty, 24, 24, "emulators")

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

        # Game statistics
        statistics = OrderedDict({
            _("Total play time"):
                parse_timedelta(self.game.play_time),
        })

        text = list()
        for key in statistics.keys():
            text.append("<b>%s</b>: %s" % (key, statistics[key]))

        self.label_statistic.set_markup('\n'.join(text))

        # Environment variables
        for key in sorted(self.game.environment.keys()):
            self.store_environment.append([key, self.game.environment[key]])

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
            self.button_accept.set_sensitive(True)

        else:
            self.button_accept.set_sensitive(False)

        self.entry_arguments.set_placeholder_text(default)


    def __on_cancel_clicked(self, widget):
        """ Click on close button

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        self.response(Gtk.ResponseType.CLOSE)


    def __on_accept_clicked(self, widget):
        """ Click on accept button

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        self.response(Gtk.ResponseType.APPLY)


class DialogRemove(Dialog):

    def __init__(self, parent, game):
        """ Constructor

        Parameters
        ----------
        parent : Gtk.Window
            Parent object
        game : gem.api.Game
            Game object
        """

        Dialog.__init__(self, parent, _("Remove a game"), Icons.Delete, True)

        # ------------------------------------
        #   Variables
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

        self.set_size(520, -1)

        self.headerbar.set_show_close_button(False)

        self.dialog_box.set_spacing(0)

        # ------------------------------------
        #   Grid
        # ------------------------------------

        grid = Gtk.Box()

        # Properties
        grid.set_spacing(6)
        grid.set_orientation(Gtk.Orientation.VERTICAL)

        # ------------------------------------
        #   Action buttons
        # ------------------------------------

        self.button_close = Gtk.Button()

        self.button_accept = Gtk.Button()

        # Properties
        self.button_close.set_label(_("No"))

        self.button_accept.set_label(_("Yes"))
        self.button_accept.get_style_context().add_class("destructive-action")

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
        self.check_database.set_margin_top(12)
        self.check_database.set_label(_("Remove game's data from database"))

        self.check_save_state.set_margin_top(12)
        self.check_save_state.set_label(_("Remove game save files"))

        self.check_screenshots.set_label(_("Remove game screenshots"))

        # ------------------------------------
        #   Integrate widgets
        # ------------------------------------

        self.headerbar.pack_start(self.button_close)
        self.headerbar.pack_end(self.button_accept)

        grid.pack_start(label, False, True, 0)
        grid.pack_start(label_game, False, True, 0)
        grid.pack_start(self.check_database, False, True, 0)
        grid.pack_start(self.check_save_state, False, True, 0)
        grid.pack_start(self.check_screenshots, False, True, 0)

        self.dialog_box.pack_start(grid, False, True, 0)


    def __init_signals(self):
        """ Initialize widgets signals
        """

        self.button_close.connect("clicked", self.__on_cancel_clicked)
        self.button_accept.connect("clicked", self.__on_accept_clicked)


    def __start_interface(self):
        """ Load data and start interface
        """

        self.show_all()

        self.check_database.set_active(True)


    def __on_cancel_clicked(self, widget):
        """ Click on close button

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        self.response(Gtk.ResponseType.NO)


    def __on_accept_clicked(self, widget):
        """ Click on accept button

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        self.response(Gtk.ResponseType.YES)


class DialogViewer(Dialog):

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

        Dialog.__init__(self, parent, title, Icons.Image, True)

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

        self.headerbar.set_has_subtitle(True)

        self.dialog_box.set_spacing(0)
        self.dialog_box.set_border_width(0)

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
        self.button_overlay_next.set_margin_bottom(6)
        self.button_overlay_next.set_margin_right(6)
        self.button_overlay_next.set_margin_left(6)
        self.button_overlay_next.set_margin_top(6)

        # ------------------------------------
        #   Integrate widgets
        # ------------------------------------

        self.headerbar.pack_start(self.grid_move_buttons)
        self.headerbar.pack_end(self.grid_zoom_buttons)
        self.headerbar.pack_end(self.scale_zoom)

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

        self.dialog_box.pack_start(self.overlay, True, True, 0)


    def __init_signals(self):
        """ Initialize widgets signals
        """

        if self.auto_resize:
            self.connect("size-allocate", self.update_screenshot)

        self.connect("key-press-event", self.change_screenshot)

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

        self.set_default_size(int(self.__width), int(self.__height))

        self.show_all()

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
            info that has been registered with the target in the Gtk.TargetList
        time : int
            timestamp at which the data was received
        """

        if exists(self.current_path):
            data.set_uris(["file://%s" % self.current_path])


    def change_screenshot(self, widget=None, event=None):
        """ Change current screenshot

        Other Parameters
        ----------------
        widget : Gtk.Widget
            Object which receive signal (Default: None)
        event : Gdk.EventButton or Gdk.EventKey
            Event which triggered this signal (Default: None)
        """

        # Keyboard
        if widget is self:
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
            self.zoom_actual = 200

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

        Other Parameters
        ----------------
        widget : Gtk.Widget
            Object which receive signal (Default: None)
        event : Gdk.EventButton or Gdk.EventKey
            Event which triggered this signal (Default: None)
        """

        # Get the current screenshot path
        path = expanduser(self.screenshots[self.index])

        # Avoid to recreate a pixbuf for the same file
        if not path == self.current_path:
            self.current_path = path

            # Set headerbar subtitle with current screenshot path
            self.headerbar.set_subtitle(self.current_path)

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
                height = int((height * self.__default_size) / width)
                width = self.__default_size

            else:
                width = int((width * self.__default_size) / height)
                height = self.__default_size

            # Zoom to fit current window
            if self.zoom_fit:
                allocation = self.scroll_image.get_allocation()

                ratio_x = float(allocation.width / width)
                ratio_y = float(allocation.height / height)

                self.zoom_actual = int(min(ratio_x, ratio_y) * 100)

            if not self.current_pixbuf_zoom == self.zoom_actual:
                self.current_pixbuf_zoom = self.zoom_actual

                # Calc ratio from current zoom percent
                ratio_width = int((self.zoom_actual * width) / 100)
                ratio_height = int((self.zoom_actual * height) / 100)

                # Update scale adjustment
                self.adjustment_zoom.set_value(float(self.zoom_actual))

                self.image.set_from_pixbuf(self.current_pixbuf.scale_simple(
                    ratio_width, ratio_height, InterpType.TILES))


class DialogConsoles(Dialog):

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

        Other Parameters
        ----------------
        previous : str or None
            Previous selected console (Default: None)
        """

        Dialog.__init__(self, parent, _("Drag & Drop"), Icons.Gaming, True)

        # ------------------------------------
        #   Initialize variables
        # ------------------------------------

        self.current = None

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

        self.dialog_box.set_spacing(0)

        self.headerbar.set_show_close_button(False)

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
        #   Action buttons
        # ------------------------------------

        self.button_close = Gtk.Button()

        self.button_accept = Gtk.Button()

        # Properties
        self.button_close.set_label(_("Close"))

        self.button_accept.set_label(_("Apply"))
        self.button_accept.get_style_context().add_class("suggested-action")

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

        self.headerbar.pack_start(self.button_close)
        self.headerbar.pack_end(self.button_accept)

        self.scroll_consoles.add(self.view_consoles)
        self.view_consoles.add(self.treeview_consoles)

        grid.pack_start(self.label_description, False, False, 0)
        grid.pack_start(self.label_game, False, False, 0)
        grid.pack_start(self.scroll_consoles, True, True, 0)
        grid.pack_start(grid_checkbutton, False, False, 0)
        grid.pack_start(self.label_explanation, False, False, 0)

        grid_checkbutton.pack_start(self.label_checkbutton, True, True, 0)
        grid_checkbutton.pack_start(self.switch, False, False, 0)

        self.dialog_box.pack_start(grid, True, True, 0)


    def __init_signals(self):
        """ Initialize widgets signals
        """

        self.button_close.connect("clicked", self.__on_cancel_clicked)
        self.button_accept.connect("clicked", self.__on_accept_clicked)

        self.cell_consoles_status.connect("toggled", self.on_cell_toggled)


    def __start_interface(self):
        """ Load data and start interface
        """

        self.button_accept.set_sensitive(False)

        self.show_all()

        for console in self.consoles:
            status = False
            if self.previous is not None and self.previous.name == console.name:
                status = True

                self.current = console
                self.button_accept.set_sensitive(True)

            # Get console icon
            icon = icon_from_data(
                console.icon, self.interface.empty, subfolder="consoles")

            self.model_consoles.append([status, icon, console.name])


    def __on_cancel_clicked(self, widget):
        """ Click on close button

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        self.response(Gtk.ResponseType.CLOSE)


    def __on_accept_clicked(self, widget):
        """ Click on accept button

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        self.response(Gtk.ResponseType.APPLY)


    def on_cell_toggled(self, widget, path):
        """ Toggled a radio cell in treeview

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        path : Gtk.TreePath
            Path to be activated
        """

        self.button_accept.set_sensitive(True)

        selected_path = Gtk.TreePath(path)

        treeiter = self.model_consoles.get_iter(selected_path)
        self.current = self.model_consoles.get_value(treeiter, 2)

        for row in self.model_consoles:
            row[0] = (row.path == selected_path)


# ------------------------------------------------------------------------------
#   Misc functions
# ------------------------------------------------------------------------------

def icon_from_data(icon, fallback=None, width=24, height=24, subfolder=None):
    """ Load an icon from path

    This function search if an icon is available in GEM icons folder and return
    a generate Pixbuf from the icon path. If no icon was found, return an empty
    generate Pixbuf.

    Parameters
    ----------
    icon : str
        Absolute or relative icon path

    Other Parameters
    ----------------
    fallback : GdkPixbuf.Pixbuf
        Fallback icon to return instead of empty (Default: None)
    width : int
        Icon width in pixels (Default: 24)
    height : int
        Icon height in pixels (Default: 24)
    subfolder : str
        Subfolder in GEM icons path (Default: None)

    Returns
    -------
    GdkPixbuf.Pixbuf
        Pixbuf icon object
    """

    if icon is not None:
        path = icon

        if not exists(expanduser(icon)):
            path = path_join(GEM.Local, "icons", "%s.%s" % (icon, Icons.Ext))

            if subfolder is not None:
                path = path_join(
                    GEM.Local, "icons", subfolder, "%s.%s" % (icon, Icons.Ext))

        if path is not None and exists(expanduser(path)):
            try:
                return Pixbuf.new_from_file_at_size(
                    expanduser(path), width, height)
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

    Other Parameters
    ----------------
    width : int
        Icon width in pixels (Default: 16)
    fallback : str or GdkPixbuf.Pixbuf
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

    Other Parameters
    ----------------
    status : bool
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
