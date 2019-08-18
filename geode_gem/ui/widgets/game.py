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

# Datetime
from datetime import datetime

# GObject
try:
    from gi.repository import GObject

except ImportError as error:
    from sys import exit

    exit("Cannot found python3-gobject module: %s" % str(error))

# Processus
from subprocess import PIPE
from subprocess import Popen

# System
from os import environ

# Threading
from threading import Thread


# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class GameThread(Thread, GObject.GObject):

    __gsignals__ = {
        "game-started": (GObject.SignalFlags.RUN_FIRST, None, [object]),
        "game-terminate": (GObject.SignalFlags.RUN_LAST, None, [object]),
    }

    def __init__(self, parent, game, fullscreen=False):
        """ Constructor

        Parameters
        ----------
        parent : gem.interface.Interface
            Main interface to access public variables
        game : gem.api.Game
            Game object
        fullscreen : bool
            Fullscreen mode
        """

        Thread.__init__(self)
        GObject.GObject.__init__(self)

        # ------------------------------------
        #   Initialize variables
        # ------------------------------------

        self.parent = parent
        self.logger = parent.logger

        self.name = game.id
        self.game = game

        self.fullscreen = fullscreen

        self.delta = None
        self.error = False

        # ------------------------------------
        #   Generate data
        # ------------------------------------

        self.path = parent.api.get_local("logs", game.id + ".log")

    def run(self):
        """ Launch GameThread instance

        This function start a new processus with Popen and wait until it stop.
        When it finish, GameThread emit a signal to main interface.
        """

        # Call game-started signal on main window
        self.parent.emit("game-started", self.game)

        started = datetime.now()

        self.logger.info("Launch %s" % self.game.name)

        try:
            command = self.game.command(self.fullscreen)

            self.logger.debug("Command: %s" % ' '.join(command))

            # ------------------------------------
            #   Check environment
            # ------------------------------------

            # Get a copy of current environment
            environment = environ.copy()

            # Check if current game has specific environment variable
            for key, value in self.game.environment.items():
                environment[key] = value

            # ------------------------------------
            #   Start process
            # ------------------------------------

            self.logger.info("Log to %s" % self.path)

            # Logging process output
            with open(self.path, 'w') as pipe:
                self.proc = Popen(
                    command,
                    stdin=PIPE,
                    stdout=pipe,
                    stderr=pipe,
                    env=environment,
                    start_new_session=True,
                    universal_newlines=True)

                self.proc.communicate()

            self.logger.info("Close %s" % self.game.name)

            self.proc.terminate()

            # ------------------------------------
            #   Play time
            # ------------------------------------

            self.delta = (datetime.now() - started)

        except OSError as error:
            self.logger.error("Cannot access to game: %s" % str(error))
            self.error = True

        except MemoryError as error:
            self.logger.error("A memory error occur: %s" % str(error))
            self.error = True

        except KeyboardInterrupt:
            self.logger.info("Terminate by keyboard interrupt")

        except Exception as error:
            self.logger.info("An exception error occur: %s" % str(error))
            self.error = True

        # Call game-terminate signal on main window
        self.parent.emit("game-terminate", self)
