#coding:utf8
import logging
from logging.handlers import RotatingFileHandler

import redis
from flask import Flask
from flask.ext.wtf import CSRFProtect
from sqlalchemy.orm import Session #用来指定session的存储位置
from flask_sqlalchemy import SQLAlchemy
from config import config_dict

#db的初始化
from ihome.utils.commons import RegexConverter

db = SQLAlchemy()
# 此处SQLAlchemy的内部代码调用了init_app才关联上了app，所以关联这一步可以挪到下面方法里再执行

redis_store = None


def create_app(config_name):
    app = Flask(__name__)

    config = config_dict.get(config_name)
    # 日志信息，通过配置对象config去拿，所以要放到config底下
    log_file(config.log_level)

    app.config.from_object(config)

    # 搭建数据库
    # 创建数据库
    # 关联app
    db.init_app(app)

    # 配置redis
    # 创建redis                   在实际操作中可能要连接一台远程的redis
    global redis_store
    redis_store = redis.StrictRedis(host=config.REDIS_HOST, port=config.REDIS_PORT)

    # 配置session
    # 关联app
    Session(app)

    # 配置CSRF
    CSRFProtect(app)

    # 将转换器添加到默认列表中
    app.url_map.converters["re"] = RegexConverter

    from ihome.api_1_0 import api
    # 注册蓝图                  url_prefix加前缀的功能,前缀也可以在创建蓝图式__name__后面添加
    app.register_blueprint(api,url_prefix="/api/v1.0")
    #注册静态蓝图到app中
    from ihome.web_html import web_html
    app.register_blueprint(web_html)

    print app.url_map

    return app



def log_file(log_level):
    # 设置日志的记录等级:常见debug<info<waring<error
    logging.basicConfig(level=log_level)  # 调试debug级
    # 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
    file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024 * 1024 * 100, backupCount=10)
    # 创建日志记录的格式                 日志等级    输入日志信息的文件名 行数    日志信息
    formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
    # 为刚创建的日志记录器设置日志记录格式
    file_log_handler.setFormatter(formatter)
    # 为全局的日志工具对象（flask app使用的）添加日记录器
    logging.getLogger().addHandler(file_log_handler)
