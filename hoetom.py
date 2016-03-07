# coding: utf-8

import logging

import lib.url

from app.hoetom import *
from app.html import *


class Player(object):
    def __init__(self):
        pass
    pass


class Hoetom(object):
    Encoding = 'GB18030'


class PlayerSpider(Hoetom):

    def __init__(self, set_hoetom_db=None, set_html_db=None):
        self.db_hoetom = HoetomDb(**set_hoetom_db) if set_hoetom_db else HoetomDb()
        self.html_client = HtmlClient(**set_html_db) if set_html_db else HtmlClient()

    def open_db(self):
        self.db_hoetom.open()
        logging.info('open hoetom db')
        self.html_client.open_db()
        logging.info('open html db')
        return self

    def __enter__(self):
        return self.open_db()

    def close_db(self):
        self.db_hoetom.close()
        logging.info('close hoetom db')
        self.html_client.close_db()
        logging.info('close html db')

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.close_db()

    def update_playerinfo(self, playerid):
        logging.info('update player: playerid={}'.format(playerid))

        player_url = PlayerUrl(playerid)
        player_html = self.html_client.get(url=player_url.urlstr, encoding=self.Encoding)

        if player_html:
            logging.info('http get: code={}, url={}'.format(player_html['html_url'], player_html['html_code']))
            logging.info('title: {}'.format(player_html.get_title()))

            self.html_client.save(player_html)

            logging.info('html save: {}'.format(player_html))

            player_info = get_playerinfo(player_html.text)
            logging.info('player info: {}'.format(player_info))

            if player_info:
                p_sex = SEX.from_obj(player_info['p_sex'])

                p_nat = self.db_hoetom.country.get(name=player_info['p_nat']) or \
                    self.db_hoetom.country.add(CountryTable(name=player_info.get('p_nat')))

                p_rank = self.db_hoetom.rank.get(rank=player_info.get('p_rank')) or \
                    self.db_hoetom.rank.add(RankTable(rank=player_info.get('p_rank')))

                player_update = dict(
                    p_id=player_info.get('p_id'),
                    p_name=player_info.get('p_name'),
                    p_sex=p_sex.value,
                    p_nat=p_nat.get_primarykey(),
                    p_rank=p_rank.get_primarykey(),
                    p_birth=player_info.get('p_birth')
                )
                player = self.db_hoetom.player.get(p_id=player_info.get('p_id')) or \
                    self.db_hoetom.player.get(p_name=player_info.get('p_name')) or \
                    PlayerTable()
                player.update(**player_update)
                self.db_hoetom.player.save(player)
                logging.info('player save: {}'.format(player))
                return player.get_primarykey()

    def update_playerid_many(self):
        update_urls = PlayerListUrl.list()
        update_urls.append(PlayerRankingUrl)

        for update_url in update_urls:
            logging.info('update: {}'.format(update_url))

            update_html = self.html_client.get(url=update_url)

            if update_html:
                logging.info('update: code={}, url={}'.format(update_html['html_code'], update_html['html_url']))
                logging.info('title: {}'.format(update_html.get_title()))

                self.html_client.save(update_html)
                logging.info('update html: {}'.format(update_html))

                update_id_list = get_playerid(update_html.text)
                for update_id in update_id_list:
                    playerid = self.db_hoetom.playerid.get(playerid=update_id)
                    if not playerid:
                        playerid = self.db_hoetom.playerid.add(PlayeridTable(playerid=update_id))
                    logging.info('playerid: {}'.format(playerid))
            else:
                logging.info('update error: code={}, url={}'.format(update_html['html_code'], update_html['html_url']))


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    # 1694
    with PlayerSpider() as s:
        pass
