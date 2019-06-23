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
from gem.ui.widgets.window import CommonWindow

# GObject
try:
    from gi import require_version

    require_version("Gtk", "3.0")

    from gi.repository import Gtk
    from gi.repository import Pango

except ImportError as error:
    from sys import exit

    exit("Cannot found python3-gobject module: %s" % str(error))

# Translation
from gettext import gettext as _


# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class MessageDialog(CommonWindow):

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

        # Start interface
        self.__start_interface()

    def __init_widgets(self):
        """ Initialize interface widgets
        """

        self.set_size(480, -1)

        self.set_spacing(6)

        self.set_resizable(True)

        # ------------------------------------
        #   Message
        # ------------------------------------

        text = Gtk.Label()

        # Properties
        text.set_line_wrap(True)
        text.set_use_markup(True)
        text.set_markup(self.message)
        text.set_line_wrap_mode(Pango.WrapMode.WORD)

        if(self.center):
            text.set_justify(Gtk.Justification.CENTER)

        else:
            text.set_justify(Gtk.Justification.FILL)

        # ------------------------------------
        #   Integrate widgets
        # ------------------------------------

        self.pack_start(text, True, True)

    def __start_interface(self):
        """ Load data and start interface
        """

        self.add_button(_("Close"), Gtk.ResponseType.CLOSE, Gtk.Align.END)
