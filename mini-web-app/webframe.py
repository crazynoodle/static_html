import os
import re, cgi, json, threading, logging
from urllib.parse import parse_qs
from wsgiref.headers import Headers
from jinja2 import Environment, FileSystemLoader
from common import lib

#define a global threading object(:ctx) to store Request\Response\Session
ctx = threading.local()

# Implement of URL Interceptor
_RE_INTERCEPTOR_STARTS_WITH = re.compile(r'^([^\*\?]+)\*?$')
_RE_INTERCEPTOR_ENDS_WITH = re.compile(r'^\*([^\*\?]+)$')

def _build_pattern_fn(pattern):
    """
    传入需要匹配的字符串： URL
    返回一个函数，该函数接收一个字符串参数，检测该字符串是否
    符合pattern
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
    拦截器接受一个next函数，这样，一个拦截器可以决定调用next()继续处理请求还是直接返回
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
    logging.info('try to bind user from session cookie...')
    user = None
    # cookie = ctx.request.cookies.get(_COOKIE_NAME)
    ctx.session = check_session()
    if ctx.session
        logging.info('parse session cookie _sid...')
        user_acct = ctx.session['user']
        user = User.get(user_acct)
        if user:
            logging.info('bind user <%s> to session...' % user.account)
    else:
        #the logic might be wrong, this case forbid traveler to do further visiting
        #raise HttpError.redirect('/') #if dont have any session record,redirect to index.html page
        #if she is a traveler,it should pass
    try:
        ctx.request.user = user
        return next()
    finally:
        if ctx.session:
            ctx.session.save()

# If she is an user of this website,we should check her authority,
# to see if she has the right to access further
@interceptor('/user/')
def user_interceptor(next):
    user = ctx.request.user
    if not user:
        raise HttpError.redirect('/')#return to home page
    return next

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
        添加header， 如果header为空则 添加powered by header
        """
        if not self._headers:
            self._headers = [_HEADER_X_POWERED_BY]
        self._headers.append((name, value))

    @property
    def headers(self):
        """
        使用setter方法实现的 header属性
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

class Request:
    """ Request Content """
    def __init__(self, environ, charset='utf-8'):
        self.environ = environ
        self._body = None
        self.charset = charset

    @property
    def forms(self):
        form = cgi.FieldStorage(
            fp=self.environ['wsgi.input'],
            environ=self.environ,
            keep_blank_values=True,
        )
        params = {k: form[k].value for k in form}
        return params

    @property
    def query(self):
        return parse_qs(self.environ['QUERY_STRING'])

    @property
    def body(self):
        if self._body is None:
            content_length = int(self.environ.get('CONTENT_LENGTH', 0))
            self._body = self.environ['wsgi.input'].read(content_length)
        return self._body

    @property
    def text(self):
        return self.body.decode(self.charset)

    @property
    def json(self):
        return json.loads(self.body)


class Response:
    default_status = '200 OK'
    default_content_type = 'text/html; charset=UTF-8'

    def __init__(self, body='', status=None, headers=None, charset='utf-8'):
        self._body = body
        self.status = status or self.default_status
        self.headers = Headers()
        self.charset = charset

        if headers:
            for name, value in headers.items():
                self.headers.add_header(name, value)

    @property
    def body(self):
        if isinstance(self._body, str):
            return self._body.encode(self.charset)
        return self._body

    @property
    def header_list(self):
        if 'Content-Type' not in self.headers:
            self.headers.add_header('Content-Type', self.default_content_type)
        return self.headers.items()

class Jinja2Template(object):
    def __init__(self, filename, charset='utf-8', **tpl_args):
        self.filename = filename
        self.tpl_args = tpl_args
        self.charset = charset

    def render_body(self, jinja2_environment):
        template = jinja2_environment.get_template(self.filename)
        return template.render(**self.tpl_args).encode(self.charset)

class App:
    def __init__(self, templates=None):
        self.router = Router()
        self._interceptors = []
        if templates is None:
            templates = [os.path.join(os.path.abspath('.'), 'templates')]
        self.jinja2_environment = Environment(loader=FileSystemLoader(templates))

    def route(self, path=None, method='GET', callback=None):
        def decorator(callback_func):
            self.router.add(method, path, callback_func)
            return callback_func
        return decorator(callback) if callback else decorator

    def fn_route(self):
        request_method = ctx.request.request_method
        path_info = ctx.request.path_info
        callback, kwargs = self.router.match(request_method,path_info)
        return callback(**kwargs)

    def add_interceptor(self, func):
        """ add interceptor """
        self._interceptors.append(func)
        logging.info('Add interceptor: %s' % str(func))


    def __call__(self, env, start_response):
        ctx.request = Request(env)
        response = ctx.response = Response()
        ctx.session = None
        ctx.root_path = os.path.join(os.path.abspath('.'))

        self.add_interceptor(basic_interceptor)
        self.add_interceptor(user_interceptor)
        fn_exec = _build_interceptor_chain(self.fn_route(), *self._interceptors)
        
        try:
            r = fn_exec()
            if isinstance(r, Jinja2Template):
                r = [r.render_body(self.jinja2_environment)]
            if isinstance(r, unicode):
                r = r.encode('utf-8')
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
            return ['<html><body><h1>500 Internal Server Error</h1></body></html>']
        finally:
            del ctx.root_path
            del ctx.request
            del ctx.response
            del ctx.session
