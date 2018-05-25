# coding:utf8
import user

from flask import current_app
from flask import g
from flask import request
from flask import session, jsonify

from ihome import constants
from ihome import db
from ihome.utils.image_storage import image_storage
from ihome.models import User, Order, House
from ihome.utils.commons import login_required
from ihome.utils.response_code import RET
from . import api


# 功能：获取用户所有订单
# 请求路径：/api/v1.0/user/orders
# 请求方式：get
# 请求参数：role(角色，房东，房客)
@api.route('/user/orders')
@login_required
def get_user_orders():
    #获取参数
    role = request.args.get("role")
    user_id = g.user_id
    #检验参数
    if not role in ["custom","landrod"]:
        return jsonify(errno=RET.PARAMERR,errmsg="参数错误")
    #根据角色查询所有订单
    orders = []
    if role == "custom":
        orders = Order.query.filter(Order.user_id == user_id).all()
    else:
        #查询房东所有房子
        houses = House.query.filter(House.user_id == user_id).all()
        #查询房东所有房子编号
        houses_ids = [house.id for house in houses]
        #查询订单中的编号在房子编号中的订单
        orders = Order.query.filter(Order.house_id == houses_ids).all()

    #将订单对象列表转成字典列表
    order_list = []
    for order in orders:
        order_list.append(order.to_dict())
    #返回
    return jsonify(errno=RET.OK,errmsg="获取成功",data={"orders":order_list})





# 功能：获取用户发布的所有房子
# 请求路径：/api/v1.0/user/houses
# 请求方式：get
# 获取参数：无
# 返回值：所有房子的列表
@api.route('/user/houses')
@login_required
def get_user_houses():
    # 通过编号获取用户对象
    try:
        user = User.query.get(g.user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="登录异常")
    # 判断用户对象是否存在
    if not user:
        return jsonify(errno=RET.NODATA, errmsg="用户不存在")
    # 查询处用户所有的房子
    # 这里的houses都是对象，所有后面要转换成列表
    houses = user.houses
    # 将房子信息转成字典列表
    houses_list = []
    for house in houses:
        houses_list.append(house.to_basic_dict())
    # 返回前端
    return jsonify(errno=RET.OK, errmsg="获取成功", data={"houses": houses_list})


# 功能：获取用户的实名认证信息
# 请求路径：/api/v1.0/user/auth
# 请求方式get
# 获取参数：无
# 返回值：真实姓名，身份证号
@api.route('/user/auth')
@login_required
def get_user_auth():
    # 获取用户编号
    user_id = g.user_id
    # 获取用户对象
    try:
        user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询异常")
    # 判断用户对象是否存在
    if not user_id:
        return jsonify(errno=RET.NODATA, errmsg="用户不存在")
    # 取出用户对象的真实姓名，身份证号，并拼接成字典
    user_dict = {
        "real_name": user.real_name,
        "id_card": user.id_card
    }
    # 返回
    return jsonify(errno=RET.OK, errmsg="获取成功", data=user_dict)


# 功能：设置用户的实名认证信息
# 请求路径：/api/v1.0/user/auth
# 请求方式put/post
# 请求参数：真实姓名，身份证号
@api.route('/user/auth', methods=["POST"])
@login_required
def set_user_auth():
    # 从前端网页中获取参数
    real_name = request.get_json().get("real_name")
    id_card = request.get_json().get("id_card")

    if not all([real_name, id_card]):
        return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

    # 此处可以校验用户身份证的正确性


    # 取出用户编号
    user_id = g.user_id
    # 根据用户编号获取对象
    try:
        user = User.query.filter(User.id == user_id).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库查询异常")
    # 判断用户对象是否存在
    if not user:
        return jsonify(errno=RET.NODATA, errmsg="该用户不存在")
    # 将信息设置到用户对象中更新数据库
    user.id_card = id_card
    user.real_name = real_name
    # 更新数据库
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据更新异常")
    # 返回前段页面
    return jsonify(errno=RET.OK, errmsg="更新成功")


# 功能：修改用户名
# 请求路径：/api/v1.0/user/name
# 请求方式put/post
# 请求参数：用户名
@api.route('/user/name', methods=["PUT"])
@login_required
def update_user_name():
    # 获取参数
    name = request.json.get("name")
    # 获取用户编号
    user_id = g.user_id
    # 通过编号取出用户对象
    try:
        user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询失败")
    # 判断用户对象是否存在
    if not user:
        return jsonify(errno=RET.NODATA, errmsg="用户不存在")
    # 修改用户名字
    user.name = name
    # 提交到数据库
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据更新异常")
    # 返回修改状态
    return jsonify(errno=RET.OK, errmsg="用户更新成功")


@api.route('/user/avatar',methods=["POST"])
@login_required
def upload_image():
    """
    1.获取用户上传的头像,读取成二进制流
    2.获取用户的编号
    3.通过编号查询到用户对象
    4.判断用户对象是否存在
    5.上传头像
    6.将头像赋赋值给用户对象
    7.提交改动到数据库中
    8.返回
    :return:
    """
    # 1.获取用户上传的头像,读取成二进制流
    avatar = request.files.get("avatar")
    image_data = avatar.read()

    # 2.获取用户的编号
    user_id = g.user_id

    # 3.通过编号查询到用户对象
    try:
        user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="查询失败")

    # 4.判断用户对象是否存在
    if not user:
        return jsonify(errno=RET.NODATA, errmsg="该用户不存在")

    # 5.上传头像
    try:
        image_name = image_storage(image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR,errmsg="上传失败")

    # 6.将头像赋赋值给用户对象
    if image_name:
        user.avatar_url =  image_name

    # 7.提交改动到数据库中
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="用户头像更新失败")

    # 8.返回
    avatar_url = constants.QINIU_DOMIN_PREFIX + image_name
    return jsonify(errno=RET.OK,errmsg="上传成功",data={"avatar_url":avatar_url})




# 功能：获取用户个人信息
# 请求路径：/api/v1.0/user
# 请求方式get
# 请求参数：用户编号
@api.route('/user')
@login_required
def get_user_info():
    # 获取用户编号
    # user_id = session.get("user_id")
    user_id = g.user_id
    # 判断y用户编号是否存在
    if not user_id:
        return jsonify(errno=RET.NODATA, errmsg="该用户未登录")
    # 取出用户对象
    try:
        user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="数据库查询异常")
    # 判断对象
    if not user:
        return jsonify(errno=RET.NODATA, errmsg="该用户不存在")
    # 将用户对象信息转成字典信息返回至前端页面

    return jsonify(errno=RET.OK, errmsg="获取成功", data=user.to_list())
