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
from datetime import timedelta

# Filesystem
from pathlib import Path

from shutil import copy2

# Regex
from re import sub

# System
from os import environ

from sys import version_info


# ------------------------------------------------------------------------------
#   Methods
# ------------------------------------------------------------------------------

def get_data(*args, egg="gem"):
    """ Provides easy access to data in a python egg or local folder

    This function search a path in a specific python egg or in local folder.
    The local folder is check before egg to allow quick debugging.

    Thanks Deluge :)

    Parameters
    ----------
    args : list
        File path as strings list
    egg : str, optional
        Python egg name (Default: gem)

    Returns
    -------
    pathlib.Path
        File path instance
    """

    path = Path(*args).expanduser()

    try:
        # Only available for Python >= 3.7
        from importlib.resources import path as resource_filename

        # Generate a module name based on egg name and file resource path
        module_name = '.'.join([egg, *args[:-1]])

        # Open resource to retrieve Path instance
        with resource_filename(module_name, args[-1]) as filepath:
            data = filepath.expanduser()

    except ImportError:
        from pkg_resources import resource_filename

        data = Path(resource_filename(egg, str(path))).expanduser()

    except Exception:
        data = path

    if data.exists():
        return data

    return path


def parse_timedelta(delta):
    """ Parse a deltatime to string

    Get a string from the deltatime formated as HH:MM:SS

    Parameters
    ----------
    delta : datetime.deltatime
        Deltatime to parse

    Returns
    -------
    str or None
        Parse value
    """

    if delta is None:
        return None

    hours, minutes, seconds = int(), int(), int()

    if type(delta) is timedelta:
        hours, seconds = divmod(delta.seconds, 3600)

        if seconds > 0:
            minutes, seconds = divmod(seconds, 60)

        hours += delta.days * 24

    return "{:02d}:{:02d}:{:02d}".format(hours, minutes, seconds)


def get_binary_path(binary):
    """ Get a list of available binary paths from $PATH variable

    This function get all the path from $PATH variable which match binary
    request.

    Parameters
    ----------
    binary : str
        Binary name or path

    Returns
    -------
    list
        List of available path

    Examples
    --------
    >>> get_binary_path("ls")
    ['/bin/ls']
    """

    available = list()

    if binary is None or len(str(binary)) == 0:
        return available

    binary = Path(binary).expanduser()

    if binary.exists():
        available.append(binary.name)

    for path in set(environ["PATH"].split(':')):
        binary_path = Path(path, binary)

        if binary_path.exists() and binary_path.name not in available:
            available.append(str(binary_path))

    return available


def generate_identifier(name):
    """ Generate an identifier from a name string

    Parameters
    ----------
    name : pathlib.Path or str
        Path to parse into indentifier

    Returns
    -------
    str
        Identifier string

    Examples
    --------
    >>> generate_identifier("Double Dragon (Europe).nes")
    'double-dragon-europe-nes-25953832'
    """

    inode = int()

    if isinstance(name, Path):
        # Retrieve file inode number
        inode = name.stat().st_ino
        # Retrieve file basename
        name = name.name

    # Retrieve only alphanumeric element from filename
    name = sub(r"[^\w\d]+", ' ', name.lower())
    # Remove useless spaces and replace the others with a dash
    name = sub(r"[\s|_]+", '-', name.strip())

    if inode > 0:
        name = "%s-%d" % (name, inode)

    return name


def generate_extension(extension):
    """ Generate a regex pattern to check lower and upper case extensions

    Thanks to https://stackoverflow.com/a/10148272

    Parameters
    ----------
    extension : str
        Extension to parse without the first dot

    Returns
    -------
    str
        Regex pattern

    Examples
    --------
    >>> generate_extensions("nes")
    '[nN][eE][sS]'
    """

    pattern = str()

    for character in extension:
        if not character == '.':
            pattern += "[%s%s]" % (character.lower(), character.upper())

        else:
            pattern += '.'

    return pattern


def copy(src, dst, follow_symlinks=True):
    """ Compat function to use shutil.copy on python < 3.6

    More informations with shutil.copy2 module

    Parameters
    ----------
    src : str or pathlib.Path
        File source
    dst : str or pathlib.Path
        File destination
    follow_symlinks : bool, optional
        Retrieve metadata from symlinks origins if True
    """

    if version_info.major == 3 and version_info.minor < 6:

        if not isinstance(src, str):
            src = str(src)

        if not isinstance(dst, str):
            dst = str(dst)

    copy2(src, dst, follow_symlinks=follow_symlinks)
