# coding:utf8
from logging.handlers import RotatingFileHandler

import logging
import redis
from flask.ext.wtf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import Session
from config import config_dict
from flask import Flask

# db的初始化
db = SQLAlchemy()


# 此处SQLAlchemy的内部代码调用了init_app才关联上了app，所以关联这一步可以挪到下面方法里再执行

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
    redis_store = redis.StrictRedis(host=config.REDIS_HOST, port=config.REDIS_PORT)

    # 配置session
    # 关联app
    Session(app)

    # 配置CSRF
    CSRFProtect(app)

    from ihome.api_1_0 import api
    # 注册蓝图
    app.register_blueprint(api)

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
