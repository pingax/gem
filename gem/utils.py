# ------------------------------------------------------------------
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
# ------------------------------------------------------------------

# ------------------------------------------------------------------
#   Modules
# ------------------------------------------------------------------

# System
from os import environ

from os.path import exists
from os.path import basename
from os.path import splitext
from os.path import expanduser
from os.path import join as path_join

from datetime import datetime

# Translation
from gettext import gettext as _
from gettext import textdomain
from gettext import bindtextdomain

# ------------------------------------------------------------------
#   Modules - Packages
# ------------------------------------------------------------------

try:
    from pkg_resources import resource_filename
    from pkg_resources import DistributionNotFound

except ImportError as error:
    sys_exit("Import error with python3-pkg-resources module: %s" % str(error))

# ------------------------------------------------------------------
#   Methods
# ------------------------------------------------------------------

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


def string_from_date(date, date_format="%d-%m-%Y %H:%M:%S"):
    """ Convert a datetime to a pretty string

    Get a pretty string from the interval between NOW() and the wanted date

    Parameters
    ----------
    date : datetime.datetime
        Date to compare with NOW()

    Other Parameters
    ----------------
    date_format : str
        Format using to parse time when date type is a string
        (Default: %d-%m-%Y %H:%M:%S)

    Returns
    -------
    str or None
        Convert value
    """

    if date is None:
        return None

    if type(date) is str:
        date = datetime.strptime(str(date), date_format)

    days = (datetime.now() - date).days

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


def string_from_time(date, date_format="%H:%M:%S"):
    """ Convert a time to a pretty string

    Get a pretty string from the interval between NOW() and the wanted date

    Parameters
    ----------
    date : datetime.datetime
        Date to compare with NOW()

    Other Parameters
    ----------------
    date_format : str
        Format using to parse date when date type is a string
        (Default: %H:%M:%S)

    Returns
    -------
    str or None
        Convert value
    """

    if date is None:
        return None

    if type(date) is str:
        date = datetime.strptime(str(date), date_format)

    if date.hour == 0:
        if date.minute == 0:
            if date.second == 0:
                return str()
            elif date.second == 1:
                return _("1 second")

            return _("%d seconds") % date.second

        elif date.minute == 1:
            return _("1 minute")

        return _("%d minutes") % date.minute

    elif date.hour == 1:
        return _("1 hour")

    return _("%d hours") % date.hour


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
