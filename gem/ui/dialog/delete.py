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
from gem.engine.utils import *

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

        CommonWindow.__init__(self,
            parent, _("Remove a game"), Icons.Symbolic.Delete, classic_theme)

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
            "<span weight='bold' size='large'>%s</span>" % \
            replace_for_markup(self.game.name))
        self.label_title.set_use_markup(True)
        self.label_title.set_halign(Gtk.Align.CENTER)
        self.label_title.set_ellipsize(Pango.EllipsizeMode.END)

        # ------------------------------------
        #   Description
        # ------------------------------------

        self.label_description = Gtk.Label()

        # Properties
        self.label_description.set_text(_("The following game going to be "
            "removed from your harddrive. This action is irreversible !"))
        self.label_description.set_line_wrap(True)
        self.label_description.set_max_width_chars(8)
        self.label_description.set_single_line_mode(False)
        self.label_description.set_justify(Gtk.Justification.FILL)
        self.label_description.set_line_wrap_mode(Pango.WrapMode.WORD)

        # ------------------------------------
        #   Options
        # ------------------------------------

        self.label_data = Gtk.Label()

        self.label_database = Gtk.Label()
        self.check_database = Gtk.Switch()

        self.label_desktop = Gtk.Label()
        self.check_desktop = Gtk.Switch()

        self.label_save_state = Gtk.Label()
        self.check_save_state = Gtk.Switch()

        self.label_screenshots = Gtk.Label()
        self.check_screenshots = Gtk.Switch()

        # Properties
        self.label_data.set_markup(
            "<b>%s</b>" % _("Optional data to remove"))
        self.label_data.set_margin_top(12)
        self.label_data.set_hexpand(True)
        self.label_data.set_use_markup(True)
        self.label_data.set_single_line_mode(True)
        self.label_data.set_halign(Gtk.Align.CENTER)
        self.label_data.set_ellipsize(Pango.EllipsizeMode.END)

        self.label_database.set_margin_top(12)
        self.label_database.set_halign(Gtk.Align.START)
        self.label_database.set_label(_("Game's data from database"))
        self.label_database.get_style_context().add_class("dim-label")
        self.check_database.set_margin_top(12)

        self.label_desktop.set_margin_top(12)
        self.label_desktop.set_halign(Gtk.Align.START)
        self.label_desktop.set_label(_("Desktop file"))
        self.label_desktop.get_style_context().add_class("dim-label")
        self.check_desktop.set_margin_top(12)

        self.label_save_state.set_margin_top(12)
        self.label_save_state.set_halign(Gtk.Align.START)
        self.label_save_state.set_label(_("Save files"))
        self.label_save_state.get_style_context().add_class("dim-label")
        self.check_save_state.set_margin_top(12)

        self.label_screenshots.set_halign(Gtk.Align.START)
        self.label_screenshots.set_label(_("Game screenshots"))
        self.label_screenshots.get_style_context().add_class("dim-label")

        # ------------------------------------
        #   Integrate widgets
        # ------------------------------------

        self.grid_switch.attach(self.check_database, 0, 1, 1, 1)
        self.grid_switch.attach(self.label_database, 1, 1, 1, 1)
        self.grid_switch.attach(self.check_desktop, 0, 2, 1, 1)
        self.grid_switch.attach(self.label_desktop, 1, 2, 1, 1)
        self.grid_switch.attach(self.check_save_state, 0, 3, 1, 1)
        self.grid_switch.attach(self.label_save_state, 1, 3, 1, 1)
        self.grid_switch.attach(self.check_screenshots, 0, 4, 1, 1)
        self.grid_switch.attach(self.label_screenshots, 1, 4, 1, 1)

        self.pack_start(self.label_title, False, False)
        self.pack_start(self.label_description, False, False)
        self.pack_start(self.label_data, False, False)
        self.pack_start(self.grid_switch)


    def __start_interface(self):
        """ Load data and start interface
        """

        self.add_button(_("No"), Gtk.ResponseType.NO)
        self.add_button(_("Yes"), Gtk.ResponseType.YES, Gtk.Align.END)

        self.check_database.set_active(True)
        self.check_desktop.set_active(True)
