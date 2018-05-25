#coding:utf8
from datetime import datetime
from flask import current_app
from flask import g
from flask import request, jsonify
from ihome import db
from ihome.models import House, Order
from ihome.utils.commons import login_required
from ihome.utils.response_code import RET
from . import api
# from sqlalchemy import and_,or_,not_

#功能描述: 发表评价
#请求路路径: /api/v1.0/orders/<int:order_id>/comment
#请求方式: PUT
#请求参数: 订单编号,评价内容
@api.route('/orders/<int:order_id>/comment', methods=['PUT'])
@login_required
def send_comment(order_id):
    """
    1.获取到评论信息
    2.校验参数
    3.根据订单编号获取订单对象
    4.判断订单是否存在
    5.更改订单状态,设置评论内容
    6.更数据库返回
    :return:
    """
    # 1.获取到评论信息
    comment = request.json.get("comment")

    # 2.校验参数
    if not all([order_id,comment]):
        return jsonify(errno=RET.PARAMERR,errmsg="参数不完整")

    # 3.根据订单编号获取订单对象
    try:
        order = Order.query.get(order_id)

         # 格式: asert bool表达式A, 内容1,   A为True继续走下面, A为False 提示异常信息内容1
        assert order.user_id == g.user_id, "不是同一个人"

    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="获取订单异常")

    # 4.判断订单是否存在
    if not order:
        return jsonify(errno=RET.NODATA,errmsg="该订单不存在")

    # 5.更改订单状态,设置评论内容
    order.status = "COMPLETE"
    order.comment = comment

    # 6.更数据库返回
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="更新失败")

    return jsonify(errno=RET.OK,errmsg="发表更新成功")

#功能描述: 接单,拒单功能
#请求路路径: /api/v1.0/orders/<int:order_id>
#请求方式: PUT
#请求参数: 订单编号
@api.route('/orders/<int:order_id>', methods=['PUT'])
def receive_reject_order(order_id):
    """
    1.获取参数
    2.校验参数
    3.根据订单编号查询订单对象
    4.根据操作类型(接单,拒单),做对应的处理
    5.改变订单的状态
    6.更新数据库
    7.返回
    :return:
    """
    # 1.获取参数
    action = request.args.get("action")

    # 2.校验参数
    if not order_id or not action in ["accept","reject"]:
        return jsonify(errno=RET.PARAMERR,errmsg="参数不完整")

    # 3.根据订单编号查询订单对象
    try:
        order = Order.query.get(order_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="查询异常")

    if action == "accept":
        # 5.改变订单的状态
        order.status = "WAIT_COMMENT" #待评价
    else:
        order.status = "REJECTED"
        order.comment = request.json.get("reason","")


    # 6.更新数据库
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="更新失败")

    # 7.返回
    return jsonify(errno=RET.OK,errmsg="更新成功")


#功能描述: 创建订单
#请求路路径: /api/v1.0/orders
#请求方式: POST
#请求参数: 房子编号,开始时间,结束时间
@api.route('/orders', methods=['POST'])
@login_required
def create_order():
    """
    1.获取参数
    2.校验参数,并转换
    3.通过编号找到房子
    4.判断房子是否存在
    5.根据时间查询在该段时间内是否有冲突订单
    6.创建订单
    7.设置订单属性
    8.添加到数据库
    9.返回
    :return:
    """
    # 1.获取参数
    house_id = request.get_json().get("house_id")
    start_date_str = request.get_json().get("start_date")
    end_date_str = request.get_json().get("end_date")
    print 1, house_id, start_date_str, end_date_str
    # 2.校验参数,并转换
    if not all([house_id,start_date_str,end_date_str]):
        return jsonify(errno=RET.PARAMERR,errmsg="参数不完整")

    # 3.通过编号找到房子
    try:
        house = House.query.get(house_id)

        #将时间转成日期格式
        start_date = datetime.strptime(start_date_str,"%Y-%m-%d")
        end_date = datetime.strptime(end_date_str,"%Y-%m-%d")

    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="查询异常")
    print 1, house_id, start_date_str, end_date_str

    # 4.判断房子是否存在
    if not house:
        return jsonify(errno=RET.NODATA,errmsg="该房子不存在")

    # 5.根据时间查询在该段时间内是否有冲突订单
    try:
        conlict_orders = Order.query.filter(start_date<Order.end_date,end_date>Order.begin_date,Order.house_id == house_id).all()
        # conlict_orders = Order.query.filter(and_(start_date<Order.end_date,end_date>Order.begin_date)).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="查询订单异常")

    if conlict_orders:
        return jsonify(errno=RET.DATAERR, errmsg="该房子时间段内已被预定")

    # 6.创建订单
    order = Order()

    # 7.设置订单属性
    days = (end_date - start_date).days
    order.user_id = g.user_id
    order.house_id = house_id
    order.begin_date = start_date
    order.end_date = end_date
    order.days = days
    order.house_price = house.price
    order.amount = house.price * days

    # 8.添加到数据库
    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="订单创建失败")

    # 9.返回
    return jsonify(errno=RET.OK,errmsg="创建成功")
