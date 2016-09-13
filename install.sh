#!/bin/bash

if [ $UID == 0 ] ; then
    echo "==> Install GEM"
    python3 setup.py install

    echo "==> Remove build folders"
    rm -Rf build dist gem.egg-info

    echo "==> Install desktop file"
    cp gem.desktop /usr/share/applications/

else
    echo "Need to use root account to install GEM"
fi
