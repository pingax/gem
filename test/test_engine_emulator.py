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

# Filesystem
from pathlib import Path

# Geode
from geode_gem.engine.emulator import Emulator
from geode_gem.engine.game import Game

# System
from tempfile import gettempdir

# Unittest
import unittest


# ------------------------------------------------------------------------------
#   Tests
# ------------------------------------------------------------------------------

class GeodeGEMEmulatorTC(unittest.TestCase):

    def setUp(self):
        """ Initialize each test with some data
        """

        self.savestates = list()
        self.screenshots = list()

        files = [
            ("savestates", "game_001.png"),
            ("savestates", "game_002.jpg"),
            ("savestates", "game_003.bmp"),
            ("savestates", "Game_004.gif"),
            ("screenshots", "game_001.png"),
            ("screenshots", "game_002.jpg"),
            ("screenshots", "game_003.bmp"),
            ("screenshots", "game_004.gif")]

        self.tempdirectory = Path(gettempdir())
        for directory, filename in files:
            path = self.tempdirectory.joinpath(directory)
            if not path.exists():
                path.mkdir()

            filepath = path.joinpath(filename)
            filepath.touch()

            data = getattr(self, directory)
            data.append(filepath)

        self.emulator = Emulator(
            name="Amazing Emulator",
            binary="python3",
            savestates=self.tempdirectory.joinpath("savestates",
                                                   "<lname>_*.*"),
            screenshots=self.tempdirectory.joinpath("screenshots",
                                                    "<name>_*.*"))

        self.path = self.tempdirectory.joinpath("game.ext")
        self.path.touch()

        self.game = Game(None, self.path)
        self.game.name = "Game"

    def tearDown(self):
        """ Remove data from initialization when test terminate
        """

        for filepath in self.savestates:
            filepath.unlink()

        for filepath in self.screenshots:
            filepath.unlink()

        Path(gettempdir(), "savestates").rmdir()
        Path(gettempdir(), "screenshots").rmdir()

        if self.path.exists():
            self.path.unlink()

    def test_emulator_as_dict(self):
        """ Check geode_gem.engine.emulator.Emulator.as_dict method
        """

        data = self.emulator.as_dict()

        self.assertEqual(sorted(data.keys()), [
            "binary", "configuration", "default", "fullscreen", "icon",
            "save", "snaps", "windowed"])

        self.assertEqual(data["binary"], Path(self.emulator.binary))

    def test_emulator_exists(self):
        """ Check geode_gem.engine.emulator.Emulator.exists property
        """

        self.assertTrue(self.emulator.exists)

        emulator = Emulator(binary="oops-not-exists")
        self.assertFalse(emulator.exists)

    def test_emulator_get_savestates(self):
        """ Check geode_gem.engine.emulator.Emulator.get_savestates method
        """

        data = self.emulator.get_savestates(self.game)

        self.assertIsNotNone(data)
        self.assertEqual(len(data), 3)

    def test_emulator_get_screenshots(self):
        """ Check geode_gem.engine.emulator.Emulator.get_screenshots method
        """

        data = self.emulator.get_screenshots(self.game)

        self.assertIsNotNone(data)
        self.assertEqual(len(data), 4)

    def test_emulator_get_command_line(self):
        """ Check geode_gem.engine.emulator.Emulator.get_command_line method
        """

        with self.assertRaises(FileNotFoundError):
            emulator = Emulator(binary="oops-damn")
            emulator.get_command_line(self.game)

        data = self.emulator.get_command_line(self.game)
        self.assertEqual(data[0], str(self.emulator.binary))
        self.assertEqual(data[-1], str(self.game.path))
        self.assertEqual(len(data), 2)

        self.emulator.windowed = "-w"
        self.emulator.fullscreen = "-f"

        data = self.emulator.get_command_line(self.game)
        self.assertIn(self.emulator.windowed, data)
        self.assertEqual(len(data), 3)

        data = self.emulator.get_command_line(self.game, fullscreen=True)
        self.assertIn(self.emulator.fullscreen, data)
        self.assertEqual(len(data), 3)

        self.game.default = "--option=value"
        data = self.emulator.get_command_line(self.game)
        self.assertIn(self.game.default, data)
        self.assertEqual(len(data), 4)

        self.game.default = "--use <rom_path>"
        data = self.emulator.get_command_line(self.game)
        self.assertEqual(data[-1], str(self.game.path.parent))
        self.assertEqual(len(data), 4)
