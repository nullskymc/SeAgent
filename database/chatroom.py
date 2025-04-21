from datetime import datetime
from typing import Optional

from passlib.context import CryptContext
from peewee import *
from playhouse.sqlite_ext import JSONField
from pydantic import ConfigDict, BaseModel

db = SqliteDatabase('./chatroom.db')


class PeeweeBaseModel(Model):
    class Meta:
        database = db


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(PeeweeBaseModel):
    id = AutoField()
    user_id = CharField(unique=True, null=False)
    user_password = CharField(null=False)
    email = CharField(unique=True, null=False)  # Add email field

    def set_password(self, password: str):
        self.user_password = pwd_context.hash(password)


class Message_store(PeeweeBaseModel):
    id = AutoField()
    session_id = IntegerField()
    message = JSONField()


class Message(PeeweeBaseModel):
    user_id = IntegerField(null=True)  # 用户ID字段，允许为空
    message = TextField()  # 消息字段
    timestamp = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')], default=datetime.now)  # 默认值
    role = CharField()


class UserCreate(BaseModel):
    username: str
    password: str
    email: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class MessageCreate(BaseModel):
    user_id: Optional[int]  # 用户ID可以是可选的
    message: str
    role: str


class MessageResponse(BaseModel):
    id: int
    user_id: Optional[int]
    message: str
    timestamp: str
    role: str

    model_config = ConfigDict(from_attributes=True)  # 使用 Pydantic v2 的新配置


def get_latest_messages(limit=6):
    return Message.select().order_by(Message.timestamp.desc()).limit(limit)
