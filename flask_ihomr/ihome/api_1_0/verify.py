# coding:utf8
# 图片验证码，短信验证码
import errno
import random
import re

from flask import current_app, jsonify
from flask import make_response
from flask import request

from ihome import constants
from ihome import redis_store
from ihome.utils.captcha.captcha import captcha
from ihome.utils.response_code import RET
from ihome.utils.sms import CCP
from . import api


# 发送短信
# 请求路径：/api/v1.0/sms_code
# 请求方式：POST
@api.route('/get_sms_code')
def get_sms_code():
    # 获取参数
    json_data = request.data
    dict_data = json_data.loads(json_data)
    mobile = dict_data.get("mobile")
    image_code = dict_data.get("image_code")
    image_code_id = dict_data.get("image_code_id")
    # 检验参数，为空检验
    if not all([mobile, image_code, image_code_id]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")
    # 检验手机号格式
    if not re.match(r"1[34578]\d{9}", mobile):
        return jsonify(errno=RET.DATAERR, errmsg="手机号格式不正确")

    # 取出redis中的图片验证码
    try:
        redis_image_code = redis_store.get("image_code:%s" % image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="图片验证码获取失败")
    # 校验图片验证码编号
    if not redis_image_code:
        return jsonify(errno=RET.DATAERR, errmsg="短信验证码过期")
        # 删除redis中的图片验证码
    redis_store.delete("image_code:%s" % image_code_id)
    # 判断
    if image_code != redis_image_code:
        return jsonify(errno=RET.DATAERR, errmsg="短信验证码错误")
    # 发送短信
    # 生成短信验证码
    sms_code = "%06d" % random.randint(0, 999999)
    # 位宽占位符

    current_app.logger.debug("短信验证码是：%s"%sms_code)

    #用云通讯发短信
    # ccp = CCP()
    # result = ccp.sendTemplateSMS(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES / 60], 1)

    # 判断是否发送成功
    # if result == -1:
    #     return jsonify(errno=RET.THIRDERR, errmsg="短信发送失败")

    # 保存短信验证码到redis中       用电话号码标记
    redis_store.set("sms_code:%s" % mobile, sms_code, constants.SMS_CODE_REDIS_EXPIRES)
    # 返回发送内容给前端页面
    return jsonify(errno=RET.OK, errmsg="发送成功")


# 图片验证码基本获取
# 请求路径：/api/v1.0/image_code
# 请求方式：GET
@api.route('/image_code')
def get_image_code():
    # 获取参数
    cur_id = request.args.get("cur_id")
    pre_id = request.args.get("pre_id")
    # 调用方法。获取图片验证码内容
    name, text, image_data = captcha.generate_captcha()

    try:
        # 保存到redis
        redis_store.set("image_code:%s" % cur_id, text, constants.IMAGE_CODE_REDIS_EXPIRES)

        if pre_id:
            redis_store.delete("image_code:%s" % pre_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="验证码保存失败")

    # 返回图片验证码
    response = make_response(image_data)
    response.headers["Content-Type"] = "image/jpg"
    return response
