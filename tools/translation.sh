#!/usr/bin/env bash
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

LOCALE_PATH="geode_gem/data/i18n"

# ------------------------------------------------------------------------------
#   Functions
# ------------------------------------------------------------------------------

function update_project() {
    # Update the .pot file

    echo "[INFO] Generate translation template…"
    xgettext \
        --package-name="Geode-GEM" \
        --package-version="0.10.2" \
        --copyright-holder="Kawa-Team" \
        --from-code="UTF-8" \
        --language="Python" \
        --add-location \
        --indent \
        --keyword="_" \
        --omit-header \
        --sort-output \
        --strict \
        --output="${LOCALE_PATH}/gem.pot" \
        geode_gem/*.py \
        geode_gem/engine/*.py \
        geode_gem/ui/*.py \
        geode_gem/ui/dialog/*.py \
        geode_gem/ui/preferences/*.py \
        geode_gem/ui/widgets/*.py
}

function update_locale() {
    # Update the .po file for a specific locale

    LANG_PATH="${LOCALE_PATH}/${1}"

    if [ ! -d "${LANG_PATH}" ] ; then
        mkdir -p "${LANG_PATH}"
    fi

    if [ ! -f "${LANG_PATH}/gem.po" ] ; then
        echo "[INFO] Initialize translation for ${1}"
        msginit \
            --no-translator \
            --input="${LOCALE_PATH}/gem.pot" \
            --output="${LANG_PATH}/gem.po"
    fi

    echo "[INFO] Update translation for ${1}"
    msgmerge \
        --verbose \
        --update \
        --sort-output \
        "${LANG_PATH}/gem.po" \
        "${LOCALE_PATH}/gem.pot"
}

function generate_locale() {
    # Generate the .mo file for a specific locale

    LANG_PATH="${LOCALE_PATH}/${1}"

    if [ ! -d "${LANG_PATH}/LC_MESSAGES" ] ; then
        mkdir -p "${LANG_PATH}/LC_MESSAGES"
    fi

    echo "[INFO] Merge translation for ${1}"
    msgfmt \
        "${LANG_PATH}/gem.po" \
        --output="${LANG_PATH}/LC_MESSAGES/gem.mo"
}

# ------------------------------------------------------------------------------
#   Launcher
# ------------------------------------------------------------------------------

if [ -z $@ ] ; then
    echo "Usage: $(basename $0) update|merge"
    exit 1
fi

case "${1}" in
    update)
        update_project

        for LANG in "${TRANSLATIONS[@]}" ; do
            update_locale "${LANG}"
        done
        ;;

    merge)
        for LANG in "${TRANSLATIONS[@]}" ; do
            generate_locale "${LANG}"
        done
        ;;
esac
