from app import App, Jinja2Template, HttpError
from wsgiref.simple_server import make_server
from wsgi_static_middleware import StaticMiddleware

def temRedirect(location):
	return HttpError.seeother(location)

def perRedirect(location):
	return HttpError.redirect(location)

app = App()

@app.route('^/signin','POST')
def signin():





@app.route('^/$','GET')
def index():
	user = ctx.request.user
	return Jinja2Template('index.html',_user=user,goods=_goods)
	


@app.route('^/user/$', 'POST')
def create_user(request):
    return JSONResponse({'message': 'User Created'}, status='201 Created')


@app.route('^/user/$', 'GET')
def users(request):
    users = ['user%s' % i for i in range(10)]
    return Jinja2Template('users.html', title='User List', users=users)


@app.route('^/user/(?P<name>\w+)$', 'GET')
def user_detail(request, name):
    return Response('Hello {name}'.format(name=name))

app = StaticMiddleware(app, static_root='static')

# if __name__ == '__main__':
#     app = StaticMiddleware(app, static_root='static')
#     httpd = make_server('', 8000, app)
#     httpd.serve_forever()
