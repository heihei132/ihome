#coding:utf8

#功能:专门处理静态文件

from flask import Blueprint
from flask import current_app
from flask_wtf.csrf import generate_csrf

"""
需求:
1. 直接通过静态的html文件就可以访问到指定的内容
    方式: 使用current_app.send_static_file(路径)  可以根据指定的路径找到static底下的静态文件资源

2. 如果直接访问根路径,就自动跳转到首页index.html中
    方式: 自定义转换器,判断如果没有任何文件名传递进来,就拼接index.html即可

3. 如何设置logo小图标
    方式:所有的浏览器，在访问网站的时候都会去找ｓｔａｔｉｃ资源文件下的favicon.ico
        如果是favicon.ico文件名的情况下,不作处理

"""

#1.创建蓝图对象
web_html = Blueprint("web_html",__name__)

#2.使用蓝图装饰视图函数
@web_html.route('/<re(r".*"):file_name>')
def get_static_html(file_name):

    #判断file_name是否有内容
    if not file_name:
        file_name = "index.html"

    #判断如果不是favicon.ico的情况下才做拼接
    if file_name != "favicon.ico":
        file_name = "html/" + file_name

    #调用send_static_file方法，获取static文件底下的资源，返回response对象
    response = current_app.send_static_file(file_name)

    #设置csrf_token
    csrf_token = generate_csrf()
    response.set_cookie("csrf_token",csrf_token)

    return response


