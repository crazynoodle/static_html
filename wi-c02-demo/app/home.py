# coding: utf8
from common import lib, db
import hashlib

class Home(lib.AuthHandler):
    def get(self):
        user = db.get_user(self.session['user'])
        token = self.session.get('token')
        data = {'_user': user, '_token': token}
        return self.respond('home.html', data)

class Index(lib.AuthHandler):
    def get(self):
        posts = db.get_posts()
        user = db.get_user(self.session['user'])
        data = {'_user': user, 'posts': posts}
        return self.respond('index.html', data)

class Post(lib.AuthHandler):
    def post(self):
        content = self.request.get('content')
        if content:
            name = self.session['user']
            db.new_post(name, content)
        return self.redirect('/index')

class Transfer(lib.AuthHandler):
    def post(self):
        receiver = self.request.get('receiver')
        amount = self.request.get('amount')
        token = self.session.get('token')
        hashstr = hashlib.sha1(token).hexdigest()
        # print token
        # print hashstr
        # print self.request.get('hash')
        if cmp(hashstr, self.request.get('hash')):
            return self.redirect('/')
        if receiver and amount:
            amount = int(amount)
            name = self.session['user']
            db.transfer(name, receiver, amount)
        return self.redirect('/')

