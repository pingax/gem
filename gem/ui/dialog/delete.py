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

class DeleteDialog(CommonWindow):

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
