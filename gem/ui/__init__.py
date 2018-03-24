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
from gem.engine import *

# Processus
from subprocess import PIPE
from subprocess import Popen
from subprocess import STDOUT

# Threading
from threading import Thread

# ------------------------------------------------------------------------------
#   Modules - GTK+
# ------------------------------------------------------------------------------

try:
    from gi import require_version

    require_version("Gtk", "3.0")

    from gi.repository import Gtk
    from gi.repository import Gdk
    from gi.repository import Pango

    from gi.repository.Gdk import EventType

    from gi.repository.GLib import idle_add
    from gi.repository.GLib import source_remove

    from gi.repository.GObject import GObject
    from gi.repository.GObject import MainLoop
    from gi.repository.GObject import SIGNAL_RUN_LAST
    from gi.repository.GObject import SIGNAL_RUN_FIRST

    from gi.repository.GdkPixbuf import Pixbuf
    from gi.repository.GdkPixbuf import InterpType
    from gi.repository.GdkPixbuf import Colorspace

except ImportError as error:
    sys_exit("Import error with python3-gobject module: %s" % str(error))