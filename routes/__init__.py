# 路由模块初始化文件
from fastapi import APIRouter

# 创建主路由
api_router = APIRouter()

# 导入并包含各模块路由
from routes.auth import router as auth_router
from routes.chat import router as chat_router
from routes.messages import router as messages_router
from routes.knowledge import router as knowledge_router

# 注册子路由
api_router.include_router(auth_router, prefix="/auth", tags=["认证"])
api_router.include_router(chat_router, prefix="/api", tags=["聊天"])
api_router.include_router(messages_router, prefix="/messages", tags=["消息管理"])
api_router.include_router(knowledge_router, prefix="/knowledge", tags=["知识库管理"])