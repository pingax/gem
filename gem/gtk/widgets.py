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

        Others Parameters
        -----------------
        classic : bool
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


    def destroy(self):
        """ Destroy dialog
        """

        # Gtk.Window
        if self.parent is None:
            Gtk.main_quit()

        # Gtk.Dialog
        else:
            self.window.destroy()


    def add_widget(self, widget, align=Gtk.Align.START,
        expand=False, fill=False, padding=0):
        """ Add a widget to dialog headerbar

        Parameters
        ----------
        widget : Gtk.Widget
            Widget to add

        Others Parameters
        -----------------
        align : Gtk.Align
            Widget alignment (Default: Gtk.Align.START)
        expand : bool
            Extra space will be divided evenly between all children that use
            this option (Default: False)
        fill : bool
            Always allocated the full size of a Gtk.Box (Default: False)
        padding : int
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

        Others Parameters
        -----------------
        align : Gtk.Align
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
            if response == Gtk.ResponseType.APPLY:
                button.get_style_context().add_class("suggested-action")
            elif response == Gtk.ResponseType.YES:
                button.get_style_context().add_class("destructive-action")

            if align == Gtk.Align.END:
                self.headerbar.pack_end(button)
            else:
                self.headerbar.pack_start(button)

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


    def pack_end(self, child, expand=True, fill=True, padding=0):
        """ Packing child widget into dialog grid

        Parameters
        ----------
        child : Gtk.Widget
            Child widget to pack

        Others Parameters
        -----------------
        expand : bool
            Extra space will be divided evenly between all children that use
            this option (Default: True)
        fill : bool
            Always allocated the full size of a Gtk.Box (Default: True)
        padding : int
            Extra space in pixels to put between this child and its neighbors
            (Default: 0)
        """

        self.grid.pack_end(child, expand, fill, padding)


    def pack_start(self, child, expand=True, fill=True, padding=0):
        """ Packing child widget into dialog grid

        Parameters
        ----------
        child : Gtk.Widget
            Child widget to pack

        Others Parameters
        -----------------
        expand : bool
            Extra space will be divided evenly between all children that use
            this option (Default: True)
        fill : bool
            Always allocated the full size of a Gtk.Box (Default: True)
        padding : int
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

        self.window.set_size_request(width, height)
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


class CheckMenuItem(Gtk.MenuItem):

    __gsignals__ = { "toggled": (SIGNAL_RUN_FIRST, None, [object]) }

    def __init__(self):
        """ Constructor
        """

        Gtk.MenuItem.__init__(self)

        # ------------------------------------
        #   Check label
        # ------------------------------------

        self.__menu_item_check = Gtk.CheckButton()

        # Properties
        self.__menu_item_check.set_halign(Gtk.Align.START)
        self.__menu_item_check.set_use_underline(True)

        # ------------------------------------
        #   Integrate widgets
        # ------------------------------------

        self.add(self.__menu_item_check)


    def get_label(self):
        """ Get the label from widget

        Returns
        -------
        str
            Label content
        """

        return self.__menu_item_check.get_label()


    def set_label(self, label):
        """ Set the widget label content

        Parameters
        ----------
        label : str
            New label string
        """

        if type(label) is not str:
            raise TypeError(
                "Cannot use %s as label, expected str" % str(type(label)))

        self.__menu_item_check.set_label(label)


    def get_active(self):
        """ Get the widget status

        Returns
        -------
        bool
            Toggle button status
        """

        return self.__menu_item_check.get_active()


    def set_active(self, status):
        """ Set the widget status

        Parameters
        ----------
        status : bool
            New widget status
        """

        if type(status) is not bool:
            raise TypeError(
                "Cannot use %s as status, expected str" % str(type(status)))

        self.__menu_item_check.set_active(status)


class ImageMenuItem(Gtk.MenuItem):

    def __init__(self):
        """ Constructor
        """

        Gtk.MenuItem.__init__(self)

        # ------------------------------------
        #   Grid
        # ------------------------------------

        self.__box = Gtk.Box()

        # Properties
        self.__box.set_spacing(6)
        self.__box.set_orientation(Gtk.Orientation.HORIZONTAL)

        # ------------------------------------
        #   Icon image
        # ------------------------------------

        self.__menu_item_image = Gtk.Image()

        # Properties
        self.__menu_item_image.set_halign(Gtk.Align.START)

        # ------------------------------------
        #   Accelerator label
        # ------------------------------------

        self.__menu_item_label = Gtk.Label()
        self.__menu_item_label_accel = Gtk.Label()

        # Properties
        self.__menu_item_label.set_halign(Gtk.Align.START)
        self.__menu_item_label.set_use_underline(True)
        self.__menu_item_label.set_use_markup(True)

        self.__menu_item_label_accel.get_style_context().add_class("dim-label")
        self.__menu_item_label_accel.set_xalign(1)

        # ------------------------------------
        #   Integrate widgets
        # ------------------------------------

        self.__box.add(self.__menu_item_image)
        self.__box.pack_start(
            self.__menu_item_label, True, True, 0)
        self.__box.pack_end(
            self.__menu_item_label_accel, False, False, 0)

        self.add(self.__box)


    def get_image(self):
        """ Get the image from widget

        Returns
        -------
        Gtk.Image
            Current using image
        """

        return self.__menu_item_image


    def set_image_from_pixbuf(self, pixbuf):
        """ Set the image from a specific pixbuf

        Parameters
        ----------
        pixbuf : GdkPixbuf.Pixbuf
            the Pixbuf object
        """

        if type(pixbuf) is not Pixbuf:
            raise TypeError(
                "Cannot use %s as pixbuf, expected GdkPixbuf.Pixbuf" % str(
                type(pixbuf)))

        self.__menu_item_image.set_from_pixbuf(pixbuf)


    def set_image_from_icon_name(self, icon_name, icon_size=Gtk.IconSize.MENU):
        """ Set the image from a specific icon name

        Parameters
        ----------
        icon_name : str
            the icon name string

        Others Parameters
        -----------------
        icon_size : Gtk.IconSize
            the icon size (Default: Gtk.IconSize.MENU)
        """

        if type(icon_name) is not str:
            raise TypeError(
                "Cannot use %s as icon_name, expected str" % str(
                type(icon_name)))

        if type(icon_size) is not Gtk.IconSize:
            raise TypeError(
                "Cannot use %s as icon_size, expected Gtk.IconSize" % str(
                type(icon_size)))

        self.__menu_item_image.set_from_icon_name(icon_name, icon_size)


    def get_label(self):
        """ Get the label from widget

        Returns
        -------
        str
            Label content
        """

        return self.__menu_item_label.get_label()


    def set_label(self, label):
        """ Set the widget label content

        Parameters
        ----------
        label : str
            New label string
        """

        if type(label) is not str:
            raise TypeError(
                "Cannot use %s as label, expected str" % str(type(label)))

        self.__menu_item_label.set_label(label)


    def get_accelerator(self):
        """ Get the accelerator from widget

        Returns
        -------
        str
            Accelerator content
        """

        return self.__menu_item_label_accel.get_label()


    def set_accelerator(self, max_width, key, mod):
        """ Set the widget accelerator

        Parameters
        ----------
        max_width : int
            the maximum size of shortcut label
        key : int
            the key value
        mod: Gdk.ModifierType
            the modifier mask for the accel
        """

        if type(key) is not int:
            raise TypeError(
                "Cannot use %s as key, expected int" % str(
                type(key)))

        if type(mod) is not Gdk.ModifierType:
            raise TypeError(
                "Cannot use %s as mod, expected Gdk.ModifierType" % str(
                type(mod)))

        self.__menu_item_label_accel.set_width_chars(max_width)
        self.__menu_item_label_accel.set_label(
            Gtk.accelerator_get_label(key, mod))
