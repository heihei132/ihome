#coding:utf8
from flask import current_app, jsonify
from flask import g
from flask import json
from flask import request

from ihome import constants, db
from ihome import redis_store
from ihome.api_1_0 import api
from ihome.models import Area, House, Facility, HouseImage
from ihome.utils.commons import login_required
from ihome.utils.image_storage import image_storage
from ihome.utils.response_code import RET


# 功能：获取房屋详细信息
# 请求路径：/api/v1.0/houses/<int:house_id>
# 请求方式：get
# 请求参数：
@api.route('/houses/<int:house_id>')
def get_house_detail(house_id):
    #从redis中获取房屋详细信息
    # 缓存房屋详细信息
    try:
        redis_house_detail = redis_store.get("house_detail:%s" % house_id)
    except Exception as e:
        current_app.logger.error(e)

    if redis_house_detail:
        return jsonify(errno=RET.OK,errmsg="获取成功",data={"house":json.loads(redis_house_detail)})






    #通过编号获取房屋对象
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="查询异常")
    #判断房屋对象是否存在
    if not house:
        return jsonify(errno=RET.NODATA,errmsg="房屋不存在")


    #缓存房屋详细信息
    try:
        redis_store.set("house_detail:%s"%house_id,json.dumps(house.to_full_dict()),constants.HOUSE_DETAIL_REDIS_EXPIRE_SECOND)
    except Exception as e:
        current_app.logger.error(e)
        # return jsonify(errno=RET.DBERR,errmsg="缓存异常")



    #将房屋对象信息转成字典信息，返回给前端
    return jsonify(errno=RET.OK, errmsg="获取成功",data={"house":house.to_full_dict()})


# 功能：获取首页房屋图片信息
# 请求路径：/api/v1.0/houses/index
# 请求方式：get
# 请求参数：无
@api.route('/houses/index')
def get_index_house():
    #查询数据库，前五个热门房源
    houses = None
    try:
        houses = House.query.order_by(House.order_count.desc()).limit(constants.HOME_PAGE_MAX_HOUSES)
    except Exception as e:
        current_app.logger.order(e)
        return jsonify(errno=RET.DBERR,errmsg="查询异常")
    #将对项列表转成字典列表
    house_list = []
    for house in houses:
        house_list.append(house.to_basic_dict())
    #返回
    return jsonify(errno=RET.OK,errmsg="获取成功",data=house_list)

# 功能：发布房屋图片信息
# 请求路径：/api/v1.0/houses/<int:house_id>/images
# 请求方式：post/put
# 请求参数：图片
@api.route('/houses/<int:house_id>/images',methods=["PUT"])
@login_required
def send_house_image_info(house_id):
    #获取参数，图片，并读取成二进制流#####这里首从前端页面信息读取的
    image_data = request.files.get("house_image").read()
    #通过房屋编号查询房屋对应下图片是否存在
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="查询异常")

    if not house:
        return jsonify(errno=RET.NODATA,errmsg="房屋为空")
    #上传图片，七牛云
    try:
        image_name = image_storage(image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR,errmsg="七牛云异常")
    #将图片设置到房屋对象
    if not house.index_image_url:
        house.index_image_url = image_name
    #创建房屋对象
    house_image = HouseImage()
    house_image.house_id = house_id#设置图片属于那个房子
    house_image.url = image_name
    #更新数据库
    try:
        db.session.add(house_image)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="图片上传异常")
    #返回前端，携带图片链接
    image_url = constants.QINIU_DOMIN_PREFIX + image_name
    return jsonify(errno=RET.OK, errmsg="图片上传成功",data={"url":image_url})


# 功能：发布房屋基本信息(基本信息，设施信息)
# 请求路径：/api/v1.0/houses
# 请求方式：post
# 请求参数：基本信息，设施信息
@api.route('/houses',methods=["POST"])
@login_required
def send_house_basic_info():
    #获取提交的参数
    title = request.json.get("title")
    price = request.json.get("price")
    area_id = request.json.get("area_id")
    address = request.json.get("address")
    room_count = request.json.get("room_count")
    acreage = request.json.get("acreage")
    unit = request.json.get("unit")
    capacity = request.json.get("capacity")
    beds = request.json.get("beds")
    deposit = request.json.get("deposit")
    min_days = request.json.get("min_days")
    max_days = request.json.get("max_days")
    facilities = request.json.get("facility") #格式:[1,2,3,4]
    #检验参数，基本信息校验
    if not all([facilities,max_days,min_days,deposit,title,price,area_id,address,room_count,acreage,unit,capacity,beds]):
        return jsonify(errno=RET.PARAMERR,errmsg="参数不完整")
    #创建房屋对象
    house = House()
    #设置房屋对象的数据
    house.title = title
    house.price = price
    house.area_id = area_id
    house.address = address
    house.room_count = room_count
    house.acreage = acreage
    house.unit = unit
    house.capacity = capacity
    house.beds = beds
    house.deposit = deposit
    house.min_days = min_days
    house.max_days = max_days

    #设置设施信息[facility]
    facility_dict = Facility.query.filter(Facility.id.in_(facilities)).all
    house.user_id = g.user_id

    #设置房屋的主人
    house.user_id = g.user_id

    #保存到数据库
    try:
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,ermsg="保存异常")
    #返回
    return jsonify(errno=RET.OK, ermsg="保存成功",data={"house_id":house.id})


# 功能：获取用户的实名认证信息
# 请求路径：/api/v1.0/areas
# 请求方式get
# 请求参数：无
# 返回值：字典列表
@api.route('/areas',methods=["GET"])
def get_areas():
    #先从redis中获取################################
    try:
        redis_json_areas = redis_store.get("areas")
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取失败")
    if redis_json_areas:
        return jsonify(errno=RET.OK, errmsg="获取成功",data=json.loads(redis_json_areas))



    #获取城区信息
    try:
        areas = Area.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="查询失败")
    #将城区信息转成字典
    areas_list = []
    for area in areas:
        areas_list.append(area.to_dict())
    #存储到redis中
    try:
        #redis里存字符串，要转成字符串
        redis_store.set("areas",json.dumps(areas_list),constants.AREA_INFO_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="存储失败")
    #返回
    return jsonify(errno=RET.OK,errmsg="查询成功",data=areas_list)


