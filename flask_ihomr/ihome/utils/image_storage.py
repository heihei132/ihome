#coding:utf8
from qiniu import Auth, put_file, etag,put_data

#需要填写你的 Access Key 和 Secret Key
access_key = 'v3n5FPnRvLujRroKe3X9FxjMSgtWCmMWBeharusu'
secret_key = 'd3uJUlaQ9iKh0b5XkhU-Tlx5hjrDiWDDeHA4xotw'

#构建鉴权对象
q = Auth(access_key, secret_key)

#要上传的空间
bucket_name = 'ihome'

#生成上传 Token，可以指定过期时间等
token = q.upload_token(bucket_name, None, 3600)










#上传图片的方法(用于测试#############################)
def image_storage(image_data):

    #要上传文件的本地路径
    # localfile = './22.png'
    # ret, info = put_file(token, None, localfile)
    ret, info = put_data(token, None, image_data)

    #根据返回值 判断是否上传成功 info是一个类的对象 取对象用.
    if info.status_code == 200:
        return ret.get("key")
    else:
        return ""

if __name__ == '__main__':

    #方式一:
    """
    file = open('./22.png')

    #读取一下可以变成二进制流
    image_data = file.read()

    result = image_storage(image_data)

    if result:
        print "image name is %s" % result
    else:
        print "没有成上传成功"

    file.close()
    """

    #方式二:
    with open('./22.png') as file:
        image_storage(file.read())

