#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Models for user, goods, account,goods_order,topup_order.
'''

import time, uuid

from db import random_id
from orm import Model, StringField, BooleanField, FloatField, TextField,IntegerField,TimeField

class User(Model):
    __table__ = 'user'

    id = IntegerField(primary_key=True,insertable=False,ddl='int(11)')
    account = StringField(updatable=False,ddl='varchar(50)')
    password = StringField(updatable=False,ddl='varchar(50)',defalult='********')
    name = StringField(updatable=False,ddl='varchar(20)')
    birthday = StringField(updatable=False,ddl='varchar(20)')
    phone = StringField(updatable=False,ddl='varchar(16)')
    address = StringField(updatable=False,ddl='varchar(100)')
    post = StringField(updatable=False,ddl='varchar(8)')
    status = IntegerField(ddl='tinyint(1)')

class Goods(Model):
    __table__ = 'goods'

    id = IntegerField(primary_key=True,insertable=False,ddl='int(11)')
    goods_id = StringField(updatable=False,ddl='varchar(50)')
    goods_name = StringField(updatable=False,ddl='varchar(20)')
    owner_account = StringField(updatable=False, ddl='varchar(50)')
    buyer_account = StringField(ddl='varchar(50)')
    img_filename = StringField(updatable=False,ddl='varchar(50')
    description = StringField(updatable=False,default='',ddl='varchar(500)')
    goods_price = FloatField(updatable=False,default=0.0, ddl='real')
    status = IntegerField(default=0,ddl='tinyint(1)')
    deal_time = TimeField(default=0,ddl='timestamp')


class Account(Model):
    __table__ = 'account'

    id = IntegerField(primary_key=True,insertable=False,ddl='int(11)')
    account = StringField(updatable=False, ddl='varchar(50)')
    balance = FloatField(default=0.0,ddl='real')
    status = IntegerField(default=0.0,ddl='tinyint(1)')

class Goodstag(Model):
    __table__ = 'goodstag'

    id = IntegerField(primary_key=True,insertable=False,ddl='int(11)')
    tag_name = StringField(updatable=False, ddl='varchar(20)')
    goods_id = StringField(updatable=False, ddl='varchar(50)')
    status = IntegerField(updatable=True)

class Dealorder(Model):
    __table__ = 'dealorder'

    id = StringField(primary_key=True, default=random_id, ddl='varchar(50)')
    buyer_account = StringField(updatable=False, ddl='varchar(50)')
    seller_account = StringField(updataeble=False, ddl='varchar(50)')
    goods_price = FloatField(updatable=False, default=0.0)
    status = IntegerField(default=0)

class Topuporder(Model):
    __table__ = 'topuporder'

    id = StringField(primary_key=True, default=random_id, ddl='varchar(50)')
    account = StringField(ddl='varchar(50)')
    topup_amount = FloatField(updatable=False,default=0.0)
    status = IntegerField(updatable=True,default=0)





