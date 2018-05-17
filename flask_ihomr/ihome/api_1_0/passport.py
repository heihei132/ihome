#coding:utf8
#功能描述: 注册,登录,获取登录状态,退出登录
import re

from flask import current_app
from flask import json, jsonify
from flask import request
from flask import session

from ihome import redis_store, db
from ihome.models import User
from ihome.utils.commons import login_required
from ihome.utils.response_code import RET
from . import api

#功能描述: 退出登录
#请求路径: /api/v1.0/session
#请求方式:delete
#请求参数:无
@api.route('/session',methods=["DELETE"])
# @login_required
def logout():
    """
    1.删除sessioin中的状态信息
    2.返回前端页面
    :return:
    """
    # 1.删除sessioin中的状态信息
    session.pop("user_id")
    session.pop("name")

    # 2.返回前端页面
    return jsonify(errno=RET.OK,errmsg="退出成功")

#功能描述: 获取用户登录状态
#请求路径: /api/v1.0/session
#请求方式:GET
#请求参数:无
@api.route('/session')
def get_user_login_state():
    #1.获取用户的登录状态信息
    user_id = session.get("user_id")
    # user_id = g.user_id

    #2.判断id是否存在
    if not user_id:
        return jsonify(errno=RET.DATAERR,errmsg="该用户没有登录")

    #3.通过编号查询用户对象
    try:
        user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="数据库查询异常")

    #4.判断用户是否存在
    if not user:
        return jsonify(errno=RET.NODATA,errmsg="该用户不存在")

    #5.返回用户的信息给前端页面
    user_dict = {
        "user_id" :user.id,
        "name": user.name
    }
    return jsonify(errno=RET.OK,errmsg="获取成功",data=user_dict)

#功能描述: 登录功能
#请求路径: /api/v1.0/session
#请求方式:ＰＯＳＴ
#请求参数:手机号,密码
@api.route('/session', methods=['POST'])
def login():
    """
    1.获取参数
    2.校验参数
    3.判断手机号格式
    4.通过手机号取出用户对象
    5.判断用户对象是否存在
    6.验证码密码是否正确
    7.返回登录信息给前端
    :return:
    """
    # 1.获取参数
    dict_data = request.get_json()
    mobile = dict_data.get("mobile")
    password= dict_data.get("password")

    # 2.校验参数
    if not all([mobile,password]):
        return jsonify(errno=RET.PARAMERR,errmsg="参数不完整")

    # 3.判断手机号格式
    if not re.match(r'1[3456789]\d{9}',mobile):
        return jsonify(errno=RET.DATAERR,errmsg="手机号格式错误")

    #取出错误次数,看有没有达到设置的值
    try:
        login_num = redis_store.get("login_num:%s"%mobile)
    except Exception as e:
        current_app.logger.error(e)
        login_num = 0 #如果异常了,设置成0

    #如果没有值默认设置成0
    if not login_num:
        login_num = 0

    #将取出来的错误次数转成整数
    try:
        login_num = int(login_num)
    except Exception as e:
        current_app.logger.error(e)
        login_num = 0

    #判断用户的错误次数
    if login_num >= 5:
        return jsonify(errno=RET.DATAERR,errmsg="今天的次用完了,明天再试")


    # 4.通过手机号取出用户对象
    try:
        user = User.query.filter(User.mobile == mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="数据库查询异常")

    # 5.判断用户对象是否存在
    if not user:
        return jsonify(errno=RET.NODATA, errmsg="该用户不存在")

    # 6.验证码密码是否正确
    if not user.check_password(password):

        #记录用户的登录错误次数
        try:
            redis_store.incr("login_num:%s"%mobile)
            redis_store.expire("login_num:%s"%mobile,20)#给当前key设置有效期,时间20秒
        except Exception as e:
            current_app.logger.error(e)

        return jsonify(errno=RET.DATAERR,errmsg="密码不正确")

    #记录用户的登录状态信息
    session["user_id"] = user.id
    session["name"] = user.name

    # 7.返回登录信息给前端
    return jsonify(errno=RET.OK,errmsg="登录成功")

#功能描述: 注册
#请求路径:/api/v1.0/user
#请求方式:post
#请求参数:手机号,短信验证码,密码
@api.route('/user', methods=['POST'])
def register():
    """
    1.获取参数
    2.校验参数
    3.判断手机号格式正确性
    4.取出redis中的短信验证码
    5.判断是否过期
    6.删除短信验证码
    7.判断短信验证码是否正确
    8.创建用户对象
    9.赋值参数,手机号,用户名,密码
    10.保存到数据库
    11.返回注册信息给前端页面
    :return:
    """

    # 1.获取参数,三种方式可以获取请求体中的内容
    # json_data = request.data
    # dict_data = json.loads(json_data)

    # dict_data = request.get_json()

    dict_data = request.json
    mobile = dict_data.get("mobile")
    sms_code = dict_data.get("sms_code")
    password = dict_data.get("password")

    # 2.校验参数
    if not all([mobile,sms_code,password]):
        return jsonify(errno=RET.PARAMERR,errmsg="参数不完整")

    # 3.判断手机号格式正确性
    if not re.match(r"1[3456789]\d{9}",mobile):
        return jsonify(errno=RET.DATAERR, errmsg="手机号格式错误")

    # 4.取出redis中的短信验证码
    try:
        redis_sms_code = redis_store.get("sms_code:%s"%mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="获取短信验证码失败")

    # 5.判断是否过期
    if not redis_sms_code:
        return jsonify(errno=RET.NODATA, errmsg="短信验证码已过期")

    # 6.删除短信验证码
    try:
        redis_store.delete("sms_code:%s"%mobile)
    except Exception as e:
        current_app.logger.error(e)
        # return jsonify(errno=RET.DBERR,errmsg="删除短信验证码失败") #到底要不要删除,产品会给出详细的设计

    # 7.判断短信验证码是否正确
    if sms_code != redis_sms_code:
        return jsonify(errno=RET.DATAERR,errmsg="短信验证码填写出错")

    # 8.创建用户对象
    user = User()

    # 9.赋值参数,手机号,用户名,密码
    user.name = mobile
    user.mobile = mobile
    #TODO 密码需要加密处理
    # user.password_hash = user.jiami_password(password) #也可以
    user.password = password

    # 10.保存到数据库
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="用户注册失败")

    # 11.返回注册信息给前端页面
    return jsonify(errno=RET.OK,errmsg="注册成功")
