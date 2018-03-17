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
from gem.ui import *
from gem.ui.data import *

from gem.ui.widgets.window import CommonWindow

# Translation
from gettext import gettext as _

# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class EditorDialog(CommonWindow):

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

        self.button_up.set_image(self.image_up)

        self.image_bottom.set_from_icon_name(
            Icons.Symbolic.Next, Gtk.IconSize.BUTTON)

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
        self.entry_search.connect("icon-press", self.__on_entry_clear)

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
