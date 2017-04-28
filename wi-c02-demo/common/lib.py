# coding: utf8

import cPickle as pickle
import random
import string

import jinja2
import redis
import webapp2

from config import REDIS_CONF


##############################
def to_unicode(data, encoding='utf-8'):
    import collections
    _encoding = encoding
    def _convert(data):
        if isinstance(data, unicode):
            return data
        elif isinstance(data, str):
            return unicode(data, _encoding)
        elif isinstance(data, collections.Mapping):
            return dict(map(_convert, data.iteritems()))
        elif isinstance(data, collections.Iterable):
            return type(data)(map(_convert, data))
        else:
            return data
    return _convert(data)

def render(file_path, data={}):
    encoding = 'utf-8'
    data = to_unicode(data, encoding)
    env = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))
    template = env.get_template(file_path)
    return template.render(**data).encode(encoding)

def random_string(length):
    choices = string.ascii_letters + string.digits
    return ''.join(random.choice(choices) for _ in xrange(length))

##############################
class RedisSession(object):
    _prefix = 'web-security-session-'
    _expire_time = 3600

    def __init__(self, sid, data):
        self.sid = sid
        self.data = data
        # self.token = token

    @staticmethod
    def create_new():
        return RedisSession(random_string(32), {'token':random_string(32)})

    @classmethod
    def get_by_sid(cls, sid):
        raw_data = cls.get_conn().get(cls._prefix + sid)
        if not raw_data:
            return None
        return RedisSession(sid, pickle.loads(raw_data))

    def save(self):
        self.get_conn().setex(self._prefix + self.sid, self._expire_time,
                              pickle.dumps(self.data))

    def delete(self):
        self.get_conn().delete(self._prefix + self.sid)

    def __getitem__(self, key):
        return self.data[key]

    def get(self, key, default=None):
        return self.data.get(key, default)

    def __delitem__(self, key):
        del self.data[key]

    def __setitem__(self, key, value):
        self.data[key] = value

    @classmethod
    def get_conn(cls):
        return redis.StrictRedis(**REDIS_CONF)

##############################
class BaseHandler(webapp2.RequestHandler):
    _must_login = False

    def respond(self, pat, data={}):
        self.response.body = render(pat, data)

    def respond_err(self, msg):
        self.response.body = render('msg.html', {'msg': msg})

    def check_session(self):
        sid = self.request.cookies.get('_sid')
        if not sid:
            return None
        return RedisSession.get_by_sid(sid)

    def dispatch(self):
        self.session = self.check_session()
        if not self.session and self._must_login:
            return self.redirect('/login')
        try:
            return super(BaseHandler, self).dispatch()
        finally:
            if self.session:
                self.session.save()

class AuthHandler(BaseHandler):
    _must_login = True
