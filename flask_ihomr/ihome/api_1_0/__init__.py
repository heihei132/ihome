#coding:utf8
from flask import Blueprint

#1.创建蓝图对象

api = Blueprint("api_1_0",__name__)

from . import index