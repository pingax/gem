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
from gem.engine import *
from gem.engine.api import GEM
from gem.engine.utils import *

# Translation
from gettext import gettext as _

# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class GameThread(Thread, GObject):

    __gsignals__ = {
        "game-started": (SignalFlags.RUN_FIRST, None, [object]),
        "game-terminate": (SignalFlags.RUN_LAST, None, [object]),
    }

    def __init__(self, parent, console, emulator, game, command):
        """ Constructor

        Parameters
        ----------
        parent : gem.interface.Interface
            Main interface to access public variables
        emulator : gem.api.Console
            Console object
        emulator : gem.api.Emulator
            Emulator object
        game : gem.api.Game
            Game object
        command : list
            Command parameters list
        """

        Thread.__init__(self)
        GObject.__init__(self)

        # ------------------------------------
        #   Initialize variables
        # ------------------------------------

        self.parent = parent
        self.logger = parent.logger

        self.name = generate_identifier(game.name)
        self.command = command
        self.console = console
        self.emulator = emulator
        self.game = game

        self.delta = None
        self.error = False

        # ------------------------------------
        #   Generate data
        # ------------------------------------

        self.path = parent.api.get_local(game.log)


    def run(self):
        """ Launch GameThread instance

        This function start a new processus with Popen and wait until it stop.
        When it finish, GameThread emit a signal to main interface.
        """

        # Call game-started signal on main window
        self.parent.emit("game-started", self.game)

        started = datetime.now()

        self.logger.info(_("Launch %s") % self.game.name)

        try:
            self.logger.debug("Command: %s" % ' '.join(self.command))

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

            self.logger.info(_("Log to %s") % self.path)

            # Logging process output
            with open(self.path, 'w') as pipe:
                self.proc = Popen(
                    self.command,
                    stdin=PIPE,
                    stdout=pipe,
                    stderr=pipe,
                    env=environment,
                    universal_newlines=True)

                output, error_output = self.proc.communicate()

            self.logger.info(_("Close %s") % self.game.name)

            self.proc.terminate()

            # ------------------------------------
            #   Play time
            # ------------------------------------

            self.delta = (datetime.now() - started)

        except OSError as error:
            self.logger.error(_("Cannot access to game: %s") % str(error))
            self.error = True

        except MemoryError as error:
            self.logger.error(_("A memory error occur: %s") % str(error))
            self.error = True

        except KeyboardInterrupt as error:
            self.logger.info(_("Terminate by keyboard interrupt"))

        except Exception as error:
            self.logger.info(_("An exception error occur: %s") % str(error))
            self.error = True

        # Call game-terminate signal on main window
        self.parent.emit("game-terminate", self)
