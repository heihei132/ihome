# coding:utf8

# 这是一个配置文件

import logging
import redis


class BaseConfig(object):
    SECRET_KEY = "jdfkdjkfjkd"

    # 数据库配置
    SQLALCHEMY_DATABASE_URI = "mysql://root:mysql@localhost:3306/flask_ihome"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # redis配置
    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6379

    # session配置
    SESSION_TYPE = "redis"  # 存储类型
    SESSION_USE_SIGNER = True  # 签名处理
    SESSION_REDIS = redis.StrictRedis(REDIS_HOST, REDIS_PORT)  # 存储位置
    PERMANENT_SESSION_LIFETIME = 3600 * 24 * 2  # 默认的时间是31天,单位秒,设置成两天


# 开发模式
class DevelopConfig(BaseConfig):
    DEBUG = True
    log_level = logging.DEBUG


# 生产模式
class ProductConfig(BaseConfig):
    log_level = logging.ERROR
    pass


# 提供一个统一的获取方式
config_dict = {
    "develop": DevelopConfig,
    "product": ProductConfig
}
