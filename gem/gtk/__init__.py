# ------------------------------------------------------------------------------
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License.
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

# ------------------------------------------------------------------------------
#   Modules
# ------------------------------------------------------------------------------

# Filesystem
from os.path import expanduser
from os.path import join as path_join

# ------------------------------------------------------------------------------
#   Modules - XDG
# ------------------------------------------------------------------------------

try:
    from xdg.BaseDirectory import xdg_data_home
    from xdg.BaseDirectory import xdg_config_home

except ImportError as error:
    from os import environ

    if "XDG_DATA_HOME" in environ:
        xdg_data_home = environ["XDG_DATA_HOME"]
    else:
        xdg_data_home = expanduser("~/.local/share")

    if "XDG_CONFIG_HOME" in environ:
        xdg_config_home = environ["XDG_CONFIG_HOME"]
    else:
        xdg_config_home = expanduser("~/.config")

# ------------------------------------------------------------------------------
#   Class
# ------------------------------------------------------------------------------

class Documents:
    Desktop     = "template.desktop"

class Folders:
    Apps        = path_join(expanduser(xdg_data_home), "applications")

class Icons:
    Ext         = "png"
    # Actions
    Quit        = "application-exit"
    Properties  = "document-properties"
    Open        = "document-open"
    Save        = "document-save"
    Clear       = "edit-clear"
    Copy        = "edit-copy"
    Delete      = "edit-delete"
    Find        = "edit-find"
    Paste       = "edit-paste"
    Bottom      = "go-bottom"
    Down        = "go-down"
    First       = "go-first"
    Home        = "go-home"
    Jump        = "go-jump"
    Last        = "go-last"
    Next        = "go-next"
    Previous    = "go-previous"
    Top         = "go-top"
    Up          = "go-up"
    About       = "help-about"
    Content     = "help-contents"
    Faq         = "help-faq"
    Add         = "list-add"
    Remove      = "list-remove"
    Launch      = "media-playback-start"
    Menu        = "open-menu" # Not standard
    Stop        = "process-stop"
    Checkspell  = "tools-check-spelling"
    Fullscreen  = "view-fullscreen"
    Restore     = "view-restore"
    Close       = "window-close"
    ZoomFit     = "zoom-fit-best"
    ZoomIn      = "zoom-in"
    Zoom        = "zoom-original"
    ZoomOut     = "zoom-out"
    # Applications
    Editor      = "accessories-text-editor"
    Keyboard    = "preferences-desktop-keyboard"
    Terminal    = "utilities-terminal"
    Help        = "system-help"
    # Categories
    Desktop     = "preferences-desktop"
    Other       = "applications-other"
    System      = "preferences-system"
    # Devices
    Gaming      = "input-gaming"
    Video       = "video-display"
    # Emblems
    Document    = "emblem-documents"
    Download    = "emblem-downloads"
    Favorite    = "emblem-favorite"
    Important   = "emblem-important"
    Photos      = "emblem-photos"
    Users       = "system-users" # Not standard
    # Faces
    Monkey      = "face-monkey"
    Sad         = "face-sad"
    SmileBig    = "face-smile-big"
    # Mimes
    Text        = "text-x-generic"
    Image       = "image-x-generic"
    # Places
    Folder      = "folder"
    # Status
    Error       = "dialog-error"
    Warning     = "dialog-warning"
    Question    = "dialog-question"
    Information = "dialog-information"
    Loading     = "image-loading"
    Missing     = "image-missing"


class Columns:
    Favorite        = 0
    Icon            = 1
    Name            = 2
    Played          = 3
    LastPlay        = 4
    LastTimePlay    = 5
    TimePlay        = 6
    Installed       = 7
    Except          = 8
    Snapshots       = 9
    Multiplayer     = 10
    Save            = 11
    Filename        = 12