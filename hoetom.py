# coding: utf-8

import logging

from api.html import *
from app.hoetom.html import *
from app.hoetom.mapping import *
from app.hoetom.url import *

Encoding = 'GB18030'


def update_playerid(beg=0, end=None):
    htmldb = HtmlDb()
    hoetomdb = HoetomDb()
    htmldb.open()
    logging.info('open htmldb: %s' % htmldb.config)
    hoetomdb.open()
    logging.info('open hoetomdb: %s' % hoetomdb.config)

    for indexurl in PlayerListUrl.list(beg, end):
        logging.info('update: %s' % indexurl)
        indexhtml = htmldb.html.get(html_url=indexurl)
        if not indexhtml:
            indexhtml = HtmlTable(html_url=indexurl, html_encoding=Encoding)
        indexpage = HtmlPage(lib.url.parse(indexhtml['html_url']), Encoding)
        if indexpage.get():
            logging.info('title=%s, code=%s' % (indexpage.get_title(), indexpage.code))
            indexhtml['html_encoding'] = indexpage.encoding
            indexhtml['html_code'] = indexpage.code
            logging.info('http get: url=%s, encoding=%s' % (indexpage.urlstr, indexpage.encoding))
            indexpage.save()
            indexhtml = htmldb.html.save(indexhtml)

            logging.info(str(indexhtml))
            playeridlist = get_playerid(indexpage.text)
            for p_id in playeridlist:
                playerid = hoetomdb.playerid.get(playerid=p_id)
                if not playerid:
                    playerid = hoetomdb.playerid.add(PlayeridTable(playerid=p_id))
                logging.info(str(playerid))
        else:
            logging.warning('http get: code=%s' % indexpage.code)

    htmldb.close()
    logging.info('htmldb close')
    hoetomdb.close()
    logging.info('hoetomdb close')


def update_playerinfo():
    htmldb = HtmlDb()
    hoetomdb = HoetomDb()
    htmldb.open()
    logging.info('open htmldb: %s' % htmldb.config)
    hoetomdb.open()
    logging.info('open hoetomdb: %s' % hoetomdb.config)
    times = 0
    for playerid in hoetomdb.playerid:
        times += 1
        logging.info('times={}'.format(times))
        logging.info('playerid={}'.format(playerid))
        url = PlayerInfoUrl(playerid['playerid'])
        infohtml = htmldb.html.get(html_url=url.urlstr)
        if not infohtml:
            infohtml = HtmlTable(html_url=url.urlstr, html_encoding=Encoding)
        infopage = HtmlPage(url.urlparse, encoding=Encoding)
        if infopage.get():
            logging.info('code={}, encoding={}, url={}'
                         .format(infopage.code, infopage.encoding, infopage.urlstr))
            infohtml['html_encoding'] = infopage.encoding
            infohtml['html_code'] = infopage.code
            infopage.save()
            infohtml = htmldb.html.save(infohtml)
            logging.info(str(infohtml))

            getplayerinfo = get_playerinfo(infopage.text)
            logging.info('playerdata={}'.format(getplayerinfo))
            if getplayerinfo:
                p_sex = SEX.from_obj(getplayerinfo.get('p_sex'))

                p_nat = hoetomdb.country.get(name=getplayerinfo.get('p_nat'))
                if not p_nat:
                    p_nat = hoetomdb.country.add(CountryTable(name=getplayerinfo.get('p_nat')))

                p_rank = hoetomdb.rank.get(rank=getplayerinfo.get('p_rank'))
                if not p_rank:
                    p_rank = hoetomdb.rank.add(RankTable(rank=getplayerinfo.get('p_rank')))

                playerinfo = hoetomdb.player.get(p_id=getplayerinfo.get('p_id')) or \
                    hoetomdb.player.get(p_name=getplayerinfo.get('p_name'))
                if not playerinfo:
                    playerinfo = PlayerTable(
                        p_id=getplayerinfo.get('p_id'),
                        p_name=getplayerinfo.get('p_name'),
                        p_sex=p_sex.value,
                        p_nat=p_nat.get_primarykey(),
                        p_rank=p_rank.get_primarykey(),
                        p_birth=getplayerinfo.get('p_birth')
                    )
                    playerinfo = hoetomdb.player.add(playerinfo)
                else:
                    playerinfo.update(
                            p_id=getplayerinfo.get('p_id'),
                            p_name=getplayerinfo.get('p_name'),
                            p_sex=p_sex.value,
                            p_nat=p_nat.get_primarykey(),
                            p_rank=p_rank.get_primarykey(),
                            p_birth=getplayerinfo.get('p_birth')
                        )
                    playerinfo = hoetomdb.player.update(playerinfo)
                logging.info('playerinfo={}'.format(playerinfo))

        else:
            logging.warning('http error: code={}, url={}'.format(infopage.code, infopage.urlstr))
            break

    htmldb.close()
    logging.info('htmldb close')
    hoetomdb.close()
    logging.info('hoetomdb close')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    # 1694
    update_playerinfo()
