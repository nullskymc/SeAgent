from peewee import SqliteDatabase
import os

# 创建数据库实例
db_path = os.getenv('DB_PATH', './chatroom.db')
db = SqliteDatabase(db_path)