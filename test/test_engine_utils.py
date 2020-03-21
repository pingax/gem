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
from datetime import datetime, timedelta

# Filesystem
from pathlib import Path

# Geode
from geode_gem.engine.utils import (copy,
                                    generate_extension,
                                    generate_identifier,
                                    get_binary_path,
                                    get_creation_datetime,
                                    get_data,
                                    parse_timedelta)

# System
from tempfile import gettempdir

# Unittest
import unittest


# ------------------------------------------------------------------------------
#   Tests
# ------------------------------------------------------------------------------

class GeodeGEMUtilsTC(unittest.TestCase):

    def test_copy(self):
        """ Check geode_gem.engine.utils.copy method
        """

        awesome_bytes = b"Dear diary, this is my life..."

        original_path = Path(gettempdir(), "file_to_copy.txt")
        original_path.write_bytes(awesome_bytes)

        self.assertTrue(original_path.exists())

        copy_path = Path(gettempdir(), "new_file.txt")
        copy(original_path, copy_path)

        self.assertTrue(copy_path.exists())
        self.assertFalse(copy_path.is_symlink())
        self.assertEqual(copy_path.read_bytes(), awesome_bytes)

        self.assertEqual(
            original_path.stat().st_size, copy_path.stat().st_size)
        self.assertEqual(
            original_path.stat().st_mode, copy_path.stat().st_mode)

        original_path.unlink()
        copy_path.unlink()

    def test_get_data(self):
        """ Check geode_gem.engine.utils.get_data method
        """

        path = get_data("test", "test_engine_utils.py")
        self.assertTrue(path.exists())

        path = get_data("setup.py")
        self.assertTrue(path.exists())

        path = get_data("config", "not_exists.file")
        self.assertFalse(path.exists())

    def test_get_binary_path(self):
        """ Check geode_gem.engine.utils.get_binary_path method
        """

        self.assertGreater(len(get_binary_path("python3")), 0)

        self.assertEqual(len(get_binary_path("were-binary_of_doom")), 0)

    def test_get_creation_datetime(self):
        """ Check geode_gem.engine.utils.get_creation_datetime method
        """

        creation_date = get_creation_datetime(
            get_data("test", "test_engine_utils.py"))
        self.assertIs(type(creation_date), datetime)

        creation_date = get_creation_datetime("not_exists.file")
        self.assertIsNone(creation_date)

    def test_generate_extension(self):
        """ Check geode_gem.engine.utils.generate_extension method
        """

        self.assertEqual(
            "[nN][eE][sS]", generate_extension("NES"))

        self.assertEqual(
            ".[oO][gG][gG]", generate_extension(".ogg"))

        self.assertEqual(
            ".[tT][aA][rR].[xX][zZ]", generate_extension(".tAr.Xz"))

    def test_generate_identifier_from_file(self):
        """ Check geode_gem.engine.utils.generate_identifier method
        """

        path = Path(gettempdir(), "Best Game in, the (World).gnu")
        path.touch()
        self.assertTrue(path.exists())

        self.assertEqual(f"best-game-in-the-world-gnu-{path.stat().st_ino}",
                         generate_identifier(path))
        path.unlink()

        path = Path("It's an unexistant_file!.obvious")
        self.assertFalse(path.exists())

        self.assertEqual("it-s-an-unexistant-file-obvious",
                         generate_identifier(path))

    def test_generate_identifier_from_strings(self):
        """ Check geode_gem.engine.utils.generate_identifier method
        """

        strings = [("Unexistant_File.ext", "unexistant-file-ext"),
                   ("An  other File  .oops", "an-other-file-oops")]

        for string, result in strings:
            self.assertEqual(generate_identifier(string), result)

    def test_parse_timedelta(self):
        """ Check geode_gem.engine.utils.parse_timedelta method
        """

        self.assertIsNone(parse_timedelta(None))

        self.assertEqual(
            parse_timedelta(timedelta()), "00:00:00")
        self.assertEqual(
            parse_timedelta(timedelta(seconds=30)), "00:00:30")
        self.assertEqual(
            parse_timedelta(timedelta(seconds=3600*24)), "24:00:00")
        self.assertEqual(
            parse_timedelta(timedelta(days=2)), "48:00:00")
        self.assertEqual(
            parse_timedelta(timedelta(days=1337, seconds=42)), "32088:00:42")


if __name__ == "__main__":
    unittest.main()
