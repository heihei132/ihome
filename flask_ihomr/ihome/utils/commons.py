#coding:utf8

#自定义转换器
#定义类，继承自BaseConverter
#编写init方法，接受两个参数
#初始化父类方法，子类规则
#将转换器添加到默认转换器


from werkzeug.routing import BaseConverter

class RegexConverter(BaseConverter):
    def __init__(self,url_map,regex):
                            #regex:新正则规则
        super(RegexConverter,self).__init__(url_map)
        self.regex = regex


