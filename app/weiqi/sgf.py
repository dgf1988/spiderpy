# coding: utf-8
import re
import logging
import lib.orm


@lib.orm.table('sgf', 'id s_black s_white s_sgf s_name s_rule s_result s_msg s_place s_time s_update', 'id')
class SgfTable(lib.orm.Table):
    id = lib.orm.AutoIntField()
    s_black = lib.orm.CharField()
    s_white = lib.orm.CharField()
    s_sgf = lib.orm.TextField()
    s_name = lib.orm.CharField(nullable=True)
    s_rule = lib.orm.CharField(nullable=True)
    s_result = lib.orm.CharField(nullable=True)
    s_msg = lib.orm.TextField(nullable=True)
    s_place = lib.orm.CharField(nullable=True)
    s_time = lib.orm.DatetimeField(nullable=True)
    s_update = lib.orm.DatetimeField(current_timestamp=True, on_update=True)


class SgfDb(lib.orm.TableSet):
    def __init__(self, db):
        super().__init__(db, SgfTable)


class Sgf(object):
    __slots__ = ('id', 'black', 'white', 'sgf', 'name', 'rule', 'result', 'msg', 'time', 'place', 'update')

    def __init__(self):
        self.id = None
        self.black = None
        self.white = None
        self.sgf = None
        self.name = None
        self.rule = None
        self.result = None
        self.msg = None
        self.place = None
        self.time = None
        self.update = None

    def to_dict(self):
        return dict(
            id=self.id, black=self.black, white=self.white, sgf=self.sgf, name=self.name,
            rule=self.rule, result=self.result, msg=self.msg, place=self.place, time=self.time, update=self.update
        )

    def to_table(self):
        return SgfTable(
            id=self.id, s_black=self.black, s_white=self.white, s_sgf=self.sgf, s_name=self.name,
            s_rule=self.rule, s_result=self.result, s_msg=self.msg, s_place=self.place, s_time=self.time,
            s_update=self.update
        )


class SgfFile(object):
    def __init__(self, file_string):
        self.text = file_string


class SgfTitle(dict):
    def __init__(self, iterable=(), **kwargs):
        super().__init__(iterable, **kwargs)

    PatternTitle = r'((?P<key>\w+)(?P<value>(\[[^]]*\])+))+?'
    PatternItem = r'\[([^]]*)\]'

    @classmethod
    def parse(cls, string):
        result_parse = dict()
        for title in re.finditer(cls.PatternTitle, string):
            print(title.group('key'), title.group('value'))
            items = re.findall(cls.PatternItem, title.group('value'))
            if items:
                result_parse[title.group('key')] = items if len(items) > 1 else items[0]
        return cls(**result_parse)


class SgfNode(object):
    PatternNode = r'(?P<key>\w+)(?P<value>(\[[^]]*\])+)'
    PatternNodeMany = r'(?P<node>\w+(\[[^]]*\])+)'

    def __init__(self, key, value):
        self.key = key
        self.value = value

    def __iter__(self):
        yield self.key
        yield self.value

    def __str__(self):
        return '<SgfNode: {}={}>'.format(self.key, self.value)

    def __repr__(self):
        return self.__str__()

    @classmethod
    def from_string(cls, string):
        m_node = re.match(cls.PatternNode, string)
        if m_node:
            return cls(m_node.group('key'), list(m_item.group(1) for m_item in re.finditer(r'\[([^]]*)\]', m_node.group('value')) if m_item))

    @classmethod
    def from_string_many(cls, string):
        nodes = []
        for node in re.finditer(cls.PatternNodeMany, string):
            nodes.append(cls.from_string(node.group('node')))
        return nodes


class SgfTree(object):
    PatternTree = r'(?P<data>.*?)(?P<mark>\(;|\))'

    def __init__(self, data=(), child=()):
        self.data = list(data)
        self.child = list(child)

    def __str__(self):
        return '<SgfTree: {}, {}>'.format(self.data, self.child)

    def __repr__(self):
        # return '<SgfTree: data={}, child={}>'.format(self.data, self.child)
        return self.__str__()

    def __len__(self):
        return sum(len(item) for item in self.child) + len(self.data)

    @classmethod
    def from_string(cls, string):
        print(string)
        trees = [cls()]
        ms = re.finditer(cls.PatternTree, string)
        for m in ms:
            if m.group('mark') == '(;':
                if m.group('data'):
                    trees.append(cls(SgfNode.from_string_many(nodes) for nodes in re.split(r';', m.group('data'))))
            elif m.group('mark') == ')':
                if m.group('data'):
                    node = cls(SgfNode.from_string_many(nodes) for nodes in re.split(r';', m.group('data')))
                else:
                    node = trees.pop()
                trees[len(trees)-1].child.append(node)
            logging.info(trees)
        return trees[0]


t1 = '(;EV[农心杯三国擂台赛第14局：柯洁VS李世石]PC[中国]PB[柯洁]RE[黑中盘胜]BR[九段]KM[6.5]PW[李世石]WR[九段]CA[gb2312]SZ[19];B[qd];W[dc];B[pq];W[dq];B[do];W[co];B[cn];W[cp];B[ce];W[dn];B[fd];W[ed];B[ee];W[fc];B[gd];W[gc];B[hd];W[hc];B[id];W[jc];B[cm];W[en];B[dk];W[qo];B[cc];W[de];B[df];W[dd];B[cd];W[db];B[ef];W[nq];B[op];W[np];B[pn];W[qm];B[qp];W[pm];B[on];W[jp];B[qn];W[rn];B[ro];W[qi];B[hq];W[jq];B[go];W[fp];B[gp];W[fq];B[gl];W[ci];B[cj];W[ei];B[fj];W[cg];B[cf];W[gh];B[ii];W[ih];B[jh];W[gj];B[fk];W[dj];B[bj];W[hk];B[fi];W[fh];B[ig];W[gi];B[im];W[ij];B[ir];W[jr];B[or];W[ck];B[bk];W[km];B[jl];W[ji];B[hh];W[hl];B[gm];W[hm];B[hn];W[in];B[kl];W[lk];B[eh];W[ll];B[fg];W[so];B[rp];W[ki];B[qg];W[oc];B[pc];W[od];B[pf];W[rl];B[lc];W[pb];B[qb];W[nb];B[pa];W[gg];B[ob];W[ff];B[eg];W[hf];B[le];W[of];B[og];W[nf];B[ng];W[mf];B[jd];W[kc];B[ld];W[mg];B[cb];W[if];B[eb];W[da];B[ic];W[ib];B[jb];W[ha];B[kb];W[kf];B[mn];W[ek];B[dl];W[el];B[ej];W[pe];B[qe];W[fn];B[gn];W[no];B[nn];W[ln];B[mo];W[nr];B[lp];W[lr];B[gr];W[io];B[ds];W[cs];B[ca];W[fa];B[rh];W[mb];B[fe];W[nh];B[oh];W[oi];B[ni];W[mh];B[pi];W[oj];B[pj];W[ph];B[pg];W[pk];B[qj];W[rj];B[qh];W[ok];B[bo];W[bp];B[es];W[fl];B[gk];W[fr];B[fs];W[cr];B[ri];W[bn];B[bm];W[ao];B[lf];W[ke];B[kd];W[lg];B[gf];W[hg];B[nl];W[sp];B[sq];W[sn];B[rr];W[rk];B[nk];W[nj];B[fo];W[eo];B[di];W[oq];B[pr];W[oo];B[po];W[lq];B[mm];W[lm];B[js];W[ks];B[is];W[gq];B[hp];W[iq];B[kp];W[mp];B[lo];W[ko];B[pd];W[oe];B[me];W[nc];B[kq];W[kr];B[am];W[er];B[hr];W[os];B[ps];W[ns];B[an];W[bo];B[mk];W[mj];B[je];W[jf];B[ol];W[om];B[pp];W[si];B[sh];W[sj];B[he];W[pl];B[qk]C[黑中盘胜，祝贺中国队获得冠军！])'
t2 = '(;AB[qd][qc][qf][oc][nc][nb]AW[rc][qb][pb][ob](;B[ra];W[rb];B[oa];W[rd];B[re];W[sd];B[sb]C[RIGHT])(;B[rd];W[ra];B[sc];W[sb])(;B[rb];W[ra];B[sb];W[sc];B[oa];W[pa])(;B[oa];W[ra];B[sb];W[pa])(;B[sb];W[ra]))'
t3 = '(;GM[1];W[pj](;W[jp];B[dp])(;W[jd];B[dd](;W[dj])(;W[jj])))'

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    t = SgfTree.from_string(t2)
    print(t)
    print(len(t))