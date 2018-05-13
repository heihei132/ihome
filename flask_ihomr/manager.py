# coding:utf8

# 爱家项目
# 数据库配置
# redis配置
# session配置
# CSRF配置
# 日志配置
from ihome import create_app,db
from flask_script import Manager
from flask_migrate import Migrate,MigrateCommand

app = create_app("develop")

#数据库迁移
manager = Manager(app)
Migrate(app,db)
manager.add_command("db",MigrateCommand)

if __name__ == "__main__":
    manager.run()
