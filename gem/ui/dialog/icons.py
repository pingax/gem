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

# Filesystem
from pathlib import Path

# GEM
from gem.ui.data import Icons
from gem.ui.data import Folders
from gem.ui.utils import magic_from_file
from gem.ui.widgets.window import CommonWindow

# GObject
try:
    from gi import require_version

    require_version("Gtk", "3.0")

    from gi.repository import Gtk
    from gi.repository import GLib
    from gi.repository import GdkPixbuf

except ImportError as error:
    from sys import exit

    exit("Cannot found python3-gobject module: %s" % str(error))

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

        CommonWindow.__init__(self,
                              parent,
                              title,
                              Icons.Symbolic.IMAGE,
                              parent.use_classic_theme)

        # ------------------------------------
        #   Variables
        # ------------------------------------

        self.api = parent.api

        self.icons = parent.icons

        # Current file path
        self.path = path
        # The new file path
        self.new_path = None

        # File selector management
        self.__file_path = None
        self.__file_active = False

        # Collection type
        self.folder = folder

        # Collection thread loading instance
        self.thread = int()

        # ------------------------------------
        #   Initialization
        # ------------------------------------

        # Init widgets
        self.__init_widgets()

        # Init packing
        self.__init_packing()

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
        self.file_icons.set_current_folder(str(Path.home()))

        # ------------------------------------
        #   Icons
        # ------------------------------------

        self.view_icons = Gtk.IconView()
        self.model_icons = Gtk.ListStore(GdkPixbuf.Pixbuf, str)

        self.scroll_icons = Gtk.ScrolledWindow()

        # Properties
        self.view_icons.set_model(self.model_icons)
        self.view_icons.set_pixbuf_column(0)
        self.view_icons.set_tooltip_column(1)
        self.view_icons.set_selection_mode(Gtk.SelectionMode.SINGLE)

        self.model_icons.set_sort_column_id(1, Gtk.SortType.ASCENDING)

        self.scroll_icons.set_hexpand(True)
        self.scroll_icons.set_vexpand(True)
        self.scroll_icons.set_shadow_type(Gtk.ShadowType.OUT)
        self.scroll_icons.set_policy(
            Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

    def __init_packing(self):
        """ Initialize widgets packing in main window
        """

        if self.folder == "consoles":
            self.stack.add_titled(self.scroll_icons, "library", _("Library"))

            self.scroll_icons.add(self.view_icons)

            self.stack.add_titled(self.frame_icons, "file", _("File"))

            self.frame_icons.add(self.file_icons)

            self.pack_start(self.stack_switcher, False, False)
            self.pack_start(self.stack, True, True)

        else:
            self.frame_icons.add(self.file_icons)

            self.pack_start(self.frame_icons, True, True)

    def __init_signals(self):
        """ Initialize widgets signals
        """

        # Only activate the last child cause there are RadioButton
        children = self.stack_switcher.get_children()
        if len(children) > 0:
            children[-1].connect("clicked", self.__on_switch_stack_view)

        self.file_icons.connect("file-activated", self.__on_selected_icon)

        self.view_icons.connect("item-activated", self.__on_selected_icon)

    def __start_interface(self):
        """ Load data and start interface
        """

        self.add_button(_("Close"), Gtk.ResponseType.CLOSE)
        self.add_button(_("Accept"), Gtk.ResponseType.APPLY, Gtk.Align.END)

        self.load_interface()

        response = self.run()

        # Remove icons listing thread
        if not self.thread == 0:
            GLib.source_remove(self.thread)

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

    def __on_switch_stack_view(self, widget):
        """ Check file selector to avoid to lost file selection

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        # The focus is not in the file selector anymore
        if not widget.get_active():
            self.__file_active = False

            self.__file_path = self.file_icons.get_filename()

        elif not self.__file_active and self.__file_path is not None:
            self.__file_active = True

            self.file_icons.set_filename(self.__file_path)

    def load_interface(self):
        """ Insert data into interface's widgets
        """

        # Set authorized mime types for file selector
        self.__file_patterns.add_mime_type("image/*")

        # Fill icons view
        if self.api is not None:

            # Load icons collection
            if self.folder == "consoles":
                self.icons_data = dict()

                if not self.thread == 0:
                    GLib.source_remove(self.thread)

                self.thread = GLib.idle_add(self.append_icons(64).__next__)

            # Check the choosen path
            if self.path is not None and self.path.exists():

                if self.folder == "consoles":
                    self.frame_icons.show()
                    self.stack.set_visible_child(self.frame_icons)

                self.file_icons.set_filename(str(self.path))

                self.__file_path = self.path
                self.__file_active = True

    def save_interface(self):
        """ Return all the data from interface
        """

        # Retrieve path from file selector
        self.new_path = self.file_icons.get_filename()

        # Check icons collection
        if self.folder == "consoles":

            # Retrieve icon from icons collection
            if self.stack.get_visible_child_name() == "library":
                self.new_path = None

                items = self.view_icons.get_selected_items()

                # An icon is selected
                if len(items) > 0:
                    self.new_path = self.model_icons.get_value(
                        self.model_icons.get_iter(items[0]), 1)

    def append_icons(self, size):
        """ Append icons in icons view with a specific size

        Parameters
        ----------
        size : int
            Specified icon size
        """

        yield True

        # Retrieve files from icons collection
        collection_path = Folders.LOCAL.joinpath("icons")

        for path in sorted(collection_path.glob("*.png")):

            # Retrieve an empty icon
            icon = self.icons.blank(size)

            # Generate an icon for found file
            if path.exists() and path.is_file():

                # Check the file mime-type to avoid non-image file
                if magic_from_file(path, mime=True).startswith("image/"):
                    icon = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                        str(path), size, size, True)

            self.icons_data[path.stem] = \
                self.model_icons.append([icon, path.stem])

            # Current icon match the choosen one
            if str(self.path) == path.stem:

                # Only select current icon if no selection is available
                if len(self.view_icons.get_selected_items()) == 0:
                    self.view_icons.select_path(
                        self.model_icons.get_path(self.icons_data[path.stem]))

            yield True

        # Remove thread id from memory
        self.thread = int()

        yield False
