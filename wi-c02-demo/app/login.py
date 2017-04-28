# coding: utf8
from common import lib, db

accounts = {
    'ada': '123',
    'bob': '123',
    'candy': '123',
    'david': '123',
}

class Login(lib.BaseHandler):
    def get(self):
        data = {'accounts': sorted(accounts.items())}
        self.respond('login.html', data)

    def post(self):
        name = self.request.get('name')
        passwd = self.request.get('passwd')

        user = db.get_user2(name, passwd)
        if not user:
            return self.respond_err('name / password not match')

        ss = lib.RedisSession.create_new()
        ss['user'] = name
        ss.save()

        self.response.set_cookie('_sid', ss.sid, path='/')
        self.redirect('/index')

class Logout(lib.BaseHandler):
    def get(self):
        self.response.delete_cookie('_sid', path='/')
        if self.session:
            self.session.delete()
            self.session = None
        self.redirect('/login')
