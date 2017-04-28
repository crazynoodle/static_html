# coding: utf8
import MySQLdb
from MySQLdb.cursors import DictCursor
from config import MYSQL_CONF

def db_exec(sql, params=()):
    _db = MySQLdb.connect(**MYSQL_CONF)
    _c = _db.cursor(DictCursor)
    _c.execute(sql, params)
    _db.commit()
    return _c.fetchall()

def get_user(name):
    return db_exec('SELECT * FROM user WHERE name=%s', (name,))[0]

def get_user2(name, passwd):
    return db_exec("SELECT * FROM user WHERE name=%s and password=%s", (name,passwd))

def new_post(name, content):
    db_exec("INSERT INTO post (name, content, ts) VALUES (%s, %s, NOW())", (name, content))
    db_exec('UPDATE user SET credit = credit + 1000 WHERE name=%s', (name,))

def get_posts(count=10):
    return db_exec('SELECT * FROM post ORDER BY id DESC LIMIT %s', (count,))

def transfer(name, receiver, amount):
    db_exec('UPDATE user SET credit = credit - %s WHERE name=%s', (amount, name))
    db_exec('UPDATE user SET credit = credit + %s WHERE name=%s', (amount, receiver))


