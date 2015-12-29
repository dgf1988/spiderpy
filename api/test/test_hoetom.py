# -*- coding: utf-8 -*-
import unittest
from api.hoetom import *


class TestHoetomObject(unittest.TestCase):
    def setUp(self):
        self.db = HoetomDBClient()
        self.db.open()

    def tearDown(self):
        self.db.close()

    def test_country(self):
        get_country = Country.get(self.db, id=3)
        self.assertEqual(get_country.to_str(), '中国')

        dict_coutry = get_country.to_dict()
        self.assertEqual(len(dict_coutry), 2)
        self.assertIn('id', dict_coutry)
        self.assertIn('name', dict_coutry)
        self.assertNotIn('rank', dict_coutry)

        find_country = Country.find(self.db, name='中国')
        self.assertEqual(get_country.to_dict(), find_country[0].to_dict())
        self.assertEqual(len(find_country), 1)

        list_country = Country.list(self.db, 10)
        self.assertEqual(len(list_country), 10)
        for each in list_country:
            self.assertIsInstance(each, Country)
            print(each.to_json())

    def test_rank(self):
        get_rank = Rank.get(self.db, id=3)
        self.assertEqual(get_rank.to_str(), '三段')

        dict_rank = get_rank.to_dict()
        self.assertEqual(len(dict_rank), 2)
        self.assertEqual(dict_rank['id'], 3)
        self.assertEqual(dict_rank['rank'], '三段')

        find_rank = Rank.find(self.db, rank='三段')
        self.assertEqual(len(find_rank), 1)
        self.assertEqual(dict_rank, find_rank[0].to_dict())

        list_rank = Rank.list(self.db, 10)
        self.assertEqual(len(list_rank), 10)
        for each in list_rank:
            self.assertIsInstance(each, Rank)

    def test_player(self):
        get_player = Player.get(self.db, id=10)
        self.assertEqual(get_player.to_json(), {'p_name': '安国铉', 'p_rank': '五段', 'hoetomid': 7756, 'p_nat': '韩国', 'p_birth': '1992-07-23', 'id': 10, 'p_sex': '男'})

        find_player = Player.find(self.db, p_name='安国铉')
        self.assertEqual(find_player.__len__(), 1)
        self.assertEqual(find_player[0].to_json(), {'p_name': '安国铉', 'p_rank': '五段', 'hoetomid': 7756, 'p_nat': '韩国', 'p_birth': '1992-07-23', 'id': 10, 'p_sex': '男'})

        list_player = Player.list(self.db, 10)
        self.assertEqual(len(list_player), 10)
        for each in list_player:
            self.assertIsInstance(each, Player)
            print(each.to_json().__str__())

        a = Player.get(self.db, id=30)
        b = Player.get(self.db, id=30)
        self.assertEqual(a.to_json(), b.to_json())

    def test_playerid(self):
        listid = PlayerID.list(self.db)
        num = 0
        for id in listid:
            num += 1
            print(num)
            if isinstance(id, PlayerID):
                print(int(id))
                html = HoetomHtml(url=id.to_url_str())
                html.httpget()




if __name__ == '__main__':
    unittest.main()
