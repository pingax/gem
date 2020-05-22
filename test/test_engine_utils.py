# ------------------------------------------------------------------------------
#  Copyleft 2015-2020  PacMiam
#
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

# Datetime
from datetime import datetime, timedelta

# Filesystem
from pathlib import Path

# Geode
from geode_gem.engine.utils import (are_equivalent_timestamps,
                                    copy,
                                    generate_extension,
                                    generate_identifier,
                                    get_binary_path,
                                    get_boot_datetime_as_timestamp,
                                    get_creation_datetime,
                                    get_data,
                                    parse_timedelta)

# System
from os import environ
from tempfile import gettempdir, TemporaryDirectory

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

        path = TemporaryDirectory(prefix="geode-gem-", suffix="-test")

        filepath = Path(path.name).joinpath("binary_test")
        filepath.touch()

        self.assertEqual(len(get_binary_path("binary_test")), 0)

        # Add a new entry into PATH environment to retrieve binary_test
        environ["PATH"] = f"{filepath.parent}:{environ['PATH']}"
        self.assertEqual(len(get_binary_path("binary_test")), 1)

        # Ensure to have an unreadable directory for current test
        filepath.parent.chmod(0o033)
        self.assertEqual(len(get_binary_path("binary_test")), 0)

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

    def test_get_boot_datetime_as_timestamp(self):
        """ Check geode_gem.engine.utils.get_boot_datetime_as_timestamp method
        """

        with self.assertRaises(FileNotFoundError):
            get_boot_datetime_as_timestamp("unknown-path")

        path = TemporaryDirectory(prefix="geode-gem-", suffix="-test")
        with self.assertRaises(FileNotFoundError):
            get_boot_datetime_as_timestamp(path.name)

        uptime_path = Path(path.name, "uptime")
        uptime_path.touch()

        self.assertIsNone(get_boot_datetime_as_timestamp(path.name))

        with uptime_path.open('w') as pipe:
            pipe.write("1337.0 42.0")

        result = get_boot_datetime_as_timestamp(path.name)
        self.assertIsNotNone(result)

        self.assertAlmostEqual(
            result, datetime.now().timestamp() - 1337.0, delta=1)

    def test_are_equivalent_timestamps(self):
        """ Check geode_gem.engine.utils.are_equivalent_timestamps method
        """

        data = [(1587400601, 1587400601, 0, True),
                (1587400601, 1587400604, 0, False),
                (1587400601, 1587400604, 2, False),
                (1587400601, 1587400604, 3, True)]

        for first, second, delta, result in data:
            self.assertEqual(
                are_equivalent_timestamps(first, second, delta=delta),
                result)


if __name__ == "__main__":
    unittest.main()
