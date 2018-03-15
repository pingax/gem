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

# GEM
from gem.engine import *

# Regex
from re import sub

# Translation
from gettext import gettext as _

# ------------------------------------------------------------------------------
#   Modules - Packages
# ------------------------------------------------------------------------------

try:
    from pkg_resources import resource_filename
    from pkg_resources import DistributionNotFound

except ImportError as error:
    sys_exit("Import error with python3-setuptools module: %s" % str(error))

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
    egg : str, optional
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

    except KeyError as error:
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

    hours, minutes, seconds = int(), int(), int()

    if type(time_object) is timedelta:
        hours, seconds = divmod(time_object.seconds, 3600)

        if seconds > 0:
            minutes, seconds = divmod(seconds, 60)

        hours += time_object.days * 24

    if hours == 0:
        if minutes == 0:
            if seconds == 0:
                return str()
            elif seconds == 1:
                return _("1 second")

            return _("%d seconds") % seconds

        elif minutes == 1:
            return _("1 minute")

        return _("%d minutes") % minutes

    elif hours == 1:
        return _("1 hour")

    return _("%d hours") % hours


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


def replace_for_markup(text):
    """ Replace some characters in text for markup compatibility

    Parameters
    ----------
    text : str
        Text to parser

    Returns
    -------
    str
        Replaced text
    """

    characters = {
        '&': "&amp;",
        '<': "&lt;",
        '>': "&gt;",
    }

    for key, value in characters.items():
        text = text.replace(key, value)

    return text


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
