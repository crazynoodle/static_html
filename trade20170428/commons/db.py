# coding: utf8
import MySQLdb
from MySQLdb.cursors import DictCursor
from DBUtils.PooledDB import PooledDB
from config import MYSQL_CONF

db_pool = None


class DBPool(object):
    """docstring for DBPool"""
    def __init__(self, pool):
        self.pool = pool

    def get_conn(self):
        return self.pool.connection()
        
def create_mdb_pool():
    _pool = PooledDB(**MYSQL_CONF)
    db_pool = DBPool(_pool)



def random_id(t=None):
    """
    生成一个唯一id   由 当前时间 + 随机数（由伪随机数得来）拼接得到
    """
    if t is None:
        t = time.time()
    return '%015d%s000' % (int(t * 1000), uuid.uuid4().hex)

class Dict(dict):
    """
    dict object
    can access a dict like: x.key = value
    """
    def __init__(self, names=(), values=(), **kw):
        super(Dict, self).__init__(**kw)
        for k, v in zip(names, values):
            self[k] = v

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Dict' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value        

def _select(sql,first,*args):
    sql = sql.replace('?','%s')
    _db = MySQLdb.connect(**MYSQL_CONF)
    _c = _db.cursor()
    _c.execute(sql,args)
    try:
        if first:
            values = _c.fetchone()
            if not values:
                return None
            return Dict(names, values)
        return [Dict(names, x) for x in _c.fetchall()]
    finally:
        if _c:
            _c.close()

def select(sql, *args):
    return _select(sql,False, *args)

def select_one(sql,*args):
    return _select(sql, True, *args)

def _update(sql, *args):
    sql = sql.replace('?','%s')
    _db = MySQLdb.connect(**MYSQL_CONF)
    _c = _db.cursor()
    _c.execute(sql,args)
    try:
        r = _c.rowcount
        _db.commit()
        return r
    except MySQLdb.Error,e:
        if _db:
            _db.rollback()
    finally:
        if _c:
            _c.close()

def update(sql, *args):
    return _update(sql, *args)

def insert(table, **kw):
    """
    execute insert sql
    """
    cols, args = zip(*kw.iteritems())
    sql = 'insert into `%s` (%s) values (%s)' % (table, ','.join(['`%s`' % col for col in cols]), ','.join(['?' for i in range(len(cols))]))
    return _update(sql, *args)

def db_exec(sql, params=()):
    _db = MySQLdb.connect(**MYSQL_CONF)
    _c = _db.cursor(DictCursor)
    _c.execute(sql, params)
    _db.commit()
    return _c.fetchall()

def get_goods_by_tag(tag_name):
    #TODO: inplement the join search
    return db_exec('SELECT * FROM user WHERE name=%s', (name,))