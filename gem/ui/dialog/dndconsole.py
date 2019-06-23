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
from gem.ui.widgets.window import CommonWindow
from gem.ui.widgets.widgets import ListBoxItem
from gem.ui.widgets.widgets import ScrolledListBox

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

class DNDConsoleDialog(CommonWindow):

    def __init__(self, parent, filepaths):
        """ Constructor

        Parameters
        ----------
        parent : Gtk.Window
            Parent object
        filepaths : dict
            Filepaths storage with corresponding consoles
        """

        classic_theme = False
        if parent is not None:
            classic_theme = parent.use_classic_theme

        CommonWindow.__init__(self,
                              parent,
                              _("Drag & Drop"),
                              Icons.Symbolic.GAMING,
                              classic_theme)

        # ----------------------------------------
        #   Initialize variables
        # ----------------------------------------

        self.api = parent.api

        self.filepaths = filepaths

        self.__notebook_pages = dict()

        # ----------------------------------------
        #   Prepare interface
        # ----------------------------------------

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

        self.set_spacing(0)

        self.set_resizable(True)

        # ----------------------------------------
        #   Grid
        # ----------------------------------------

        self.grid.set_spacing(6)

        # ----------------------------------------
        #   Games
        # ----------------------------------------

        self.label_games = Gtk.Label()

        self.notebook_games = Gtk.Notebook()

        self.frame_games = ScrolledListBox()
        self.frame_error = ScrolledListBox()

        # Properties
        self.label_games.set_markup(
            "<b>%s</b>" % _("Drop games"))
        self.label_games.set_hexpand(True)
        self.label_games.set_use_markup(True)
        self.label_games.set_single_line_mode(True)
        self.label_games.set_halign(Gtk.Align.CENTER)
        self.label_games.set_ellipsize(Pango.EllipsizeMode.END)

        # ----------------------------------------
        #   Options
        # ----------------------------------------

        self.label_options = Gtk.Label()

        self.frame_options = Gtk.Frame()
        self.scroll_options = Gtk.ScrolledWindow()
        self.listbox_options = Gtk.ListBox()

        self.widget_copy = ListBoxItem()
        self.switch_copy = Gtk.Switch()

        self.widget_replace = ListBoxItem()
        self.switch_replace = Gtk.Switch()

        self.widget_create = ListBoxItem()
        self.switch_create = Gtk.Switch()

        # Properties
        self.label_options.set_markup(
            "<b>%s</b>" % _("Available actions"))
        self.label_options.set_margin_top(12)
        self.label_options.set_hexpand(True)
        self.label_options.set_use_markup(True)
        self.label_options.set_single_line_mode(True)
        self.label_options.set_halign(Gtk.Align.CENTER)
        self.label_options.set_ellipsize(Pango.EllipsizeMode.END)

        self.scroll_options.set_propagate_natural_height(True)

        self.listbox_options.set_activate_on_single_click(True)
        self.listbox_options.set_selection_mode(Gtk.SelectionMode.NONE)

        self.widget_copy.set_widget(self.switch_copy)
        self.widget_copy.set_option_label(
            _("Copy files"))
        self.widget_copy.set_description_label(
            _("Make copy of dropped files instead of moving them"))

        self.widget_replace.set_widget(self.switch_replace)
        self.widget_replace.set_option_label(
            _("Replace files"))
        self.widget_replace.set_description_label(
            _("Replace existing files on disk"))

        self.widget_create.set_widget(self.switch_create)
        self.widget_create.set_option_label(
            _("Generate subdirectory"))
        self.widget_create.set_description_label(
            _("Create consoles games subdirectory if missing"))

        # ----------------------------------------
        #   Integrate widgets
        # ----------------------------------------

        self.listbox_options.add(self.widget_copy)
        self.listbox_options.add(self.widget_replace)
        self.listbox_options.add(self.widget_create)

        self.scroll_options.add(self.listbox_options)
        self.frame_options.add(self.scroll_options)

        self.grid.pack_start(self.label_games, False, False, 0)
        self.grid.pack_start(self.notebook_games, True, True, 0)
        self.grid.pack_start(self.label_options, False, False, 0)
        self.grid.pack_start(self.frame_options, False, False, 0)

    def __init_signals(self):
        """ Initialize widgets signals
        """

        self.frame_games.listbox.connect(
            "row-activated", self.on_activate_listboxrow)

        self.listbox_options.connect(
            "row-activated", self.on_activate_listboxrow)

    def __start_interface(self):
        """ Load data and start interface
        """

        self.add_button(_("Cancel"), Gtk.ResponseType.CLOSE)
        self.add_button(_("Accept"), Gtk.ResponseType.APPLY, Gtk.Align.END)

        self.set_response_sensitive(Gtk.ResponseType.APPLY, False)

        self.switch_copy.set_active(True)
        self.switch_create.set_active(True)

        # ----------------------------------------
        #   Retrieve data
        # ----------------------------------------

        self.__notebook_pages.clear()

        for path, consoles in sorted(self.filepaths.items()):
            row = DNDGameRow(self.parent, path, consoles)

            if len(consoles) == 0:
                self.frame_error.listbox.add(row)

            elif len(consoles) == 1:
                self.frame_games.listbox.add(row)

            else:
                extension = str()

                # Only retrieve extensions and not part of the name
                for subextension in path.suffixes:
                    if subextension not in path.stem:
                        extension += subextension.lower()

                # Generate a tab for the new extension
                if extension not in self.__notebook_pages.keys():
                    self.__notebook_pages[extension] = \
                        DNDSelector(self, consoles)

                self.__notebook_pages[extension].listbox_manual.add(row)

                row.set_console(self.__notebook_pages[extension].get_console())

        # ----------------------------------------
        #   Show notebook tabs
        # ----------------------------------------

        if len(self.frame_games.listbox) > 0:
            self.notebook_games.append_page(
                self.frame_games,
                Gtk.Image.new_from_icon_name(
                    Icons.Symbolic.OK, Gtk.IconSize.MENU))

            self.set_response_sensitive(Gtk.ResponseType.APPLY, True)

        for label, widget in self.__notebook_pages.items():
            self.notebook_games.append_page(widget, Gtk.Label.new(label))

            self.set_response_sensitive(Gtk.ResponseType.APPLY, True)

        if len(self.frame_error.listbox) > 0:
            self.notebook_games.append_page(
                self.frame_error,
                Gtk.Image.new_from_icon_name(
                    Icons.Symbolic.ERROR, Gtk.IconSize.MENU))

    def get_data(self):
        """ Retrieve validate dropped files

        Returns
        -------
        dict
            Validate files as dict structure
        """

        data = dict()

        for row in self.frame_games.listbox:
            data[row.path] = row.console

        for widget in self.__notebook_pages.values():
            for row in widget.listbox_manual:
                data[row.path] = row.console

        return data

    def get_options(self):
        """ Retrieve options values

        Returns
        -------
        dict
            Options values as dict structure
        """

        return {
            "copy": self.switch_copy.get_active(),
            "replace": self.switch_replace.get_active(),
            "create": self.switch_create.get_active()
        }


class DNDSelector(Gtk.Box):

    def __init__(self, parent, consoles):
        """ Constructor

        Parameters
        ----------
        parent : gem.ui.dialog.DNDConsoleDialog
            Parent instance
        consoles : list
            Consoles data list
        """

        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL)

        # ----------------------------------------
        #   Variables
        # ----------------------------------------

        self.dialog = parent

        self.consoles = consoles

        # ----------------------------------------
        #   Prepare interface
        # ----------------------------------------

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

        # ----------------------------------------
        #   Automatic selection
        # ----------------------------------------

        self.frame_automatic_description = ScrolledListBox()
        self.item_automatic_description = ListBoxItem.new(
            _("Automatic selection"))

        self.store_consoles = Gtk.ListStore(GdkPixbuf.Pixbuf, str, object)
        self.combo_consoles = Gtk.ComboBox()
        self.cell_consoles_icon = Gtk.CellRendererPixbuf()
        self.cell_consoles_text = Gtk.CellRendererText()

        # Properties
        self.item_automatic_description.set_widget(self.combo_consoles)
        self.item_automatic_description.set_description_label(
            _("Select this console for every rows"))

        self.combo_consoles.set_id_column(1)
        self.combo_consoles.set_hexpand(True)
        self.combo_consoles.set_halign(Gtk.Align.FILL)
        self.combo_consoles.set_model(self.store_consoles)
        self.combo_consoles.pack_start(self.cell_consoles_icon, False)
        self.combo_consoles.pack_start(self.cell_consoles_text, True)
        self.combo_consoles.add_attribute(self.cell_consoles_icon, "pixbuf", 0)
        self.combo_consoles.add_attribute(self.cell_consoles_text, "text", 1)

        # ----------------------------------------
        #   Manual selection
        # ----------------------------------------

        self.scroll_manual = Gtk.ScrolledWindow()
        self.listbox_manual = Gtk.ListBox()

        # Properties
        self.scroll_manual.set_propagate_natural_height(True)

        self.listbox_manual.set_activate_on_single_click(True)
        self.listbox_manual.set_selection_mode(Gtk.SelectionMode.NONE)

    def __init_packing(self):
        """ Initialize widgets packing in main window
        """

        self.frame_automatic_description.listbox.add(
            self.item_automatic_description)

        self.scroll_manual.add(self.listbox_manual)

        self.pack_start(self.frame_automatic_description, False, False, 0)
        self.pack_start(Gtk.Separator(), False, False, 0)
        self.pack_start(self.scroll_manual, True, True, 0)

    def __init_signals(self):
        """ Initialize widgets signals
        """

        self.frame_automatic_description.listbox.connect(
            "row-activated", self.dialog.on_activate_listboxrow)

        self.combo_consoles.connect(
            "changed", self.__on_select_console)

        self.listbox_manual.connect(
            "row-activated", self.dialog.on_activate_listboxrow)

    def __start_interface(self):
        """ Load data and start interface
        """

        for console in self.consoles:

            icon = self.dialog.parent.get_pixbuf_from_cache(
                "consoles", 24, console.id, console.icon)

            if icon is None:
                icon = self.dialog.parent.icons.blank(24)

            self.store_consoles.append([icon, console.name, console])

        self.combo_consoles.set_active(0)

    def __on_select_console(self, widget, *args):
        """ Change every consoles based on combobox selection

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        console = self.get_console()

        for row in self.listbox_manual:
            row.set_console(console)

    def get_console(self):
        """ Retrieve current selected console

        Returns
        -------
        gem.engine.console.Console
            Console instance
        """

        return self.store_consoles.get_value(
            self.combo_consoles.get_active_iter(), 2)


class DNDGameRow(ListBoxItem):

    def __init__(self, parent, path, consoles):
        """ Constructor

        Parameters
        ----------
        parent : Gtk.Window
            Parent object
        path : pathlib.Path
            Game filepath
        consoles : list
            Consoles instances list
        """

        ListBoxItem.__init__(self)

        # ----------------------------------------
        #   Initialize variables
        # ----------------------------------------

        self.parent = parent

        self.path = path
        self.consoles = consoles

        self.console = None

        # ----------------------------------------
        #   Prepare interface
        # ----------------------------------------

        # Init widgets
        self.__init_widgets()

        # Start interface
        self.__start_interface()

    def __init_widgets(self):
        """ Initialize interface widgets
        """

        # ----------------------------------------
        #   Console icon
        # ----------------------------------------

        self.image_console = Gtk.Image()

        # ----------------------------------------
        #   Console selector
        # ----------------------------------------

        self.menu_console = Gtk.Menu()

        self.button_console = Gtk.MenuButton()

        # Properties
        self.button_console.set_popup(self.menu_console)

    def __start_interface(self):
        """ Load data and start interface
        """

        self.set_option_label(self.path.name)

        # No console available
        if len(self.consoles) == 0:
            self.set_description_label(_("No corresponding console"))

        # One console available
        elif len(self.consoles) == 1:
            self.console = self.consoles[0]

            self.set_description_label(str(self.console.path))

            self.set_icon(self.console)

            self.set_widget(self.image_console)

        # Multi-consoles availables
        else:
            self.set_widget(self.button_console)

            self.button_console.set_image(self.image_console)

            for console in self.consoles:
                item = Gtk.MenuItem.new_with_label(console.name)
                item.connect("activate", self.__on_select_console)

                setattr(item, "console", console)

                self.menu_console.append(item)

            self.menu_console.show_all()

    def __on_select_console(self, widget, *args):
        """ Select a specific console for current row

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        """

        self.set_console(widget.console)

    def set_icon(self, console):
        """ Update icon image based on console data

        Parameters
        ----------
        console : gem.engine.console.Console
            Console instance
        """

        icon = self.parent.get_pixbuf_from_cache(
            "consoles", 24, console.id, console.icon)

        if icon is None:
            icon = self.parent.icons.blank(24)

        self.image_console.set_from_pixbuf(icon)

    def set_console(self, console):
        """ Set selected console

        Paremeters
        ----------
        console : gem.engine.console.Console
            Console instance
        """

        self.console = console

        self.set_icon(console)

        self.set_description_label(str(console.path))
