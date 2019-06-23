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
from gem.ui.data import Icons
from gem.ui.utils import on_entry_clear
from gem.ui.utils import replace_for_markup
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

class RenameDialog(CommonWindow):

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

        CommonWindow.__init__(self,
                              parent,
                              _("Rename a game"),
                              Icons.Symbolic.EDITOR,
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
        #   Title
        # ------------------------------------

        self.label_title = Gtk.Label()

        # Properties
        self.label_title.set_markup(
            "<span weight='bold' size='large'>%s</span>" % (
                replace_for_markup(self.game.name)))
        self.label_title.set_use_markup(True)
        self.label_title.set_halign(Gtk.Align.CENTER)
        self.label_title.set_ellipsize(Pango.EllipsizeMode.END)

        # ------------------------------------
        #   Options
        # ------------------------------------

        self.entry_name = Gtk.Entry()

        # Properties
        self.entry_name.set_placeholder_text("%s…" % _("New name"))
        self.entry_name.set_icon_from_icon_name(
            Gtk.EntryIconPosition.SECONDARY, Icons.Symbolic.CLEAR)

        # ------------------------------------
        #   Integrate widgets
        # ------------------------------------

        self.pack_start(self.label_title, False, False)
        self.pack_start(self.entry_name, False, False)

    def __init_signals(self):
        """ Initialize widgets signals
        """

        self.entry_name.connect("icon-press", on_entry_clear)

        self.entry_name.connect("changed", self.check_name)

    def __start_interface(self):
        """ Load data and start interface
        """

        self.add_button(_("Cancel"), Gtk.ResponseType.CANCEL)
        self.add_button(_("Apply"), Gtk.ResponseType.APPLY, Gtk.Align.END)

        self.set_default_response(Gtk.ResponseType.APPLY)

        if len(self.game.name) > 0:
            self.entry_name.set_text(self.game.name)

        else:
            self.set_response_sensitive(Gtk.ResponseType.APPLY, False)

    def get_name(self):
        """ Retrieve the new name from entry widget

        Returns
        -------
        str
            New name
        """

        return self.entry_name.get_text()

    def check_name(self, *args):
        """ Check the name value to update button sensitivity
        """

        self.set_response_sensitive(
            Gtk.ResponseType.APPLY,
            len(self.entry_name.get_text().strip()) > 0)
