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

TRANSLATIONS=(fr es)

LOCALE_PATH="gem/data/i18n"

# ------------------------------------------------------------------------------
#   Check default files
# ------------------------------------------------------------------------------

echo "[INFO] Check translations…"

# Create .pot files
for LANG in "${TRANSLATIONS[@]}" ; do
    LANG_PATH="${LOCALE_PATH}/${LANG}"

    if [ ! -d "${LANG_PATH}" ] ; then
        mkdir -p "${LANG_PATH}"
    fi

    if [ ! -f "${LANG_PATH}/gem.po" ] ; then
        echo "[INFO] Generate translation for ${LANG}"

        msginit \
            --input="${LOCALE_PATH}/gem.pot" \
            --output="${LANG_PATH}/gem.po"
    fi
done

# ------------------------------------------------------------------------------
#   Generate translations
# ------------------------------------------------------------------------------

echo "[INFO] Generate translations…"

# Generate .po files
xgettext \
    --package-name=gem \
    --package-version="0.10.2" \
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

for LANG in "${TRANSLATIONS[@]}" ; do
    echo "[INFO] Merge translation for ${LANG}"
    LANG_PATH="${LOCALE_PATH}/${LANG}"

    msgmerge \
        --verbose \
        --update \
        --sort-output \
        "${LANG_PATH}/gem.po" \
        "${LOCALE_PATH}/gem.pot"

    if [ ! -d "${LANG_PATH}/LC_MESSAGES" ] ; then
        mkdir -p "${LANG_PATH}/LC_MESSAGES"
    fi

    echo "[INFO] Update translation for ${LANG}"

    msgfmt \
        "${LANG_PATH}/gem.po" \
        --output="${LANG_PATH}/LC_MESSAGES/gem.mo"
done
