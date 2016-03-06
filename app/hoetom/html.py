# coding: utf-8
import re
import datetime

from api.html import *


class PlayerInfoHtml(Html):
    def get_info(self):
        if not self.page or not self.page.text:
            return None
        m_player = re.search(r'href="\?id=(?P<id>\d+)&refresh=y">(?P<name>[^<]+)', self.page.text, re.IGNORECASE)
        if not m_player:
            return None
        hoetomid = int(m_player.group('id'))
        name = m_player.group('name')

        m_sex = re.search(r'性别</th>\s*?<td><b>(?P<sex>\w+)', self.page.text, re.I)
        sex = ''
        if m_sex:
            sex = m_sex.group('sex')

        m_nat = re.search(r'国籍</th>\s*?<td><b>(?P<nat>\w+)', self.page.text, re.I)
        nat = ''
        if m_nat:
            nat = m_nat.group('nat')

        m_rank = re.search(r'段位</th>\s*?<td><b>(?P<rank>\w+)', self.page.text, re.I)
        rank = ''
        if m_rank:
            rank = m_rank.group('rank')

        m_birth = re.search(r'出生日期</th>\s*?<td><b>(?P<birth>[\d\-]+)', self.page.text, re.I)
        birth = ''
        if m_birth:
            birth = m_birth.group('birth')

        return dict(
            p_id=hoetomid, p_name=name, p_sex=sex, p_nat=nat, p_rank=rank,
            p_birth=datetime.datetime.strptime(birth, '%Y-%m-%d').date() if birth else None
        )


def get_playerinfo(html):
        if not html:
            return None
        m_player = re.search(r'href="\?id=(?P<id>\d+)&refresh=y">(?P<name>[^<]+)', html, re.IGNORECASE)
        if not m_player:
            return None
        hoetomid = int(m_player.group('id'))
        name = m_player.group('name')

        m_sex = re.search(r'性别</th>\s*?<td><b>(?P<sex>\w+)', html, re.I)
        sex = ''
        if m_sex:
            sex = m_sex.group('sex')

        m_nat = re.search(r'国籍</th>\s*?<td><b>(?P<nat>\w+)', html, re.I)
        nat = ''
        if m_nat:
            nat = m_nat.group('nat')

        m_rank = re.search(r'段位</th>\s*?<td><b>(?P<rank>\w+)', html, re.I)
        rank = ''
        if m_rank:
            rank = m_rank.group('rank')

        m_birth = re.search(r'出生日期</th>\s*?<td><b>(?P<birth>[\d\-]+)', html, re.I)
        birth = ''
        if m_birth:
            birth = m_birth.group('birth')

        return dict(
            p_id=hoetomid, p_name=name, p_sex=sex, p_nat=nat, p_rank=rank,
            p_birth=datetime.datetime.strptime(birth, '%Y-%m-%d').date() if birth else None
        )


def get_playerid(html):
    if not html:
        return None
    findall = re.findall(r'playerinfor_2011\.jsp\?id=(\d+)', html, re.I)
    if findall:
        return [int(item) for item in findall]


class PlayerListHtml(Html):
    def get_playerid(self):
        if self.page.text:
            findall = re.findall(r'playerinfor_2011\.jsp\?id=(\d+)', self.page.text, re.I)
            if findall:
                return [int(item) for item in findall]

if __name__ == '__main__':
    pass
