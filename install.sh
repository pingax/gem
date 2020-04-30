#!/usr/bin/env bash
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

if [ -z "$BASH_VERSION" ]; then
    bash $0 $@
    exit $?
fi

if [ $EUID -ne 0 ] ; then
    echo "Need to use root account to install GEM"

else
    PREFIX="${PREFIX:=/usr}"

    # ----------------------------------------
    #   Setup script
    # ----------------------------------------

    echo -e "\033[1m==> Install GEM\033[0m"
    python3 setup.py install --root="/" --prefix="${PREFIX}" -O1

    echo -e "\033[1m==> Remove build folders\033[0m"
    rm -Rfv "build" "dist" "gem.egg-info"

    # ----------------------------------------
    #   Application data
    # ----------------------------------------

    echo -e "\033[1m==> Install icon files\033[0m"
    mkdir -pv "${PREFIX}/share/pixmaps/"
    cp -v "geode_gem/data/desktop/gem.svg" \
          "${PREFIX}/share/pixmaps/"

    mkdir -pv "${PREFIX}/share/icons/hicolor/scalable/apps/"
    cp -v "geode_gem/data/desktop/gem.svg" \
          "${PREFIX}/share/icons/hicolor/scalable/apps/"

    echo -e "\033[1m==> Install desktop file\033[0m"
    mkdir -pv "${PREFIX}/share/applications/"
    cp -v "geode_gem/data/desktop/gem.desktop" \
          "${PREFIX}/share/applications/"
fi
