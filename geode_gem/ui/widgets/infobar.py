# ------------------------------------------------------------------------------
#  Copyleft 2015-2020  PacMiam
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
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

# GObject
from gi.repository import Gtk


# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class GeodeGtkInfoBar(Gtk.InfoBar):

    def __init__(self):
        """ Constructor
        """

        Gtk.InfoBar.__init__(self)

        self.__inner_grid = self.get_content_area()

        self.__inner_widgets = {
            "label": Gtk.Label.new(None),
        }

        # ------------------------------------
        #   Properties
        # ------------------------------------

        self.set_show_close_button(False)

        self.__inner_widgets.get("label").set_use_markup(True)

        # ------------------------------------
        #   Packing
        # ------------------------------------

        self.__inner_grid.pack_start(
            self.__inner_widgets.get("label"), True, True, 4)

    def do_show(self):
        """ Virtual method called when self.show() method is called
        """

        Gtk.InfoBar.do_show(self)

        # Ensure to show all internal widgets
        self.__inner_grid.show_all()

    def set_message(self, message_type, message_text):
        """ Set a new message with a specific type

        Parameters
        ----------
        message_type : Gtk.MessageType
            Infobar message type
        message_text : str
            The new infobar label text

        Raises
        ------
        TypeError
            When specified message_type type is not a Gtk.MessageType
        """

        if not isinstance(message_type, Gtk.MessageType):
            raise TypeError(
                "The message_type parameter must be a Gtk.MessageType")

        self.set_message_type(message_type)
        if message_type and not self.get_visible():
            self.set_visible(True)

        self.__inner_widgets.get("label").set_markup(message_text)
