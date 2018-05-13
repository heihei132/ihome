#coding:utf8
#图片验证码，短信验证码
from flask import request

from ihome import constants
from ihome import redis_store
from ihome.utils.captcha.captcha import captcha
from . import api


#图片验证码基本获取
@api.route('/image_code')
def get_image_code():
    #获取参数
    cur_id  = request.args.get("cur_id")
    #调用方法。获取图片验证码内容
    name,text,image_data = captcha.generate_captcha()
    #保存到redis
    redis_store.set("image_code:%s"%cur_id,text,constants.IMAGE_CODE_REDIS_EXPIRES)
    #返回图片验证码
    return image_data


