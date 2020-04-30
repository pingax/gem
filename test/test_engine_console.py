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

# Filesystem
from pathlib import Path

# Geode
from geode_gem.engine.console import Console
from geode_gem.engine.emulator import Emulator
from geode_gem.engine.game import Game
from geode_gem.engine.utils import generate_identifier

# System
from tempfile import gettempdir, NamedTemporaryFile, TemporaryDirectory

# Unittest
import unittest


# ------------------------------------------------------------------------------
#   Tests
# ------------------------------------------------------------------------------

class GeodeGEMConsoleTC(unittest.TestCase):

    def setUp(self):
        """ Initialize each test with some data
        """

        self.directory = TemporaryDirectory()

        self.files = list()
        for index in range(0, 5):
            filename = NamedTemporaryFile(suffix=f"_{index}.ext",
                                          dir=self.directory.name)
            filename.write(b"something to generate the file, yay")

            self.files.append(filename)

        self.console = Console(None,
                               path=Path(self.directory.name),
                               emulator=Emulator(binary="python3"),
                               extensions=["ext", "nop"])

        self.first_game = Path(self.files[0].name)
        self.first_game_id = generate_identifier(self.first_game)

    def tearDown(self):
        """ Remove data from initialization when test terminate
        """

        for filename in self.files:
            filename.close()

    def test_console_as_dict(self):
        """ Check geode_gem.engine.console.Console.as_dict method
        """

        data = self.console.as_dict()

        self.assertEqual(sorted(data.keys()), [
            "emulator", "exts", "favorite", "icon", "ignores", "recursive",
            "roms"])

        self.assertEqual(data["exts"], ';'.join(self.console.extensions))

    def test_console_init_games(self):
        """ Check geode_gem.engine.console.Console.init_games method
        """

        with self.assertRaises(FileNotFoundError):
            Console(None, path="anywhere-but-here").init_games()

        with NamedTemporaryFile() as pipe:
            with self.assertRaises(NotADirectoryError):
                Console(None, path=Path(pipe.name)).init_games()

        with TemporaryDirectory() as pipe:
            path = Path(pipe)
            path.chmod(0o333)

            with self.assertRaises(PermissionError):
                Console(None, path=path).init_games()

        self.console.init_games()
        self.assertEqual(len(self.console.get_games()), 5)

    def test_console_add_game(self):
        """ Check geode_gem.engine.console.Console.add_game method
        """

        with self.assertRaises(FileNotFoundError):
            self.console.add_game("oops-not-exist")

        game = self.console.add_game(self.first_game)
        self.assertEqual(game.path, self.first_game)
        self.assertEqual(game.name, self.first_game.stem)
        self.assertEqual(game.emulator, self.console.emulator)

        with self.assertRaises(ValueError):
            self.console.add_game(self.first_game)

    def test_console_delete_game(self):
        """ Check geode_gem.engine.console.Console.delete_game method
        """

        with self.assertRaises(KeyError):
            self.console.delete_game(Game(None, self.first_game))

        with self.assertRaises(TypeError):
            self.console.delete_game(self.first_game)

        self.console.init_games()

        games = self.console.get_games()
        self.assertEqual(len(games), 5)

        self.console.delete_game(games[0])
        self.assertEqual(len(self.console.get_games()), 4)

    def test_console_get_game(self):
        """ Check geode_gem.engine.console.Console.get_game method
        """

        self.console.init_games()

        game = self.console.get_game("I am error")
        self.assertIsNone(game)

        game = self.console.get_game(self.first_game_id)
        self.assertIsNotNone(game)

    def test_console_search_game(self):
        """ Check geode_gem.engine.console.Console.search_game method
        """

        self.console.init_games()

        games = self.console.search_game("I am error")
        self.assertEqual(len(games), 0)

        games = self.console.search_game(self.first_game.stem)
        self.assertEqual(len(games), 1)

        games = self.console.search_game(self.first_game_id)
        self.assertEqual(len(games), 1)
