# ------------------------------------------------------------------
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
# ------------------------------------------------------------------

# ------------------------------------------------------------------
#   Modules
# ------------------------------------------------------------------

# Datetime
from datetime import datetime

# Filesystem
from os.path import splitext
from os.path import basename
from os.path import expanduser
from os.path import join as path_join

# Process
from subprocess import PIPE
from subprocess import Popen
from subprocess import STDOUT

# Threading
from threading import Thread

# Translation
from gettext import gettext as _
from gettext import textdomain
from gettext import bindtextdomain

# ------------------------------------------------------------------
#   Modules - Interface
# ------------------------------------------------------------------

try:
    from gi.repository.GObject import idle_add
    from gi.repository.GObject import Object
    from gi.repository.GObject import GObject
    from gi.repository.GObject import SIGNAL_RUN_LAST

except ImportError as error:
    sys_exit("Import error with python3-gobject module: %s" % str(error))

# ------------------------------------------------------------------
#   Modules - GEM
# ------------------------------------------------------------------

try:
    from gem import *
    from gem.utils import *

except ImportError as error:
    sys_exit("Import error with gem module: %s" % str(error))

# ------------------------------------------------------------------
#   Translation
# ------------------------------------------------------------------

bindtextdomain("gem", get_data("i18n"))
textdomain("gem")

# ------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------

class GameThread(Thread, GObject):

    __gsignals__ = { "game-terminate": (SIGNAL_RUN_LAST, None, [object]) }

    def __init__(self, parent, emulator, filename, command, title):
        """ Constructor

        Parameters
        ----------
        parent : gem.interface.Interface
            Main interface to access public variables
        emulator : str
            Emulator name
        filename : str
            Game file name
        command : list
            Command parameters list
        title : str
            Game title for log output
        """

        Thread.__init__(self)
        GObject.__init__(self)

        # ----------------------------
        #   Variables
        # ----------------------------

        self.parent = parent
        self.logger = parent.logger

        self.name = title
        self.command = command
        self.emulator = emulator
        self.filename = filename

        self.delta = None
        self.error = False

        # ----------------------------
        #   Generate data
        # ----------------------------

        self.path = path_join(expanduser(Path.Logs), "%s.log" % filename)


    def run(self):
        """
        """

        started = datetime.now()

        try:
            # ----------------------------
            #   Launch game
            # ----------------------------

            self.logger.info(_("Launch %s") % ' '.join(self.command))

            self.proc = Popen(
                self.command,
                stdin=PIPE,
                stdout=PIPE,
                stderr=STDOUT,
                universal_newlines=True)

            output, error_output = self.proc.communicate()

            self.logger.info(_("Close %s") % self.name)

            self.proc.terminate()

            # ----------------------------
            #   Play time
            # ----------------------------

            self.delta = (datetime.now() - started)

            # ----------------------------
            #   Log data
            # ----------------------------

            self.logger.info(_("Log to %s") % self.path)

            # Write output into game's log
            with open(self.path, 'w') as pipe:
                pipe.write(str())
                pipe.write("%s\n\n" % " ".join(self.command))
                pipe.write(output)

        except OSError as error:
            self.logger.error(_("OSError occurs: %s" % error))
            self.error = True

        except MemoryError as error:
            self.logger.error(_("MemoryError occurs: %s" % error))
            self.error = True

        except KeyboardInterrupt as error:
            self.logger.info(_("Terminate by keyboard interrupt"))

        # Call game-terminate signal on main window
        self.parent.emit("game-terminate", self)
