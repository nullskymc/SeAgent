from peewee import Model
from database.db import db

class BaseModel(Model):
    """基础模型类，所有模型都应继承自此类"""
    class Meta:
        database = db