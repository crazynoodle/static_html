#!/usr/bin/python
# Filename: dispath.py

from webframe import App, Jinja2Template, HttpError,ctx
from wsgiref.simple_server import make_server
from wsgi_static_middleware import StaticMiddleware
from commons.model import User, Goods, Dealorder, Topuporder, Account,Goodstag
from commons import lib,db
import logging

def temRedirect(location):
	raise HttpError.seeother(location)

def perRedirect(location):
	raise HttpError.redirect(location)

def unAuthorizedError():
	raise HttpError.unauthorized()

#web entrance interface
app = App()

# @app.route(r'^/$','GET')
# def index():
# 	user = ctx.request.user
# 	#implemet get_goods
# 	goods = None
# 	return Jinja2Template('index.html',_user=user,_goods=goods)

@app.route(r'^/$','GET')
def index():
	user = ctx.request.user
	logging.warning('path_info: ' + ctx.request.path_info)
	#TODO:: complete the get_goods function
	goods = None
	logging.warning('index func is called!!!')
	return Jinja2Template('index.html',_user=user,_goods=goods)

@app.route(r'^/login$','GET')
def login():
	return perRedirect('/')

@app.route(r'^/login$','POST')
def user_login():
	account = ctx.request.get('account').lower()
	passwd = ctx.request.get('password')

	user = User.find_first('where account=?',account)
	if not user:
		return unAuthorizedError()

	ss = lib.RedisSession.create_new()
	ss['user'] = account
	ss.save()

	ctx.response.set_cookie('_sid', ss.sid,max_age=3600)
	return perRedirect('/')

@app.route(r'^/user/logout$','GET')
def logout():
	user = ctx.request.user
	ctx.response.delete_cookie('_sid')
	if ctx.session:
		ctx.session.delete()
		ctx.session = None
	return perRedirect('/')

@app.route(r'^/register$','GET')
def register():
	return Jinja2Template('register.html',)

@app.route(r'^/register$', 'POST')
def user_register():
	umsg = ctx.request.input(account='',name='',password='',birthday='',phone='',address='',post='')
	account = umsg.account.strip()
	name = umsg.name.strip()
	password = umsg.password.strip()
	birthday = umsg.birthday.strip()
	phone = umsg.phone.strip()
	address = umsg.address.strip()
	post = umsg.post.strip()
	#TODO:add some format check for the fllowing params
	if not account:
		msg = 'account is empty!'
		return Jinja2Template('msg.html',{'msg':msg})
	if not name:
		msg = 'name is empty!'
		return Jinja2Template('msg.html',{'msg':msg})
	if not password:
		msg = 'password is empty!'
		return Jinja2Template('msg.html',{'msg':msg})
	if not birthday:
		msg = 'password is empty!'
		return Jinja2Template('msg.html',{'msg':msg})
	if not phone:
		msg = 'phone number is empty!'
		return Jinja2Template('msg.html',{'msg':msg})
	if not address:
		msg = 'address is empty!'
		return Jinja2Template('msg.html',{'msg':msg})
	user = User.find_first('where account=?',account)
	if user:
		msg = 'user has been register before!'
		return Jinja2Template('msg.html',{'msg':msg})
	user  = User(account=account,name=name,password=password,\
			birthday=birthday,phone=phone,address=address,post=post)
	user.insert()

	status = 0
	account = Account(account=account,status=status)
	account.insert()
	return perRedirect('/')

@app.route(r'^/user/addgoods$','POST')
def add_goods():
	goods_info = ctx.request.input(goods_name='',description='',tags='',goods_price='')
	goods_name = goods_info.goods_name.strip()
	goods_description = goods_info.description.strip()
	goods_ori_img = ctx.request.get('goods_img')
	img_filename = goods_img.Filename
	img_type = img_filename.spilt('.')[-1]
	#generate a unique fileid for the img file of this goods
	img_filename = random_id() + img_type if img_type else random_id() + '.jpg'
	fout = open(ctx.root_path +'/static/img/' + img_filename,'w')
	fout.write(goods_ori_img.file.read())
	fout.close()
	goods_owner_acct = user.account
	goods_id = random_id()
	#insert the goods into 
	goods = Goods(goods_id=goods_id,owner_account=goods_owner_acct,goods_name=goods_name,\
					img_filename=img_filename,description=goods_description,goods_price=goods_price,status=3)
	goods.insert()

	#build the relation between goods and tags
	goods_tags_list = goods_info.tags.strip().split(' ')
	for tag in goods_tags_list:
		goodstag = Goodstag(goods_id=goods_id,tag_name=tag,status=0)
		goodstag.insert()

		goods_added = Goods.find_first('where goods_id=?',goods_id)
	# goods_added.update(status=3) #need to add a new db_interface
	goods_added.status = 3
	goods_added.update()
	return redirect('/') #need to modified

def parsequery(querystring):
	qstr = querystring.split('&')
	qdict = db.Dict()
	for s in qstr:
		substr = s.split('=')
		qdict[substr[0]] = substr[1]
	return qdict

# acess method:
# 1.through url
# 2.construct an url with params,then access it by href
# 3.use GET method to summit a form
@app.route(r'^/user/showitem$','GET')
def showitemdetails():
	#get the query_string
	qstr = ctx.request.query_string()
	#parse the query_string
	qstr_dict = parsequery(qstr)
	#get the goods_id
	goods_id = qstr_dict.goods_id.lower()
	item = Goods.find_first('where goods_id = ?',goods_id)
	if not item:
		raise perRedirect('/')#redirect to a page that

	buyer = None
	if item.buyer_account:
		buyer = User.find_first('where account = ?',item.buyer_account)
	item.img_filename = '/img/' + item.img_filename
	tags = Goodstag.find_by('where goods_id = ? and status = 0',goods_id)

	_user = ctx.request.user
	return Jinja2Template('item_detail.html',_user=user,_item=item, _buyer=buyer,_tags=tags)


app = StaticMiddleware(app, static_root='static')

if __name__ == '__main__':
    httpd = make_server('', 8000, app)
    httpd.serve_forever()
