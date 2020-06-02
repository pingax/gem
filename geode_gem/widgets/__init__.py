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

from geode_gem.widgets.button import (GeodeGtkButton,
                                      GeodeGtkMenuButton,
                                      GeodeGtkToggleButton)
from geode_gem.widgets.cellrenderer import (GeodeGtkCellRendererPixbuf,
                                            GeodeGtkCellRendererText)
from geode_gem.widgets.entry import GeodeGtkSearchEntry
from geode_gem.widgets.frame import GeodeGtkFrame
from geode_gem.widgets.headerbar import GeodeGtkHeaderBar
from geode_gem.widgets.iconview import GeodeGtkIconView
from geode_gem.widgets.infobar import GeodeGtkInfoBar
from geode_gem.widgets.listbox import (GeodeGtkListBox,
                                       GeodeGtkListBoxItem,
                                       GeodeGtkListBoxCheckItem)
from geode_gem.widgets.menu import (GeodeGtkCheckMenuItem,
                                    GeodeGtkMenu,
                                    GeodeGtkMenuItem,
                                    GeodeGtkRadioMenuItem)
from geode_gem.widgets.popover import GeodeGtkPopover
from geode_gem.widgets.statusbar import GeodeGtkStatusbar
from geode_gem.widgets.toolbar import (GeodeGtkToolbar,
                                       GeodeGtkToolbarBox,
                                       GeodeGtkToolbarSwitch)
from geode_gem.widgets.treeview import (GeodeGtkTreeView,
                                           GeodeGtkTreeViewColumn)


# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class GeodeGtk:
    """ Custom widgets for Geode-GEM applications
    """

    Button = GeodeGtkButton
    CheckMenuItem = GeodeGtkCheckMenuItem
    Frame = GeodeGtkFrame
    HeaderBar = GeodeGtkHeaderBar
    IconView = GeodeGtkIconView
    InfoBar = GeodeGtkInfoBar
    ListBox = GeodeGtkListBox
    ListBoxCheckItem = GeodeGtkListBoxCheckItem
    ListBoxItem = GeodeGtkListBoxItem
    Menu = GeodeGtkMenu
    MenuButton = GeodeGtkMenuButton
    MenuItem = GeodeGtkMenuItem
    Popover = GeodeGtkPopover
    RadioMenuItem = GeodeGtkRadioMenuItem
    SearchEntry = GeodeGtkSearchEntry
    Statusbar = GeodeGtkStatusbar
    ToggleButton = GeodeGtkToggleButton
    Toolbar = GeodeGtkToolbar
    ToolbarBox = GeodeGtkToolbarBox
    ToolbarSwitch = GeodeGtkToolbarSwitch
    TreeView = GeodeGtkTreeView
    CellRendererPixbuf = GeodeGtkCellRendererPixbuf
    CellRendererText = GeodeGtkCellRendererText
    TreeViewColumn = GeodeGtkTreeViewColumn
