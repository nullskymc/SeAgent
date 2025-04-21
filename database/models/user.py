from peewee import AutoField, CharField
from passlib.context import CryptContext
from pydantic import BaseModel
from typing import Optional

from database.models.base import BaseModel as PeeweeBaseModel

# 密码哈希工具
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(PeeweeBaseModel):
    """用户数据模型"""
    id = AutoField()
    user_id = CharField(unique=True, null=False)
    user_password = CharField(null=False)
    email = CharField(unique=True, null=False)

    def set_password(self, password: str):
        """设置哈希密码"""
        self.user_password = pwd_context.hash(password)


# Pydantic模型 - API请求和响应模型
class UserCreate(BaseModel):
    """用户创建请求模型"""
    username: str
    password: str
    email: str


class LoginRequest(BaseModel):
    """登录请求模型"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """令牌响应模型"""
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    """用户信息响应模型"""
    id: int
    username: str
    email: str