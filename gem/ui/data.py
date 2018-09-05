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

# GEM
from gem.engine import *
from gem.engine.lib import *

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
    Edit        = "document-edit"
    Open        = "document-open"
    Save        = "document-save"
    SaveAs      = "document-save-as"
    Send        = "document-send"
    Clear       = "edit-clear"
    Copy        = "edit-copy"
    Delete      = "edit-delete"
    Find        = "edit-find"
    Paste       = "edit-paste"
    Undo        = "edit-undo"
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
    AddText     = "insert-text"
    Add         = "list-add"
    Remove      = "list-remove"
    Launch      = "media-playback-start"
    Menu        = "open-menu" # Not standard
    Stop        = "process-stop"
    Checkspell  = "tools-check-spelling"
    Fullscreen  = "view-fullscreen"
    Refresh     = "view-refresh"
    Restore     = "view-restore"
    ViewMore    = "view-more" # Not standard
    Close       = "window-close"
    ZoomFit     = "zoom-fit-best"
    ZoomIn      = "zoom-in"
    Zoom        = "zoom-original"
    ZoomOut     = "zoom-out"
    # Applications
    Editor      = "accessories-text-editor"
    Addon       = "application-x-addon" # Not standard
    Keyboard    = "preferences-desktop-keyboard"
    Terminal    = "utilities-terminal"
    Monitor     = "utilities-system-monitor"
    Help        = "system-help"
    # Categories
    Desktop     = "preferences-desktop"
    Preferences = "preferences-other"
    Other       = "applications-other"
    System      = "preferences-system"
    # Devices
    Camera      = "camera-photo"
    Floppy      = "media-floppy"
    Gaming      = "input-gaming"
    Video       = "video-display"
    # Emblems
    Document    = "emblem-documents"
    Download    = "emblem-downloads"
    Favorite    = "emblem-favorite"
    Important   = "emblem-important"
    Photos      = "emblem-photos"
    Sync        = "emblem-synchronizing"
    Users       = "system-users" # Not standard
    # Faces
    Monkey      = "face-monkey"
    Sad         = "face-sad"
    Smile       = "face-smile"
    SmileBig    = "face-smile-big"
    Uncertain   = "face-uncertain"
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
    Password    = "dialog-password"
    Loading     = "image-loading"
    Missing     = "image-missing"
    NoStarred   = "non-starred" # Not standard
    Starred     = "starred" # Not standard
    # View
    List        = "view-list" # Not standard
    Grid        = "view-grid" # Not standard

    # This class is filled with Icons values in interface initialization
    class Symbolic:
        pass

class Columns:
    Favorite        = 0
    Multiplayer     = 1
    Finish          = 2
    Name            = 3
    Played          = 4
    LastPlay        = 5
    LastTimePlay    = 6
    TimePlay        = 7
    Score           = 8
    Installed       = 9
    Except          = 10
    Snapshots       = 11
    Save            = 12
    Object          = 13
