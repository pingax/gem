# Graphical Emulators Manager

GEM (Graphical Emulators Manager) is a GTK+ Graphical User Interface (GUI) for
GNU/Linux which allows you to easily manage your emulators. This software aims
to stay the simplest.

![GEM main interface](https://gem.tuxfamily.org/data/medias/preview.tb.png)

GEM is available under [GPLv3 license](http://www.gnu.org/licenses/gpl-3.0.html).

More informations on [GEM website](https://gem.tuxfamily.org/).

## Authors

### Developpers

* PacMiam (Lubert Aurélien)

### Translators

* French: PacMiam (Lubert Aurélien)
* Spanish: DarkNekros (José Luis)

### Packages

#### Frugalware

Thanks to Pingax !

```
$ pacman-g2 -S gem
```

[Informations](https://frugalware.org/packages/219539)

#### Solus

Thanks to Devil505 !

```
$ eopkg install gem
```

[Informations](https://dev.solus-project.com/source/gem/)

### Icons

* Interface: [Tango](http://tango.freedesktop.org/Tango_Desktop_Project)
* Emulators: [Gelide](http://gelide.sourceforge.net/index.php?lang=en) (for most of them)
* Consoles: [Evan-Amos](https://commons.wikimedia.org/wiki/User:Evan-Amos)

## Dependencies

* gtk+3
* python3
* python3-magic
* python3-gobject
* python3-setuptools

### Optional

* gnome-icon-theme
* gnome-icon-theme-symbolic
* gtksourceview
* python3-xdg

## Retrieve source code

To retrieve source code, you just need to use git with:

```
git clone https://framagit.org/PacMiam/gem.git
```

Or directly from [GEM download repository](https://download.tuxfamily.org/gem/releases/).

## Running GEM

Go to the GEM source code root folder and launch the following command:

```
$ python3 -m gem
```

It's possible to set the configuration folders with --config and --local
arguments:

```
$ python3 -m gem --config ~/.config/gem --local ~/.local/gem
```

Note: GEM not create the specified folders by default. This behavior is
available with the --create-folders argument.

## Installation

An installation script is available to help you to install GEM. You just need to
launch the following command with root privilege:

```
# ./install.sh
```

This script install GEM with setuptools and setup a **gem-ui** script under
/usr/bin.

GEM is also available in your desktop environment menu under **Games** category.

## Emulators

Default configuration files allow you to use the following emulators out of the
box:

* Mame
* Mednafen
* Stella (Atari 2600)
* Hatari (Atari ST)
* Fceux (Nintendo NES)
* Nestopia (Nintendo NES)
* Zsnes (Nintendo SNES)
* Snes9x (Nintendo SNES)
* Mupen64plus (Nintendo 64)
* VisualBoyAdvance (Nintendo GBA)
* Desmume (Nintendo DS)
* Dolphin (Nintendo GameCube et Nintendo Wii)
* Gens (Sega Genesis)
