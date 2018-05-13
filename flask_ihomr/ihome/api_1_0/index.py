#coding:utf8
from flask import session

from . import api
import logging
from flask import current_app
from ihome import models


@api.route('/',methods=["GET","POST"])
def index():

    # session["name"] = "zhangsan"

    #使用logging模块打印数据
    logging.debug("调试信息")
    logging.info("详细信息")
    logging.warning("警告信息")
    logging.error("错误信息")

    #还可以通过应用程序来输出, 和上面的格式输出在控制台不一样,在文件中一样
    current_app.logger.debug("===调试信息")
    current_app.logger.info("===详细信息")
    current_app.logger.warning("===警告信息")
    current_app.logger.error("===错误信息")


    return "helloworld"