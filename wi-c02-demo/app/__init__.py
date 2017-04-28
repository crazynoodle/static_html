# coding: utf-8

from paste.urlparser import StaticURLParser
from paste.cascade import Cascade
import webapp2

from home import Home, Index, Post, Transfer
from login import Login, Logout


web_app = webapp2.WSGIApplication([
    ('/', Home),
    ('/index', Index),
    ('/post', Post),
    ('/transfer', Transfer),
    ('/login', Login),
    ('/login/logout', Logout),
])

# 在真实应用中，应该让 http server 直接响应静态请求
# 此处 demo 中用 WSGI 来响应仅仅是为了方便
static_app = StaticURLParser('static/')

application = Cascade([static_app, web_app])
