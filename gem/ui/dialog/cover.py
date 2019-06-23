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
from gem.ui.utils import replace_for_markup
from gem.ui.widgets.window import CommonWindow

# GObject
try:
    from gi import require_version

    require_version("Gtk", "3.0")

    from gi.repository import Gtk
    from gi.repository import GdkPixbuf
    from gi.repository import Pango

except ImportError as error:
    from sys import exit

    exit("Cannot found python3-gobject module: %s" % str(error))

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
            self, parent, _("Game cover"), Icons.Symbolic.IMAGE, classic_theme)

        # ------------------------------------
        #   Initialize variables
        # ------------------------------------

        self.game = game

        self.mimetypes = [
            "image/bmp",
            "image/jpeg",
            "image/png",
            "image/svg+xml",
            "image/svg+xml-compressed",
        ]

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

        self.set_spacing(6)

        self.set_resizable(True)

        # ------------------------------------
        #   Grid
        # ------------------------------------

        self.grid_content = Gtk.Box()

        # Properties
        self.grid_content.set_spacing(6)

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
        self.label_image_selector.set_markup("<b>%s</b>" % _("Thumbnail file"))
        self.label_image_selector.set_margin_top(12)
        self.label_image_selector.set_hexpand(True)
        self.label_image_selector.set_use_markup(True)
        self.label_image_selector.set_single_line_mode(True)
        self.label_image_selector.set_halign(Gtk.Align.CENTER)
        self.label_image_selector.set_ellipsize(Pango.EllipsizeMode.END)

        for pattern in self.mimetypes:
            self.filter_image_selector.add_mime_type(pattern)

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
            Icons.Symbolic.CLEAR, Gtk.IconSize.BUTTON)

        # ------------------------------------
        #   Image preview
        # ------------------------------------

        self.label_preview = Gtk.Label()

        self.scroll_preview = Gtk.ScrolledWindow()
        self.view_preview = Gtk.Viewport()

        self.image_preview = Gtk.Image()

        # Properties
        self.label_preview.set_markup("<b>%s</b>" % _("Preview"))
        self.label_preview.set_margin_top(12)
        self.label_preview.set_hexpand(True)
        self.label_preview.set_use_markup(True)
        self.label_preview.set_single_line_mode(True)
        self.label_preview.set_halign(Gtk.Align.CENTER)
        self.label_preview.set_ellipsize(Pango.EllipsizeMode.END)

        self.scroll_preview.set_shadow_type(Gtk.ShadowType.OUT)

        self.image_preview.set_halign(Gtk.Align.CENTER)
        self.image_preview.set_valign(Gtk.Align.CENTER)
        self.image_preview.set_hexpand(True)
        self.image_preview.set_vexpand(True)

        # ------------------------------------
        #   Integrate widgets
        # ------------------------------------

        self.button_reset.add(self.image_reset)

        self.grid_content.pack_start(self.file_image_selector, True, True, 0)
        self.grid_content.pack_start(self.button_reset, False, False, 0)

        self.view_preview.add(self.image_preview)
        self.scroll_preview.add(self.view_preview)

        self.pack_start(self.label_title, False, False)
        self.pack_start(self.label_image_selector, False, False)
        self.pack_start(self.grid_content, False, False)
        self.pack_start(self.label_preview, False, False)
        self.pack_start(self.scroll_preview)

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

        if self.game.cover is not None and self.game.cover.exists():
            self.file_image_selector.set_filename(str(self.game.cover))

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
            self.image_preview.set_from_pixbuf(
                GdkPixbuf.Pixbuf.new_from_file_at_scale(path, 400, 236, True))

        except Exception:
            self.__on_reset_cover()

    def __on_reset_cover(self, *args):
        """ Reset cover filechooser
        """

        self.file_image_selector.unselect_all()

        self.image_preview.set_from_icon_name(Icons.MISSING, Gtk.IconSize.DND)
