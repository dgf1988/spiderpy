# coding: utf-8
import re
import datetime

import api.html
import app.hoetom.table as mmodel


class Action(object):
    pass


class Player(Action):

    _base_url_ = 'http://www.hoetom.com/playerinfor_2011.jsp?id=%s'

    def __init__(self):
        pass

    def get_url(self, playerid):
        return self._base_url_ % playerid

    def get_html(self, playerid):
        return api.html.get(self.get_url(playerid))

    def get_dict(self, playerid):
        _html = self.get_html(playerid)
        return self.from_html(_html.text)

    def save(self, playerid):
        _html = self.get_html(playerid)
        _html.save()

    def update(self, playerid):
        return api.html.update(self.get_url(playerid))

    @classmethod
    def from_html(cls, str_html):
        m_player = re.search(r'href="\?id=(?P<id>\d+)&refresh=y">(?P<name>[^<]+)', str_html, re.IGNORECASE)
        if not m_player:
            return None
        hoetomid = m_player.group('id')
        name = m_player.group('name')

        m_sex = re.search(r'性别</th>\s*?<td><b>(?P<sex>\w+)', str_html, re.I)
        sex = ''
        if m_sex:
            sex = m_sex.group('sex')

        m_nat = re.search(r'国籍</th>\s*?<td><b>(?P<nat>\w+)', str_html, re.I)
        nat = ''
        if m_nat:
            nat = m_nat.group('nat')

        m_rank = re.search(r'段位</th>\s*?<td><b>(?P<rank>\w+)', str_html, re.I)
        rank = ''
        if m_rank:
            rank = m_rank.group('rank')

        m_birth = re.search(r'出生日期</th>\s*?<td><b>(?P<birth>[\d\-]+)', str_html, re.I)
        birth = ''
        if m_birth:
            birth = m_birth.group('birth')

        return dict(p_id=int(hoetomid), p_name=name, p_sex=mmodel.SEX.from_str(sex), p_nat=nat, p_rank=rank,
                    p_birth=datetime.datetime.strptime(birth, '%Y-%m-%d').date() if birth else None)


class Hoetom(object):
    def __init__(self, user='root', passwd='guofeng001', database='hoetom'):
        self.player = Player()
        pass


if __name__ == '__main__':
    api.html.db.open()

    hoetom = Hoetom()
    html = hoetom.player.get_html(1000)
    html.save()
    print(html)

    api.html.db.close()
