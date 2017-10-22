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

    from gi.repository.GdkPixbuf import Pixbuf

except ImportError as error:
    sys_exit("Import error with python3-gobject module: %s" % str(error))

# ------------------------------------------------------------------------------
#   Modules - GEM
# ------------------------------------------------------------------------------

try:
    from gem.gtk import *

except ImportError as error:
    sys_exit("Import error with gem module: %s" % str(error))

# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class Dialog(Gtk.Dialog):

    def __init__(self, parent, title, icon, remove_icon=False):
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
        remove_icon : bool
            Remove the top left icon in dialog (Default: False)
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
            self.set_transient_for(parent)

        self.set_modal(True)
        self.set_can_focus(True)
        self.set_resizable(False)
        self.set_keep_above(True)
        self.set_destroy_with_parent(True)

        self.set_type_hint(Gdk.WindowTypeHint.DIALOG)

        self.set_position(Gtk.WindowPosition.CENTER)

        self.set_border_width(0)

        # ------------------------------------
        #   Main grid
        # ------------------------------------

        self.dialog_box = self.get_content_area()

        # Properties
        self.dialog_box.set_spacing(12)
        self.dialog_box.set_border_width(18)

        # ------------------------------------
        #   Headerbar
        # ------------------------------------

        self.headerbar = Gtk.HeaderBar()

        # Properties
        self.headerbar.set_title(self.title)
        self.headerbar.set_has_subtitle(False)
        self.headerbar.set_show_close_button(True)

        # ------------------------------------
        #   Header
        # ------------------------------------

        image_header = Gtk.Image()

        # Properties
        image_header.set_from_icon_name(self.icon, Gtk.IconSize.LARGE_TOOLBAR)

        # ------------------------------------
        #   Integrate widgets
        # ------------------------------------

        self.set_titlebar(self.headerbar)

        if not remove_icon:
            self.headerbar.pack_start(image_header)


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


    def set_help(self, parent, data):
        """ Set an help dialog

        Parameters
        ----------
        text : str
            Help string
        """

        image = Gtk.Image()
        self.button_help = Gtk.Button()

        # Properties
        image.set_from_icon_name(Icons.Symbolic.Help, Gtk.IconSize.MENU)

        self.button_help.set_image(image)

        # ------------------------------------
        #   Generate help text
        # ------------------------------------

        text = list()

        # Get help data from specified order
        for item in data["order"]:

            # Dictionnary value
            if type(data[item]) is dict:
                text.append("<b>%s</b>" % item)

                for key, value in sorted(
                    data[item].items(), key=lambda key: key[0]):

                    text.append("\t<b>%s</b>\n\t\t%s" % (
                        key.replace('>', "&gt;").replace('<', "&lt;"), value))

            # List value
            elif type(data[item]) is list:
                text.append("\n\n".join(data[item]))

            # String value
            elif type(data[item]) is str:
                text.append(data[item])

        # ------------------------------------
        #   Connect signal
        # ------------------------------------

        self.button_help.connect(
            "clicked", self.show_help, parent, '\n\n'.join(text))

        # ------------------------------------
        #   Insert help into headerbar
        # ------------------------------------

        self.headerbar.pack_end(self.button_help)


    def show_help(self, widget, parent, text):
        """ Launch help dialog

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        text : str
            Help message
        """

        dialog = DialogHelp(parent, _("Help"), text, Icons.Help)
        dialog.set_size(640, 480)

        dialog.run()
        dialog.destroy()


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

        self.dialog_box.set_spacing(0)

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

        self.dialog_box.pack_start(text, False, False, 0)


    def __start_interface(self):
        """ Load data and start interface
        """

        self.show_all()


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
        """ Return the ImageMenuItem Gtk.Image object

        Returns
        -------
        Gtk.Image
            the current image using in ImageMenuItem
        """

        return self.__menu_item_image


    def set_image_from_pixbuf(self, pixbuf):
        """ The new Pixbuf to set in icon image

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
        """ The new Pixbuf to set in icon image

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
        """ Return the ImageMenuItem accelerator Gtk.Label object

        Returns
        -------
        str
            Menu label string
        """

        return self.__menu_item_label.get_label()


    def set_label(self, label):
        """ The new label to set in label

        Parameters
        ----------
        label : str
            the label string
        """

        if type(label) is not str:
            raise TypeError(
                "Cannot use %s as label, expected str" % str(
                type(label)))

        self.__menu_item_label.set_label(label)


    def get_accelerator(self):
        """ Return the ImageMenuItem accelerator Gtk.Label object

        Returns
        -------
        str
            Accelerator label string
        """

        return self.__menu_item_label_accel.get_label()


    def set_accelerator(self, max_width, key, mod):
        """ The new accelerator to set

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
