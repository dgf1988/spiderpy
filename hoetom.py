# coding: utf-8

import logging
import re
import json

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
        self.hoetom = HoetomDb(**set_hoetom_db) if set_hoetom_db else HoetomDb()
        self.html = HtmlDb(**set_html_db) if set_html_db else HtmlDb()

    def open_db(self):
        self.hoetom.open()
        logging.info('open hoetom db')
        self.html.open()
        logging.info('open html db')
        return self

    def __enter__(self):
        return self.open_db()

    def close_db(self):
        self.hoetom.close()
        logging.info('close hoetom db')
        self.html.close()
        logging.info('close html db')

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.close_db()

    def update_playerinfo(self, playerid):
        logging.info('update player: playerid={}'.format(playerid))

        player_url = PlayerUrl(playerid)
        player_html = self.html.html.get(html_url=player_url.urlstr) or \
            HtmlTable(html_url=player_url.urlstr, html_encoding=self.Encoding)
        player_page = HtmlPage(url=player_html.get('html_url'), encoding=player_html.get('html_encoding'))
        if player_page.get() == 200:
            player_page.save()
            logging.info('http get: {}'.format(player_page))

            player_html.update(html_encoding=player_page.encoding, html_code=player_page.code)
            self.html.html.save(player_html)
            logging.info('html save: {}'.format(player_html))

            player_info = get_playerinfo(player_page.text)
            logging.info('player info: {}'.format(player_info))

            if player_info:
                p_sex = SEX.from_obj(player_info['p_sex'])

                p_nat = self.hoetom.country.get(name=player_info['p_nat']) or \
                        self.hoetom.country.add(CountryTable(name=player_info.get('p_nat')))

                p_rank = self.hoetom.rank.get(rank=player_info.get('p_rank')) or \
                         self.hoetom.rank.add(RankTable(rank=player_info.get('p_rank')))

                player_update = dict(
                    p_id=player_info.get('p_id'),
                    p_name=player_info.get('p_name'),
                    p_sex=p_sex.value,
                    p_nat=p_nat.get_primarykey(),
                    p_rank=p_rank.get_primarykey(),
                    p_birth=player_info.get('p_birth')
                )
                player = self.hoetom.player.get(p_id=player_info.get('p_id')) or \
                         self.hoetom.player.get(p_name=player_info.get('p_name')) or \
                         PlayerTable()
                player.update(**player_update)
                self.hoetom.player.save(player)
                logging.info('player save: {}'.format(player))
                return player.get_primarykey()
        else:
            logging.warning('http error: {}'.format(player_page))

    def update_playerid_many(self):
        update_urls = PlayerListUrl.list()
        update_urls.append(PlayerRankingUrl)

        for update_url in update_urls:
            logging.info('update: {}'.format(update_url))

            update_html = self.html.html.get(html_url=update_url) or \
                HtmlTable(html_url=update_url, html_encoding=self.Encoding)
            update_page = HtmlPage(url=update_html['html_url'], encoding=update_html['html_encoding'])
            if update_page.get() == 200:
                update_page.save()
                logging.info('http get: {}'.format(update_page))

                update_html.update(html_encoding=update_page.encoding, html_code=update_page.code)
                self.html.html.save(update_html)
                logging.info('html save: {}'.format(update_html))

                update_id_list = get_playerid(update_html.text)
                for update_id in update_id_list:
                    playerid = self.hoetom.playerid.get(playerid=update_id)
                    if not playerid:
                        playerid = self.hoetom.playerid.add(PlayeridTable(playerid=update_id))
                    logging.info('playerid: {}'.format(playerid))
            else:
                logging.info('update error: {}'.format(update_page))


def get_sgfinfo(html):
    p_name = r'height="25" nowrap>对局名称：</td>[^<]*<td>([^<]*)</td>'
    p_black = r'height="25">执黑选手：</td>[^<]*<td>([^<]*)<font'
    p_white = r'height="25">执白选手：</td>[^<]*<td>([^<]*)<font'
    p_rule = r'height="25">规则：</td>[^<]*<td>([^<]*)</td>'
    p_result = r'height="25">比赛结果：</td>[^<]*<td>([^<]*)</td>'
    p_time = r'height="25">比赛日期：</td>[^<]*<td>([^<]*)</td>'
    p_place = r'height="25">比赛地点：</td>[^<]*<td>([^<]*)</td>'
    if not html:
        return None
    sgfinfo = dict()
    m_name = re.search(p_name, html, re.I)
    if m_name:
        sgfinfo['name'] = m_name.group(1)
    m_black = re.search(p_black, html, re.I)
    if m_black:
        sgfinfo['black'] = m_black.group(1)
    m_white = re.search(p_white, html, re.I)
    if m_white:
        sgfinfo['white'] = m_white.group(1)
    m_rule = re.search(p_rule, html, re.I)
    if m_rule:
        sgfinfo['rule'] = m_rule.group(1)
    m_result = re.search(p_result, html, re.I)
    if m_result:
        sgfinfo['result'] = m_result.group(1)
    m_time = re.search(p_time, html, re.I)
    if m_time:
        sgfinfo['time'] = m_time.group(1)
    m_place = re.search(p_place, html, re.I)
    if m_place:
        sgfinfo['place'] = m_place.group(1)
    return sgfinfo


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    # 1694
    with PlayerSpider() as s:
        s.update_playerid_many()

