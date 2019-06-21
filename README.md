Graphical Emulators Manager
===========================

GEM (Graphical Emulators Manager) is a GTK+ Graphical User Interface (GUI) for
GNU/Linux which allows you to easily manage your emulators. This software aims
to stay the simplest.

![GEM main interface](preview.jpg)

More informations on [GEM website](https://gem.tuxfamily.org/).

Licenses
--------

GEM is available under [GPLv3 license](https://www.gnu.org/licenses/gpl-3.0.html).

GEM logo is available under [Free Art License](http://artlibre.org/licence/lal/en/).

Consoles icons come from [Evan-Amos](https://commons.wikimedia.org/wiki/User:Evan-Amos)
gallery and are available under [Public Domain](https://en.wikipedia.org/wiki/Public_domain)
license.

More informations about available emulators licenses [here](docs/LICENSE.emulators.md).

Authors
-------

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

[Informations](https://dev.getsol.us/source/gem/)

Dependencies
------------

* file
* gtk+3
* python3 >= 3.5
* python3-gobject
* python3-setuptools
* xdg-utils

### Optional

* gnome-icon-theme
* gnome-icon-theme-symbolic
* gtksourceview
* python3-xdg

Retrieve source code
--------------------

To retrieve source code, you just need to use git with:

```
git clone https://framagit.org/PacMiam/gem.git
```

Or directly from [GEM download repository](https://download.tuxfamily.org/gem/releases/).

Running GEM
-----------

Go to the GEM source code root folder and launch the following command:

```
$ python3 -m gem
```

It's possible to set the configuration folders with --cache, --config and
--local arguments:

```
$ python3 -m gem --cache ~/.cache --config ~/.config --local ~/.local/share
```

Installation
------------

An installation script is available to help you to install GEM. You just need to
launch the following command with root privilege:

```
# ./install.sh
```

This script install GEM with setuptools and setup a **gem-ui** script under
/usr/bin.

GEM is also available in your desktop environment menu under **Games** category.

Emulators
---------

Default configuration files allow you to use the following emulators out of the
box:

* Mednafen
* Stella (Atari 2600)
* Hatari (Atari ST)
* Fceux (Nintendo NES)
* Nestopia (Nintendo NES)
* Mupen64plus (Nintendo 64)
* Desmume (Nintendo DS)
* Dolphin (Nintendo GameCube et Nintendo Wii)
* Gens (Sega Genesis)
* DosBOX
