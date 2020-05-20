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

from geode_gem.ui.widgets.infobar import GeodeGtkInfoBar
from geode_gem.ui.widgets.menu import GeodeGtkMenu, GeodeGtkMenuItem
from geode_gem.ui.widgets.statusbar import GeodeGtkStatusbar


# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class GeodeGtk:
    """ Custom widgets for Geode-GEM applications
    """

    InfoBar = GeodeGtkInfoBar
    Menu = GeodeGtkMenu
    MenuItem = GeodeGtkMenuItem
    Statusbar = GeodeGtkStatusbar
