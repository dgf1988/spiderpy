import unittest
from api.hoetombot import *


class TestHoetomBot(unittest.TestCase):
    def setUp(self):
        self.db = HoetomDBClient()
        self.db.open()

    def tearDown(self):
        self.db.close()

    def test_player(self):
        print(Player.sql_list(10))
        player_list_10 = Player.db_list(self.db, 10)
        print(player_list_10)

if __name__ == '__main__':
    unittest.main()
