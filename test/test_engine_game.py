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

# Geode
from geode_gem.engine.game import Game
from geode_gem.engine.utils import generate_identifier

# System
from tempfile import gettempdir

# Unittest
import unittest


# ------------------------------------------------------------------------------
#   Tests
# ------------------------------------------------------------------------------

class GeodeGEMGameTC(unittest.TestCase):

    def setUp(self):
        """ Initialize each test with some data
        """

        self.path = Path(gettempdir(), "awesome_game.ext")
        self.path.touch()

        self.game = Game(None, self.path)

    def tearDown(self):
        """ Remove data from initialization when test terminate
        """

        if self.path.exists():
            self.path.unlink()

    def test_game_copy(self):
        """ Check geode_gem.engine.game.Game.copy method
        """

        with self.assertRaises(FileNotFoundError):
            self.game.copy(Path(gettempdir(), "unexisting_game.txt"))

        path = Path(gettempdir(), "duplicate_game.txt")
        path.touch()

        game = self.game.copy(path)

        self.assertEqual(game.id, generate_identifier(path))
        self.assertEqual(game.name, path.stem)

        path.unlink()

    def test_game_reset(self):
        """ Check geode_gem.engine.game.Game.reset method
        """

        self.game.name = "This is an awesome game, yay !"
        self.game.score = 5
        self.game.multiplayer = True

        self.game.reset()

        self.assertEqual(self.game.name, self.path.stem)
        self.assertEqual(self.game.score, 0)
        self.assertFalse(self.game.multiplayer)

    def test_game_extension(self):
        """ Check geode_gem.engine.game.Game.extension property
        """

        data = [("awesome_game.ext", ".ext"),
                ("multi_extensions.tar.xz", ".xz"),
                ("damn.this_is_a.strange_name.what", ".what")]

        for filename, extension in data:
            path = Path(gettempdir(), filename)
            path.touch()

            self.assertEqual(Game(None, path).extension, extension)
            path.unlink()

    def test_game_as_dict(self):
        """ Check geode_gem.engine.game.Game.as_dict method
        """

        self.game.play_time = timedelta(seconds=42)
        self.game.tags = ["platform", "action"]

        data = self.game.as_dict()

        self.assertEqual(sorted(data.keys()), [
            "arguments", "cover", "emulator", "favorite", "filename", "finish",
            "key", "last_play", "last_play_time", "multiplayer", "name",
            "play", "play_time", "score", "tags"])

        self.assertEqual(data["play_time"], "00:00:42")
        self.assertEqual(data["name"], self.game.name)
        self.assertEqual(data["tags"], "platform;action")
