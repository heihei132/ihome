#coding:utf8
#功能: 图片验证码, 短信验证码
import random
import re

from flask import current_app, jsonify
from flask import json
from flask import make_response
from flask import request

from ihome import constants
from ihome import redis_store
from ihome.models import User
from ihome.utils.response_code import RET
# from ihome.utils.sms import CCP
from . import api
from ihome.utils.captcha.captcha import captcha

#功能描述:发型短信
#请求路径:/api/v1.0/sms_code
#请求方式:POST
#请求参数: 手机号,图片验证码,图片验证码编号
@api.route('/sms_code',methods=["POST"])
def get_sms_code():
    """
    1.获取参数
    2.校验参数,为空校验
    3.校验手机号格式
    4.取出redis中的图片验证码
    5.校验图片验证码编号
    6.发送短信
    7.保存短信验证码到redis中
    8.返回发送内容给前端页面
    :return:
    """
    # 1.获取参数
    json_data = request.data
    dict_data = json.loads(json_data)
    mobile = dict_data.get("mobile")
    image_code = dict_data.get("image_code")
    image_code_id = dict_data.get("image_code_id")

    # 2.校验参数,为空校验
    if not all([mobile,image_code,image_code_id]):
        return jsonify(errno=RET.PARAMERR,errmsg="参数不完整")

    # 3.校验手机号格式
    if not re.match(r'1[34578]\d{9}',mobile):
        return jsonify(errno=RET.DATAERR,errmsg="手机号格式不正确")

    #根据手机号取出用户对象
    try:
        user = User.query.filter(User.mobile == mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="数据库查询失败")

    #判断用户对象是否存在
    if user:
        return jsonify(errno=RET.DATAEXIST, errmsg="该用户已存在")

    # 4.取出redis中的图片验证码
    try:
        redis_image_code = redis_store.get("image_code:%s"%image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="图片验证码获取失败")

    # 5.校验图片验证码编号
    if not redis_image_code:
        return jsonify(errno=RET.DATAERR,errmsg="短信验证码过期")

    #删除redis中的图片验证码
    try:
        redis_store.delete("image_code:%s"%image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        # return jsonify(errno=RET.DBERR, errmsg="删除失败")

    #判断
    if image_code != redis_image_code:
        return jsonify(errno=RET.DATAERR,errmsg="图片验证码填写错误")

    # 6.发送短信
    #生成短信验证码
    sms_code = "%06d"%random.randint(0,999999)

    current_app.logger.debug("短信验证码是:%s"%sms_code)

    # ccp = CCP()
    # try:
        # result = ccp.sendTemplateSMS(mobile,[sms_code,constants.SMS_CODE_REDIS_EXPIRES/60],1)
        #判断是否发送成功
        # if result == -1:
        #     return jsonify(errno=RET.THIRDERR,errmsg="短信发送失败")
    # except Exception as e:
    #     current_app.logger.error(e)
    #     return jsonify(errno=RET.THIRDERR, errmsg="云通讯短信发送失败")


    # 7.保存短信验证码到redis中
    try:
        redis_store.set("sms_code:%s"%mobile,sms_code,constants.SMS_CODE_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="短信验证码保存失败")


    # 8.返回发送内容给前端页面
    return jsonify(errno=RET.OK,errmsg="发送成功")

#功能描述: 图片验证码
#请求路径: /api/v1.0/image_code
#请求方式: GET
#请求参数:
@api.route('/image_code')
def get_image_code():

    #获取参数
    cur_id = request.args.get("cur_id")
    pre_id = request.args.get("pre_id")

    #调用方法,获取图片验证码内容
    name,text,image_data = captcha.generate_captcha()

    #保存到redis中
    try:
        redis_store.set("image_code:%s"%cur_id, text,constants.IMAGE_CODE_REDIS_EXPIRES)

        if pre_id:
            redis_store.delete("image_code:%s"%pre_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="验证码保存失败")

    #返回图片验证码
    response = make_response(image_data)
    response.headers["Content-Type"] = "image/jpg"
    return response

