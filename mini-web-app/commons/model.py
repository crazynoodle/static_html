#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Models for user, goods, account,goods_order,topup_order.
'''

import time, uuid

from db import random_id
from orm import Model, StringField, BooleanField, FloatField, TextField

class User(Model):
    __table__ = 'user'

    account = StringField(primary_key=True, default=random_id, ddl='varchar(50)')
    password = StringField(ddl='varchar(30)' default='')
    name = StringField(ddl='varchar(20)')
    birthday = StringField(ddl='varchar(20)')
    phone = StringField(ddl='varchar(20)')
    address = StringField(updatable=False, ddl='varchar(100)')
    post = IntegerField()

class Goods(Model):
    __table__ = 'goods'

    id = StringField(primary_key=True, default=random_id, ddl='varchar(50)')
    owner_account = StringField(updatable=False, ddl='varchar(50)')
    goods_name = StringField(ddl='varchar(20)')
    img_filename = StringField(ddl='varchar(50')
    goods_price = FloatField(default=0.0, ddl='real(4)')
    buyer_account = StringField(ddl='varchar(50)')
    description = StringField(updatable=False,ddl='varchar(200)')
    status = IntegerField(default=0)


class Account(Model):
    __table__ = 'account'

    id = StringField(primary_key=True, default=random_id, ddl='varchar(50)')
    account = StringField(updatable=False, ddl='varchar(50)')
    balance = FloatField(updatable=False, default=0.0)
    status = IntegerField(default=0.0)

class Goodstag(Model):
    __table__ = 'goodstag'

    id = StringField(primary_key=True, default=random_id, ddl='varchar(50)')
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





