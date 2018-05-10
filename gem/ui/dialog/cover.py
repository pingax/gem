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

class CoverDialog(CommonWindow):

    def __init__(self, parent, game):
        """ Constructor

        Parameters
        ----------
        parent : Gtk.Window
            Parent object
        game : gem.api.Game
            Game object instance
        """

        classic_theme = False
        if parent is not None:
            classic_theme = parent.use_classic_theme

        CommonWindow.__init__(
            self, parent, _("Game cover"), Icons.Symbolic.Image, classic_theme)

        # ------------------------------------
        #   Initialize variables
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

        self.set_size(640, 480)

        self.set_spacing(0)

        # ------------------------------------
        #   Grid
        # ------------------------------------

        self.grid_content = Gtk.Grid()

        # Properties
        self.grid_content.set_column_spacing(12)
        self.grid_content.set_row_spacing(12)

        # ------------------------------------
        #   Image selector
        # ------------------------------------

        self.label_image_selector = Gtk.Label()

        self.filter_image_selector = Gtk.FileFilter.new()

        self.dialog_image_selector = Gtk.FileChooserDialog(
            use_header_bar=not self.use_classic_theme)

        self.file_image_selector = Gtk.FileChooserButton.new_with_dialog(
            self.dialog_image_selector)

        self.image_reset = Gtk.Image()
        self.button_reset = Gtk.Button()

        # Properties
        self.label_image_selector.set_halign(Gtk.Align.END)
        self.label_image_selector.set_justify(Gtk.Justification.RIGHT)
        self.label_image_selector.get_style_context().add_class("dim-label")
        self.label_image_selector.set_text(_("Cover image"))

        for pattern in [ "png", "jpg", "jpeg", "svg" ]:
            self.filter_image_selector.add_pattern("*.%s" % pattern)

        self.dialog_image_selector.add_button(
            _("Cancel"), Gtk.ResponseType.CANCEL)
        self.dialog_image_selector.add_button(
            _("Accept"), Gtk.ResponseType.ACCEPT)
        self.dialog_image_selector.set_filter(self.filter_image_selector)
        self.dialog_image_selector.set_action(Gtk.FileChooserAction.OPEN)
        self.dialog_image_selector.set_create_folders(False)
        self.dialog_image_selector.set_local_only(True)

        self.file_image_selector.set_hexpand(True)

        self.image_reset.set_from_icon_name(
            Icons.Symbolic.Clear, Gtk.IconSize.BUTTON)

        # ------------------------------------
        #   Image preview
        # ------------------------------------

        self.image_preview = Gtk.Image()

        # Properties
        self.image_preview.set_halign(Gtk.Align.CENTER)
        self.image_preview.set_valign(Gtk.Align.CENTER)
        self.image_preview.set_hexpand(True)
        self.image_preview.set_vexpand(True)

        # ------------------------------------
        #   Integrate widgets
        # ------------------------------------

        self.button_reset.add(self.image_reset)

        self.grid_content.attach(self.label_image_selector, 0, 0, 1, 1)
        self.grid_content.attach(self.file_image_selector, 1, 0, 1, 1)
        self.grid_content.attach(self.button_reset, 2, 0, 1, 1)
        self.grid_content.attach(self.image_preview, 0, 1, 3, 1)

        self.pack_start(self.grid_content)


    def __init_signals(self):
        """ Initialize widgets signals
        """

        self.file_image_selector.connect("file-set", self.__update_preview)

        self.button_reset.connect("clicked", self.__on_reset_cover)


    def __start_interface(self):
        """ Load data and start interface
        """

        self.add_button(_("Cancel"), Gtk.ResponseType.CANCEL)
        self.add_button(_("Accept"), Gtk.ResponseType.APPLY, Gtk.Align.END)

        if self.game.cover is not None and exists(self.game.cover):
            self.file_image_selector.set_filename(self.game.cover)

        self.__update_preview()


    def __update_preview(self, *args):
        """ Update image preview
        """

        self.__on_set_preview(self.file_image_selector.get_filename())


    def __on_set_preview(self, path):
        """ Set a new preview from selector filepath

        Parameters
        ----------
        path : str
            Image file path
        """

        try:
            pixbuf = Pixbuf.new_from_file(path)

            if pixbuf.get_width() >= pixbuf.get_height():
                self.image_preview.set_from_pixbuf(
                    Pixbuf.new_from_file_at_scale(path, 400, -1, True))

            else:
                self.image_preview.set_from_pixbuf(
                    Pixbuf.new_from_file_at_scale(path, -1, 236, True))

        except:
            self.__on_reset_cover()


    def __on_reset_cover(self, *args):
        """ Reset cover filechooser
        """

        self.file_image_selector.unselect_all()

        self.image_preview.set_from_icon_name(
            Icons.Missing, Gtk.IconSize.DND)
