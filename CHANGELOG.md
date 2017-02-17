# GEM Changelog

## Version 0.6 - Magicball

* Add the possibility to switch ui theme between dark and light
* Add an icon in consoles combobox to alert user when a binary is missing
* Add the possibility to use basename for emulator binary instead of full path
* Add &lt;conf_path&gt;, &lt;rom_path&gt;, &lt;rom_name&gt;, &lt;rom_file&gt; to default argument
* Add the possibility to create notes pad for a game
* Add translucent icons into games treeview
* Add debug mode
* Add a new logo based on GNOME input-gaming icon
* Move some items in game menu to submenu
* Fix cannot open viewer when rom filename has many dots
* Fix cannot open parameters dialog when data from database are empty
* Fix avoid RecursionError when use forward_search
* Fix cannot see roms folder with ~ in path
* Fix set icons size to 22 pixels instead of 24 pixels
* Fix drag a game to an extern application send the good file-uri

## Version 0.5.2 - Flintheart Glomgold (29 Nov, 2016)

* Fix cannot launch GEM from a fresh installation
* Fix show errors when use emulator configurator with missing binary

## Version 0.5.1 - Magica De Spell (5 Nov, 2016)

* Change default rom folders for consoles.conf
* Change default shortcut for "Remove from database" from Delete to Control+D
* Fix forget to set shortcut for "Launch" entry in game menu
* Fix use correct data for version and code name
* Fix command generator not use specific default argument

## Version 0.5 - Rich Duck (25 Oct, 2016)

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

## Version 0.4 - Blue Bomber (20 Aug, 2016)

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

## Version 0.3 - Fast Hedgehog (29 Feb, 2016)

* Improve database module to allow quick databases creation with configuration files.
* Add a system to convert old database (version &lt; 0.3) to new schema.
* Add few explanations on consoles and emulators preferences.
* Add possibility to configure shortcuts in preferences.
* Add possibility to hide output tab and statusbar in preferences.
* Add a function to append missing data in configuration file.
* Add possibility to set a specific emulator for a ROM file.
* Separate SNK NeoGeo Pocket and SNK NeoGeo Pocket Color consoles
* Move exceptions data into database.
* Remove "date" option in main configuration file.
* Fix game launcher which can run missing binaries.

## Version 0.2 - Jumping Plumber (03 Feb, 2016)

* Extend main toolbar with common widgets.
* Restructure configuration files to be more simple.
* Add logging module to get some usefull output.
* Create a preferences window to configure GEM.
* Add Stella, Hatari, Zsnes, Fceux and Dolphin emulators.
* Add Nintendo GameCube, Nintendo Wii, NEC PC-Engine, Sega Game Gear, SNK NeoGeo Pocket and MAME consoles

## Version 0.1 (16 May, 2015)

* First stable release
