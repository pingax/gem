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

# Datetime
from datetime import timedelta

# Geode
from geode_gem.ui.data import Columns
from geode_gem.ui.utils import string_from_date, string_from_time
from geode_gem.ui.placeholder import GeodeGEMPlaceholder
from geode_gem.widgets import GeodeGtk
from geode_gem.widgets.common import GeodeGtkCommon

# GObject
from gi.repository import Gdk, GdkPixbuf, Gtk, Pango

# Python
from enum import Enum

# Regex
from re import match, IGNORECASE

# Translation
from gettext import gettext as _


# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class CommonGamesView(GeodeGtkCommon, Gtk.ScrolledWindow):

    def __init__(self, identifier, interface, view):
        """ Constructor

        Parameters
        ----------
        identifier : str
            String to identify this object in internal container
        interface : geode_gem.ui.interface.MainWindow
            Main interface instance
        view : geode_gem.ui.view.CommonGamesView
            View instance
        """

        GeodeGtkCommon.__init__(self, identifier)
        Gtk.ScrolledWindow.__init__(self)

        self.interface = interface
        self.view = view

        self.storage = dict()

        # ------------------------------------
        #   Packing
        # ------------------------------------

        self.add(self.view)
        self.append_widget(self.view)

    def clear(self):
        """ Remove all items from games view
        """

        self.view.unselect_all()
        self.view.clear()

        self.storage.clear()

    def append_item(self, identifier, data):
        """ Append a new item in games view

        Parameters
        ----------
        identifier : str
            Treeiter identifier
        data : list
            Data structure for specific view
        """

        self.storage[identifier] = self.view.append(data)

        return self.storage.get(identifier)

    def has_item(self, identifier):
        """ Check if a specific identifier exists in main storage

        Parameters
        ----------
        identifier : str
            Item identifier used in main storage

        Returns
        -------
        bool
            True if item exists in main storage, False otherwise
        """

        return identifier in self.storage

    def remove_item(self, identifier):
        """ Remove an item from games view

        Parameters
        ----------
        identifier : str
            Treeiter identifier
        """

        if identifier in self.storage:
            self.view.remove(self.storage.get(identifier))

            del self.storage[identifier]

    def get_treeiter(self, identifier):
        """ Retrieve an item from main storage for a specific identifier

        Parameters
        ----------
        identifier : str
            Item identifier used in main storage

        Returns
        -------
        Gtk.TreeIter
            Item instance is found, None otherwise
        """

        return self.storage.get(identifier, None)


class GeodeGEMViews(GeodeGtkCommon, Gtk.Box):

    __target__ = [
        Gtk.TargetEntry.new("text/uri-list", 0, 1337)
    ]

    class Name(Enum):

        LIST = "list"
        GRID = "grid"

    def __init__(self, interface):
        """ Constructor

        Parameters
        ----------
        interface : geode_gem.ui.interface.MainWindow
            Main interface instance
        """

        GeodeGtkCommon.__init__(self)
        Gtk.Box.__init__(self)

        self.interface = interface
        self.logger = interface.logger

        self.games_identifier_storage = list()

        self.visible_view = None

        # ------------------------------------
        #   Properties
        # ------------------------------------

        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.set_spacing(0)

        # ------------------------------------
        #   Widgets
        # ------------------------------------

        self.view_placeholder = GeodeGEMPlaceholder(self.interface)
        self.view_list = GeodeGEMTreeView(self.interface)
        self.view_grid = GeodeGEMIconView(self.interface)

        # ------------------------------------
        #   Drag and drop
        # ------------------------------------

        self.drag_dest_set(Gtk.DestDefaults.MOTION | Gtk.DestDefaults.DROP,
                           self.__target__,
                           Gdk.DragAction.COPY)

        self.view_list.view.drag_source_set(
            Gdk.ModifierType.BUTTON1_MASK,
            self.__target__,
            Gdk.DragAction.COPY)

        self.view_grid.view.drag_source_set(
            Gdk.ModifierType.BUTTON1_MASK,
            self.__target__,
            Gdk.DragAction.COPY)

        # ------------------------------------
        #   Signals
        # ------------------------------------

        self.connect(
            "drag-data-received", interface.on_drag_data_to_main_interface)

        # ------------------------------------
        #   Packing
        # ------------------------------------

        self.pack_start(self.view_placeholder, True, True, 0)

        self.pack_start(self.view_list, True, True, 0)
        self.append_widget(self.view_list)

        self.pack_start(self.view_grid, True, True, 0)
        self.append_widget(self.view_grid)

    @property
    def iconview(self):
        """ Retrieve iconview instance

        Returns
        -------
        GeodeGtk.IconView
            Iconview instance
        """

        return self.view_grid.view

    @property
    def placeholder(self):
        """ Retrieve placeholder instance

        Returns
        -------
        GeodeGEM.Placeholder
            Placeholder instance
        """

        return self.view_placeholder

    @property
    def treeview(self):
        """ Retrieve treeview instance

        Returns
        -------
        GeodeGtk.TreeView
            Treeview instance
        """

        return self.view_list.view

    def clear(self):
        """ Clear views and lists storages
        """

        self.games_identifier_storage.clear()

        self.logger.debug("Clear games treeview content")
        self.view_list.clear()

        self.logger.debug("Clear games iconview content")
        self.view_grid.clear()

    def append_games(self, console, games):
        """ Append games in both views

        Parameters
        ----------
        console : geode_gem.engine.console.Console
            Console instance
        games : list
            Games object list
        """

        self.treeview.freeze_child_notify()

        for index, game in enumerate(games, start=1):
            self.append_game(console, game)

            self.treeview.thaw_child_notify()
            yield index, game
            self.treeview.freeze_child_notify()

        self.treeview.thaw_child_notify()

    def append_game(self, console, game):
        """ Append a game to games views

        Parameters
        ----------
        console : geode_gem.engine.console.Console
            Console instance
        game : geode_gem.engine.game.Game
            Game instance
        """

        # Hide games which match ignores regex
        show = all([match(element, game.name, IGNORECASE) is not None
                    for element in console.ignores])

        if show:
            self.view_grid.append_item(console, game)
            self.view_list.append_item(console, game)

            self.games_identifier_storage.append(game.id)

    def get_selected_game(self):
        """ Retrieve selected game from visible view

        Returns
        -------
        Gtk.TreeIter
            Selected game if found, None otherwise
        """

        treeiter = None

        if self.visible_view == GeodeGEMViews.Name.LIST:
            model = self.treeview.get_model()
            treeiter = self.treeview.get_selected_treeiter()

            if treeiter is not None:
                return model.get_value(treeiter, Columns.List.OBJECT)

        elif self.visible_view == GeodeGEMViews.Name.GRID:
            model = self.iconview.get_model()
            treeiter = self.iconview.get_selected_treeiter()

            if treeiter is not None:
                return model.get_value(treeiter, Columns.Grid.OBJECT)

        return None

    def get_iter_from_key(self, identifier):
        """ Retrieve views iters for a specific game identifier

        Parameters
        ----------
        identifier : str
            Game identifier
        """

        return [getattr(self, f"view_{key}").get_treeiter(identifier)
                for key in ("list", "grid")]

    def has_game(self, identifier):
        """ Check if a specific identifier exists in main storage

        Parameters
        ----------
        identifier : str
            Game identifier used in main storage

        Returns
        -------
        bool
            True if game exists in main storage, False otherwise
        """

        return identifier in self.games_identifier_storage

    def refilter(self):
        """ Refilter games views
        """

        self.treeview.refilter()
        self.iconview.refilter()

    def remove_game(self, identifier):
        """ Remove a game from games views

        Parameters
        ----------
        identifier : str
            Game identifier
        """

        if identifier in self.games_identifier_storage:
            del self.games_identifier_storage[identifier]

        self.view_list.remove_item(identifier)
        self.view_grid.remove_item(identifier)

    def set_placeholder_visibility(self, is_visible):
        """ Define placeholder visibility

        Parameters
        ----------
        is_visible : bool
            Placeholder visibility status
        """

        if is_visible:
            self.view_list.hide()
            self.view_grid.hide()
            self.view_placeholder.show_all()

        else:
            self.set_view(self.visible_view)
            self.view_placeholder.hide()

    def set_view(self, identifier):
        """ Set the games view to show

        Parameters
        ----------
        identifier : str, optional
            View identifier, used the placeholder by default
        """

        if not isinstance(identifier, GeodeGEMViews.Name):
            raise KeyError(
                f"Cannot found '{identifier}' in GeodeGEMViews.Name")

        for key in GeodeGEMViews.Name:
            widget = getattr(self, f"view_{key.value}")
            widget.set_visible(key is identifier)

            if widget.get_visible():
                widget.show_all()

                self.visible_view = key

    def unselect_all(self):
        """ Unselect selections from both games views
        """

        self.logger.debug("Unselect games on both views")
        self.iconview.unselect_all()
        self.treeview.unselect_all()


class GeodeGEMTreeView(CommonGamesView):

    def __init__(self, interface):
        """ Constructor

        Parameters
        ----------
        interface : geode_gem.ui.interface.MainWindow
            Main interface instance
        """

        CommonGamesView.__init__(
            self,
            "treeview",
            interface,
            GeodeGtk.TreeView(
                "games",
                Gtk.ListStore(
                    str,                # Favorite icon
                    str,                # Multiplayer icon
                    str,                # Finish icon
                    str,                # Name
                    int,                # Played
                    str,                # Last play
                    str,                # Last time play
                    str,                # Time play
                    int,                # Score
                    str,                # Installed
                    str,                # Custom parameters
                    str,                # Screenshots
                    str,                # Save states
                    object,             # Game object
                    GdkPixbuf.Pixbuf    # Thumbnail
                ),
                GeodeGtk.TreeViewColumn(
                    "favorite",
                    None,
                    GeodeGtk.CellRendererPixbuf(
                        "cell_favorite",
                        index=Columns.List.FAVORITE,
                        mode="icon-name",
                        padding=(4, 0),
                    ),
                    resizable=False,
                    sizing=Gtk.TreeViewColumnSizing.FIXED,
                    sort_column_id=Columns.List.FAVORITE,
                ),
                GeodeGtk.TreeViewColumn(
                    "multiplayer",
                    None,
                    GeodeGtk.CellRendererPixbuf(
                        "cell_multiplayer",
                        index=Columns.List.MULTIPLAYER,
                        mode="icon-name",
                        padding=(4, 0),
                    ),
                    resizable=False,
                    sizing=Gtk.TreeViewColumnSizing.FIXED,
                    sort_column_id=Columns.List.MULTIPLAYER,
                ),
                GeodeGtk.TreeViewColumn(
                    "finish",
                    None,
                    GeodeGtk.CellRendererPixbuf(
                        "cell_finish",
                        index=Columns.List.FINISH,
                        mode="icon-name",
                        padding=(4, 0),
                    ),
                    resizable=False,
                    sizing=Gtk.TreeViewColumnSizing.FIXED,
                    sort_column_id=Columns.List.FINISH,
                ),
                GeodeGtk.TreeViewColumn(
                    "name",
                    _("Name"),
                    GeodeGtk.CellRendererPixbuf(
                        "cell_thumbnail",
                        ellipsize=Pango.EllipsizeMode.END,
                        index=Columns.List.THUMBNAIL,
                        padding=(2, 0),
                    ),
                    GeodeGtk.CellRendererText(
                        "cell_name",
                        alignment=(0, 0.5),
                        ellipsize=Pango.EllipsizeMode.END,
                        expand=True,
                        index=Columns.List.NAME,
                        padding=(4, 4),
                    ),
                    alignment=0,
                    expand=True,
                    min_width=100,
                    fixed_width=300,
                    sort_column_id=Columns.List.NAME,
                ),
                GeodeGtk.TreeViewColumn(
                    "play",
                    _("Launch"),
                    GeodeGtk.CellRendererText(
                        "cell_play",
                        index=Columns.List.PLAYED,
                        padding=(4, 4),
                    ),
                    sort_column_id=Columns.List.PLAYED,
                ),
                GeodeGtk.TreeViewColumn(
                    "last_play",
                    _("Last launch"),
                    GeodeGtk.CellRendererText(
                        "cell_last_play",
                        alignment=(0, .5),
                        index=Columns.List.LAST_PLAY,
                        padding=(4, 0),
                    ),
                    GeodeGtk.CellRendererText(
                        "cell_last_launch_time",
                        alignment=(1, .5),
                        index=Columns.List.LAST_TIME_PLAY,
                        padding=(4, 0),
                    ),
                    sort_column_id=Columns.List.LAST_PLAY,
                ),
                GeodeGtk.TreeViewColumn(
                    "play_time",
                    _("Play time"),
                    GeodeGtk.CellRendererText(
                        "cell_last_launch",
                        index=Columns.List.TIME_PLAY,
                        padding=(4, 0),
                    ),
                    sort_column_id=Columns.List.TIME_PLAY,
                ),
                GeodeGtk.TreeViewColumn(
                    "score",
                    _("Score"),
                    *[
                        GeodeGtk.CellRendererPixbuf(
                            f"cell_score_{index}",
                            expand=True,
                            padding=(2, 0),
                        ) for index in range(1, 6)
                    ],
                    cell_data_func=self.on_update_cells,
                    sort_column_id=Columns.List.SCORE,
                ),
                GeodeGtk.TreeViewColumn(
                    "installed",
                    _("Installed"),
                    GeodeGtk.CellRendererText(
                        "cell_installed",
                        index=Columns.List.INSTALLED,
                        padding=(4, 0),
                    ),
                    sort_column_id=Columns.List.INSTALLED,
                ),
                GeodeGtk.TreeViewColumn(
                    "flags",
                    _("Flags"),
                    GeodeGtk.CellRendererPixbuf(
                        "cell_customize",
                        expand=True,
                        index=Columns.List.PARAMETER,
                        mode="icon-name",
                        padding=(2, 0),
                    ),
                    GeodeGtk.CellRendererPixbuf(
                        "cell_screenshot",
                        expand=True,
                        index=Columns.List.SCREENSHOT,
                        mode="icon-name",
                        padding=(2, 0),
                    ),
                    GeodeGtk.CellRendererPixbuf(
                        "cell_savestate",
                        expand=True,
                        index=Columns.List.SAVESTATE,
                        mode="icon-name",
                        padding=(2, 0),
                    ),
                ),
                enable_search=False,
                filterable=True,
                has_tooltip=True,
                search_column=Columns.List.NAME,
                show_expanders=False,
                sorterable=True,
                sort_func=interface.on_sort_games_view,
                visible_func=interface.check_game_is_visible,
            )
        )

    def append_item(self, console, game):
        """ See geode_gem.ui.view.CommonGamesView.append_item

        Parameters
        ----------
        console : geode_gem.engine.console.Console
            Console instance
        game : geode_gem.engine.game.Game
            Game instance
        """

        thumbnail = self.interface.get_pixbuf_from_cache(
            "games", 22, game.id, game.cover)
        if thumbnail is None:
            thumbnail = self.interface.icons_games_views.get("treeview")

        row_data = [
            self.interface.get_ui_icon(
                Columns.List.FAVORITE, game.favorite),
            self.interface.get_ui_icon(
                Columns.List.MULTIPLAYER, game.multiplayer),
            self.interface.get_ui_icon(
                Columns.List.FINISH, game.finish),
            game.name,
            game.played,
            (string_from_date(game.last_launch_date)
                if not game.last_launch_date.strftime("%d%m%y") == "010101"
                else None),
            (string_from_time(game.last_launch_time)
                if not game.last_launch_time == timedelta() else None),
            (string_from_time(game.play_time)
                if not game.play_time == timedelta() else None),
            game.score,
            string_from_date(game.installed) if game.installed else None,
            self.interface.get_ui_icon(
                Columns.List.PARAMETER,
                not game.emulator == console.emulator or game.default),
            self.interface.get_ui_icon(
                Columns.List.SCREENSHOT, game.screenshots),
            self.interface.get_ui_icon(
                Columns.List.SAVESTATE, game.savestates),
            game,
            thumbnail,
        ]

        return super().append_item(game.id, row_data)

    def on_update_cells(self, column, cell, model, treeiter, *args):
        """ Manage specific columns behavior during games adding

        Parameters
        ----------
        column : Gtk.TreeViewColumn
            Treeview column which contains cell
        cell : Gtk.CellRenderer
            Cell that is being rendered by column
        model : Gtk.TreeModel
            Rendered model
        treeiter : Gtk.TreeIter
            Rendered row
        """

        if not column.get_visible():
            return

        if cell.identifier.startswith("cell_score"):
            score = model.get_value(treeiter, Columns.List.SCORE)

            for index in range(1, 6):
                widget = self.view.get_widget(f"cell_score_{index}")

                icon_name = self.interface.get_ui_icon(
                    Columns.List.SCORE, score >= index)

                widget.set_sensitive(score >= index)
                widget.set_property("icon-name", icon_name)


class GeodeGEMIconView(CommonGamesView):

    def __init__(self, interface):
        """ Constructor

        Parameters
        ----------
        interface : geode_gem.ui.interface.MainWindow
            Main interface instance
        """

        CommonGamesView.__init__(
            self,
            "iconview",
            interface,
            GeodeGtk.IconView(
                "games",
                Gtk.ListStore(
                    GdkPixbuf.Pixbuf,   # Cover icon
                    str,                # Name
                    object              # Game object
                ),
                pixbuf_column=0,
                text_column=1,
                item_width=96,
                spacing=6,
                filterable=True,
                has_tooltip=True,
                sorterable=False,
                sorting_column=1,
                visible_func=interface.check_game_is_visible,
            )
        )

    def append_item(self, console, game):
        """ See geode_gem.ui.view.CommonGamesView.append_item

        Parameters
        ----------
        console : geode_gem.engine.console.Console
            Console instance
        game : geode_gem.engine.game.Game
            Game instance
        """

        thumbnail = self.interface.get_pixbuf_from_cache(
            "games", 96, game.id, game.cover)
        if thumbnail is None:
            thumbnail = self.interface.icons_games_views.get("iconview")

        return super().append_item(game.id, [thumbnail, game.name, game])
