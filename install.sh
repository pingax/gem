#!/bin/bash

if [ $UID == 0 ] ; then
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

else
    echo "Need to use root account to install GEM"
fi
