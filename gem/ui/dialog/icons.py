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
from gem.ui.utils import *

from gem.ui.widgets.window import CommonWindow

# Translation
from gettext import gettext as _

# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class IconsDialog(CommonWindow):

    def __init__(self, parent, title, path, folder):
        """ Constructor

        Parameters
        ----------
        parent : Gtk.Window
            Parent object
        title : str
            Window title
        path : str
            Selected icon path
        folder : str
            Icons folder
        """

        CommonWindow.__init__(self, parent, title, Icons.Symbolic.Image,
            parent.use_classic_theme)

        # ------------------------------------
        #   Variables
        # ------------------------------------

        self.path = path
        self.new_path = None

        self.folder = folder

        if parent is None:
            self.api = None

            self.empty = Pixbuf(Colorspace.RGB, True, 8, 24, 24)
            self.empty.fill(0x00000000)

        else:
            self.api = parent.api

            self.empty = parent.empty

        # ------------------------------------
        #   Initialization
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

        self.set_size(800, 600)

        self.set_resizable(True)

        self.set_spacing(6)
        self.set_border_width(6)

        # ------------------------------------
        #   Grid
        # ------------------------------------

        self.stack = Gtk.Stack()
        self.stack_switcher = Gtk.StackSwitcher()

        # Properties
        self.stack.set_transition_type(Gtk.StackTransitionType.NONE)

        self.stack_switcher.set_stack(self.stack)
        self.stack_switcher.set_halign(Gtk.Align.CENTER)

        # ------------------------------------
        #   File patterns
        # ------------------------------------

        self.__file_patterns = Gtk.FileFilter.new()

        # ------------------------------------
        #   Custom
        # ------------------------------------

        self.frame_icons = Gtk.Frame()

        self.file_icons = Gtk.FileChooserWidget.new(Gtk.FileChooserAction.OPEN)

        # Properties
        self.frame_icons.set_shadow_type(Gtk.ShadowType.OUT)

        self.file_icons.set_hexpand(True)
        self.file_icons.set_vexpand(True)
        self.file_icons.set_filter(self.__file_patterns)
        self.file_icons.set_current_folder(expanduser('~'))

        # ------------------------------------
        #   Icons
        # ------------------------------------

        self.view_icons = Gtk.IconView()
        self.model_icons = Gtk.ListStore(Pixbuf, str)

        self.scroll_icons = Gtk.ScrolledWindow()

        # Properties
        self.view_icons.set_model(self.model_icons)
        self.view_icons.set_pixbuf_column(0)
        self.view_icons.set_tooltip_column(1)
        # self.view_icons.set_item_width(96)
        self.view_icons.set_selection_mode(Gtk.SelectionMode.SINGLE)

        self.model_icons.set_sort_column_id(1, Gtk.SortType.ASCENDING)

        self.scroll_icons.set_hexpand(True)
        self.scroll_icons.set_vexpand(True)
        self.scroll_icons.set_shadow_type(Gtk.ShadowType.OUT)
        self.scroll_icons.set_policy(
            Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        # ------------------------------------
        #   Add widgets into interface
        # ------------------------------------

        self.stack.add_titled(self.scroll_icons, "library", _("Library"))

        self.scroll_icons.add(self.view_icons)

        self.stack.add_titled(self.frame_icons, "file", _("File"))

        self.frame_icons.add(self.file_icons)

        self.pack_start(self.stack_switcher, False, False)
        self.pack_start(self.stack, True, True)


    def __init_signals(self):
        """ Initialize widgets signals
        """

        self.file_icons.connect("file-activated", self.__on_selected_icon)

        self.view_icons.connect("item-activated", self.__on_selected_icon)


    def __start_interface(self):
        """ Load data and start interface
        """

        self.add_button(_("Close"), Gtk.ResponseType.CLOSE)
        self.add_button(_("Accept"), Gtk.ResponseType.APPLY, Gtk.Align.END)

        self.load_interface()

        response = self.run()

        if response == Gtk.ResponseType.APPLY:
            self.save_interface()


    def __on_selected_icon(self, widget, path=None):
        """ Select an icon in treeview

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        path : Gtk.TreePath, optional
            Path to be activated (Default: None)
        """

        self.emit_response(None, Gtk.ResponseType.APPLY)


    def load_interface(self):
        """ Insert data into interface's widgets
        """

        self.icons_data = dict()

        # Set authorized pattern for file selector
        for pattern in [ "png", "jpg", "jpeg", "svg" ]:
            self.__file_patterns.add_pattern("*.%s" % pattern)

        # Fill icons view
        if self.api is not None:

            for icon in glob(self.api.get_local("icons", self.folder, "*.png")):
                name = splitext(basename(icon))[0]

                if not exists(expanduser(icon)):
                    icon = self.api.get_local(
                        "icons", self.folder, "%s.%s" % (icon, Icons.Ext))

                self.icons_data[name] = self.model_icons.append([
                    icon_from_data(icon, self.empty, 72, 72), name ])

            # Set filechooser or icons view selected item
            if self.path is not None:

                # Check if current path is a gem icons
                data = self.api.get_local(
                    "icons", self.folder, self.path + ".png")

                if data is not None and exists(data):
                    self.view_icons.select_path(
                        self.model_icons.get_path(self.icons_data[self.path]))

                else:
                    self.frame_icons.show()
                    self.stack.set_visible_child(self.frame_icons)

                    self.file_icons.set_filename(self.path)


    def save_interface(self):
        """ Return all the data from interface
        """

        if self.stack.get_visible_child_name() == "library":
            selection = self.view_icons.get_selected_items()[0]

            path = self.model_icons.get_value(
                self.model_icons.get_iter(selection), 1)

        else:
            path = self.file_icons.get_filename()

        if not path == self.path:
            self.new_path = path
