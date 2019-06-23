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
from gem.engine.utils import generate_identifier

# GObject
try:
    from gi.repository import GObject

except ImportError as error:
    from sys import exit

    exit("Cannot found python3-gobject module: %s" % str(error))

# Processus
from subprocess import Popen

# Threading
from threading import Thread


# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class ScriptThread(Thread, GObject.GObject):

    __gsignals__ = {
        "script-terminate": (GObject.SignalFlags.RUN_LAST, None, [object]),
    }

    def __init__(self, parent, path, game):
        """ Constructor

        Parameters
        ----------
        parent : gem.interface.Interface
            Main interface to access public variables
        path : str
            Script path
        game : gem.api.Game
            Game object
        """

        Thread.__init__(self)
        GObject.GObject.__init__(self)

        # ------------------------------------
        #   Initialize variables
        # ------------------------------------

        self.parent = parent
        self.logger = parent.logger

        self.path = path
        self.game = game

        self.name = generate_identifier(game.name)

    def run(self):
        """ Launch GameThread instance

        This function start a new processus with Popen and wait until it stop.
        When it finish, ScriptThread emit a signal to main interface.
        """

        try:
            self.proc = Popen([self.path, self.game.name])

            output, error_output = self.proc.communicate()

            self.proc.terminate()

        except OSError as error:
            self.logger.error("Cannot access to script: %s" % str(error))

        except MemoryError as error:
            self.logger.error("A memory error occur: %s" % str(error))

        except KeyboardInterrupt:
            self.logger.info("Terminate by keyboard interrupt")

        except Exception as error:
            self.logger.info("An exception error occur: %s" % str(error))

        # Call game-terminate signal on main window
        self.parent.emit("script-terminate", self)
