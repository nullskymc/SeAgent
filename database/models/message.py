from datetime import datetime
from typing import Optional, List
from peewee import AutoField, IntegerField, TextField, DateTimeField, CharField, SQL, ForeignKeyField
from playhouse.sqlite_ext import JSONField
from pydantic import BaseModel, ConfigDict, Field

from database.models.base import BaseModel as PeeweeBaseModel
from database.models.user import User


class Chat(PeeweeBaseModel):
    """聊天会话模型"""
    id = AutoField()
    title = CharField(default="新对话")  # 对话标题
    user_id = IntegerField()  # 所属用户ID
    created_at = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')], default=datetime.now)
    updated_at = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')], default=datetime.now)
    is_active = IntegerField(default=1)  # 是否活跃状态，1=活跃，0=已删除


class Message(PeeweeBaseModel):
    """用户消息模型"""
    id = AutoField()
    chat_id = ForeignKeyField(Chat, backref='messages')  # 关联到Chat表
    user_id = IntegerField(null=True)  # 用户ID字段，允许为空
    message = TextField()  # 消息字段
    timestamp = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')], default=datetime.now)
    role = CharField()  # 消息角色（user/model/system）


class Message_store(PeeweeBaseModel):
    """消息会话存储模型 (LangChain用)"""
    id = AutoField()
    session_id = IntegerField()  # 对应chat_id
    message = JSONField()


# Pydantic 模型 - API请求和响应模型
class ChatCreate(BaseModel):
    """聊天创建请求模型"""
    user_id: int
    title: str = "新对话"


class ChatUpdate(BaseModel):
    """聊天更新请求模型"""
    title: Optional[str] = None


class ChatResponse(BaseModel):
    """聊天响应模型"""
    id: int
    user_id: int
    title: str
    created_at: str
    updated_at: str
    last_message: Optional[str] = None
    message_count: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class MessageCreate(BaseModel):
    """消息创建请求模型"""
    chat_id: int
    user_id: Optional[int] = None
    message: str
    role: str = "user"


class MessageResponse(BaseModel):
    """消息响应模型"""
    id: int
    chat_id: int
    user_id: Optional[int] = None
    message: str
    timestamp: str
    role: str

    model_config = ConfigDict(from_attributes=True)


def get_latest_messages(chat_id, limit=20):
    """获取特定聊天的最新消息"""
    return Message.select().where(Message.chat_id == chat_id).order_by(Message.timestamp.desc()).limit(limit)


def get_user_chats(user_id):
    """获取用户的所有活跃聊天会话"""
    # 简化查询，只获取聊天记录，不再使用 join 和 alias
    return (
        Chat.select()
        .where(
            (Chat.user_id == user_id) &
            (Chat.is_active == 1)
        )
        .order_by(Chat.updated_at.desc())
    )