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

# Datetime
from datetime import date
from datetime import datetime

# Filesystem
from os.path import exists
from os.path import basename
from os.path import expanduser
from os.path import join as path_join

# Regex
from re import sub

# System
from os import environ
from sys import exit as sys_exit

# ------------------------------------------------------------------------------
#   Modules - Packages
# ------------------------------------------------------------------------------

try:
    from pkg_resources import resource_filename
    from pkg_resources import DistributionNotFound

except ImportError as error:
    sys_exit("Import error with python3-pkg-resources module: %s" % str(error))

# ------------------------------------------------------------------------------
#   Modules - Translation
# ------------------------------------------------------------------------------

from gettext import gettext as _
from gettext import textdomain
from gettext import bindtextdomain

# ------------------------------------------------------------------------------
#   Methods
# ------------------------------------------------------------------------------

def get_data(path, egg="gem"):
    """ Provides easy access to data in a python egg or local folder

    This function search a path in a specific python egg or in local folder. The
    local folder is check before egg to allow quick debugging.

    Thanks Deluge :)

    Parameters
    ----------
    path : str
        File path

    Other Parameters
    ----------------
    egg : str
        Python egg name (Default: gem)

    Returns
    -------
    str or None
        Path
    """

    try:
        data = resource_filename(egg, path)

        if exists(expanduser(data)):
            return data

        return path

    except DistributionNotFound as error:
        return path

    return None


def string_from_date(date_object):
    """ Convert a datetime to a pretty string

    Get a pretty string from the interval between NOW() and the wanted date

    Parameters
    ----------
    date_object : datetime.datetime
        Date to compare with NOW()

    Returns
    -------
    str or None
        Convert value
    """

    if date_object is None:
        return None

    days = (date.today() - date_object).days

    if days == 0:
        return _("Today")
    elif days == 1:
        return _("Yesterday")
    elif days < 30:
        return _("%d days ago") % int(days)

    months = int(days / 30)

    if months == 1:
        return _("Last month")
    elif months < 12:
        return _("%d months ago") % int(months)

    years = int(months / 12)

    if years < 2:
        return _("Last year")

    return _("%d years ago") % int(years)


def string_from_time(time_object):
    """ Convert a time to a pretty string

    Get a pretty string from the interval between NOW() and the wanted date

    Parameters
    ----------
    time_object : datetime.datetime
        Date to compare with NOW()

    Returns
    -------
    str or None
        Convert value
    """

    if time_object is None:
        return None

    if time_object.hour == 0:
        if time_object.minute == 0:
            if time_object.second == 0:
                return str()
            elif time_object.second == 1:
                return _("1 second")

            return _("%d seconds") % time_object.second

        elif time_object.minute == 1:
            return _("1 minute")

        return _("%d minutes") % time_object.minute

    elif time_object.hour == 1:
        return _("1 hour")

    return _("%d hours") % time_object.hour


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

    if len(binary) == 0:
        return available

    if exists(expanduser(binary)):
        available.append(binary)
        binary = basename(binary)

    for path in set(environ["PATH"].split(':')):
        binary_path = expanduser(path_join(path, binary))

        if exists(binary_path) and not binary_path in available:
            available.append(binary_path)

    return available


def generate_identifier(name):
    """ Generate an identifier from a name string

    Parameters
    ----------
    name : str
        String to parse into indentifier

    Returns
    -------
    str
        Identifier string

    Examples
    --------
    >>> generate_identifier("Double Dragon III - The Sacred Stones (Europe)")
    'double-dragon-iii-the-sacred-stones-europe'
    """

    # Replace special characters
    name = sub(",|'|\)|\[|\]|!|\?|\.|~", ' ', name)
    name = sub("\(|:|_", '-', name)

    # Replace multiple dashs with only one
    name = sub("-+", ' ', name)

    # Replace multiple spaces with only one
    name = sub(" +", ' ', name)

    return name.strip().replace(' ', '-').lower()
