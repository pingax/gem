#!/bin/bash

translation=(fr es)

# Create .pot files
for lang in "${translation[@]}" ; do
    if [ ! -d gem/i18n/$lang ] ; then
        mkdir -p gem/i18n/$lang
    fi

    if [ ! -f gem/i18n/$lang/gem.po ] ; then
        msginit -i gem/i18n/gem.pot -o gem/i18n/$lang/gem.po
    fi
done

# Generate .po files
xgettext -k_ -i --strict -s --omit-header -o gem/i18n/gem.pot \
    --copyright-holder="Kawa Team" --package-name=gem \
    --package-version="0.6.1" --from-code="utf-8" gem/*.py

for lang in "${translation[@]}" ; do
    msgmerge -s -U gem/i18n/$lang/gem.po gem/i18n/gem.pot

    if [ ! -d gem/i18n/$lang/LC_MESSAGES ] ; then
        mkdir -p gem/i18n/$lang/LC_MESSAGES
    fi

    msgfmt gem/i18n/$lang/gem.po -o gem/i18n/$lang/LC_MESSAGES/gem.mo
done
