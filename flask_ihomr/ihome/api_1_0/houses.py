#coding:utf8
#功能描述: 城区信息获取
from datetime import datetime
from flask import current_app, jsonify
from flask import g
from flask import json
from flask import request
from ihome.utils.image_storage import image_storage
from ihome import constants, db
from ihome import redis_store
from ihome.models import Area, House, Facility, HouseImage, Order
from ihome.utils.commons import login_required
from ihome.utils.response_code import RET
from . import api



#功能描述: 搜索房源
#请求路径:/api/v1.0/houses
#请求方式:GET
#请求参数: 区域编号(aid),搜索关键字(sk),分页(p,表示要查询的是哪一页),开始时间(sd),结束时间(ed),
@api.route('/houses')
def search_houses():
    """
    1.查询所有的房子
    2.将所有的房子转成字典列表
    3.返回
    :return:
    """
    #获取参数
    aid = request.args.get("aid")
    # 共有四中情况,booking(订单量),price-inc(低-高), price-des(高-低),默认情况按房子创建时间
    sk = request.args.get("sk")
    p = request.args.get("p",1)
    start_date_str = request.args.get("sd")
    end_date_str = request.args.get("ed")

    #参数转换
    try:
        #将分页的参数转成整数
        p = int(p)

        #将字符串类型转成日期类型
        start_date = None
        if start_date_str:
            start_date = datetime.strptime(start_date_str,"%Y-%m-%d")

        end_date = None
        if end_date_str:
            end_date = datetime.strptime(end_date_str,"%Y-%m-%d")

        #校验操作,如果开始时间结束时间两者都有,那么开始时间一定要小于结束时间
        assert start_date <= end_date, "开始时间要小于结束时间"

    except Exception as e:
        current_app.logger.error(e)
        p = 1

    #获取缓存中的内容
    try:
        search_data = "search_%s_%s_%s_%s"%(aid, sk, start_date, end_date)
        redis_search_data = redis_store.hget(search_data,p)
    except Exception as e:
        current_app.logger.error(e)

    if redis_search_data:
        # return jsonify(errno=RET.OK,errmsg="获取成功",data=json.loads(redis_search_data))
        return jsonify(errno=RET.OK,errmsg="获取成功",data=json.loads(redis_search_data))


    # 1.查询所有的房子
    try:
        #1.0获取查询对象
        house_query = House.query

        #1.1 增加区域编号条件
        if aid:
            house_query= house_query.filter(House.area_id == aid)

        #1.2 增加排序方式
        if sk == "booking":
            house_query = house_query.order_by(House.order_count)
        elif sk == "price-inc":
            house_query = house_query.order_by(House.price.asc())
        elif sk == "price-des":
            house_query = house_query.order_by(House.price.desc())
        else:
            house_query = house_query.order_by(House.create_time.desc())

        #1.4 增加时间(冲突房源过滤)
        conflict_orders = []
        if start_date and end_date:
            conflict_orders = Order.query.filter(start_date < Order.end_date, end_date > Order.begin_date).all()
        elif start_date:
            conflict_orders = Order.query.filter(start_date < Order.end_date).all()
        elif end_date:
            conflict_orders = Order.query.filter(end_date > Order.begin_date).all()

        #根据冲突的订单编号,反向推出不冲突的房子
        if conflict_orders:
            #冲突的房子编号
            conflict_house_ids = [order.house_id for order in conflict_orders]
            house_query = house_query.filter(House.id.notin_(conflict_house_ids))

        #1.3 分页查询
        #参数1: 表示要查询哪一页,参数2:表示每页有几条数据,参数3:是否要进行错误输出
        paginate = house_query.paginate(p,constants.HOUSE_LIST_PAGE_CAPACITY,False)

        #取出分页对象中的所有页数,所有对象
        items = paginate.items #当前页所有的对象
        total = paginate.pages #所有页数

        # 查询满足条件的所有房子
        # houses = house_query.all()
        houses = items

    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="查询失败")

    # 2.将所有的房子转成字典列表
    house_list = []
    for house in houses:
        house_list.append(house.to_basic_dict())

    data = {"houses":house_list,"total_page":total}

    #2.1缓存分页数据
    try:

        #使用管线对象管理redis_store(了解即可)
        pipeline =  redis_store.pipeline()
        #开启事物
        pipeline.multi()

        search_data = "search_%s_%s_%s_%s"%(aid,sk,start_date,end_date)
        pipeline.hset(search_data,p,json.dumps(data))
        pipeline.expire(search_data,constants.HOUSE_LIST_REDIS_EXPIRES)

        #执行事物
        pipeline.execute()


    except Exception as e:
        current_app.logger.error(e)
        # return jsonify(errno=RET.DBERR,errmsg="设置缓存失败")

    # 3.返回
    return jsonify(errno=RET.OK,errmsg="获取成功",data = data)


#功能描述: 获取房子的详情信息
#请求路径:/api/v1.0/houses/<int:house_id>
#请求方式:GET
#请求参数:无
@api.route('/houses/<int:house_id>')
@login_required
def get_house_detail(house_id):
    """
    1.通过编号获取房屋对象
    2.判断房屋对象是否存在
    3.将房屋对象信息转成字典信息,返回个前端
    :return:
    """

    #0从redis中查询房屋的详情信息
    try:
        redis_house_detail = redis_store.get("house_detail:%s" % house_id)
    except Exception as e:
        current_app.logger.error(e)
        # return jsonify(errno=RET.DBERR,errmsg="获取缓存异常")

    if redis_house_detail:
        return jsonify(errno=RET.OK,errmsg="获取成功",data={"house":json.loads(redis_house_detail),"user_id":g.user_id})

    # 1.通过编号获取房屋对象
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="查询异常")

    # 2.判断房屋对象是否存在
    if not house:
        return jsonify(errno=RET.NODATA,errmsg="该房屋不存在")

    #3.缓存房屋详情信息
    try:
        redis_store.set("house_detail:%s"%house_id,json.dumps(house.to_full_dict()),constants.HOUSE_DETAIL_REDIS_EXPIRE_SECOND)
    except Exception as e:
        current_app.logger.error(e)
        # return jsonify(errno=RET.DBERR,errmsg="缓存异常")

    # 4.将房屋对象信息转成字典信息,返回给前端
    return jsonify(errno=RET.OK,errmsg="获取成功",data={"house":house.to_full_dict(),"user_id":g.user_id})


#功能描述: 获取首页图片展示
#请求路径: /api/v1.0/houses/index
#请求方式:GET
#请求参数: 无
@api.route('/houses/index')
def get_index_house():
    """
    1.查询数据库,前3个热门房源
    2.将对象列表,转成字典列表
    3.返回
    :return:
    """
    # 1.查询数据库,前3个热门房源
    houses = None
    try:
        houses = House.query.order_by(House.order_count.desc()).limit(constants.HOME_PAGE_MAX_HOUSES)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="查询异常")

    # 2.将对象列表,转成字典列表
    house_list = []
    for house in houses:
        house_list.append(house.to_basic_dict())

    # 3.返回
    return jsonify(errno=RET.OK,errmsg="获取成功",data=house_list)


#功能描述u: 发布房屋的图片信息
#请求路径:/api/v1.0/houses/<int:house_id>/images
#请求方式:PUT
#请求参数: 图片
@api.route('/houses/<int:house_id>/images',methods=["PUT"])
def send_house_image_info(house_id):
    """
    1.获取参数,图片,并读取成二进制流
    2.通过房屋编号查询房屋对下你给是否存在
    3.上传图片,七牛云
    4.将图片名字设置到房屋对象
    5.更新数据库
    6.返回前端,携带图片链接
    :return:
    """
    # 1.获取参数,图片,并读取成二进制流
    image_data = request.files.get("house_image").read()

    # 2.通过房屋编号查询房屋对下你给是否存在
    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="查询异常")

    if not house:
        return jsonify(errno=RET.NODATA,errmsg="该房屋不存在")

    # 3.上传图片,七牛云
    try:
        image_name = image_storage(image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR,errmsg="七牛云异常")


    # 4.将图片名字设置到房屋对象, 如果房屋没有默认图片
    if not house.index_image_url:
        house.index_image_url= image_name

    #5.创建图片对象
    house_image = HouseImage()
    house_image.house_id = house_id #设置图片属于哪个房子
    house_image.url = image_name

    # 6.更新数据库
    try:
        db.session.add(house_image)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="图片上传异常")


    # 7.返回前端,携带图片链接
    image_url = constants.QINIU_DOMIN_PREFIX + image_name
    return jsonify(errno=RET.OK,errmsg="上传成功",data={"url":image_url})


#功能描述: 发布房屋的基本信息(房屋基本信息,设施信息)
#请求路径:/api/v1.0/houses
#请求方式:POST
#请求参数: 基本信息,设施信息
@api.route('/houses', methods=['POST'])
@login_required
def send_house_basic_info():
    """
    1.获取提交的参数
    2.校验参数,基本信息校验
    3.创建房屋对象
    4.设置房屋对象的数据
    5.需要设置房屋的主人
    6.保存数据库
    7.返回
    :return:
    """
    # 1.获取提交的参数
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

    # 2.校验参数,基本信息校验
    if not all([title,price,area_id,address,room_count,acreage,unit,capacity,beds,deposit,min_days,max_days]):
        return jsonify(errno=RET.PARAMERR,errmsg="参数不完整")

    # 3.创建房屋对象
    house = House()

    # 4.设置房屋对象的数据
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

    #设置设施信息, [facility,faclity]
    facility_list = Facility.query.filter(Facility.id.in_(facilities)).all()
    house.facilities = facility_list

    # 5.需要设置房屋的主人
    house.user_id = g.user_id

    # 6.保存数据库
    try:
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="保存异常")

    # 7.返回
    return jsonify(errno=RET.OK,errmsg="发布成功",data={"house_id":house.id})



#功能描述: 城区信息获取
#请求路径: /api/v1.0/areas
#请求方式:GET
#请求参数: 无
#返回值: 字典列表
@api.route('/areas')
def get_areas():
    """
    1.获取城区信息
    2.将城区信息转成字典列表
    3.返回
    :return:
    """

    #0.先从redis中获取
    try:
        redis_json_areas = redis_store.get("areas")
    except Exception as e:
        current_app.logger.error(e)
        # return jsonify(errno=RET.DBERR,errmsg="获取失败")

    if redis_json_areas:
        return jsonify(errno=RET.OK, errmsg="获取成功",data=json.loads(redis_json_areas))


    # 1.获取城区信息
    try:
        areas = Area.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg="查询失败")

    # 2.将城区信息转成字典列表
    areas_list = []
    for area in areas:

        areas_list.append(area.to_dict())

    #3.存储城区信息到redis中
    try:
        redis_store.set("areas",json.dumps(areas_list),constants.AREA_INFO_REDIS_EXPIRES)
    except Exception as e:
        current_app.logger.error(e)
        # return jsonify(errno=RET.DBERR,errmsg="存储失败")


    #4.返回
    return jsonify(errno=RET.OK,errmsg="获取成功",data = areas_list)