GEM Changelog
=============

Version 0.10.1 - Mr. Resetti
----------------------------

### Setup

* Add `librsvg` system depend

### Fix

* Cannot retrieve resources with Python 3.7
* Cannot validate the rename dialog entry with Return key
* Click inside the empty area treeview, select the first game without showing his informations

Version 0.10.0 - Forest Life (28 Aug, 2019)
-------------------------------------------

### Data

* Add emulators licenses file
* Switch 'Nintendo SNES' emulator to mednafen from consoles.conf
* Switch 'SEGA Megadrive' emulator to mednafen from consoles.conf
* Remove consoles `old` folder
* Remove emulators icons
* Remove MAME console
* Remove Snes9x, MAME, visualBoyAdvance and ZSNES emulators from emulators.conf
* Move `gem.svg` and `gem.desktop` into `/data`

### Engine

* Add cover field to game database
* Add score field to game database
* Add installed date field to game object
* Add favorite field to console object
* Add `GEM.get_game_tags` function to API
* Add `GEM.update_console` function to API
* Add `GEM.update_emulator` function to API
* Add `Console.add_game` function to API
* Add `Console.delete_game` function to API
* Add dynamic files parameter to `write_data` function to write only some configuration file
* Allow to set specific configuration paths in constructor parameters
* Modify `GEM.add_emulator` to return the new emulator
* Modify `GEM.add_console` to return the new console

### GTK+ interface

* New dependency → xdg-utils
* New logo
* Add the statusbar for default theme and rewrite his contents
* Add a tags selector to game properties dialog
* Add more informations into game sidebar
* Add some tooltips for date labels in game sidebar
* Add a background color to filter button when some filters are active
* Add to remove the desktop file when removing a game
* Add a dialog to alert the user when a GEM instance already exists
* Add a maintenance dialog to replace the clean database dialog
* Add a cache folder to save games and consoles icons
* Add a thumbnail next to game name in games treeview
* Allow to reorder games treeview columns
* Allow to drag the sidebar image to another application
* Allow to duplicate a game and his data
* Allow to sort games list treeview
* Allow to import or export game note
* Allow to configure console from console context menu in main interface
* Allow to remove a console from console context menu in main interface
* Allow to configure emulator from console context menu in main interface
* Allow to add an emulator or a console from console main menu in main interface
* Allow to open games directory path from console main menu in main interface
* Allow to copy games directory path from console main menu in main interface
* Allow to restore sidebars position during startup
* Allow to change sidebar position from main menu in main interface
* Allow to edit game file when the mime type is `text/*`
* Avoid to save consoles and emulators before apply changes in preferences
* Restore GTK+ menuitem behavior to main and game menus
* Restore old dialog buttons behavior to both themes
* Restore old renaming system based on dialog window
* Improve drag & drop system
* Fix wrong object set during drag and drop process
* Fix missing global shortcuts in default theme
* Fix game tooltip not update after game renaming
* Fix shortcuts not updated after preferences modifications
* Fix notes are not correctly close when closing application
* Fix remove game note when the user save an empty text buffer
* Fix console without icon raise TypeError exceptions
* Fix disable consoles selector when no console available
* Fix wrong treeiter used when games list was filtered
* Fix a console is selected before the last used console selection with the 'load_console_startup' option
* Fix loose file selection in icons file selector when switch from 'Library' to 'File'

### Launcher

* Add --cache argument to specify an icons cache folder (Default: $XDG_CACHE_HOME)
* Move consoles icons from `icons/consoles` to `icons` in local folder ($XDG_DATA_HOME/gem)
* Remove --create-folders argument

Version 0.9.1 - Lavos (17 Feb, 2018)
------------------------------------

### GTK+ interface

* Fix crash when launching mednafen memory file dialog

Version 0.9 - Frog Knight (21 Jan, 2018)
----------------------------------------

### Engine

* Add `GEM.get_games` function to API
* Add `GEM.get_consoles` function to API
* Add `GEM.get_emulators` function to API
* Add `Game.new` static function to API
* Add `Game.reset` function to API
* Add finish flag field
* Add console recursive mode field
* Add environment variables management from configuration file
* Fix wrong type for play_time and last_launch_time in api
* Fix reset a game not remove it from database
* Fix cannot check game with [ and ] in name

### GTK+ interface

* Add current screenshot path in screenshots viewer
* Add screenshots viewer dialog size storage to gem.conf
* Add drag system to screenshots viewer dialog to share image with applications
* Add an infobar to inform user for incorrect values without open a dialog
* Add a new filter system
* Add a tooltip for games treeview
* Add a console reminder option when use D&D
* Add a refresh buffer option for log dialogs
* Add a games placeholder when no game available
* Add classic theme appearance to dialog
* Add a statistic field to game properties dialog
* Add a environment variables field to game properties dialog
* Update interface to support some design from GNOME Human Interface Guidelines
* Fix wrong parameter for dolphin-emu
* Fix wrong exception in icon_from_data

Version 0.8 - Shadow Blade (26 July, 2017)
------------------------------------------

* Add an option to hide game in games list with specific regex
* Add a sidebar which show game informations and a random screenshot
* Add a tags system for game
* Add a GameID in game parameters for Dolphin emulator
* Add Solus package template in contrib folder - Thanks Devil505
* Update Snes9x
* Update Dolphin
* Fix reload console games when a roms has been droped
* Fix cannot drop a game which can be on multiple consoles (like .bin extension)
* Fix set emulator.id in consoles.conf instead of emulator.name
* Fix wrong variable in get_emulator, console instead of emulator
* Fix write data in api set empty list as None
* Fix send emulator object in console.as_dict instead of emulator.name
* Fix icons viewer not load file selector by default for absolute icon path
* Fix cannot remove options from emulator in preferences
* Fix editor dialog which has a wrong behavior with modified buffer
* Fix editor dialog which crash without GtkSource
* Fix create missing consoles roms folders

Version 0.7.1 - Count Dracula (13 June, 2017)
---------------------------------------------

* Fix wrong generate command for emulator without default arguments

Version 0.7 - Vampire hunter (08 June, 2017)
--------------------------------------------

* Add an API to manage emulators, consoles and games
* Add the backup memory type file generation for Mednafen
* Add Sony Playstation console
* Rewrite interface into python scripts instead of glade files
* Fix game with custom name won't work correctly in self.__on_game_launch
* Fix shortcuts in preferences are not store correctly in main configuration

Version 0.6.1 - Dr. Funfrock (30 Mar, 2017)
-------------------------------------------

* Add windows size memorization
* Add a lock to avoid multi GEM instances
* Fix block preferences when some games are launched
* Fix manage preferences window as Dialog when open from GEM window
* Fix preferences window crash when use drag and drop in main window while preferences is open
* Fix specify bash for install.sh
* Fix random segfault when a game terminate
* Fix cannot launch Exec command in generate menu entries when filepath has some spaces

Version 0.6 - Magicball (26 Feb, 2017)
--------------------------------------

* Add the possibility to switch ui theme between dark and light
* Add an icon in consoles combobox to alert user when a binary is missing
* Add the possibility to use basename for emulator binary instead of full path
* Add `<conf_path>`, `<rom_path>`, `<rom_name>`, `<rom_file>` to default argument
* Add the possibility to create notes pad for a game
* Add translucent icons into games treeview
* Add debug mode
* Add a new logo based on GNOME input-gaming icon
* Move multithreading as experimental option (desactivate by default)
* Move some items in game menu to submenu
* Fix cannot open viewer when rom filename has many dots
* Fix cannot open parameters dialog when data from database are empty
* Fix avoid RecursionError when use forward_search
* Fix cannot see roms folder with ~ in path
* Fix set icons size to 22 pixels instead of 24 pixels
* Fix drag a game to an extern application send the good file-uri

Version 0.5.2 - Flintheart Glomgold (29 Nov, 2016)
--------------------------------------------------

* Fix cannot launch GEM from a fresh installation
* Fix show errors when use emulator configurator with missing binary

Version 0.5.1 - Magica De Spell (5 Nov, 2016)
---------------------------------------------

* Change default rom folders for consoles.conf
* Change default shortcut for "Remove from database" from Delete to Control+D
* Fix forget to set shortcut for "Launch" entry in game menu
* Fix use correct data for version and code name
* Fix command generator not use specific default argument

Version 0.5 - Rich Duck (25 Oct, 2016)
--------------------------------------

* Add an entry in game and main menus to remove a ROM and his data.
* Add an entry in main menu to show GEM log.
* Add an argument to specify rom path in snap and save regex.
* Add a drag and drop system to install rom files.
* Add the possibility to use regex with filter entry.
* Add a multithreading support to launch multiple games as the same time.
* Add a desktop entry generator for games.
* Restore the possibility to rename emulators and consoles from preferences.
* Switch to GTK+3 and Python 3.x.
* Avoid to save as last console a console which is already save as last console.
* Save previous log file to gem.log.old.
* Show emulators icons in parameters and console dialogs
* Add nestopia to emulators.
* Fix wrong paths for log and editor windows.
* Fix wrong name in headerbar when rename a game.
* Fix old selection remain when reload interface.
* Fix hide output from xdg-open.
* Fix allow to validate an icon with double clicks in preferences.
* Fix wrong dialog size in some distributions.
* Fix cannot launch non native viewer if wrong binary.
* Fix hide error when use a wrong regex in filter entry.
* Fix write old value for emulators and consoles when a path not exists.

Version 0.4 - Blue Bomber (20 Aug, 2016)
----------------------------------------

* Add a native screenshots viewer.
* Add the possibility to choose between native and custom screenshots viewer.
* Add the possibility to hide some columns from roms view.
* Add an argument to reconstruct database.
* Add the possibility to copy current ROM directory path.
* Add the possibility to open current ROM directory path.
* Add a column which inform user when the rom has been add to hardrive.
* Add the possibility to change editor font from preferences.
* Add default icons which are loaded when there is no icons theme.
* Change the log system to save log per games in ~/.local/share/gem/logs/.
* Move database into ~/.local/share/gem folder insteal of ~/.config/gem.
* Using Control+C in terminal when a game is started, kill the game only.
* Restore games list after apply preferences modifications.
* Save last selected console in configuration to reload quickly during next launch.
* Fix cannot save informations from Mednafen configurator plugin.
* Fix duplicate version from gem database.
* Fix add missing shortcuts from gem.conf into preferences window.
* Fix wrong values in image viewer when use fit zoom.
* Fix wrong years values for last play date value.

Version 0.3 - Fast Hedgehog (29 Feb, 2016)
------------------------------------------

* Improve database module to allow quick databases creation with configuration files.
* Add a system to convert old database (version `< 0.3`) to new schema.
* Add few explanations on consoles and emulators preferences.
* Add possibility to configure shortcuts in preferences.
* Add possibility to hide output tab and statusbar in preferences.
* Add a function to append missing data in configuration file.
* Add possibility to set a specific emulator for a ROM file.
* Separate SNK NeoGeo Pocket and SNK NeoGeo Pocket Color consoles
* Move exceptions data into database.
* Remove "date" option in main configuration file.
* Fix game launcher which can run missing binaries.

Version 0.2 - Jumping Plumber (03 Feb, 2016)
--------------------------------------------

* Extend main toolbar with common widgets.
* Restructure configuration files to be more simple.
* Add logging module to get some usefull output.
* Create a preferences window to configure GEM.
* Add Stella, Hatari, Zsnes, Fceux and Dolphin emulators.
* Add Nintendo GameCube, Nintendo Wii, NEC PC-Engine, Sega Game Gear, SNK NeoGeo Pocket and MAME consoles

Version 0.1 (16 May, 2015)
--------------------------

* First stable release
