# ------------------------------------------------------------------
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
# ------------------------------------------------------------------

# ------------------------------------------------------------------
#   Modules
# ------------------------------------------------------------------

# Path
from os.path import exists
from os.path import expanduser

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
    from gi.repository import GLib
    from gi.repository import Pango

    from gi.repository.GdkPixbuf import Pixbuf
    from gi.repository.GdkPixbuf import Colorspace
    from gi.repository.GdkPixbuf import InterpType

except ImportError as error:
    sys_exit("Import error with python3-gobject module: %s" % str(error))

# ------------------------------------------------------------------
#   Modules - GEM
# ------------------------------------------------------------------

try:
    from gem import *
    from gem.utils import *

except ImportError as error:
    sys_exit("Import error with gem module: %s" % str(error))

# ------------------------------------------------------------------
#   Translation
# ------------------------------------------------------------------

bindtextdomain("gem", get_data("i18n"))
textdomain("gem")

# ------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------

class Dialog(Gtk.Dialog):

    def __init__(self, parent, title, icon):
        """ Constructor

        Parameters
        ----------
        parent : Gtk.Window
            Parent object
        title : str
            Dialog title
        icon : str
            Default icon name
        """

        Gtk.Dialog.__init__(self)

        # ------------------------------------
        #   Initialize variables
        # ------------------------------------

        self.interface = parent
        self.title = title
        self.icon = icon

        # ------------------------------------
        #   Main dialog
        # ------------------------------------

        self.set_title(title)
        self.set_default_icon_name(icon)

        if parent is not None:
            self.set_transient_for(parent.window)

        self.set_modal(True)
        self.set_can_focus(True)
        self.set_resizable(False)
        self.set_keep_above(True)
        self.set_destroy_with_parent(True)

        self.set_type_hint(Gdk.WindowTypeHint.DIALOG)

        self.set_position(Gtk.WindowPosition.CENTER_ALWAYS)

        self.set_border_width(4)

        # ------------------------------------
        #   Main grid
        # ------------------------------------

        self.dialog_box = self.get_content_area()

        # Properties
        self.dialog_box.set_spacing(8)
        self.dialog_box.set_border_width(4)

        # ------------------------------------
        #   Header
        # ------------------------------------

        grid_header = Gtk.Box()

        image_header = Gtk.Image()
        label_header = Gtk.Label()

        # Properties
        grid_header.set_spacing(2)
        grid_header.set_orientation(Gtk.Orientation.HORIZONTAL)
        grid_header.set_border_width(4)

        image_header.set_from_icon_name(self.icon, Gtk.IconSize.DND)

        label_header.set_alignment(0, .5)
        label_header.set_use_markup(True)
        label_header.set_single_line_mode(True)
        label_header.set_ellipsize(Pango.EllipsizeMode.END)
        label_header.set_markup("<span font='14'><b>%s</b></span>" % \
            GLib.markup_escape_text(self.title, -1))

        # ------------------------------------
        #   Integrate widgets
        # ------------------------------------

        grid_header.pack_start(image_header, False, True, 8)
        grid_header.pack_start(label_header, True, True, 0)

        self.dialog_box.pack_start(grid_header, False, True, 0)


    def set_size(self, width, height):
        """ Set a new size for dialog

        Parameters
        ----------
        width : int
            Dialog width
        height : int
            Dialog height
        """

        self.set_size_request(width, height)
        self.set_default_size(width, height)


class TemplateDialog(Dialog):

    def __init__(self, parent, title, message, icon, center=True):
        """ Constructor

        Parameters
        ----------
        parent : Gtk.Window
            Parent object
        title : str
            Dialog title
        message : str
            Dialog message
        icon : str
            Default icon name

        Other Parameters
        ----------------
        center : bool
            If False, use justify text insted of center (Default: True)
        """

        Dialog.__init__(self, parent, title, icon)

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

        # Start interface
        self.__start_interface()


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

        if(self.center):
            text.set_alignment(.5, .5)
            text.set_justify(Gtk.Justification.CENTER)
        else:
            text.set_alignment(0, .5)
            text.set_justify(Gtk.Justification.FILL)


        # ------------------------------------
        #   Integrate widgets
        # ------------------------------------

        self.dialog_box.pack_start(text, False, False, 10)


    def __start_interface(self):
        """ Load data and start interface
        """

        self.show_all()


class Message(TemplateDialog):

    def __init__(self, parent, title, message, icon="dialog-information",
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

        self.add_buttons(
            Gtk.STOCK_OK, Gtk.ResponseType.OK)


class Question(TemplateDialog):

    def __init__(self, parent, title, message, icon="dialog-question",
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
            Default icon name (Default: dialog-question)
        center : bool
            If False, use justify text insted of center (Default: True)
        """

        TemplateDialog.__init__(self, parent, title, message, icon, center)

        self.add_buttons(
            Gtk.STOCK_NO, Gtk.ResponseType.NO,
            Gtk.STOCK_YES, Gtk.ResponseType.YES)


class DialogEditor(Dialog):

    def __init__(self, parent, title, file_path, editable=True,
        icon="gtk-file"):
        """ Constructor

        Parameters
        ----------
        parent : Gtk.Window
            Parent object
        title : str
            Dialog title
        file_path : str
            File path

        Other Parameters
        ----------------
        editable : bool
            If True, allow to modify and save text buffer to file_path
            (Default: True)
        icon : str
            Default icon name (Default: gtk-file)
        """

        Dialog.__init__(self, parent, title, icon)

        # ------------------------------------
        #   Initialize variables
        # ------------------------------------

        self.path = file_path
        self.editable = editable

        if type(self.editable) is not bool:
            raise TypeError("Wrong type for editable : bool wanted !")

        self.founded_iter = list()
        self.current_index = int()
        self.previous_search = str()

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

        self.set_size(800, 600)

        if self.editable:
            self.add_buttons(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_SAVE, Gtk.ResponseType.APPLY)

        else:
            self.add_buttons(
                Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE)

        # ------------------------------------
        #   Grid
        # ------------------------------------

        bottom_grid = Gtk.Box()

        # Properties
        bottom_grid.set_orientation(Gtk.Orientation.HORIZONTAL)

        # ------------------------------------
        #   Path
        # ------------------------------------

        self.entry_path = Gtk.Entry()

        # Properties
        self.entry_path.set_editable(False)
        self.entry_path.set_icon_from_icon_name(
            Gtk.EntryIconPosition.PRIMARY, "text-x-generic")
        self.entry_path.set_icon_activatable(
            Gtk.EntryIconPosition.PRIMARY, False)

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

            except ImportError as error:
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
        #   Back lines
        # ------------------------------------

        self.check_lines = Gtk.CheckButton()

        # Properties
        self.check_lines.set_label(_("Auto line break"))
        self.check_lines.set_active(False)

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
            Gtk.EntryIconPosition.PRIMARY, "edit-find")
        self.entry_search.set_icon_activatable(
            Gtk.EntryIconPosition.PRIMARY, False)
        self.entry_search.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, "edit-clear")

        self.image_up.set_from_icon_name("go-up", Gtk.IconSize.BUTTON)

        self.button_up.set_label(str())
        self.button_up.set_image(self.image_up)

        self.image_bottom.set_from_icon_name("go-down", Gtk.IconSize.BUTTON)

        self.button_bottom.set_label(str())
        self.button_bottom.set_image(self.image_bottom)

        # ------------------------------------
        #   Integrate widgets
        # ------------------------------------

        scroll_editor.add(self.text_editor)

        bottom_grid.pack_start(self.check_lines, False, True, 0)
        bottom_grid.pack_end(self.button_bottom, False, True, 0)
        bottom_grid.pack_end(self.button_up, False, True, 4)
        bottom_grid.pack_end(self.entry_search, False, True, 0)

        self.dialog_box.pack_start(self.entry_path, False, True, 0)
        self.dialog_box.pack_start(scroll_editor, True, True, 0)
        self.dialog_box.pack_start(bottom_grid, False, True, 0)


    def __init_signals(self):
        """ Initialize widgets signals
        """

        self.check_lines.connect("toggled", self.__on_break_line)

        self.entry_search.connect("activate", self.__on_entry_update)
        self.entry_search.connect("icon-press", on_entry_clear)

        self.button_bottom.connect("clicked", self.__on_move_search)
        self.button_up.connect("clicked", self.__on_move_search, True)


    def __start_interface(self):
        """ Load data and start interface
        """

        self.entry_path.set_text(self.path)

        if exists(expanduser(self.path)):
            with open(self.path, 'r') as pipe:
                self.buffer_editor.set_text(''.join(pipe.readlines()))

        self.show_all()

        self.text_editor.grab_focus()


    def __on_break_line(self, widget):
        """ Set break line mode for textview

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        if self.check_lines.get_active():
            self.text_editor.set_wrap_mode(Gtk.WrapMode.WORD)
        else:
            self.text_editor.set_wrap_mode(Gtk.WrapMode.NONE)


    def __on_move_search(self, widget=None, backward=False):
        """ Move between search results

        Other Parameters
        ----------------
        widget : Gtk.Widget
            Object which receive signal (Default: None)
        backward : bool
            If True, use backward search instead of forward (Default: False)
        """

        if len(self.founded_iter) > 0:
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
            self.founded_iter = list()
            self.current_index = int()

            if len(text) > 0:
                self.buffer_editor.remove_all_tags(
                    self.buffer_editor.get_start_iter(),
                    self.buffer_editor.get_end_iter())

                self.__on_search_and_mark(
                    text, self.buffer_editor.get_start_iter())

                if len(self.founded_iter) > 0:
                    match = self.founded_iter[self.current_index]
                    self.buffer_editor.apply_tag(
                        self.tag_current, match[0], match[1])

                    self.text_editor.scroll_to_iter(
                        match[0], .25, False, .0, .0)

                    self.previous_search = text

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


class DialogParameters(Dialog):

    def __init__(self, parent, title, emulator):
        """ Constructor

        Parameters
        ----------
        parent : Gtk.Window
            Parent object
        title : str
            Dialog title
        emulator : str
            Emulator name
        """

        Dialog.__init__(self, parent, title, "emblem-important")

        # ------------------------------------
        #   Initialize variables
        # ------------------------------------

        self.interface = parent

        self.emulator = emulator

        # HACK: Create an empty image to avoid g_object_set_qdata warning
        self.empty = Pixbuf.new(Colorspace.RGB, True, 8, 24, 24)
        self.empty.fill(0x00000000)

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

        self.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OK, Gtk.ResponseType.OK)

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
        label_emulator.set_alignment(0, .5)
        label_emulator.set_text(_("Set default emulator"))

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

        label_arguments = Gtk.Label()

        self.entry = Gtk.Entry()

        # Properties
        label_arguments.set_alignment(0, .5)
        label_arguments.set_text(_("Set default arguments"))

        self.entry.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, "gtk-clear")

        # ------------------------------------
        #   Integrate widgets
        # ------------------------------------

        self.dialog_box.pack_start(label_emulator, False, True, 0)
        self.dialog_box.pack_start(self.combo, False, True, 0)
        self.dialog_box.pack_start(Gtk.Separator(), False, True, 4)
        self.dialog_box.pack_start(label_arguments, False, True, 0)
        self.dialog_box.pack_start(self.entry, False, True, 0)


    def __init_signals(self):
        """ Initialize widgets signals
        """

        self.combo.connect("changed", self.__on_selected_emulator)

        self.entry.connect("icon-press", on_entry_clear)


    def __start_interface(self):
        """ Load data and start interface
        """

        self.show_all()

        self.model.append([self.empty, str(), self.empty])

        for emulator in self.interface.emulators.sections():
            icon = icon_from_data(self.interface.emulators.item(
                emulator, "icon"), self.empty, 24, 24, "emulators")

            path = self.interface.emulators.item(emulator, "binary")

            warning = self.empty
            if len(get_binary_path(path)) == 0:
                warning = self.interface.icons["warning"]

            row = self.model.append([icon, emulator, warning])

            if (self.emulator["rom"] is not None and \
                emulator == self.emulator["rom"]) or \
                (self.emulator["console"] is not None and \
                emulator == self.emulator["console"]):
                self.combo.set_active_iter(row)

        if self.emulator["parameters"] is not None:
            self.entry.set_text(self.emulator["parameters"])

        self.combo.grab_focus()


    def __on_selected_emulator(self, widget=None):
        """ Select an emulator in combobox and update parameters placeholder

        Other Parameters
        ----------------
        widget : Gtk.Widget
            Object which receive signal (Default: None)
        """

        default = str()

        emulator = self.combo.get_active_id()

        if emulator is not None:
            if self.interface.emulators.has_option(emulator, "default"):
                default = self.interface.emulators.get(emulator, "default")

        path = self.interface.emulators.item(emulator, "binary")

        # Allow to validate dialog if selected emulator binary exist
        if len(get_binary_path(path)) == 0:
            self.set_response_sensitive(Gtk.ResponseType.OK, False)

        else:
            self.set_response_sensitive(Gtk.ResponseType.OK, True)

        self.entry.set_placeholder_text(default)


class DialogRemove(Dialog):

    def __init__(self, parent, title):
        """ Constructor

        Parameters
        ----------
        parent : Gtk.Window
            Parent object
        title : str
            Dialog title
        """

        Dialog.__init__(self, parent, title, "edit-delete")

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

        self.add_buttons(
            Gtk.STOCK_NO, Gtk.ResponseType.NO,
            Gtk.STOCK_YES, Gtk.ResponseType.YES)

        # ------------------------------------
        #   Description
        # ------------------------------------

        label = Gtk.Label()

        # Properties
        label.set_alignment(0, .5)
        label.set_text(_("This game is going to be removed from your disk and "
            "this action is irreversible."))
        label.set_line_wrap(True)
        label.set_single_line_mode(False)
        label.set_line_wrap_mode(Pango.WrapMode.CHAR)

        # ------------------------------------
        #   Options
        # ------------------------------------

        self.check_database = Gtk.CheckButton()
        self.check_save_state = Gtk.CheckButton()
        self.check_screenshots = Gtk.CheckButton()

        # Properties
        self.check_database.set_label(_("Remove game's data from database"))
        self.check_save_state.set_label(_("Remove game save files"))
        self.check_screenshots.set_label(_("Remove game screenshots"))

        # ------------------------------------
        #   Integrate widgets
        # ------------------------------------

        self.dialog_box.pack_start(label, False, True, 0)
        self.dialog_box.pack_start(Gtk.Separator(), False, True, 4)
        self.dialog_box.pack_start(self.check_database, False, True, 0)
        self.dialog_box.pack_start(Gtk.Separator(), False, True, 4)
        self.dialog_box.pack_start(self.check_save_state, False, True, 0)
        self.dialog_box.pack_start(self.check_screenshots, False, True, 0)


    def __start_interface(self):
        """ Load data and start interface
        """

        self.show_all()

        self.check_database.set_active(True)


class DialogRename(Dialog):

    def __init__(self, parent, title, description, name=str()):
        """ Constructor

        Parameters
        ----------
        parent : Gtk.Window
            Parent object
        title : str
            Dialog title
        description : str
            Dialog message

        Other Parameters
        ----------------
        name : str
            Rom current name (Default: "")
        """

        Dialog.__init__(self, parent, title, "tools-check-spelling")

        # ------------------------------------
        #   Initialize variables
        # ------------------------------------

        self.description = description
        self.name = name

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

        self.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_APPLY, Gtk.ResponseType.APPLY)

        # ------------------------------------
        #   Widgets
        # ------------------------------------

        self.label = Gtk.Label()

        self.entry = Gtk.Entry()

        # Properties
        self.label.set_alignment(0, .5)
        self.label.set_line_wrap(True)
        self.label.set_single_line_mode(False)
        self.label.set_line_wrap_mode(Pango.WrapMode.CHAR)

        self.entry.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, "gtk-clear")

        # ------------------------------------
        #   Integrate widgets
        # ------------------------------------

        self.dialog_box.pack_start(self.label, False, True, 0)
        self.dialog_box.pack_start(self.entry, False, True, 0)


    def __init_signals(self):
        """ Initialize widgets signals
        """

        self.entry.connect("icon-press", on_entry_clear)


    def __start_interface(self):
        """ Load data and start interface
        """

        self.show_all()

        self.label.set_text(self.description)
        self.entry.set_text(self.name)


class DialogViewer(Dialog):

    def __init__(self, parent, title, screenshots_path):
        """ Constructor

        Parameters
        ----------
        parent : Gtk.Window
            Parent object
        title : str
            Dialog title
        screenshots_path : list
            Screnshots path list
        """

        Dialog.__init__(self, parent, title, "image-x-generic")

        # ------------------------------------
        #   Initialize variables
        # ------------------------------------

        self.index = 0
        self.zoom_factor = 1

        self.zoom_fit = True

        self.screenshots = screenshots_path

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

        self.set_size(800, 600)

        # ------------------------------------
        #   Image
        # ------------------------------------

        self.scroll_image = Gtk.ScrolledWindow()
        view_image = Gtk.Viewport()

        self.image = Gtk.Image()

        # ------------------------------------
        #   Toolbar
        # ------------------------------------

        toolbar = Gtk.Toolbar()

        tool_separator_start = Gtk.SeparatorToolItem()
        tool_separator_end = Gtk.SeparatorToolItem()

        self.tool_first = Gtk.ToolButton()
        self.tool_previous = Gtk.ToolButton()
        self.tool_next = Gtk.ToolButton()
        self.tool_last = Gtk.ToolButton()

        self.tool_zoom_minus = Gtk.ToolButton()
        self.tool_zoom_100 = Gtk.ToolButton()
        self.tool_zoom_fit = Gtk.ToolButton()
        self.tool_zoom_plus = Gtk.ToolButton()

        # Properties
        toolbar.set_orientation(Gtk.Orientation.HORIZONTAL)

        tool_separator_start.set_draw(False)
        tool_separator_start.set_expand(True)
        tool_separator_end.set_draw(False)
        tool_separator_end.set_expand(True)

        self.tool_first.set_icon_name("gtk-goto-first")
        self.tool_previous.set_icon_name("gtk-go-back")
        self.tool_next.set_icon_name("gtk-go-forward")
        self.tool_last.set_icon_name("gtk-goto-last")

        self.tool_zoom_minus.set_icon_name("gtk-zoom-out")
        self.tool_zoom_100.set_icon_name("gtk-zoom-100")
        self.tool_zoom_fit.set_icon_name("gtk-zoom-fit")
        self.tool_zoom_plus.set_icon_name("gtk-zoom-in")

        # ------------------------------------
        #   Integrate widgets
        # ------------------------------------

        self.scroll_image.add(view_image)
        view_image.add(self.image)

        toolbar.insert(tool_separator_start, -1)
        toolbar.insert(self.tool_first, -1)
        toolbar.insert(self.tool_previous, -1)
        toolbar.insert(Gtk.SeparatorToolItem(), -1)
        toolbar.insert(self.tool_zoom_minus, -1)
        toolbar.insert(self.tool_zoom_100, -1)
        toolbar.insert(self.tool_zoom_fit, -1)
        toolbar.insert(self.tool_zoom_plus, -1)
        toolbar.insert(Gtk.SeparatorToolItem(), -1)
        toolbar.insert(self.tool_next, -1)
        toolbar.insert(self.tool_last, -1)
        toolbar.insert(tool_separator_end, -1)

        self.dialog_box.pack_start(self.scroll_image, True, True, 0)
        self.dialog_box.pack_start(toolbar, False, True, 0)


    def __init_signals(self):
        """ Initialize widgets signals
        """

        # self.connect("size-allocate", self.update_screenshot)
        self.connect("key-press-event", self.change_screenshot)

        self.tool_first.connect("clicked", self.change_screenshot)
        self.tool_previous.connect("clicked", self.change_screenshot)
        self.tool_next.connect("clicked", self.change_screenshot)
        self.tool_last.connect("clicked", self.change_screenshot)

        self.tool_zoom_minus.connect("clicked", self.change_screenshot)
        self.tool_zoom_100.connect("clicked", self.change_screenshot)
        self.tool_zoom_fit.connect("clicked", self.change_screenshot)
        self.tool_zoom_plus.connect("clicked", self.change_screenshot)


    def __start_interface(self):
        """ Load data and start interface
        """

        self.show_all()

        self.set_widgets_sensitive()
        self.update_screenshot()

        self.run()

        self.destroy()


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

            elif event.keyval == Gdk.KEY_KP_Subtract and self.zoom_factor > .1:
                self.zoom_fit = False
                self.zoom_factor -= .1
            elif event.keyval == Gdk.KEY_KP_Add and self.zoom_factor < 20:
                self.zoom_fit = False
                self.zoom_factor += .1

        # Zoom
        elif widget == self.tool_zoom_minus and self.zoom_factor > 1:
            self.zoom_fit = False
            self.zoom_factor -= .1
        elif widget == self.tool_zoom_100:
            self.zoom_fit = False
            self.zoom_factor = 1
        elif widget == self.tool_zoom_fit:
            self.zoom_fit = True
        elif widget == self.tool_zoom_plus and self.zoom_factor < 5:
            self.zoom_fit = False
            self.zoom_factor += .1

        # Move
        elif widget == self.tool_first:
            self.index = 0
        elif widget == self.tool_previous:
            self.index -= 1
        elif widget == self.tool_next:
            self.index += 1
        elif widget == self.tool_last:
            self.index = len(self.screenshots) - 1

        if self.index < 0:
            self.index = 0
        elif self.index > len(self.screenshots) - 1:
            self.index = len(self.screenshots) - 1

        if self.zoom_factor < .1:
            self.zoom_factor = .1
        elif self.zoom_factor > 20:
            self.zoom_factor = 20

        self.update_screenshot()
        self.set_widgets_sensitive()


    def set_widgets_sensitive(self):
        """ Refresh interface's widgets
        """

        self.tool_first.set_sensitive(True)
        self.tool_previous.set_sensitive(True)
        self.tool_next.set_sensitive(True)
        self.tool_last.set_sensitive(True)

        if self.index == 0:
            self.tool_first.set_sensitive(False)
            self.tool_previous.set_sensitive(False)

        if self.index == len(self.screenshots) - 1:
            self.tool_next.set_sensitive(False)
            self.tool_last.set_sensitive(False)


    def update_screenshot(self, widget=None, event=None):
        """ Change current screenshot size

        Other Parameters
        ----------------
        widget : Gtk.Widget
            Object which receive signal (Default: None)
        event : Gdk.EventButton or Gdk.EventKey
            Event which triggered this signal (Default: None)
        """

        pixbuf = Pixbuf.new_from_file(
            expanduser(self.screenshots[self.index]))

        width, height = pixbuf.get_width(), pixbuf.get_height()

        if self.zoom_fit:
            allocation = self.scroll_image.get_allocation()

            ratio_x = float(allocation.width / width)
            ratio_y = float(allocation.height / height)

            self.zoom_factor = min(ratio_x, ratio_y)

        self.image.set_from_pixbuf(pixbuf.scale_simple(
            int(self.zoom_factor * width), int(self.zoom_factor * height),
             InterpType.TILES))


class DialogConsoles(Dialog):

    def __init__(self, parent, title, consoles, previous=None):
        """ Constructor

        Parameters
        ----------
        parent : Gtk.Window
            Parent object
        title : str
            Dialog title
        consoles : list
            Consoles list

        Other Parameters
        ----------------
        previous : str or None
            Previous selected console (Default: None)
        """

        Dialog.__init__(self, parent, title, "input-gaming")

        # ------------------------------------
        #   Initialize variables
        # ------------------------------------

        self.current = None

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

        self.set_size(500, 300)

        self.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_SAVE, Gtk.ResponseType.APPLY)

        # ------------------------------------
        #   Scroll
        # ------------------------------------

        scroll_consoles = Gtk.ScrolledWindow()
        view_consoles = Gtk.Viewport()

        # ------------------------------------
        #   Description
        # ------------------------------------

        label_description = Gtk.Label()

        # Properties
        label_description.set_alignment(0, .5)
        label_description.set_max_width_chars(10)
        label_description.set_line_wrap(True)
        label_description.set_justify(Gtk.Justification.FILL)
        label_description.set_label(_("This extension is available in multiple "
            "consoles. Which one GEM must use to move this file ?"))

        # ------------------------------------
        #   Consoles
        # ------------------------------------

        self.model_consoles = Gtk.ListStore(bool, str)
        self.treeview_consoles = Gtk.TreeView()

        column_consoles = Gtk.TreeViewColumn()

        self.cell_consoles_status = Gtk.CellRendererToggle()
        cell_consoles_name = Gtk.CellRendererText()

        # Properties
        self.model_consoles.set_sort_column_id(1, Gtk.SortType.ASCENDING)

        self.treeview_consoles.set_model(self.model_consoles)
        self.treeview_consoles.set_headers_visible(False)

        column_consoles.set_expand(True)
        column_consoles.pack_start(self.cell_consoles_status, False)
        column_consoles.set_attributes(self.cell_consoles_status, active=0)
        column_consoles.pack_start(cell_consoles_name, True)
        column_consoles.set_attributes(cell_consoles_name, text=1)

        self.cell_consoles_status.set_radio(True)
        self.cell_consoles_status.set_activatable(True)

        cell_consoles_name.set_padding(8, 0)
        cell_consoles_name.set_alignment(0, .5)

        self.treeview_consoles.append_column(column_consoles)

        # ------------------------------------
        #   Integrate widgets
        # ------------------------------------

        scroll_consoles.add(view_consoles)
        view_consoles.add(self.treeview_consoles)

        self.dialog_box.pack_start(label_description, False, True, 0)
        self.dialog_box.pack_start(scroll_consoles, True, True, 0)


    def __init_signals(self):
        """ Initialize widgets signals
        """

        self.cell_consoles_status.connect("toggled", self.on_cell_toggled)


    def __start_interface(self):
        """ Load data and start interface
        """

        self.show_all()

        self.set_response_sensitive(Gtk.ResponseType.APPLY, False)

        for console in self.consoles:
            status = False
            if self.previous is not None and self.previous == console:
                status = True

                self.current = console
                self.set_response_sensitive(Gtk.ResponseType.APPLY, True)

            self.model_consoles.append([status, console])


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
        self.current = self.model_consoles.get_value(treeiter, 1)

        for row in self.model_consoles:
            row[0] = (row.path == selected_path)


# ------------------------------------------------------------------
#   Misc functions
# ------------------------------------------------------------------

def icon_from_data(icon, fallback=None, width=24, height=24, subfolder=None):
    """ Load an icon from path

    This function search if a path is available in Path.Icons folder and return
    a generate Pixbuf from the path. If no icon was found, return an empty
    generate Pixbuf.

    Parameters
    ----------
    icon : str
        Icon path

    Other Parameters
    ----------------
    fallback : GdkPixbuf.Pixbuf
        Fallback icon to return instead of empty (Default: None)
    width : int
        Icon width in pixels (Default: 24)
    height : int
        Icon height in pixels (Default: 24)
    subfolder : str
        Subfolder in Path.Icons (Default: None)

    Returns
    -------
    GdkPixbuf.Pixbuf
        Pixbuf icon object
    """

    if icon is not None:
        path = icon

        if not exists(expanduser(icon)):
            path = path_join(Path.Icons, "%s.%s" % (icon, Icons.Ext))

            if subfolder is not None:
                path = path_join(
                    Path.Icons, subfolder, "%s.%s" % (icon, Icons.Ext))

        if path is not None and exists(expanduser(path)):
            try:
                return Pixbuf.new_from_file_at_size(
                    expanduser(path), width, height)
            except GError:
                pass

    # Return an empty icon
    if fallback is None:
        fallback = Pixbuf.new(Colorspace.RGB, True, 8, width, height)
        fallback.fill(0x00000000)

    return fallback

def icon_load(name, size=16, fallback="image-missing"):
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
        "image-missing", size, Gtk.IconLookupFlags.FORCE_SVG)

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
