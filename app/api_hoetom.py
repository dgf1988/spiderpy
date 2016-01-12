
from lib.url import Url
import re


class HoetomDBClient(SqlDB):
    def __init__(self, user='root', passwd='guofeng001', db='hoetom'):
        SqlDB.__init__(self, user=user, passwd=passwd, db=db)
        
        
class HoetomClient(object):
    @staticmethod
    def httpget(url):
        if isinstance(url, str):
            return Url(url).httpget(charset='gbk')
        if isinstance(url, Url):
            return url.httpget(charset='gbk')
    
    @staticmethod
    def gethtml(url):
        code, html = HoetomClient.httpget(url)
        if code is 200:
            return html
        return ''
    

class Country(object):
    Table = 'country'
    ID = 'id'
    Name = 'name'

    def __init__(self, name='', id=0):
        self.id = 0
        self.name = ''
        if id:
            self.id = id
        if name:
            self.name = name

    def save(self, db: HoetomDBClient):
        test_save = db.table(Country.Table).where(name=self.name).select(Country.ID)
        if test_save:
            return test_save[0][Country.ID]
        return db.table(Country.Table).set(name=self.name).set()

    @staticmethod
    def list(db: HoetomDBClient, length=0, skip=0):
        return db.table(Country.Table).limit(length, skip).select()

    @staticmethod
    def find(db: HoetomDBClient, name: str):
        find = db.table(Country.Table).where(name=name).select(Country.ID, Country.Name)
        if find:
            return find[0]

    @staticmethod
    def get(db: HoetomDBClient, countryid: int):
        get = db.table(Country.Table).where(id=countryid).select(Country.ID, Country.Name)
        if get:
            return get[0]


class Rank(object):
    Table = 'rank'
    ID = 'id'
    Rank = 'rank'

    def __init__(self, rank='', id=0):
        self.id = 0
        self.rank = ''
        if id:
            self.id = id
        if rank:
            self.rank = rank

    def save(self, db: HoetomDBClient):
        test_save = db.table(Rank.Table).where(rank=self.rank).select(Rank.ID)
        if test_save:
            return test_save[0][Rank.ID]
        return db.table(Rank.Table).set(rank=self.rank).set()

    @staticmethod
    def list(db: HoetomDBClient, length=0, skip=0):
        return db.table(Rank.Table).limit(length, skip).select()

    @staticmethod
    def find(db: HoetomDBClient, rank: str):
        find = db.table(Rank.Table).where(rank=rank).select(Rank.ID, Rank.Rank)
        if find:
            return find[0]

    @staticmethod
    def get(db: HoetomDBClient, rankid: int):
        get = db.table(Rank.Table).where(id=rankid).select(Rank.ID, Rank.Rank)
        if get:
            return get[0]


class Sex(object):
    Default = 0
    Boy = 1
    Girl = 2

    @staticmethod
    def sex(sex: str):
        sex = sex.strip()
        if sex == '男':
            return Sex.Boy
        if sex == '女':
            return Sex.Girl
        return Sex.Default


class Player(object):
    Table = 'player'
    ID = 'id'
    Hoetomid = 'hoetomid'
    P_name = 'p_name'
    P_sex = 'p_sex'
    P_nat = 'p_nat'
    P_rank = 'p_rank'
    p_birth = 'p_birth'

    def __init__(self, hoetomid=0, name='', sex=Sex.Default, nat=Country(), rank=Rank(), birth='0000-00-00'):
        self.hoetomid = hoetomid
        self.p_name = name
        self.p_sex = sex
        self.p_nat = nat
        self.p_rank = rank
        if not birth:
            birth = '0000-00-00'
        self.p_birth = birth

    def save(self, db: HoetomDBClient):
        nat = self.p_nat.save(db)
        rank = self.p_rank.save(db)
        return db.table(Player.Table)\
                        .set(hoetomid=self.hoetomid,
                             p_name=self.p_name,
                             p_sex=self.p_sex,
                             p_nat=nat,
                             p_rank=rank,
                             p_birth=self.p_birth)\
                        .set()

    def update(self, db: HoetomDBClient):
        id = Player.find(db, hoetomid=self.hoetomid)[0][Player.ID]
        nat = self.p_nat.save(db)
        rank = self.p_rank.save(db)
        return db.table(Player.Table)\
                        .set(hoetomid=self.hoetomid,
                             p_name=self.p_name,
                             p_sex=self.p_sex,
                             p_nat=nat,
                             p_rank=rank,
                             p_birth=self.p_birth)\
                        .update()

    @staticmethod
    def find(db: HoetomDBClient, **kwargs):
        return db.table(Player.Table).where(**kwargs).select()

    @staticmethod
    def exist_name(db: HoetomDBClient, name: str):
        find = db.table(Player.Table).where(p_name=name).select(Player.ID)
        if find:
            return find

    @staticmethod
    def from_html(html: str):
        m_player = re.search(r'href="\?id=(?P<id>\d+)&refresh=y">(?P<name>\w+)', html, re.IGNORECASE)
        if not m_player:
            return None
        hoetomid = m_player.group('id')
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

        return Player(int(hoetomid), name, Sex.sex(sex), Country(nat), Rank(rank), birth)

    def __str__(self):
        str_items = ['hoetomid: %s' % self.hoetomid,
                     'name: %s' % self.p_name,
                     'sex: %s' % self.p_sex,
                     'nat: %s' % self.p_nat.name,
                     'rank: %s' % self.p_rank.rank,
                     'birth: %s' % self.p_birth]
        return '\n'.join(str_items)

    def __eq__(self, other):
        if not isinstance(other, Player):
            return False
        return self.p_name == other.p_name and self.p_birth == other.p_birth and self.p_nat == other.p_nat
