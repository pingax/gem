# Graphical Emulators Manager

## Présentation

GEM (Graphical Emulators Manager) est une interface qui à pour but de vous aider à gérer vos roms de jeux et vos émulateurs simplement et efficacement.

![Interface principale de GEM](https://gem.tuxfamily.org/data/medias/preview.tb.png)

GEM est disponible sous [licence GPLv3](http://www.gnu.org/licenses/gpl-3.0.html).

## Auteurs

### Développeurs

* PacMiam (Lubert Aurélien)

### Traducteurs

* Espagnol : DarkNekros (José Luis)

### Paquets

* Frugalware : Pingax
* Solus : Devil505

### Icônes

* Interface: [Tango](http://tango.freedesktop.org/Tango_Desktop_Project)
* Émulateurs: [Gelide](http://gelide.sourceforge.net/index.php?lang=en) (en partie)
* Consoles: [Evan-Amos](https://commons.wikimedia.org/wiki/User:Evan-Amos)

## Dépendances

* python3
* python3-gobject
* python3-setuptools
* python3-xdg

## Récupération des sources

Pour récupérer les sources, il est possible de passer par git via:

```
git clone https://framagit.org/PacMiam/gem.git
```

Ou directement depuis la zone de [téléchargements de GEM](https://download.tuxfamily.org/gem/releases/).

## Lancement

Une fois à la racine des sources de GEM, exécuter la commande suivante:

```
$ python3 -m gem.main
```

## Installation

Un script d'installation est disponible pour vous aider à installer GEM. Il suffit de lancer la commande suivante en mode root:

```
# ./install.sh
```

Un script sera placé sous le nom **gem-ui** dans le dossier /usr/bin. Une entrée de menu sera aussi créée, vous permettant de lancer GEM facilement.

## Émulateurs

La configuration de base vous permet d'utiliser les émulateurs suivants:

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
