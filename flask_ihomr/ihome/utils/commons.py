#coding:utf8

#自定义转换器
#定义类，继承自BaseConverter
#编写init方法，接受两个参数
#初始化父类方法，子类规则
#将转换器添加到默认转换器
from flask import g
from flask import session, jsonify
from werkzeug.routing import BaseConverter
from ihome.utils.response_code import RET
from functools import wraps


class RegexConverter(BaseConverter):
    def __init__(self,url_map,regex):
                            #regex:新正则规则
        super(RegexConverter,self).__init__(url_map)
        self.regex = regex



#########登陆装饰器 判断用户是否登陆
def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args,**kwargs):
        #取出session中的编号
        g.user_id = session.get("user_id")

        #判断g对象中的编号
        if g.user_id:
            return view_func(*args,**kwargs)
        else:
            return jsonify(errno=RET.NODATA,errmsg="该用户未登陆")

    return wrapper
