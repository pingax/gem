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

# Datetime
from datetime import date
from datetime import time
from datetime import datetime
from datetime import timedelta

# Filesystem
from os import W_OK
from os import mkdir
from os import access
from os import getpid
from os import remove
from os import makedirs

from os.path import isdir
from os.path import isfile
from os.path import exists
from os.path import dirname
from os.path import basename
from os.path import getctime
from os.path import splitext
from os.path import expanduser
from os.path import join as path_join

from glob import glob

from copy import deepcopy

from shutil import move
from shutil import copy2 as copy

# Logging
import logging

# System
from os import environ

from sys import exit as sys_exit

# Translation
from gettext import textdomain
from gettext import bindtextdomain
