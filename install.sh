#!/usr/bin/env bash

if [ -z "$BASH_VERSION" ]; then
    bash $0 $@
    exit $?
fi

if [ $EUID -ne 0 ] ; then
    echo "Need to use root account to install GEM"

else
    echo "==> Install GEM"
    python3 setup.py install

    echo "==> Remove build folders"
    rm -Rf build dist gem.egg-info

    echo "==> Install icon file"
    mkdir -p /usr/share/pixmaps/
    cp gem/ui/icons/gem.svg /usr/share/pixmaps/

    echo "==> Install desktop file"
    mkdir -p /usr/share/applications/
    cp gem.desktop /usr/share/applications/
fi
