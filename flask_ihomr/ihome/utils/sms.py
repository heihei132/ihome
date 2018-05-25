#coding:utf8
from ihome.libs.yuntongxun.CCPRestSDK import REST
import ConfigParser

# 说明：主账号，登陆云通讯网站后，可在控制台首页中看到开发者主账号ACCOUNT SID。
accountSid = '8a216da861f5a257016204a0d5ac06f0';#控制台的account id

# 说明：主账号Token，登陆云通讯网站后，可在控制台首页中看到开发者主账号AUTH TOKEN。
accountToken = '07885bc11c584f1ba6342a3cc8d7d2a4';#账号auth token

# 请使用管理控制台中已创建应用的APPID  #应用管理 的app id
appId = '8a216da86339b5e8016357432e3f0fd1';

# 说明：请求地址，生产环境配置成app.cloopen.com。
serverIP = 'app.cloopen.com';

# 说明：请求端口 ，生产环境为8883.
serverPort = '8883';

softVersion = '2013-12-26';  # 说明：REST API版本号保持不变。

#将短信发送的过程使用单利进行封装
#单利的写法有很多写法!开发中掌握一种就可以,但是面试会问很多种
class CCP(object):

    __instance = None

    #编写__new__方法
    def __new__(cls, *args, **kwargs):
        #判断该类对象中是否有实例__instance属性
        if not cls.__instance:
            cls.__instance = super(CCP, cls).__new__(cls)

            #用了单例模式以后下面创建的对象就只会被创建一次
            # 初始化REST SDK
            cls.__instance.rest = REST(serverIP, serverPort, softVersion)
            cls.__instance.rest.setAccount(accountSid, accountToken)
            cls.__instance.rest.setAppId(appId)

            return cls.__instance
        else:
            return cls.__instance

    def sendTemplateSMS(self,to, datas, tempId):

        result = self.rest.sendTemplateSMS(to, datas, tempId)

        # 只需要告诉自己服务器发送的结果即可,如果返回0表示成功,如果是-1表示失败
        if result["statusCode"] == "000000":
            return 0
        else:
            return -1

#测试代码
# print id(CCP())
# print id(CCP())

# ccp = CCP()
# print ccp.sendTemplateSMS("18210094341",[666666,5],1)


def sendTemplateSMS(to, datas, tempId):
    # 初始化REST SDK
    rest = REST(serverIP, serverPort, softVersion)
    rest.setAccount(accountSid, accountToken)
    rest.setAppId(appId)

    result = rest.sendTemplateSMS(to, datas, tempId)

    #只需要告诉自己服务器发送的结果即可,如果返回0表示成功,如果是-1表示失败
    if result["statusCode"] == "000000":
        return 0
    else:
        return -1

# 模板:【云通讯】您使用的是云通讯短信模板，您的验证码是{1}，请于{2}分钟内正确输入
#参数解释:
#参数1: 表示要发送给那个手机号
#参数2: 用来替换模板中的{1},{2}位置的值
#参数3: 表示使用的是默认模板
sendTemplateSMS("13235388529",[666666,5],1)