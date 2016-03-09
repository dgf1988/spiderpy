# coding: utf-8
import re
import json
import logging
from app.html import *
from .mapping import *


class SgfClient(object):
    BaseSgfUrl = 'http://www.hoetom.com/matchviewer_html_2011.jsp?id='
    PatternSgf = r'var steps = (\[.*\]);'
    PatternName = r'height="25" nowrap>对局名称：</td>[^<]*<td>([^<]*)</td>'
    PatternBlack = r'height="25">执黑选手：</td>[^<]*<td>([^<]*)<font'
    PatternWhite = r'height="25">执白选手：</td>[^<]*<td>([^<]*)<font'
    PatternRule = r'height="25">规则：</td>[^<]*<td>([^<]*)</td>'
    PatternResult = r'height="25">比赛结果：</td>[^<]*<td>([^<]*)</td>'
    PatternTime = r'height="25">比赛日期：</td>[^<]*<td>([^<]*)</td>'
    PatternPlace = r'height="25">比赛地点：</td>[^<]*<td>([^<]*)</td>'

    def __init__(self, set_html_db=None, set_hoetom_db=None):
        self.html = HtmlClient(set_html_db)
        self.hoetom = HoetomDb(**set_hoetom_db) if set_hoetom_db else HoetomDb()

    @classmethod
    def get_url(cls, sgfid):
        return cls.BaseSgfUrl+sgfid

    @classmethod
    def match_info(cls, html):
        if not html:
            return None
        sgfinfo = dict()
        m_name = re.search(cls.PatternName, html, re.I)
        if m_name:
            sgfinfo['name'] = m_name.group(1)
        m_black = re.search(cls.PatternBlack, html, re.I)
        if m_black:
            sgfinfo['black'] = m_black.group(1)
        m_white = re.search(cls.PatternWhite, html, re.I)
        if m_white:
            sgfinfo['white'] = m_white.group(1)
        m_rule = re.search(cls.PatternRule, html, re.I)
        if m_rule:
            sgfinfo['rule'] = m_rule.group(1)
        m_result = re.search(cls.PatternResult, html, re.I)
        if m_result:
            sgfinfo['result'] = m_result.group(1)
        m_time = re.search(cls.PatternTime, html, re.I)
        if m_time:
            sgfinfo['time'] = m_time.group(1)
        m_place = re.search(cls.PatternPlace, html, re.I)
        if m_place:
            sgfinfo['place'] = m_place.group(1)
        m_sgf = re.search(cls.PatternSgf, html, re.I)
        if m_sgf:
            sgfinfo['sgf'] = m_sgf.group(1)
        return sgfinfo

    @classmethod
    def compress_sgf(cls, sgf):
        compress_sgf = []
        for step in sgf:
            compress_sgf.append(dict(
                x=step['x'],
                y=step['y'],
                p=1 if step['black']
                else 2 if step['white']
                else None,
                c=step['comment']
            ))
        return compress_sgf

    def update_sgf(self, sgfid):
        pass

    def open_db(self):
        self.html.open_db()
        logging.info('open html db: {}'.format(self.html.db.config))
        self.hoetom.open()
        logging.info('open hoetom db: {}'.format(self.hoetom.config))
        return self

    def close_db(self):
        self.hoetom.close()
        logging.info('cloase hoetom db')
        self.html.close_db()
        logging.info('close html db')

    def __enter__(self):
        return self.open_db()

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.close_db()


if __name__ == '__main__':
    pass