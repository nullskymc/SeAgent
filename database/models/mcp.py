from datetime import datetime
from peewee import AutoField, IntegerField, TextField, DateTimeField, CharField, SQL, ForeignKeyField
from playhouse.sqlite_ext import JSONField
from pydantic import BaseModel, ConfigDict

from database.models.base import BaseModel as PeeweeBaseModel
from database.models.user import User


class McpTool(PeeweeBaseModel):
    """MCP工具配置模型"""
    id = AutoField()
    user_id = IntegerField()  # 所属用户ID
    name = CharField()  # 工具名称
    config = JSONField()  # MCP配置JSON
    created_at = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')], default=datetime.now)
    updated_at = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')], default=datetime.now)
    is_active = IntegerField(default=1)  # 是否活跃状态，1=活跃，0=已删除

    class Meta:
        table_name = 'mcp_tool'


# Pydantic 模型 - API请求和响应模型
class McpToolCreate(BaseModel):
    """MCP工具创建请求模型"""
    user_id: int
    name: str
    config: dict


class McpToolUpdate(BaseModel):
    """MCP工具更新请求模型"""
    name: str = None
    config: dict = None
    is_active: int = None


class McpToolResponse(BaseModel):
    """MCP工具响应模型"""
    id: int
    user_id: int
    name: str
    config: dict
    created_at: str
    updated_at: str
    is_active: int

    model_config = ConfigDict(from_attributes=True)