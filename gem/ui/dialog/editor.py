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
from os import R_OK
from os import W_OK
from os import access

from pathlib import Path

# GEM
from gem.ui.data import Icons
from gem.ui.utils import on_entry_clear
from gem.ui.utils import magic_from_file
from gem.ui.utils import replace_for_markup
from gem.ui.utils import on_activate_listboxrow
from gem.ui.dialog.question import QuestionDialog
from gem.ui.widgets.window import CommonWindow
from gem.ui.widgets.widgets import ListBoxItem

# GObject
try:
    from gi import require_version

    require_version("Gtk", "3.0")

    from gi.repository import Gtk
    from gi.repository import GLib
    from gi.repository import Gdk
    from gi.repository import Pango

except ImportError as error:
    from sys import exit

    exit("Cannot found python3-gobject module: %s" % str(error))

# Translation
from gettext import gettext as _

# URL
from urllib.parse import urlparse
from urllib.request import url2pathname


# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class EditorDialog(CommonWindow):

    def __init__(self, parent, title, file_path, size, icon, editable=True):
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
        icon : gem.data.Icons
            Default icon name
        editable : bool, optional
            If True, allow to modify and save text buffer to file_path
            (Default: True)
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
        #   Targets
        # ------------------------------------

        self.targets = [Gtk.TargetEntry.new("text/uri-list", 0, 1337)]

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

        self.grid_tools = Gtk.Box()
        self.grid_search = Gtk.Box()

        self.grid_menu_options = Gtk.Box()

        # Properties
        self.grid_tools.set_spacing(12)

        Gtk.StyleContext.add_class(
            self.grid_search.get_style_context(), "linked")

        self.grid_menu_options.set_spacing(6)
        self.grid_menu_options.set_border_width(6)
        self.grid_menu_options.set_orientation(Gtk.Orientation.VERTICAL)

        # ------------------------------------
        #   Path
        # ------------------------------------

        self.entry_path = Gtk.Entry()

        # Properties
        self.entry_path.set_editable(False)
        self.entry_path.set_icon_from_icon_name(
            Gtk.EntryIconPosition.PRIMARY, Icons.Symbolic.TEXT)
        self.entry_path.set_icon_activatable(
            Gtk.EntryIconPosition.PRIMARY, False)

        if not self.editable:
            self.entry_path.set_icon_from_icon_name(
                Gtk.EntryIconPosition.SECONDARY, Icons.Symbolic.REFRESH)

        # ------------------------------------
        #   Menu
        # ------------------------------------

        self.image_menu = Gtk.Image()
        self.button_menu = Gtk.MenuButton()

        self.popover_menu = Gtk.Popover()

        # Properties
        self.image_menu.set_from_icon_name(
            Icons.Symbolic.MENU, Gtk.IconSize.BUTTON)

        self.button_menu.add(self.image_menu)
        self.button_menu.set_use_popover(True)
        self.button_menu.set_popover(self.popover_menu)

        self.popover_menu.add(self.grid_menu_options)
        self.popover_menu.set_modal(True)

        # ------------------------------------
        #   Menu - Options
        # ------------------------------------

        self.frame_menu_options = Gtk.Frame()
        self.listbox_menu_options = Gtk.ListBox()

        self.widget_line = ListBoxItem()
        self.switch_line = Gtk.Switch()

        # Properties
        self.listbox_menu_options.set_activate_on_single_click(True)
        self.listbox_menu_options.set_selection_mode(
            Gtk.SelectionMode.NONE)

        self.widget_line.set_widget(self.switch_line)
        self.widget_line.set_option_label(_("Line break"))

        # ------------------------------------
        #   Menu - Actions
        # ------------------------------------

        self.frame_menu_actions = Gtk.Frame()
        self.listbox_menu_actions = Gtk.ListBox()

        self.widget_import = ListBoxItem()
        self.image_import = Gtk.Image()
        self.button_import = Gtk.Button()

        self.widget_export = ListBoxItem()
        self.image_export = Gtk.Image()
        self.button_export = Gtk.Button()

        # Properties
        self.listbox_menu_actions.set_activate_on_single_click(True)
        self.listbox_menu_actions.set_selection_mode(
            Gtk.SelectionMode.NONE)

        self.button_import.set_image(self.image_import)
        self.button_import.set_relief(Gtk.ReliefStyle.NONE)

        self.image_import.set_from_icon_name(
            Icons.Symbolic.SAVE_AS, Gtk.IconSize.BUTTON)

        self.widget_import.set_widget(self.button_import)
        self.widget_import.set_option_label("%s…" % _("Import"))

        self.button_export.set_image(self.image_export)
        self.button_export.set_relief(Gtk.ReliefStyle.NONE)

        self.image_export.set_from_icon_name(
            Icons.Symbolic.SEND, Gtk.IconSize.BUTTON)

        self.widget_export.set_widget(self.button_export)
        self.widget_export.set_option_label("%s…" % _("Export"))

        # ------------------------------------
        #   Editor
        # ------------------------------------

        self.provider_editor = Gtk.CssProvider.new()

        scroll_editor = Gtk.ScrolledWindow()

        if self.editable:
            try:
                require_version("GtkSource", "4")

                from gi.repository import GtkSource

                self.text_editor = GtkSource.View()
                self.buffer_editor = GtkSource.Buffer()

                self.language_editor = GtkSource.LanguageManager()
                self.style_editor = GtkSource.StyleSchemeManager()

                # Properties
                self.text_editor.set_insert_spaces_instead_of_tabs(True)

                self.buffer_editor.set_language(
                    self.language_editor.guess_language(str(self.path)))

                if self.parent is not None:
                    self.text_editor.set_tab_width(
                        self.parent.config.getint(
                            "editor", "tab", fallback=4))
                    self.text_editor.set_show_line_numbers(
                        self.parent.config.getboolean(
                            "editor", "lines", fallback=False))

                    self.buffer_editor.set_style_scheme(
                        self.style_editor.get_scheme(
                            self.parent.config.item(
                                "editor", "colorscheme", "classic")))

            except Exception:
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
        self.text_editor.drag_dest_set(
            Gtk.DestDefaults.MOTION | Gtk.DestDefaults.DROP, self.targets,
            Gdk.DragAction.COPY)

        self.tag_found = self.buffer_editor.create_tag(
            "found", background="yellow", foreground="black")
        self.tag_current = self.buffer_editor.create_tag(
            "current", background="cyan", foreground="black")

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
            Gtk.EntryIconPosition.PRIMARY, Icons.Symbolic.FIND)
        self.entry_search.set_icon_activatable(
            Gtk.EntryIconPosition.PRIMARY, False)
        self.entry_search.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, Icons.Symbolic.CLEAR)

        self.image_up.set_from_icon_name(
            Icons.Symbolic.PREVIOUS, Gtk.IconSize.BUTTON)

        self.button_up.set_image(self.image_up)

        self.image_bottom.set_from_icon_name(
            Icons.Symbolic.NEXT, Gtk.IconSize.BUTTON)

        self.button_bottom.set_image(self.image_bottom)

        # ------------------------------------
        #   Integrate widgets
        # ------------------------------------

        self.grid_tools.pack_start(self.entry_path, True, True, 0)
        self.grid_tools.pack_start(self.grid_search, False, False, 0)
        self.grid_tools.pack_start(self.button_menu, False, False, 0)

        self.pack_start(self.grid_tools, False, False)
        self.pack_start(scroll_editor, True, True)

        scroll_editor.add(self.text_editor)

        self.grid_search.pack_start(self.entry_search, False, True, 0)
        self.grid_search.pack_start(self.button_up, False, True, 0)
        self.grid_search.pack_start(self.button_bottom, False, True, 0)

        self.grid_menu_options.pack_start(
            self.frame_menu_options, False, False, 0)
        self.grid_menu_options.pack_start(
            self.frame_menu_actions, False, False, 0)

        self.frame_menu_options.add(self.listbox_menu_options)

        self.listbox_menu_options.add(self.widget_line)

        self.frame_menu_actions.add(self.listbox_menu_actions)

        if self.editable:
            self.listbox_menu_actions.add(self.widget_import)

        self.listbox_menu_actions.add(self.widget_export)

    def __init_signals(self):
        """ Initialize widgets signals
        """

        self.buffer_editor.connect("changed", self.__on_buffer_modified)

        self.switch_line.connect("state-set", self.__on_break_line)

        self.entry_search.connect("activate", self.__on_entry_update)
        self.entry_search.connect("icon-press", self.__on_entry_clear)

        self.button_bottom.connect("clicked", self.__on_move_search)
        self.button_up.connect("clicked", self.__on_move_search, True)

        self.button_import.connect("clicked", self.__on_import_file)
        self.button_export.connect("clicked", self.__on_export_file)

        self.listbox_menu_options.connect(
            "row-activated", on_activate_listboxrow)
        self.listbox_menu_actions.connect(
            "row-activated", on_activate_listboxrow)

        self.__drop_signal = self.text_editor.connect(
            "drag-data-received", self.__on_dnd_received_data)

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

        # Parsing font from configuration file
        try:
            font = self.parent.config.item("editor", "font", "Sans 12").split()

            # Retrieve informations based on pattern '<family font> <size>'
            font_size = int(font[-1])
            font_family = ' '.join(font[:-1])

            self.provider_editor.load_from_data(bytes(
                "textview { font: %spt '%s' }" % (font_size, font_family),
                "UTF-8"))

            self.text_editor.get_style_context().add_provider(
                self.provider_editor, Gtk.STYLE_PROVIDER_PRIORITY_USER)

        except Exception:
            self.logger.warning("Cannot parse editor font")

        self.entry_path.set_text(str(self.path))

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

            self.set_subtitle("%s…" % _("Loading"))

            self.window.set_sensitive(False)

            self.buffer_editor.delete(
                self.buffer_editor.get_start_iter(),
                self.buffer_editor.get_end_iter())

            loader = self.__on_load_file()
            self.buffer_thread = GLib.idle_add(loader.__next__)

    def __on_load_file(self):
        """ Load file content into textbuffer
        """

        yield True

        if self.path.exists() and access(self.path, R_OK):
            self.buffer_editor.set_text(self.path.read_text(errors="replace"))

            yield True

        # Remove undo stack from GtkSource.Buffer
        if type(self.buffer_editor) is not Gtk.TextBuffer:
            self.buffer_editor.set_undo_manager(None)

        self.window.set_sensitive(True)

        self.refresh_buffer = True

        self.set_subtitle("")

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
            self.text_editor.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)

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
            self.__on_search_and_mark(
                text, self.buffer_editor.get_start_iter())

    def __on_move_search(self, widget=None, backward=False):
        """ Move between search results

        Parameters
        ----------
        widget : Gtk.Widget, optional
            Object which receive signal (Default: None)
        backward : bool, optional
            If True, use backward search instead of forward (Default: False)
        """

        text = self.entry_search.get_text()

        if self.modified_buffer or not text == self.previous_search:
            # Reset cursor position if different search
            if not text == self.previous_search:
                self.current_index = -1

            self.__init_search(text)

            self.modified_buffer = False

        if len(self.founded_iter) > 0:
            # Avoid to do the same search twice
            self.previous_search = text

            # Avoid to check an index which not exist anymore
            if self.current_index not in range(len(self.founded_iter)):
                self.current_index = -1

            # Remove selector tag from previous match iter
            match = self.founded_iter[self.current_index]

            self.buffer_editor.remove_tag(self.tag_current, match[0], match[1])
            self.buffer_editor.apply_tag(self.tag_found, match[0], match[1])

            if backward:
                self.current_index -= 1

                if self.current_index < 0:
                    self.current_index = len(self.founded_iter) - 1

            else:
                self.current_index += 1

                if self.current_index >= len(self.founded_iter):
                    self.current_index = 0

            # Add selector tag to current match iter
            match = self.founded_iter[self.current_index]

            self.buffer_editor.apply_tag(self.tag_current, match[0], match[1])

            # Scroll editor to current match iter
            self.text_editor.scroll_to_iter(match[0], .25, False, .0, .0)

    def __on_entry_update(self, widget=None):
        """ Search entry value in text buffer

        Parameters
        ----------
        widget : Gtk.Widget, optional
            Object which receive signal
        """

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

        if pos == Gtk.EntryIconPosition.SECONDARY \
           and len(widget.get_text()) > 0:
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

        match = start.forward_search(text,
                                     Gtk.TextSearchFlags.CASE_INSENSITIVE,
                                     self.buffer_editor.get_end_iter())

        while match is not None:
            self.founded_iter.append(match)

            self.buffer_editor.apply_tag(self.tag_found, match[0], match[1])

            match = match[1].forward_search(
                text, Gtk.TextSearchFlags.CASE_INSENSITIVE,
                self.buffer_editor.get_end_iter())

    def __on_buffer_modified(self, textbuffer):
        """ Check buffer modification

        Parameters
        ----------
        textbuffer : Gtk.TextBuffer
            Modified buffer
        """

        self.modified_buffer = True

    def __on_import_file(self, widget, path=None):
        """ Import a plain text file

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        self.window.set_sensitive(False)

        dialog = ImportDialog(self, self.title, path)

        if dialog.run() == Gtk.ResponseType.APPLY:
            filename = dialog.file_selector.get_filename()

            if filename is not None and len(filename) > 0:
                path = Path(filename).expanduser()

                if path.exists():
                    textbuffer = path.read_text()

                    if dialog.switch_replace.get_active():
                        self.buffer_editor.set_text(textbuffer)

                    else:
                        self.buffer_editor.insert(
                            self.buffer_editor.get_end_iter(), textbuffer)

                    self.__on_entry_update()

        dialog.destroy()

        self.window.set_sensitive(True)

    def __on_export_file(self, widget):
        """ Export buffer content to a plain text file

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        self.window.set_sensitive(False)

        dialog = ExportDialog(self, self.title)

        if dialog.run() == Gtk.ResponseType.APPLY:
            filename = dialog.entry_selector.get_text()

            if len(filename) > 0:
                path = Path(filename).expanduser()

                replace = True

                if path.exists():
                    subdialog = QuestionDialog(
                        self,
                        _("Existing file"),
                        _("Would you want to replace existing file ?"))

                    if subdialog.run() == Gtk.ResponseType.NO:
                        replace = False

                    subdialog.destroy()

                if replace:
                    path.write_text(self.buffer_editor.get_text(
                        self.buffer_editor.get_start_iter(),
                        self.buffer_editor.get_end_iter(), True))

        dialog.destroy()

        self.window.set_sensitive(True)

    def __on_dnd_received_data(self, widget, context, x, y, data, info, time):
        """ Manage drag & drop acquisition

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        context : Gdk.DragContext
            Drag context
        x : int
            X coordinate where the drop happened
        y : int
            Y coordinate where the drop happened
        data : Gtk.SelectionData
            Received data
        info : int
            Info that has been registered with the target in the Gtk.TargetList
        time : int
            Timestamp at which the data was received
        """

        self.text_editor.handler_block(self.__drop_signal)

        # Current acquisition not respect text/uri-list
        if not info == 1337:
            return

        files = data.get_uris()

        if len(files) > 0:
            result = urlparse(files[0])

            if result.scheme == "file":
                path = Path(url2pathname(result.path)).expanduser()

                try:
                    mimetype = magic_from_file(path, mime=True)

                    # Check mimetype format
                    if mimetype is not None and '/' in mimetype:
                        category, *filetype = mimetype.split('/')

                        # Only retrieve text files
                        if category == "text" and path.exists():
                            self.__on_import_file(None, path)

                except Exception as error:
                    self.logger.exception(error)

        self.text_editor.handler_unblock(self.__drop_signal)


class ImportDialog(CommonWindow):

    def __init__(self, parent, title, path=None):
        """ Constructor

        Parameters
        ----------
        parent : Gtk.Window
            Parent object
        title : str
            Window title
        path : str, optional
            Set a default path in import filechooser widget
        """

        classic_theme = False
        if parent is not None:
            classic_theme = parent.use_classic_theme

        CommonWindow.__init__(self,
                              parent,
                              _("Import"),
                              Icons.Symbolic.SAVE_AS,
                              classic_theme)

        # ------------------------------------
        #   Variables
        # ------------------------------------

        self.import_title = title

        self.path = path

        self.mimetypes = ["text/plain"]

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

        self.set_spacing(6)

        self.set_resizable(True)

        # ------------------------------------
        #   Grid
        # ------------------------------------

        self.grid_switch = Gtk.Grid()

        # Properties
        self.grid_switch.set_column_spacing(12)
        self.grid_switch.set_row_spacing(6)

        # ------------------------------------
        #   Title
        # ------------------------------------

        self.label_title = Gtk.Label()

        # Properties
        self.label_title.set_markup(
            "<span weight='bold' size='large'>%s</span>" % (
                replace_for_markup(self.import_title)))
        self.label_title.set_use_markup(True)
        self.label_title.set_halign(Gtk.Align.CENTER)
        self.label_title.set_ellipsize(Pango.EllipsizeMode.END)

        # ------------------------------------
        #   File selector
        # ------------------------------------

        self.label_selector = Gtk.Label()

        self.filter_selector = Gtk.FileFilter.new()

        self.dialog_selector = Gtk.FileChooserDialog(
            use_header_bar=not self.use_classic_theme)

        self.file_selector = Gtk.FileChooserButton.new_with_dialog(
            self.dialog_selector)

        # Properties
        self.label_selector.set_markup("<b>%s</b>" % _("File"))
        self.label_selector.set_margin_top(12)
        self.label_selector.set_hexpand(True)
        self.label_selector.set_use_markup(True)
        self.label_selector.set_single_line_mode(True)
        self.label_selector.set_halign(Gtk.Align.CENTER)
        self.label_selector.set_ellipsize(Pango.EllipsizeMode.END)

        for pattern in self.mimetypes:
            self.filter_selector.add_mime_type(pattern)

        self.dialog_selector.add_button(
            _("Cancel"), Gtk.ResponseType.CANCEL)
        self.dialog_selector.add_button(
            _("Accept"), Gtk.ResponseType.ACCEPT)
        self.dialog_selector.set_filter(self.filter_selector)
        self.dialog_selector.set_action(Gtk.FileChooserAction.OPEN)
        self.dialog_selector.set_select_multiple(False)
        self.dialog_selector.set_create_folders(False)
        self.dialog_selector.set_local_only(True)

        self.file_selector.set_hexpand(True)

        # ------------------------------------
        #   Optional data
        # ------------------------------------

        self.label_data = Gtk.Label()

        self.frame_options = Gtk.Frame()
        self.scroll_options = Gtk.ScrolledWindow()
        self.listbox_options = Gtk.ListBox()

        self.widget_replace = ListBoxItem()
        self.switch_replace = Gtk.Switch()

        # Properties
        self.label_data.set_markup(
            "<b>%s</b>" % _("Options"))
        self.label_data.set_margin_top(12)
        self.label_data.set_hexpand(True)
        self.label_data.set_use_markup(True)
        self.label_data.set_single_line_mode(True)
        self.label_data.set_halign(Gtk.Align.CENTER)
        self.label_data.set_ellipsize(Pango.EllipsizeMode.END)

        self.listbox_options.set_activate_on_single_click(True)
        self.listbox_options.set_selection_mode(
            Gtk.SelectionMode.NONE)

        self.widget_replace.set_widget(self.switch_replace)
        self.widget_replace.set_option_label(
            _("Replace current buffer"))

        # ------------------------------------
        #   Integrate widgets
        # ------------------------------------

        self.listbox_options.add(self.widget_replace)

        self.scroll_options.add(self.listbox_options)

        self.frame_options.add(self.scroll_options)

        self.pack_start(self.label_title, False, False)
        self.pack_start(self.label_selector, False, False)
        self.pack_start(self.file_selector, False, False)
        self.pack_start(self.label_data, False, False)
        self.pack_start(self.frame_options)

    def __init_signals(self):
        """ Initialize widgets signals
        """

        self.file_selector.connect(
            "file-set", self.__on_file_choose)

        self.listbox_options.connect(
            "row-activated", self.on_activate_listboxrow)

    def __start_interface(self):
        """ Load data and start interface
        """

        self.add_button(_("Cancel"), Gtk.ResponseType.CANCEL)
        self.add_button(_("Apply"), Gtk.ResponseType.APPLY, Gtk.Align.END)

        self.set_default_response(Gtk.ResponseType.APPLY)

        if self.path is not None and self.path.exists():
            self.file_selector.set_filename(str(self.path))

        else:
            self.set_response_sensitive(Gtk.ResponseType.APPLY, False)

    def __on_file_choose(self, *args):
        """ User choose a file with FileChooser
        """

        status = False

        name = self.file_selector.get_filename()

        if name is not None and len(name.strip()) > 0:
            path = Path(name.strip()).expanduser()

            try:
                mimetype = magic_from_file(path, mime=True)

                # Check mimetype format
                if mimetype is not None and '/' in mimetype:
                    category, *filetype = mimetype.split('/')

                    # Only retrieve text files
                    if category == "text" and path.exists():
                        status = True

                    # Unselect this file cause is not a text one
                    else:
                        self.file_selector.unselect_all()

            except Exception as error:
                self.logger.exception(error)

        self.set_response_sensitive(Gtk.ResponseType.APPLY, status)


class ExportDialog(CommonWindow):

    def __init__(self, parent, title):
        """ Constructor

        Parameters
        ----------
        parent : Gtk.Window
            Parent object
        title : str
            Window title
        """

        classic_theme = False
        if parent is not None:
            classic_theme = parent.use_classic_theme

        CommonWindow.__init__(self,
                              parent,
                              _("Export"),
                              Icons.Symbolic.SEND,
                              classic_theme)

        # ------------------------------------
        #   Variables
        # ------------------------------------

        self.import_title = title

        self.mimetypes = ["text/plain"]

        # ------------------------------------
        #   Targets
        # ------------------------------------

        self.targets = [Gtk.TargetEntry.new("text/uri-list", 0, 1337)]

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

        self.set_spacing(6)

        self.set_resizable(True)

        # ------------------------------------
        #   Grid
        # ------------------------------------

        self.grid_selector = Gtk.Box()

        # Properties
        self.grid_selector.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.grid_selector.set_spacing(6)

        # ------------------------------------
        #   Title
        # ------------------------------------

        self.label_title = Gtk.Label()

        # Properties
        self.label_title.set_markup(
            "<span weight='bold' size='large'>%s</span>" % (
                replace_for_markup(self.import_title)))
        self.label_title.set_use_markup(True)
        self.label_title.set_halign(Gtk.Align.CENTER)
        self.label_title.set_ellipsize(Pango.EllipsizeMode.END)

        # ------------------------------------
        #   File selector
        # ------------------------------------

        self.label_selector = Gtk.Label()

        self.entry_selector = Gtk.Entry()

        self.image_selector = Gtk.Image()
        self.button_selector = Gtk.Button()

        self.filter_selector = Gtk.FileFilter.new()

        # Properties
        self.label_selector.set_markup("<b>%s</b>" % _("File"))
        self.label_selector.set_margin_top(12)
        self.label_selector.set_hexpand(True)
        self.label_selector.set_use_markup(True)
        self.label_selector.set_single_line_mode(True)
        self.label_selector.set_halign(Gtk.Align.CENTER)
        self.label_selector.set_ellipsize(Pango.EllipsizeMode.END)

        self.entry_selector.set_hexpand(True)
        self.entry_selector.set_placeholder_text("%s…" % _("Filepath"))
        self.entry_selector.set_icon_activatable(
            Gtk.EntryIconPosition.PRIMARY, False)
        self.entry_selector.set_icon_from_icon_name(
            Gtk.EntryIconPosition.PRIMARY, Icons.Symbolic.SEND)
        self.entry_selector.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, Icons.Symbolic.CLEAR)
        self.entry_selector.drag_dest_set(
            Gtk.DestDefaults.MOTION | Gtk.DestDefaults.DROP, self.targets,
            Gdk.DragAction.COPY)

        self.image_selector.set_valign(Gtk.Align.CENTER)
        self.image_selector.set_from_icon_name(
            Icons.Symbolic.OPEN, Gtk.IconSize.BUTTON)

        self.button_selector.set_image(self.image_selector)

        for pattern in self.mimetypes:
            self.filter_selector.add_mime_type(pattern)

        # ------------------------------------
        #   Integrate widgets
        # ------------------------------------

        self.grid_selector.pack_start(self.entry_selector, True, True, 0)
        self.grid_selector.pack_start(self.button_selector, False, False, 0)

        self.pack_start(self.label_title, False, False)
        self.pack_start(self.label_selector, False, False)
        self.pack_start(self.grid_selector, False, False)

    def __init_signals(self):
        """ Initialize widgets signals
        """

        self.entry_selector.connect("changed", self.__on_file_choose)
        self.entry_selector.connect("icon-press", on_entry_clear)

        self.__drop_signal = self.entry_selector.connect(
            "drag-data-received", self.__on_dnd_received_data)

        self.button_selector.connect("clicked", self.__on_file_set)

    def __start_interface(self):
        """ Load data and start interface
        """

        self.add_button(_("Cancel"), Gtk.ResponseType.CANCEL)
        self.add_button(_("Apply"), Gtk.ResponseType.APPLY, Gtk.Align.END)

        self.set_default_response(Gtk.ResponseType.APPLY)

        self.set_response_sensitive(Gtk.ResponseType.APPLY, False)

    def __on_file_set(self, *args):
        """ Open a FileChooserDialog to let user choose the export file
        """

        dialog = Gtk.FileChooserDialog(
            title="%s…" % _("Export As"),
            action=Gtk.FileChooserAction.SAVE,
            transient_for=self.window,
            use_header_bar=not self.use_classic_theme)

        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK)

        dialog.set_filter(self.filter_selector)
        dialog.set_select_multiple(False)
        dialog.set_create_folders(True)

        name = self.entry_selector.get_text().strip()

        if len(name) == 0:
            path = Path(name).expanduser()

            if not path.exists():
                dialog.set_current_folder(str(Path.home()))

            else:
                dialog.set_filename(str(path))

        else:
            dialog.set_current_folder(str(Path.home()))

        if dialog.run() == Gtk.ResponseType.OK:
            self.entry_selector.set_text(dialog.get_filename())

        dialog.destroy()

    def __on_file_choose(self, *args):
        """ User choose a file with FileChooser
        """

        status = False

        name = self.entry_selector.get_text().strip()

        if len(name) > 0:
            path = Path(name).expanduser()

            status = not path.is_dir() and access(path.parent, W_OK)

        self.set_response_sensitive(Gtk.ResponseType.APPLY, status)

    def __on_dnd_received_data(self, widget, context, x, y, data, info, time):
        """ Manage drag & drop acquisition

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        context : Gdk.DragContext
            Drag context
        x : int
            X coordinate where the drop happened
        y : int
            Y coordinate where the drop happened
        data : Gtk.SelectionData
            Received data
        info : int
            Info that has been registered with the target in the Gtk.TargetList
        time : int
            Timestamp at which the data was received
        """

        self.entry_selector.handler_block(self.__drop_signal)

        # Current acquisition not respect text/uri-list
        if not info == 1337:
            return

        files = data.get_uris()

        if len(files) > 0:
            result = urlparse(files[0])

            if result.scheme == "file":
                path = Path(url2pathname(result.path)).expanduser()

                try:
                    mimetype = magic_from_file(path, mime=True)

                    # Check mimetype format
                    if mimetype is not None and '/' in mimetype:
                        category, *filetype = mimetype.split('/')

                        # Only retrieve text files
                        if category == "text" and path.exists():
                            self.entry_selector.set_text(str(path))

                except Exception as error:
                    self.logger.exception(error)

        self.entry_selector.handler_unblock(self.__drop_signal)
