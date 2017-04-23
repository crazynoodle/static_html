import os
import re
import cgi
import json
import threading
import logging
from urllib.parse import parse_qs
from wsgiref.headers import Headers
from jinja2 import Environment, FileSystemLoader

#define a global object to store request and response
ctx = threading.local()

_RESPONSE_STATUSES = {
    # Informational
    100: 'Continue',
    101: 'Switching Protocols',
    102: 'Processing',

    # Successful
    200: 'OK',
    201: 'Created',
    202: 'Accepted',
    203: 'Non-Authoritative Information',
    204: 'No Content',
    205: 'Reset Content',
    206: 'Partial Content',
    207: 'Multi Status',
    226: 'IM Used',

    # Redirection
    300: 'Multiple Choices',
    301: 'Moved Permanently',
    302: 'Found',
    303: 'See Other',
    304: 'Not Modified',
    305: 'Use Proxy',
    307: 'Temporary Redirect',

    # Client Error
    400: 'Bad Request',
    401: 'Unauthorized',
    402: 'Payment Required',
    403: 'Forbidden',
    404: 'Not Found',
    405: 'Method Not Allowed',
    406: 'Not Acceptable',
    407: 'Proxy Authentication Required',
    408: 'Request Timeout',
    409: 'Conflict',
    410: 'Gone',
    411: 'Length Required',
    412: 'Precondition Failed',
    413: 'Request Entity Too Large',
    414: 'Request URI Too Long',
    415: 'Unsupported Media Type',
    416: 'Requested Range Not Satisfiable',
    417: 'Expectation Failed',
    418: "I'm a teapot",
    422: 'Unprocessable Entity',
    423: 'Locked',
    424: 'Failed Dependency',
    426: 'Upgrade Required',

    # Server Error
    500: 'Internal Server Error',
    501: 'Not Implemented',
    502: 'Bad Gateway',
    503: 'Service Unavailable',
    504: 'Gateway Timeout',
    505: 'HTTP Version Not Supported',
    507: 'Insufficient Storage',
    510: 'Not Extended',
}

#################################################################
# 实现URL拦截器
# 主要interceptor的实现
#################################################################
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
    """
    An @interceptor decorator.
    @interceptor('/admin/')
    def check_admin(req, resp):
        pass
    """
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
    """
    Build interceptor chain.
    >>> def target():
    ...     print 'target'
    ...     return 123
    >>> @interceptor('/')
    ... def f1(next):
    ...     print 'before f1()'
    ...     return next()
    >>> @interceptor('/test/')
    ... def f2(next):
    ...     print 'before f2()'
    ...     try:
    ...         return next()
    ...     finally:
    ...         print 'after f2()'
    >>> @interceptor('/')
    ... def f3(next):
    ...     print 'before f3()'
    ...     try:
    ...         return next()
    ...     finally:
    ...         print 'after f3()'
    >>> chain = _build_interceptor_chain(target, f1, f2, f3)
    >>> ctx.request = Dict(path_info='/test/abc')
    >>> chain()
    before f1()
    before f2()
    before f3()
    target
    after f3()
    after f2()
    123
    >>> ctx.request = Dict(path_info='/api/')
    >>> chain()
    before f1()
    before f3()
    target
    after f3()
    123
    """
    L = list(interceptors)
    L.reverse()
    fn = last_fn
    for f in L:
        fn = _build_interceptor_fn(f, fn)
    return fn


# def http404(request):
#     return Response('404 Not Found', status='404 Not Found')


@interceptor('/')
def user_interceptor(next):
    logging.info('try to bind user from session cookie...')
    user = None
    cookie = ctx.request.cookies.get(_COOKIE_NAME)
    if cookie:
        logging.info('parse session cookie...')
        user = parse_signed_cookie(cookie)
        if user:
            logging.info('bind user <%s> to session...' % user.email)
    ctx.request.user = user
    return next()


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

# 用于异常处理
class _HttpError(Exception):
    """
    HttpError that defines http error code.

    >>> e = _HttpError(404)
    >>> e.status
    '404 Not Found'
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

    >>> e = _RedirectError(302, 'http://www.apple.com/')
    >>> e.status
    '302 Found'
    >>> e.location
    'http://www.apple.com/'
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

        >>> raise HttpError.badrequest()
        Traceback (most recent call last):
          ...
        _HttpError: 400 Bad Request
        """
        return _HttpError(400)

    @staticmethod
    def unauthorized():
        """
        Send an unauthorized response.

        >>> raise HttpError.unauthorized()
        Traceback (most recent call last):
          ...
        _HttpError: 401 Unauthorized
        """
        return _HttpError(401)

    @staticmethod
    def forbidden():
        """
        Send a forbidden response.
        >>> raise HttpError.forbidden()
        Traceback (most recent call last):
          ...
        _HttpError: 403 Forbidden
        """
        return _HttpError(403)

    @staticmethod
    def notfound():
        """
        Send a not found response.

        >>> raise HttpError.notfound()
        Traceback (most recent call last):
          ...
        _HttpError: 404 Not Found
        """
        return _HttpError(404)

    @staticmethod
    def conflict():
        """
        Send a conflict response.

        >>> raise HttpError.conflict()
        Traceback (most recent call last):
          ...
        _HttpError: 409 Conflict
        """
        return _HttpError(409)

    @staticmethod
    def internalerror():
        """
        Send an internal error response.

        >>> raise HttpError.internalerror()
        Traceback (most recent call last):
          ...
        _HttpError: 500 Internal Server Error
        """
        return _HttpError(500)

    @staticmethod
    def redirect(location):
        """
        Do permanent redirect.

        >>> raise HttpError.redirect('http://www.itranswarp.com/')
        Traceback (most recent call last):
          ...
        _RedirectError: 301 Moved Permanently, http://www.itranswarp.com/
        """
        return _RedirectError(301, location)

    @staticmethod
    def found(location):
        """
        Do temporary redirect.

        >>> raise HttpError.found('http://www.itranswarp.com/')
        Traceback (most recent call last):
          ...
        _RedirectError: 302 Found, http://www.itranswarp.com/
        """
        return _RedirectError(302, location)

    @staticmethod
    def seeother(location):
        """
        Do temporary redirect.

        >>> raise HttpError.seeother('http://www.itranswarp.com/')
        Traceback (most recent call last):
          ...
        _RedirectError: 303 See Other, http://www.itranswarp.com/
        >>> e = HttpError.seeother('http://www.itranswarp.com/seeother?r=123')
        >>> e.location
        'http://www.itranswarp.com/seeother?r=123'
        """
        return _RedirectError(303, location)

class Request:
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
        """
        添加拦截器
        """
        self._interceptors.append(func)
        logging.info('Add interceptor: %s' % str(func))


    def __call__(self, env, start_response):
        # request_method = env['REQUEST_METHOD'].upper()
        # path_info = env['PATH_INFO'] or '/'
        ctx.request = Request(env)
        response = ctx.response = Response()

        self.add_interceptor(user_interceptor)
        fn_exec = _build_interceptor_chain(self.fn_route(), *self._interceptors)
        
        # callback, kwargs = self.router.match(method, path)
        # response = callback(Request(env), **kwargs)
        # start_response(response.status, response.header_list)
        # if isinstance(response, TemplateResponse):
        #     return [response.render_body(self.jinja2_environment)]
        # return [response.body]
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
            del ctx.request
            del ctx.response
