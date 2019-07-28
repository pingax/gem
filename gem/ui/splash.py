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
from gem.engine.api import GEM
from gem.engine.utils import get_data

from gem.ui.data import Metadata
from gem.ui.widgets.widgets import IconsGenerator

# GObject
try:
    from gi import require_version

    require_version("Gtk", "3.0")

    from gi.repository import Gtk
    from gi.repository import Gdk
    from gi.repository import GLib
    from gi.repository import Pango

except ImportError as error:
    from sys import exit

    exit("Cannot found python3-gobject module: %s" % str(error))

# System
from time import sleep

# Translation
from gettext import gettext as _


# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class Splash(Gtk.Window):

    def __init__(self, api):
        """ Constructor

        Parameters
        ----------
        api : gem.engine.api.GEM
            GEM API instance

        Raises
        ------
        TypeError
            if api type is not gem.engine.api.GEM
            if metadata type is not gem.engine.lib.configuration.Configuration
        """

        if not type(api) is GEM:
            raise TypeError("Wrong type for api, expected gem.engine.api.GEM")

        Gtk.Window.__init__(self)

        # ------------------------------------
        #   Initialize variables
        # ------------------------------------

        # Set rows number for progressbar
        self.length = int()

        self.main_loop = None

        # ------------------------------------
        #   Initialize API
        # ------------------------------------

        # GEM API
        self.api = api

        # Quick access to API logger
        self.logger = api.logger

        # ------------------------------------
        #   Initialize icons
        # ------------------------------------

        self.icons = IconsGenerator()

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
        """ Load widgets into main interface
        """

        # ------------------------------------
        #   Main window
        # ------------------------------------

        self.set_title(Metadata.NAME)

        self.set_modal(True)
        self.set_can_focus(True)
        self.set_resizable(False)
        self.set_keep_above(True)
        self.set_skip_taskbar_hint(True)
        self.set_type_hint(Gdk.WindowTypeHint.SPLASHSCREEN)

        self.set_position(Gtk.WindowPosition.CENTER)

        # ------------------------------------
        #   Grid
        # ------------------------------------

        self.grid = Gtk.Box()

        # Properties
        self.grid.set_spacing(4)
        self.grid.set_border_width(16)
        self.grid.set_homogeneous(False)
        self.grid.set_orientation(Gtk.Orientation.VERTICAL)

        # ------------------------------------
        #   Logo
        # ------------------------------------

        self.label_splash = Gtk.Label()
        self.image_splash = Gtk.Image()

        # Properties
        self.label_splash.set_line_wrap(True)
        self.label_splash.set_use_markup(True)
        self.label_splash.set_line_wrap_mode(Pango.WrapMode.WORD)
        self.label_splash.set_markup(
            "<span weight='bold' size='x-large'>%s - %s</span>\n<i>%s</i>" % (
                Metadata.NAME,
                Metadata.VERSION,
                Metadata.CODE_NAME))

        self.image_splash.set_from_file(
            str(get_data("data", "desktop", "gem.svg")))
        self.image_splash.set_pixel_size(256)

        # ------------------------------------
        #   Progressbar
        # ------------------------------------

        self.label_progress = Gtk.Label()

        self.progressbar = Gtk.ProgressBar()

        # Properties
        self.label_progress.set_text(_("Migrating entries from old database"))
        self.label_progress.set_line_wrap_mode(Pango.WrapMode.WORD)
        self.label_progress.set_line_wrap(True)

        self.progressbar.set_show_text(True)

    def __init_packing(self):
        """ Initialize widgets packing in main window
        """

        self.grid.pack_start(self.image_splash, True, True, 0)
        self.grid.pack_start(self.label_splash, False, False, 8)
        self.grid.pack_start(self.label_progress, False, False, 8)
        self.grid.pack_start(self.progressbar, False, False, 0)

        self.add(self.grid)

    def __start_interface(self):
        """ Load data and start interface
        """

        self.set_auto_startup_notification(False)

        self.show_all()

        self.label_progress.hide()
        self.progressbar.hide()

        self.refresh()

        # ------------------------------------
        #   Check migration
        # ------------------------------------

        GLib.idle_add(self.api.check_database, self)

        # ------------------------------------
        #   Main loop
        # ------------------------------------

        self.main_loop = GLib.MainLoop()
        self.main_loop.run()

    def close(self):
        """ Stop interface
        """

        self.set_auto_startup_notification(True)

        # Sleep to avoid ultra quick splash
        sleep(0.42)

        # Rare case where the mainloop is not init when close() is running
        if self.main_loop is not None:
            self.main_loop.quit()

        self.destroy()

    def init(self, length):
        """ Initialize progressbar

        Parameters
        ----------
        length : int
            Progression max iterations number
        """

        self.length = length

        self.label_progress.show()
        self.progressbar.show()

    def update(self, index):
        """ Update progress in progressbar widgets

        Parameters
        ----------
        index : int
            Current progession index step
        """

        self.refresh()

        if index <= self.length:
            self.progressbar.set_text("%d / %d" % (index, self.length))
            self.progressbar.set_fraction(float(index) / (self.length))

            self.refresh()

    def refresh(self):
        """ Refresh all pendings event in main interface
        """

        while Gtk.events_pending():
            Gtk.main_iteration()
