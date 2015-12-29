# -*- coding: utf-8 -*-
from lib.sqldb import *
from bs4 import BeautifulSoup
from lib.url import Url
from lib.hash import md5
from enum import unique, Enum
from api.html import Html
from lib.dbsql import *
import os
import string
import json
import datetime
import re


class HoetomDBClient(DB):
    def __init__(self, user='root', passwd='guofeng001', db='hoetom'):
        DB.__init__(**locals())


class Country(DbModel):
    __table__ = 'country'
    id = IntField(primary_key=True)
    name = CharField()


class Rank(DbModel):
    __table__ = 'rank'
    id = IntField(primary_key=True)
    rank = CharField()


class Player(DbModel):
    __table__ = 'player'
    id = IntField(primary_key=True)
    hoetomid = IntField()
    p_name = CharField()
    p_sex = IntField()
    p_nat = IntField()
    p_rank = IntField()
    p_birth = DateField()
