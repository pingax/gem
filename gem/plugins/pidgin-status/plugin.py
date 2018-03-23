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

# ------------------------------------------------------------------------------
#   Modules
# ------------------------------------------------------------------------------

# Dbus
from dbus import SessionBus

# GEM
from gem.ui.widgets.addon import Addon

# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class Plugin(Addon):

    STATUS_OFFLINE          = 1
    STATUS_AVAILABLE        = 2
    STATUS_UNAVAILABLE      = 3
    STATUS_INVISIBLE        = 4
    STATUS_AWAY             = 5
    STATUS_EXTENDED_AWAY    = 6
    STATUS_MOBILE           = 7
    STATUS_TUNE             = 8

    PURPLE_OBJECT           = "/im/pidgin/purple/PurpleObject"
    PURPLE_SERVICE          = "im.pidgin.purple.PurpleService"

    def __init__(self):
        """ Constructor
        """

        Addon.__init__(self, __file__)

        # ----------------------------------------
        #   Initialize title
        # ----------------------------------------

        self.__title = "In Game"

        # ----------------------------------------
        #   Initialize DBus session
        # ----------------------------------------

        try:
            self.__purple = SessionBus().get_object(
                self.PURPLE_SERVICE, self.PURPLE_OBJECT)

            self.__current = self.__purple.PurpleSavedstatusGetDefault()

        except:
            self.__purple = None


    def on_game_started(self, game):
        """ Set new status for purple instance

        Parameters
        ----------
        game : gem.api.Game
            Game instance
        """

        try:
            if self.__purple is not None:
                status = self.__purple.PurpleSavedstatusNew(
                    self.__title, self.STATUS_UNAVAILABLE)

                self.__purple.PurpleSavedstatusSetMessage(
                    status, "Play %s" % game.name)

                self.__purple.PurpleSavedstatusActivate(status)

        except:
            pass


    def on_game_terminate(self, game):
        """ Restore default status from purple instance

        Parameters
        ----------
        game : gem.api.Game
            Game instance
        """

        try:
            if self.__purple is not None:

                # Restore previous status
                self.__purple.PurpleSavedstatusActivate(self.__current)

                # Delete saved status
                self.__purple.PurpleSavedstatusDelete(self.__title)

        except:
            pass


if __name__ == "__main__":
    print(Plugin())
