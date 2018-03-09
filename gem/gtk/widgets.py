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

# System
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

    from gi.repository.GObject import SIGNAL_RUN_FIRST

    from gi.repository.GdkPixbuf import Pixbuf

except ImportError as error:
    sys_exit("Import error with python3-gobject module: %s" % str(error))

# ------------------------------------------------------------------------------
#   Modules - GEM
# ------------------------------------------------------------------------------

try:
    from gem.gtk import *

    from gem.api import Console
    from gem.api import Emulator
    from gem.utils import *

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

class CommonWindow(object):

    def __init__(self, parent, title, icon, classic=False):
        """ Constructor

        Parameters
        ----------
        parent : Gtk.Window
            Parent object
        title : str
            Dialog title
        icon : str
            Default icon name
        classic : bool, optional
            Using classic theme (Default: False)
        """

        # ------------------------------------
        #   Initialize variables
        # ------------------------------------

        self.parent = parent
        self.title = title
        self.icon = icon

        self.use_classic_theme = classic

        self.has_help_button = False

        self.help_data = list()
        self.sensitive_data = dict()

        # ------------------------------------
        #   Prepare interface
        # ------------------------------------

        # Init widgets
        self.__init_widgets()

        # Init signals
        self.__init_signals()


    def __init_widgets(self):
        """ Initialize interface widgets
        """

        # Gtk.Window
        if self.parent is None:
            self.window = Gtk.Window()

        # Gtk.Dialog
        else:
            self.window = Gtk.Dialog(use_header_bar=not self.use_classic_theme)

            if hasattr(self.parent, "window"):
                self.window.set_transient_for(self.parent.window)

            else:
                self.window.set_transient_for(self.parent)

            self.window.set_modal(True)
            self.window.set_destroy_with_parent(True)

        # Properties
        self.window.set_title(self.title)
        self.window.set_default_icon_name(self.icon)
        self.window.set_can_focus(True)
        self.window.set_resizable(False)
        self.window.set_keep_above(True)

        self.window.set_type_hint(Gdk.WindowTypeHint.DIALOG)

        self.window.set_position(Gtk.WindowPosition.CENTER)

        self.window.set_border_width(0)

        # ------------------------------------
        #   Grid
        # ------------------------------------

        # Gtk.Window
        if self.parent is None:
            self.grid = Gtk.Box()

            # Properties
            self.grid.set_orientation(Gtk.Orientation.VERTICAL)

        # Gtk.Dialog
        else:
            self.grid = self.window.get_content_area()

            # Remove the old action grid
            self.grid.remove(self.grid.get_children()[0])

        self.grid_tools = Gtk.Box()
        self.grid_actions = Gtk.Box()
        self.grid_actions_buttons = Gtk.ButtonBox()

        # Properties
        self.grid.set_spacing(18)
        self.grid.set_border_width(18)

        self.grid_tools.set_spacing(6)

        self.grid_actions.set_spacing(12)

        self.grid_actions_buttons.set_spacing(12)
        self.grid_actions_buttons.set_layout(Gtk.ButtonBoxStyle.END)

        # ------------------------------------
        #   Headerbar
        # ------------------------------------

        if not self.use_classic_theme:

            # Gtk.Window
            if self.parent is None:
                self.headerbar = Gtk.HeaderBar()

                # Properties
                self.headerbar.set_title(self.title)

                self.window.set_titlebar(self.headerbar)

            # Gtk.Dialog
            else:
                self.headerbar = self.window.get_header_bar()

            self.headerbar_image = Gtk.Image()

            # Properties
            self.headerbar_image.set_from_icon_name(
                self.icon, Gtk.IconSize.LARGE_TOOLBAR)

        # ------------------------------------
        #   Help button
        # ------------------------------------

        self.image_help = Gtk.Image()

        self.button_help = Gtk.Button()

        # Properties
        self.image_help.set_from_icon_name(
            Icons.Symbolic.Help, Gtk.IconSize.MENU)

        self.button_help.set_image(self.image_help)
        self.button_help.set_relief(Gtk.ReliefStyle.NONE)
        self.button_help.set_tooltip_text(_("Get some help about this dialog"))

        # ------------------------------------
        #   Integrate widgets
        # ------------------------------------

        if self.use_classic_theme:
            self.grid.pack_start(self.grid_tools, False, False, 0)

            self.grid.pack_end(self.grid_actions, False, False, 0)

            self.grid_actions.pack_end(
                self.grid_actions_buttons, False, False, 0)

        else:
            self.headerbar.pack_start(self.headerbar_image)

        # Gtk.Window
        if self.parent is None:
            self.window.add(self.grid)


    def __init_signals(self):
        """ Initialize widgets signals
        """

        # Gtk.Window
        if self.parent is None:
            self.window.connect("delete-event", self.destroy)


    def __on_show_help(self, widget):
        """ Launch help dialog

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        dialog = DialogHelp(
            self.parent, _("Help"), '\n\n'.join(self.help_data), Icons.Help)

        dialog.set_size(640, 480)

        dialog.run()
        dialog.destroy()


    def show_all(self):
        """ Recursively shows a widget, and any child widgets
        """

        if len(self.grid_tools.get_children()) == 0:
            self.grid.remove(self.grid_tools)

        if len(self.grid_actions_buttons.get_children()) == 0:
            self.grid.remove(self.grid_actions)

        self.window.hide()
        self.window.unrealize()

        self.window.show_all()


    def run(self):
        """ Start dialog

        Returns
        -------
        Gtk.ResponseType
            Dialog response
        """

        self.show_all()

        # Gtk.Dialog
        if self.parent is not None:
            return self.window.run()

        # Gtk.Window
        Gtk.main()


    def destroy(self, *args):
        """ Destroy dialog
        """

        # Gtk.Window
        if self.parent is None:
            Gtk.main_quit()

        # Gtk.Dialog
        else:
            self.window.destroy()


    def add_widget(self, widget, align=Gtk.Align.START,
        expand=False, fill=False, padding=int()):
        """ Add a widget to dialog headerbar

        Parameters
        ----------
        widget : Gtk.Widget
            Widget to add
        align : Gtk.Align, optional
            Widget alignment (Default: Gtk.Align.START)
        expand : bool, optional
            Extra space will be divided evenly between all children that use
            this option (Default: False)
        fill : bool, optional
            Always allocated the full size of a Gtk.Box (Default: False)
        padding : int, optional
            Extra space in pixels to put between this child and its neighbors
            (Default: 0)

        Raises
        ------
        TypeError
            if align type is not Gtk.Align
        """

        if type(align) is not Gtk.Align:
            raise TypeError(
                "Wrong type for align, expected Gtk.Align")

        # Using default theme
        if not self.use_classic_theme:

            if align == Gtk.Align.END:
                self.headerbar.pack_end(widget)

            else:
                self.headerbar.pack_start(widget)

                if self.headerbar_image in self.headerbar.get_children():
                    self.headerbar.remove(self.headerbar_image)

        # Using classic theme
        else:

            if align == Gtk.Align.END:
                self.grid_tools.pack_end(widget, expand, fill, padding)
            else:
                self.grid_tools.pack_start(widget, expand, fill, padding)


    def add_button(self, label, response, align=Gtk.Align.START):
        """ Add a button to dialog interface

        Parameters
        ----------
        label : str
            Button label
        response : Gtk.ResponseType
            Button response type
        align : Gtk.Align, optional
            Button alignment (Default: Gtk.Align.START)

        Returns
        -------
        Gtk.Button
            Generated button to allow signals connecting when no parent
            available (Gtk.Window mode)

        Raises
        ------
        TypeError
            if align type is not Gtk.Align
        TypeError
            if response type is not Gtk.ResponseType
        ValueError
            if a button with response type already exists
        """

        if type(response) is not Gtk.ResponseType:
            raise TypeError(
                "Wrong type for response, expected Gtk.ResponseType")

        if type(align) is not Gtk.Align:
            raise TypeError(
                "Wrong type for align, expected Gtk.Align")

        if response in self.sensitive_data.keys():
            raise ValueError(
                "Response type %s already set" % str(response))

        # ------------------------------------
        #   Button
        # ------------------------------------

        button = Gtk.Button()
        button.set_label(str(label))

        self.sensitive_data[response] = button

        # ------------------------------------
        #   Manage themes
        # ------------------------------------

        # Using default theme
        if not self.use_classic_theme:

            # Add a style to button for specific responses
            if response in [ Gtk.ResponseType.APPLY, Gtk.ResponseType.ACCEPT ]:
                button.get_style_context().add_class("suggested-action")
            elif response in [ Gtk.ResponseType.YES, Gtk.ResponseType.REJECT ]:
                button.get_style_context().add_class("destructive-action")

            if align == Gtk.Align.END:
                self.headerbar.pack_end(button)

            else:
                self.headerbar.pack_start(button)

                if self.headerbar_image in self.headerbar.get_children():
                    self.headerbar.remove(self.headerbar_image)

            if self.headerbar.get_show_close_button():
                self.headerbar.set_show_close_button(False)

        # Using classic theme
        else:

            if align == Gtk.Align.END:
                self.grid_actions_buttons.pack_end(button, False, False, 0)
            else:
                self.grid_actions_buttons.pack_start(button, False, False, 0)

        # Gtk.Dialog
        if self.parent is not None:
            button.connect("clicked", self.emit_response, response)

        return button


    def add_help(self, data):
        """ Add a button to dialog interface

        Parameters
        ----------
        data : dict
            Help data dictionary
        """

        self.help_data = list()

        # Get help data from specified order
        for item in data["order"]:

            # Dictionary value
            if type(data[item]) is dict:
                self.help_data.append("<b>%s</b>" % item)

                for key, value in sorted(
                    data[item].items(), key=lambda key: key[0]):

                    self.help_data.append("\t<b>%s</b>\n\t\t%s" % (
                        key.replace('>', "&gt;").replace('<', "&lt;"), value))

            # List value
            elif type(data[item]) is list:
                self.help_data.append("\n\n".join(data[item]))

            # String value
            elif type(data[item]) is str:
                self.help_data.append(data[item])

        # ------------------------------------
        #   Generate button data
        # ------------------------------------

        if not self.has_help_button:
            self.has_help_button = True

            self.button_help.connect("clicked", self.__on_show_help)

            # Using default theme
            if not self.use_classic_theme:
                self.headerbar.pack_end(self.button_help)

            # Using classic theme
            else:
                self.grid_actions.pack_start(self.button_help, False, False, 0)


    def pack_end(self, child, expand=True, fill=True, padding=int()):
        """ Packing child widget into dialog grid

        Parameters
        ----------
        child : Gtk.Widget
            Child widget to pack
        expand : bool, optional
            Extra space will be divided evenly between all children that use
            this option (Default: True)
        fill : bool, optional
            Always allocated the full size of a Gtk.Box (Default: True)
        padding : int, optional
            Extra space in pixels to put between this child and its neighbors
            (Default: 0)
        """

        self.grid.pack_end(child, expand, fill, padding)


    def pack_start(self, child, expand=True, fill=True, padding=int()):
        """ Packing child widget into dialog grid

        Parameters
        ----------
        child : Gtk.Widget
            Child widget to pack
        expand : bool, optional
            Extra space will be divided evenly between all children that use
            this option (Default: True)
        fill : bool, optional
            Always allocated the full size of a Gtk.Box (Default: True)
        padding : int, optional
            Extra space in pixels to put between this child and its neighbors
            (Default: 0)
        """

        self.grid.pack_start(child, expand, fill, padding)


    def set_border_width(self, border_width):
        """ Set the dialog grid border width value

        Parameters
        ----------
        border_width : int
            Container border with in pixels
        """

        self.grid.set_border_width(border_width)


    def set_spacing(self, spacing):
        """ Set the dialog grid spacing value

        Parameters
        ----------
        spacing : int
            Number of pixels between each child
        """

        self.grid.set_spacing(spacing)


    def get_size(self):
        """ Get current dialog size

        Returns
        -------
        tuple
            dialog size
        """

        return self.window.get_size()


    def set_size(self, width, height):
        """ Set a new size for dialog

        Parameters
        ----------
        width : int
            Dialog width
        height : int
            Dialog height
        """

        # self.window.set_size_request(width, height)
        self.window.set_default_size(width, height)


    def set_modal(self, modal):
        """ Set dialog modal status

        Parameters
        ----------
        modal : bool
            New dialog modal status
        """

        self.window.set_modal(modal)


    def set_orientation(self, orientation):
        """ Set dialog grid orientation

        Parameters
        ----------
        orientation : Gtk.Orientation
            Dialog grid orientation

        Raises
        ------
        TypeError
            if orientation type is not Gtk.Orientation
        """

        if type(orientation) is not Gtk.Orientation:
            raise TypeError(
                "Wrong type for orientation, expected Gtk.Orientation")

        self.grid.set_orientation(orientation)


    def set_resizable(self, resizable):
        """ Set dialog resizable mode

        Parameters
        ----------
        resizable : bool
            Dialog resizable status
        """

        self.window.set_resizable(resizable)


    def set_response_sensitive(self, response, sensitive):
        """ Set button sensitive status

        Parameters
        ----------
        response : Gtk.ResponseType
            Button response type
        sensitive : bool
            Button sensitive status

        Raises
        ------
        NameError
            if button response type has not been set previously
        """

        # Gtk.Window
        if self.parent is None or not self.use_classic_theme:

            if not response in self.sensitive_data.keys():
                raise NameError(
                    "%s type did not exists in data dictionary" % str(response))

            self.sensitive_data[response].set_sensitive(sensitive)

        # Gtk.Dialog
        else:
            self.window.set_response_sensitive(response, sensitive)



    def set_subtitle(self, subtitle):
        """ Set headerbar subtitle if available

        Parameters
        ----------
        subtitle : str
            Headerbar subtitle string
        """

        if not self.use_classic_theme:
            self.headerbar.set_subtitle(subtitle)


    def emit_response(self, widget, response):
        """ Close dialog and emit specified response

        Parameters
        ----------
        widget : Gtk.Button
            Object which received the signal
        response : Gtk.ResponseType
            Response to emit when pushing button

        Raises
        ------
        TypeError
            if response type is not Gtk.ResponseType
        """

        if type(response) is not Gtk.ResponseType:
            raise TypeError(
                "Wrong type for response, expected Gtk.ResponseType")

        self.window.response(response)


class DialogHelp(CommonWindow):

    def __init__(self, parent, title, message, icon):
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
        """

        classic_theme = False
        if parent is not None:
            classic_theme = parent.use_classic_theme

        CommonWindow.__init__(self, parent, title, icon, classic_theme)

        # ------------------------------------
        #   Initialize variables
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

        self.set_size(640, 480)

        self.set_resizable(True)

        # ------------------------------------
        #   Scrollview
        # ------------------------------------

        scroll = Gtk.ScrolledWindow()
        view = Gtk.Viewport()

        # ------------------------------------
        #   Message
        # ------------------------------------

        text = Gtk.Label()

        # Properties
        text.set_alignment(0, 0)
        text.set_line_wrap(True)
        text.set_use_markup(True)
        text.set_max_width_chars(10)
        text.set_markup(self.message)
        text.set_justify(Gtk.Justification.FILL)
        text.set_line_wrap_mode(Pango.WrapMode.WORD)

        # ------------------------------------
        #   Integrate widgets
        # ------------------------------------

        view.add(text)
        scroll.add(view)

        self.pack_start(scroll, True, True)


    def __start_interface(self):
        """ Load data and start interface
        """

        self.show_all()


class ListBoxSelector(Gtk.MenuButton):

    def __init__(self):
        """ Constructor
        """

        Gtk.MenuButton.__init__(self)

        # ------------------------------------
        #   Prepare interface
        # ------------------------------------

        # Init widgets
        self.__init_widgets()

        # Init packing
        self.__init_packing()

        # Start interface
        self.__start_interface()


    def __init_widgets(self):
        """ Initialize interface widgets
        """

        self.set_size_request(256, -1)
        self.set_use_popover(True)

        # ------------------------------------
        #   Grid
        # ------------------------------------

        self.grid_selector = Gtk.Box()

        self.grid_popover = Gtk.Box()

        # Properties
        self.grid_selector.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.grid_selector.set_spacing(12)

        self.grid_popover.set_orientation(Gtk.Orientation.VERTICAL)
        self.grid_popover.set_border_width(12)
        self.grid_popover.set_spacing(12)

        # ------------------------------------
        #   Selector
        # ------------------------------------

        self.label_selector_name = Gtk.Label()

        self.image_selector_icon = Gtk.Image()
        self.image_selector_status = Gtk.Image()

        # Properties
        self.label_selector_name.set_halign(Gtk.Align.START)
        self.image_selector_icon.set_halign(Gtk.Align.CENTER)
        self.image_selector_icon.set_valign(Gtk.Align.CENTER)
        self.image_selector_status.set_halign(Gtk.Align.CENTER)
        self.image_selector_status.set_valign(Gtk.Align.CENTER)

        # ------------------------------------
        #   Popover
        # ------------------------------------

        self.popover_selector = Gtk.Popover()

        self.entry_selector = Gtk.SearchEntry()

        self.frame_selector = Gtk.Frame()
        self.scroll_selector = Gtk.ScrolledWindow()
        self.listbox_selector = Gtk.ListBox()

        # Properties
        self.entry_selector.set_placeholder_text("%s…" % _("Filter"))

        self.scroll_selector.set_size_request(-1, 256)
        self.scroll_selector.set_policy(
            Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)


    def __init_packing(self):
        """ Initialize widgets packing in main window
        """

        self.add(self.grid_selector)

        self.set_popover(self.popover_selector)

        self.grid_selector.pack_start(
            self.image_selector_icon, False, False, 0)
        self.grid_selector.pack_start(
            self.label_selector_name, True, True, 0)
        self.grid_selector.pack_start(
            self.image_selector_status, False, False, 0)

        self.popover_selector.add(self.grid_popover)

        self.frame_selector.add(self.scroll_selector)
        self.scroll_selector.add(self.listbox_selector)

        self.grid_popover.pack_start(
            self.frame_selector, True, True, 0)
        self.grid_popover.pack_start(
            self.entry_selector, False, False, 0)


    def __start_interface(self):
        """ Load data and start interface
        """

        self.show_all()

        self.grid_popover.show_all()
        self.grid_selector.show_all()


    def __on_update_data(self, *args):
        """ Reload consoles list when user set a filter
        """

        self.listbox_selector.invalidate_sort()
        self.listbox_selector.invalidate_filter()


    def append_row(self, data, icon, status):
        """ Append a new row into selector

        Parameters
        ----------
        data : gem.api.Console or gem.api.Emulator
            GEM data instance
        icon : GdkPixbuf.Pixbuf
            Console icon
        status : GdkPixbuf.Pixbuf
            Console status icon

        Returns
        -------
        gem.gtk.widgets.ListBoxSelectorItem
            Generated row
        """

        row = ListBoxSelectorItem(data, icon, status)

        self.listbox_selector.add(row)

        return row


    def clear(self):
        """ Clear listbox items
        """

        children = self.listbox_selector.get_children()

        for child in children:
            self.listbox_selector.remove(child)


    def get_entry(self):
        """ Retrieve entry instance

        Returns
        -------
        Gtk.SearchEntry
            Search entry widget instance
        """

        return self.entry_selector


    def get_listbox(self):
        """ Retrieve listbox instance

        Returns
        -------
        Gtk.ListBox
            Listbox widget instance
        """

        return self.listbox_selector


    def get_selected_row(self):
        """ Retrieve selected row in listbox

        Returns
        -------
        gem.gtk.widgets.ListBoxSelectorItem
            Selected row
        """

        return self.listbox_selector.get_selected_row()


    def invalidate_filter(self):
        """ Filter again listbox content
        """

        self.listbox_selector.invalidate_filter()


    def invalidate_sort(self):
        """ Sort again listbox content
        """

        self.listbox_selector.invalidate_sort()


    def select_row(self, row):
        """ Select a specific row into listbox

        Parameters
        ----------
        row : gem.gtk.widgets.ListBoxSelectorItem
            Row to select
        """

        self.listbox_selector.select_row(row)

        self.label_selector_name.set_label(row.get_label_text())

        self.image_selector_icon.set_from_pixbuf(row.get_icon_pixbuf())
        self.image_selector_status.set_from_pixbuf(row.get_status_pixbuf())


    def set_row_icon(self, row, pixbuf):
        """ Set the icon pixbuf for a specific row

        Parameters
        ----------
        row : gem.gtk.widgets.ListBoxSelectorItem
            Row to modify
        pixbuf : GdkPixbuf.Pixbuf
            Pixbuf instance
        """

        if self.listbox_selector.get_selected_row() == row:
            self.image_selector_icon.set_from_pixbuf(pixbuf)

        row.set_icon_from_pixbuf(pixbuf)


    def set_row_status(self, row, pixbuf):
        """ Set the status pixbuf for a specific row

        Parameters
        ----------
        row : gem.gtk.widgets.ListBoxSelectorItem
            Row to modify
        pixbuf : GdkPixbuf.Pixbuf
            Pixbuf instance
        """

        if self.listbox_selector.get_selected_row() == row:
            self.image_selector_status.set_from_pixbuf(pixbuf)

        row.set_status_from_pixbuf(pixbuf)


    def set_filter_func(self, *args):
        """ Set a filter function to listbox
        """

        self.listbox_selector.set_filter_func(*args)


    def set_sort_func(self, *args):
        """ Set a sort function to listbox
        """

        self.listbox_selector.set_sort_func(*args)


class ListBoxSelectorItem(Gtk.ListBoxRow):

    def __init__(self, data, icon, status):
        """ Constructor

        Parameters
        ----------
        data : gem.api.Console or gem.api.Emulator
            GEM data instance
        icon : GdkPixbuf.Pixbuf
            Console icon
        status : GdkPixbuf.Pixbuf
            Console status icon
        """

        Gtk.ListBoxRow.__init__(self)

        # ------------------------------------
        #   Initialize variables
        # ------------------------------------

        self.data = data

        self.pixbuf_icon = icon
        self.pixbuf_status = status

        # ------------------------------------
        #   Prepare interface
        # ------------------------------------

        # Init widgets
        self.__init_widgets()

        # Init packing
        self.__init_packing()

        # Start interface
        self.__start_interface()


    def __init_widgets(self):
        """ Initialize interface widgets
        """

        # ------------------------------------
        #   Grid
        # ------------------------------------

        self.grid = Gtk.Box()

        # Properties
        self.grid.set_border_width(6)
        self.grid.set_spacing(12)

        # ------------------------------------
        #   Row
        # ------------------------------------

        self.image = Gtk.Image()
        self.status = Gtk.Image()

        self.label = Gtk.Label()

        # Properties
        self.image.set_from_pixbuf(self.pixbuf_icon)
        self.image.set_halign(Gtk.Align.CENTER)
        self.image.set_valign(Gtk.Align.CENTER)

        self.status.set_from_pixbuf(self.pixbuf_status)
        self.status.set_halign(Gtk.Align.CENTER)
        self.status.set_valign(Gtk.Align.CENTER)

        self.label.set_halign(Gtk.Align.START)
        self.label.set_text(self.data.name)


    def __init_packing(self):
        """ Initialize widgets packing in main window
        """

        self.add(self.grid)

        self.grid.pack_start(self.image, False, False, 0)
        self.grid.pack_start(self.label, True, True, 0)
        self.grid.pack_start(self.status, False, False, 0)


    def __start_interface(self):
        """ Load data and start interface
        """

        self.show_all()


    def get_label(self):
        """ Retrieve label instance

        Returns
        -------
        Gtk.Label
            Label widget instance
        """

        return self.label


    def get_label_text(self):
        """ Retrieve label content

        Returns
        -------
        str
            Label content
        """

        return self.label.get_text()


    def get_icon_pixbuf(self):
        """ Retrieve icon pixbuf instance

        Returns
        -------
        GdkPixbuf.Pixbuf
            Icon pixbuf widget instance
        """

        return self.image.get_pixbuf()


    def get_status_pixbuf(self):
        """ Retrieve status pixbuf instance

        Returns
        -------
        GdkPixbuf.Pixbuf
            Status pixbuf widget instance
        """

        return self.status.get_pixbuf()


    def set_icon_from_pixbuf(self, pixbuf):
        """ Set the icon pixbuf

        Parameters
        ----------
        row : gem.gtk.widgets.ListBoxSelectorItem
            Row to modify
        pixbuf : GdkPixbuf.Pixbuf
            Pixbuf instance
        """

        self.pixbuf_icon = pixbuf

        self.image.set_from_pixbuf(pixbuf)


    def set_status_from_pixbuf(self, pixbuf):
        """ Set the status pixbuf

        Parameters
        ----------
        row : gem.gtk.widgets.ListBoxSelectorItem
            Row to modify
        pixbuf : GdkPixbuf.Pixbuf
            Pixbuf instance
        """

        self.pixbuf_status = pixbuf

        self.status.set_from_pixbuf(pixbuf)


    def update(self, data, icon, status):
        """ Update row data with a specific console

        Parameters
        ----------
        console : gem.api.Console
            Console instance
        """

        if not self.data == data:
            self.data = data

            self.pixbuf_icon = icon
            self.pixbuf_status = status

            self.label.set_text(data.name)

            self.image.set_from_pixbuf(icon)
            self.status.set_from_pixbuf(status)
