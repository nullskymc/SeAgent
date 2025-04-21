# 导出所有模型，便于导入
from database.models.base import BaseModel
from database.models.user import User, UserCreate, LoginRequest, TokenResponse
from database.models.message import Message, Message_store, MessageCreate, MessageResponse, get_latest_messages, Chat, ChatCreate, ChatResponse, ChatUpdate

# 将所有需要创建表的模型列在这里，方便应用启动时一次性创建
MODELS = [User, Message, Message_store, Chat]