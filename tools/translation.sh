#!/bin/bash
# ------------------------------------------------------------------------------
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

translation=(fr es)

# ------------------------------------------------------------------------------
#   Check default files
# ------------------------------------------------------------------------------

echo "[INFO] Check translations…"

# Create .pot files
for lang in "${translation[@]}" ; do
    if [ ! -d "gem/i18n/$lang" ] ; then
        mkdir -p "gem/i18n/$lang"
    fi

    if [ ! -f "gem/i18n/$lang/gem.po" ] ; then
        echo "[INFO] Generate translation for ${lang}"

        msginit \
            --input="gem/i18n/gem.pot" \
            --output="gem/i18n/$lang/gem.po"
    fi
done

# ------------------------------------------------------------------------------
#   Generate translations
# ------------------------------------------------------------------------------

echo "[INFO] Generate translations…"

# Generate .po files
xgettext \
    --package-name=gem \
    --package-version="0.10.1" \
    --copyright-holder="Kawa-Team" \
    --from-code="UTF-8" \
    --language="Python" \
    --indent \
    --keyword="_" \
    --omit-header \
    --sort-output \
    --strict \
    --output=gem/i18n/gem.pot \
    gem/*.py \
    gem/engine/*.py \
    gem/ui/*.py \
    gem/ui/dialog/*.py \
    gem/ui/preferences/*.py \
    gem/ui/widgets/*.py

# ------------------------------------------------------------------------------
#   Update files
# ------------------------------------------------------------------------------

echo "[INFO] Update translations…"

for lang in "${translation[@]}" ; do
    echo "[INFO] Merge translation for ${lang}"

    msgmerge \
        --verbose \
        --update \
        --sort-output \
        gem/i18n/$lang/gem.po \
        gem/i18n/gem.pot

    if [ ! -d gem/i18n/$lang/LC_MESSAGES ] ; then
        mkdir -p gem/i18n/$lang/LC_MESSAGES
    fi

    echo "[INFO] Update translation for ${lang}"

    msgfmt \
        gem/i18n/$lang/gem.po \
        --output=gem/i18n/$lang/LC_MESSAGES/gem.mo
done
