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

from geode_gem.ui.dialog.cache import CleanCacheDialog
from geode_gem.ui.dialog.cover import CoverDialog
from geode_gem.ui.dialog.delete import DeleteDialog
from geode_gem.ui.dialog.dndconsole import DNDConsoleDialog
from geode_gem.ui.dialog.duplicate import DuplicateDialog
from geode_gem.ui.dialog.editor import EditorDialog
from geode_gem.ui.dialog.maintenance import MaintenanceDialog
from geode_gem.ui.dialog.mednafen import MednafenDialog
from geode_gem.ui.dialog.message import MessageDialog
from geode_gem.ui.dialog.parameter import ParametersDialog
from geode_gem.ui.dialog.question import QuestionDialog
from geode_gem.ui.dialog.rename import RenameDialog
from geode_gem.ui.dialog.viewer import ViewerDialog
from geode_gem.ui.preferences.interface import (ConsolePreferences,
                                                EmulatorPreferences,
                                                PreferencesWindow)


# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class GeodeDialog:
    """ Custom dialogs for Geode-GEM applications
    """

    CleanCache = CleanCacheDialog
    Console = ConsolePreferences
    Cover = CoverDialog
    DNDConsole = DNDConsoleDialog
    Delete = DeleteDialog
    Duplicate = DuplicateDialog
    Editor = EditorDialog
    Emulator = EmulatorPreferences
    Maintenance = MaintenanceDialog
    Mednafen = MednafenDialog
    Message = MessageDialog
    Parameters = ParametersDialog
    Preferences = PreferencesWindow
    Question = QuestionDialog
    Rename = RenameDialog
    Viewer = ViewerDialog

