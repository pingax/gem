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

# GObject
try:
    from gi import require_version

    require_version("Gtk", "3.0")

    from gi.repository import Gtk
    from gi.repository import Gdk
    from gi.repository import GdkPixbuf
    from gi.repository import GLib

except ImportError as error:
    from sys import exit

    exit("Cannot found python3-gobject module: %s" % str(error))


# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class ViewerDialog(CommonWindow):

    def __init__(self, parent, title, size, screenshots_path):
        """ Constructor

        Parameters
        ----------
        parent : Gtk.Window
            Parent object
        title : str
            Dialog title
        size : (int, int)
            Dialog size
        screenshots_path : list
            Screnshots path list
        """

        classic_theme = False
        if parent is not None:
            classic_theme = parent.use_classic_theme

        CommonWindow.__init__(self, parent, title, Icons.IMAGE, classic_theme)

        # ------------------------------------
        #   Initialize variables
        # ------------------------------------

        self.index = 0

        self.zoom_fit = True

        self.zoom_min = 10
        self.zoom_max = 400
        self.zoom_step = 5
        self.zoom_page_step = 10
        self.zoom_actual = 100

        # Allow the picture to autosize (with zoom_fit) when resize dialog
        self.auto_resize = parent.config.getboolean(
            "viewer", "auto_resize", fallback=False)

        self.screenshots = screenshots_path

        self.current_path = None
        self.current_pixbuf = None
        self.current_pixbuf_zoom = None
        self.current_pixbuf_size = tuple()

        self.targets = parent.targets

        self.__width, self.__height = size

        # ------------------------------------
        #   Manage monitor geometry
        # ------------------------------------

        self.__default_size = 800

        # Get default display
        display = Gdk.Display.get_default()

        if display is not None:
            # Retrieve default display monitor
            monitor = display.get_primary_monitor()
            # Retrieve default monitor geometry
            geometry = monitor.get_geometry()

            self.__default_size = min(
                int(geometry.width / 2), int(geometry.height / 2))

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

        self.set_resizable(True)

        self.set_spacing(0)
        self.set_border_width(0)

        self.grid_tools.set_border_width(6)

        # ------------------------------------
        #   Overlay
        # ------------------------------------

        self.overlay = Gtk.Overlay()

        # ------------------------------------
        #   Image
        # ------------------------------------

        self.scroll_image = Gtk.ScrolledWindow()
        self.view_image = Gtk.Viewport()

        self.image = Gtk.Image()

        # Properties
        self.view_image.drag_source_set(
            Gdk.ModifierType.BUTTON1_MASK, self.targets, Gdk.DragAction.COPY)

        # ------------------------------------
        #   Resize buttons
        # ------------------------------------

        self.grid_resize_buttons = Gtk.Box()

        self.image_fit = Gtk.Image()
        self.button_fit = Gtk.Button()

        self.image_original = Gtk.Image()
        self.button_original = Gtk.Button()

        # Properties
        Gtk.StyleContext.add_class(
            self.grid_resize_buttons.get_style_context(), "linked")
        self.grid_resize_buttons.set_spacing(-1)
        self.grid_resize_buttons.set_orientation(Gtk.Orientation.HORIZONTAL)

        self.image_fit.set_from_icon_name(
            Icons.Symbolic.ZOOM_FIT, Gtk.IconSize.BUTTON)

        self.button_fit.set_image(self.image_fit)

        self.image_original.set_from_icon_name(
            Icons.Symbolic.ZOOM, Gtk.IconSize.BUTTON)

        self.button_original.set_image(self.image_original)

        # ------------------------------------
        #   Move buttons
        # ------------------------------------

        self.grid_move_buttons = Gtk.Box()

        self.image_first = Gtk.Image()
        self.button_first = Gtk.Button()

        self.image_previous = Gtk.Image()
        self.button_previous = Gtk.Button()

        self.image_next = Gtk.Image()
        self.button_next = Gtk.Button()

        self.image_last = Gtk.Image()
        self.button_last = Gtk.Button()

        # Properties
        Gtk.StyleContext.add_class(
            self.grid_move_buttons.get_style_context(), "linked")
        self.grid_move_buttons.set_spacing(-1)
        self.grid_move_buttons.set_orientation(Gtk.Orientation.HORIZONTAL)

        self.image_first.set_from_icon_name(
            Icons.Symbolic.FIRST, Gtk.IconSize.BUTTON)

        self.button_first.set_image(self.image_first)

        self.image_previous.set_from_icon_name(
            Icons.Symbolic.PREVIOUS, Gtk.IconSize.BUTTON)

        self.button_previous.set_image(self.image_previous)

        self.image_next.set_from_icon_name(
            Icons.Symbolic.NEXT, Gtk.IconSize.BUTTON)

        self.button_next.set_image(self.image_next)

        self.image_last.set_from_icon_name(
            Icons.Symbolic.LAST, Gtk.IconSize.BUTTON)

        self.button_last.set_image(self.image_last)

        # ------------------------------------
        #   Zoom buttons
        # ------------------------------------

        self.grid_zoom_buttons = Gtk.Box()

        self.image_zoom_minus = Gtk.Image()
        self.button_zoom_minus = Gtk.Button()

        self.image_zoom_plus = Gtk.Image()
        self.button_zoom_plus = Gtk.Button()

        self.adjustment_zoom = Gtk.Adjustment()

        self.scale_zoom = Gtk.Scale()

        # Properties
        Gtk.StyleContext.add_class(
            self.grid_zoom_buttons.get_style_context(), "linked")
        self.grid_zoom_buttons.set_spacing(-1)
        self.grid_zoom_buttons.set_orientation(Gtk.Orientation.HORIZONTAL)

        self.image_zoom_minus.set_from_icon_name(
            Icons.Symbolic.ZOOM_OUT, Gtk.IconSize.BUTTON)

        self.button_zoom_minus.set_image(self.image_zoom_minus)

        self.image_zoom_plus.set_from_icon_name(
            Icons.Symbolic.ZOOM_IN, Gtk.IconSize.BUTTON)

        self.button_zoom_plus.set_image(self.image_zoom_plus)

        self.adjustment_zoom.set_lower(self.zoom_min)
        self.adjustment_zoom.set_upper(self.zoom_max)
        self.adjustment_zoom.set_step_increment(self.zoom_step)
        self.adjustment_zoom.set_page_increment(self.zoom_page_step)

        self.scale_zoom.set_draw_value(False)
        self.scale_zoom.set_size_request(150, -1)
        self.scale_zoom.set_adjustment(self.adjustment_zoom)
        self.scale_zoom.add_mark(self.zoom_min, Gtk.PositionType.BOTTOM, None)
        self.scale_zoom.add_mark(200, Gtk.PositionType.BOTTOM, None)
        self.scale_zoom.add_mark(self.zoom_max, Gtk.PositionType.BOTTOM, None)

        # ------------------------------------
        #   Overlay move buttons
        # ------------------------------------

        self.image_previous = Gtk.Image()
        self.button_overlay_previous = Gtk.Button()

        self.image_next = Gtk.Image()
        self.button_overlay_next = Gtk.Button()

        # Properties
        self.image_previous.set_from_icon_name(
            Icons.Symbolic.PREVIOUS, Gtk.IconSize.BUTTON)

        self.button_overlay_previous.get_style_context().add_class("osd")
        self.button_overlay_previous.set_image(self.image_previous)
        self.button_overlay_previous.set_valign(Gtk.Align.CENTER)
        self.button_overlay_previous.set_halign(Gtk.Align.START)
        self.button_overlay_previous.set_no_show_all(True)
        self.button_overlay_previous.set_margin_bottom(6)
        self.button_overlay_previous.set_margin_start(6)
        self.button_overlay_previous.set_margin_end(6)
        self.button_overlay_previous.set_margin_top(6)

        self.image_next.set_from_icon_name(
            Icons.Symbolic.NEXT, Gtk.IconSize.BUTTON)

        self.button_overlay_next.get_style_context().add_class("osd")
        self.button_overlay_next.set_image(self.image_next)
        self.button_overlay_next.set_valign(Gtk.Align.CENTER)
        self.button_overlay_next.set_halign(Gtk.Align.END)
        self.button_overlay_next.set_no_show_all(True)
        self.button_overlay_next.set_margin_bottom(6)
        self.button_overlay_next.set_margin_start(6)
        self.button_overlay_next.set_margin_end(6)
        self.button_overlay_next.set_margin_top(6)

        # ------------------------------------
        #   Integrate widgets
        # ------------------------------------

        self.scroll_image.add(self.view_image)
        self.view_image.add(self.image)

        self.grid_move_buttons.pack_start(
            self.button_first, False, False, 0)
        self.grid_move_buttons.pack_start(
            self.button_previous, False, False, 0)
        self.grid_move_buttons.pack_start(
            self.button_next, False, False, 0)
        self.grid_move_buttons.pack_start(
            self.button_last, False, False, 0)

        # self.grid_zoom_buttons.pack_start(
        #    self.button_zoom_minus, False, False, 0)
        self.grid_zoom_buttons.pack_start(
            self.button_original, False, False, 0)
        self.grid_zoom_buttons.pack_start(
            self.button_fit, False, False, 0)
        # self.grid_zoom_buttons.pack_start(
        #    self.button_zoom_plus, False, False, 0)

        self.overlay.add(self.scroll_image)
        self.overlay.add_overlay(self.button_overlay_previous)
        self.overlay.add_overlay(self.button_overlay_next)

        self.pack_start(self.overlay, True, True, 0)

    def __init_signals(self):
        """ Initialize widgets signals
        """

        if self.auto_resize:
            self.window.connect("size-allocate", self.update_screenshot)

        self.window.connect("key-press-event", self.change_screenshot)

        self.button_first.connect("clicked", self.change_screenshot)
        self.button_previous.connect("clicked", self.change_screenshot)
        self.button_next.connect("clicked", self.change_screenshot)
        self.button_last.connect("clicked", self.change_screenshot)

        self.button_zoom_minus.connect("clicked", self.change_screenshot)
        self.button_original.connect("clicked", self.change_screenshot)
        self.button_fit.connect("clicked", self.change_screenshot)
        self.button_zoom_plus.connect("clicked", self.change_screenshot)

        self.button_overlay_previous.connect("clicked", self.change_screenshot)
        self.button_overlay_next.connect("clicked", self.change_screenshot)

        self.view_image.connect("drag-data-get", self.__on_dnd_send_data)

        self.scale_zoom.connect("change_value", self.update_adjustment)

    def __start_interface(self):
        """ Load data and start interface
        """

        self.add_widget(self.grid_move_buttons)
        self.add_widget(self.grid_zoom_buttons, Gtk.Align.END)
        self.add_widget(self.scale_zoom, Gtk.Align.END)

        self.set_size(int(self.__width), int(self.__height))

        self.show_all()

        self.update_screenshot()
        self.set_widgets_sensitive()

    def __on_dnd_send_data(self, widget, context, data, info, time):
        """ Set screenshot file path uri

        This function send rom file path uri when user drag a game from gem and
        drop it to extern application

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        context : Gdk.DragContext
            Drag context
        data : Gtk.SelectionData
            Received data
        info : int
            Info that has been registered with the target in the Gtk.TargetList
        time : int
            Timestamp at which the data was received
        """

        if self.current_path is not None and self.current_path.exists():
            data.set_uris(["file://%s" % str(self.current_path)])

    def change_screenshot(self, widget=None, event=None):
        """ Change current screenshot

        Parameters
        ----------
        widget : Gtk.Widget, optional
            Object which receive signal (Default: None)
        event : Gdk.EventButton or Gdk.EventKey, optional
            Event which triggered this signal (Default: None)
        """

        # Keyboard
        if widget is self.window:
            if event.keyval == Gdk.KEY_Left:
                self.index -= 1

            elif event.keyval == Gdk.KEY_Right:
                self.index += 1

            elif event.keyval == Gdk.KEY_KP_Subtract:
                self.zoom_fit = False
                self.zoom_actual -= self.zoom_step

            elif event.keyval == Gdk.KEY_KP_Add:
                self.zoom_fit = False
                self.zoom_actual += self.zoom_step

        # Zoom
        elif widget == self.button_zoom_minus:
            self.zoom_fit = False
            self.zoom_actual -= self.zoom_step

        elif widget == self.button_original:
            self.zoom_fit = False
            self.zoom_actual = None

        elif widget == self.button_fit:
            self.zoom_fit = True

        elif widget == self.button_zoom_plus:
            self.zoom_fit = False
            self.zoom_actual += self.zoom_step

        # Move
        elif widget == self.button_first:
            self.index = 0

        elif widget in (self.button_overlay_previous, self.button_previous):
            self.index -= 1

        elif widget in (self.button_overlay_next, self.button_next):
            self.index += 1

        elif widget == self.button_last:
            self.index = len(self.screenshots) - 1

        # Fixes
        if self.index < 0:
            self.index = 0

        elif self.index > len(self.screenshots) - 1:
            self.index = len(self.screenshots) - 1

        if self.zoom_actual is not None and type(self.zoom_actual) is int:
            if self.zoom_actual < self.zoom_min:
                self.zoom_actual = self.zoom_min

            elif self.zoom_actual > self.zoom_max:
                self.zoom_actual = self.zoom_max

        self.update_screenshot()
        self.set_widgets_sensitive()

    def set_widgets_sensitive(self):
        """ Refresh interface's widgets
        """

        self.button_first.set_sensitive(True)
        self.button_previous.set_sensitive(True)
        self.button_next.set_sensitive(True)
        self.button_last.set_sensitive(True)

        if self.index == 0:
            self.button_first.set_sensitive(False)
            self.button_previous.set_sensitive(False)

            self.button_overlay_previous.hide()

        else:
            self.button_overlay_previous.show()

        if self.index == len(self.screenshots) - 1:
            self.button_last.set_sensitive(False)
            self.button_next.set_sensitive(False)

            self.button_overlay_next.hide()

        else:
            self.button_overlay_next.show()

    def update_adjustment(self, widget, scroll, value):
        """ Change current screenshot size

        Parameters
        ----------
        widget : Gtk.Widget
            Object which receive signal
        scroll : Gtk.ScrollType
            Type of scroll action that was performed
        value : float
            New value resulting from the scroll action
        """

        if int(value) >= self.zoom_min and int(value) <= self.zoom_max:
            self.zoom_fit = False
            self.zoom_actual = int(value)

            self.update_screenshot()

    def update_screenshot(self, widget=None, event=None):
        """ Change current screenshot size

        Parameters
        ----------
        widget : Gtk.Widget, optional
            Object which receive signal (Default: None)
        event : Gdk.EventButton or Gdk.EventKey, optional
            Event which triggered this signal (Default: None)
        """

        # Get the current screenshot path
        path = self.screenshots[self.index].expanduser()

        # Avoid to recreate a pixbuf for the same file
        if not str(path) == str(self.current_path):

            if path.exists() and path.is_file():
                self.current_path = path

                try:
                    # Generate a Pixbuf from current screenshot
                    self.current_pixbuf = GdkPixbuf.Pixbuf.new_from_file(
                        str(self.current_path))

                    self.current_pixbuf_size = (
                        self.current_pixbuf.get_width(),
                        self.current_pixbuf.get_height())

                    self.current_pixbuf_zoom = None

                    # Set headerbar subtitle with current screenshot path
                    self.set_subtitle(str(self.current_path))

                except GLib.Error:
                    self.current_pixbuf = None

        # Check if pixbuf has been generate correctly
        if self.current_pixbuf is not None:

            # Restore original image size
            width, height = self.current_pixbuf_size

            if width > height:
                screen_height = int((height * self.__default_size) / width)
                screen_width = self.__default_size

            else:
                screen_width = int((width * self.__default_size) / height)
                screen_height = self.__default_size

            # ------------------------------------
            #   Check zoom features
            # ------------------------------------

            # Zoom to original size
            if self.zoom_actual is None:
                ratio_x = float(width / screen_width)
                ratio_y = float(height / screen_height)

                self.zoom_actual = int(min(ratio_x, ratio_y) * 100)

            # Zoom to fit current window
            elif self.zoom_fit:
                allocation = self.scroll_image.get_allocation()

                ratio_x = float(allocation.width / screen_width)
                ratio_y = float(allocation.height / screen_height)

                self.zoom_actual = int(min(ratio_x, ratio_y) * 100)

            # ------------------------------------
            #   Reload pixbuf
            # ------------------------------------

            # Avoid to have a zoom above maximum allowed
            if self.zoom_actual > self.zoom_max:
                self.zoom_actual = self.zoom_max
            # Avoid to have a zoom under minimum allowed
            if self.zoom_actual < self.zoom_min:
                self.zoom_actual = self.zoom_min

            if not self.current_pixbuf_zoom == self.zoom_actual:
                self.current_pixbuf_zoom = self.zoom_actual

                # Calc ratio from current zoom percent
                ratio_width = int((self.zoom_actual * screen_width) / 100)
                ratio_height = int((self.zoom_actual * screen_height) / 100)

                # Update scale adjustment
                self.adjustment_zoom.set_value(float(self.zoom_actual))

                self.image.set_from_pixbuf(self.current_pixbuf.scale_simple(
                    ratio_width, ratio_height, GdkPixbuf.InterpType.TILES))
