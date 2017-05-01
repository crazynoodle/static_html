import os
import re, cgi, json, threading, logging, urllib
from wsgiref.headers import Headers
from jinja2 import Environment, FileSystemLoader
from commons.lib import Request,Response,get_curtime,RedisSession
from commons.model import User
from config import _RESPONSE_STATUSES
import functools


#define a global threading object(:ctx) to store Request\Response\Session
ctx = threading.local()

# Implement of URL Interceptor
_RE_INTERCEPTOR_STARTS_WITH = re.compile(r'^([^\*\?]+)\*?$')
_RE_INTERCEPTOR_ENDS_WITH = re.compile(r'^\*([^\*\?]+)$')

def _build_pattern_fn(pattern):
    """
    input URL str for matching:
    return a func which accept a str as params,
    check whether the str mathch pattern or not
    """
    m = _RE_INTERCEPTOR_STARTS_WITH.match(pattern)
    if m:
        return lambda p: p.startswith(m.group(1))
    m = _RE_INTERCEPTOR_ENDS_WITH.match(pattern)
    if m:
        return lambda p: p.endswith(m.group(1))
    raise ValueError('Invalid pattern definition in interceptor.')


def interceptor(pattern='/'):
    """ An @interceptor decorator. """
    def _decorator(func):
        func.__interceptor__ = _build_pattern_fn(pattern)
        return func
    return _decorator


def _build_interceptor_fn(func, next):
    """
    build the func excute chain
    """

    def _wrapper():
        if func.__interceptor__(ctx.request.path_info):
            return func(next)
        else:
            return next()
    return _wrapper


def _build_interceptor_chain(last_fn, *interceptors):
    """ Build interceptor chain. """
    L = list(interceptors)
    L.reverse()
    fn = last_fn
    for f in L:
        fn = _build_interceptor_fn(f, fn)
    return fn

def check_session():
    sid = ctx.request.cookies.get('_sid')
    if not sid:
        return None
    return RedisSession.get_by_sid(sid)


@interceptor('/')
def basic_interceptor(next):
    logging.warning('basic_interceptor func is called!!!')
    # logging.info('try to bind user from session cookie...')
    user = None
    ctx.session = check_session()
    ctx.request.user = None
    if ctx.session:
        logging.warning('parse session cookie _sid...')
        user_acct = ctx.session['user']
        user = User.get('where account = ?',user_acct)
        if user:
            logging.warning('bind user <%s> to session...' % user.account)
    # else:
        #the logic might be wrong, this case forbid traveler to do further visiting
        #raise HttpError.redirect('/') #if dont have any session record,redirect to index.html page
        #if she is a traveler,it should pass
    try:
        ctx.request.user = user
        return next()
    finally:
        logging.warning('basic_interceptor: finnally part is executed!!!')
        if ctx.session:
            ctx.session.save()

# If she is an user of this website,we should check her authority,
# to see if she has the right to access further
@interceptor('/user/')
def user_interceptor(next):
    user = ctx.request.user
    logging.warning('user_interceptor is called!')
    if user:
        return next()
    raise HttpError.seeother('/')#return to home page

class Router:
    def __init__(self):
        self.routes = []

    def add(self, method, path, callback):
        self.routes.append({
            'method': method,
            'path': path,
            'callback': callback
        })

    def match(self, method, path):
        for r in filter(lambda x: x['method'] == method.upper(), self.routes):
            matched = re.compile(r['path']).match(path)
            if matched:
                kwargs = matched.groupdict()
                return r['callback'], kwargs
        # return http404, {}
        raise HttpError.notfound()

class _HttpError(Exception):
    """
    ## Handle exception cases ##
    HttpError that defines http error code.
    """
    def __init__(self, code):
        """
        Init an HttpError with response code.
        """
        super(_HttpError, self).__init__()
        self.status = '%d %s' % (code, _RESPONSE_STATUSES[code])
        self._headers = None

    def header(self, name, value):
        """
        add the customized header
        """
        if not self._headers:
            self._headers = [_HEADER_X_POWERED_BY]
        self._headers.append((name, value))

    @property
    def headers(self):
        """
        return _headers
        """
        if hasattr(self, '_headers'):
            return self._headers
        return []

    def __str__(self):
        return self.status

    __repr__ = __str__


class _RedirectError(_HttpError):
    """
    RedirectError that defines http redirect code.

    """
    def __init__(self, code, location):
        """
        Init an HttpError with response code.
        """
        super(_RedirectError, self).__init__(code)
        self.location = location

    def __str__(self):
        return '%s, %s' % (self.status, self.location)

    __repr__ = __str__


class HttpError(object):
    """
    HTTP Exceptions
    """
    @staticmethod
    def badrequest():
        """
        Send a bad request response.

        """
        return _HttpError(400)

    @staticmethod
    def unauthorized():
        """
        Send an unauthorized response.

        """
        return _HttpError(401)

    @staticmethod
    def forbidden():
        """
        Send a forbidden response.

        """
        return _HttpError(403)

    @staticmethod
    def notfound():
        """
        Send a not found response.

        """
        return _HttpError(404)

    @staticmethod
    def conflict():
        """
        Send a conflict response.

        """
        return _HttpError(409)

    @staticmethod
    def internalerror():
        """
        Send an internal error response.

        """
        return _HttpError(500)

    @staticmethod
    def redirect(location):
        """
        Do permanent redirect.

        """
        return _RedirectError(301, location)

    @staticmethod
    def found(location):
        """
        Do temporary redirect.

        """
        return _RedirectError(302, location)

    @staticmethod
    def seeother(location):
        """
        Do temporary redirect.

        """
        return _RedirectError(303, location)

class Jinja2Template(object):
    def __init__(self, filename, charset='utf-8', **tpl_args):
        self.filename = filename
        self.charset = charset
        self.tpl_args = tpl_args

    def render_body(self, jinja2_environment):
        template = jinja2_environment.get_template(self.filename)
        return template.render(**self.tpl_args).encode(self.charset)

    def __call__(self):
        return self

class JSONRes(object):
    def __init__(self, dic, charset='utf-8', **dump_args):
        self.dic = dic
        self.json_dump_args = dump_args
        self.charset = charset
        super(JSONRes,self).__init__()

    @property
    def res(self):
        ctx.response.content_type = 'application/json'
        return json.dumps(self.dic, **self.json_dump_args).encode(self.charset)

    def __call__(self):
        return self


class App:
    def __init__(self, templates=None):
        self.router = Router()
        self._interceptors = []
        if templates is None:
            templates = [os.path.join(os.path.abspath('.'), 'templates')]
        self.jinja2_environment = Environment(loader=FileSystemLoader(templates))
        logging.basicConfig(filename='./logs/debug.log',level=logging.DEBUG, filemode='a')
        logging.warning('time: ' + get_curtime() + ' ' + 'start the debug.log')
        self.add_interceptor(basic_interceptor)
        self.add_interceptor(user_interceptor)

    def route(self, path=None, method='GET', callback=None):
        def decorator(callback_func):
            self.router.add(method, path, callback_func)
            return callback_func
        return decorator(callback) if callback else decorator

    def fn_route(self):
        logging.warning('fn_route func called!!!')
        request_method = ctx.request.request_method
        path_info = ctx.request.path_info
        callback, kwargs = self.router.match(request_method,path_info)
        return callback(**kwargs)

    def add_interceptor(self, func):
        """ add interceptor """
        self._interceptors.append(func)
        logging.warning('Add interceptor: %s' % str(func))


    def __call__(self, env, start_response):
        ctx.request = Request(env)
        response = ctx.response = Response()
        ctx.session = None
        ctx.root_path = os.path.join(os.path.abspath('.'))

        logging.warning('request path_info: ' + ctx.request.path_info)
        self._interceptors
        fn_exec = _build_interceptor_chain(self.fn_route, *self._interceptors)

        try:
            r = fn_exec()
            if isinstance(r, Jinja2Template):
                r = [r.render_body(self.jinja2_environment)]
            if isinstance(r, unicode):
                r = r.encode('utf-8')
            if isinstance(r,JSONRes):
                r = [r.res]
            if r is None:
                r = []
            start_response(response.status, response.headers)
            return r
        except _RedirectError, e:
            response.set_header('Location', e.location)
            start_response(e.status, response.headers)
            return []
        except _HttpError, e:
            start_response(e.status, response.headers)
            return ['<html><body><h1>', e.status, '</h1></body></html>']
        except Exception, e:
            logging.exception(e)
            start_response('500 Internal Server Error', [])
            return ['<html><body><h1>Oh, we are so so sorry! 500 Internal Server Error</h1></body></html>']
        finally:
            del ctx.root_path
            del ctx.request
            del ctx.response
            del ctx.session
