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

from geode_gem.widgets import (button, cellrenderer, entry, frame, headerbar,
                               iconview, image, infobar, label, listbox, menu,
                               popover, statusbar, toolbar, treeview)


# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class GeodeGtk:
    """ Custom widgets for Geode-GEM applications
    """

    Button = button.GeodeGtkButton
    CheckMenuItem = menu.GeodeGtkCheckMenuItem
    Frame = frame.GeodeGtkFrame
    HeaderBar = headerbar.GeodeGtkHeaderBar
    IconView = iconview.GeodeGtkIconView
    Image = image.GeodeGtkImage
    InfoBar = infobar.GeodeGtkInfoBar
    Label = label.GeodeGtkLabel
    ListBox = listbox.GeodeGtkListBox
    ListBoxCheckItem = listbox.GeodeGtkListBoxCheckItem
    ListBoxItem = listbox.GeodeGtkListBoxItem
    Menu = menu.GeodeGtkMenu
    MenuButton = button.GeodeGtkMenuButton
    MenuItem = menu.GeodeGtkMenuItem
    Popover = popover.GeodeGtkPopover
    RadioMenuItem = menu.GeodeGtkRadioMenuItem
    SearchEntry = entry.GeodeGtkSearchEntry
    Statusbar = statusbar.GeodeGtkStatusbar
    ToggleButton = button.GeodeGtkToggleButton
    Toolbar = toolbar.GeodeGtkToolbar
    ToolbarBox = toolbar.GeodeGtkToolbarBox
    ToolbarSwitch = toolbar.GeodeGtkToolbarSwitch
    TreeView = treeview.GeodeGtkTreeView
    CellRendererPixbuf = cellrenderer.GeodeGtkCellRendererPixbuf
    CellRendererText = cellrenderer.GeodeGtkCellRendererText
    TreeViewColumn = treeview.GeodeGtkTreeViewColumn
