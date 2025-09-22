import logging
from fastapi import APIRouter, Depends, Request, HTTPException, Path
from datetime import datetime
from pydantic import ValidationError, BaseModel, Field
from typing import Dict, Any, Optional

from database.models.message import Message, MessageCreate, MessageResponse, Chat
from database.db import db
from routes.auth import get_current_user
from utils.custom_agent import chat_with_agent

router = APIRouter()

class ChatRequest(BaseModel):
    """扩展的聊天请求模型，包含知识库选择"""
    chat_id: int
    user_id: str
    message: str
    role: str = "user"
    collection_name: Optional[str] = None  # 知识库集合名称，可选

@router.post("/chat", response_model=MessageResponse)
async def api_chat(request: Request, current_user = Depends(get_current_user)):
    """统一的聊天API接口"""
    try:
        # 获取原始请求数据
        body = await request.json()
        logging.info(f"Request headers: {request.headers}")
        logging.info(f"Request body: {body}")
        
        # 尝试解析请求数据
        try:
            data = ChatRequest(**body)
        except ValidationError as e:
            logging.error(f"验证错误: {e}")
            raise HTTPException(status_code=422, detail=str(e))
        
        # 验证chat_id是否存在且属于当前用户
        chat = Chat.get_or_none((Chat.id == data.chat_id) & (Chat.is_active == 1))
        if not chat:
            raise HTTPException(
                status_code=404,
                detail="聊天不存在或已被删除"
            )
        
        if chat.user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="没有权限访问此聊天"
            )
        
        # 更新聊天会话的更新时间
        chat.updated_at = datetime.now()
        chat.save()
        
        # 与代理对话，传入用户ID和知识库集合名称
        result = await chat_with_agent(
            data.message, 
            data.user_id, 
            user_id=str(current_user.id), 
            collection_name=data.collection_name
        )

        # 保存用户消息到数据库
        new_message = Message.create(
            chat_id=data.chat_id,
            user_id=data.user_id, 
            message=data.message, 
            role=data.role
        )

        # 保存模型回复
        model_message = Message.create(
            chat_id=data.chat_id,
            user_id=data.user_id, 
            message=result, 
            role="model"
        )
        
        # 返回响应
        return {
            "id": model_message.id,
            "chat_id": model_message.chat_id_id,  # 使用chat_id_id来获取外键值
            "user_id": model_message.user_id,
            "message": model_message.message,
            "timestamp": model_message.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            "role": model_message.role
        }
        
    except Exception as e:
        logging.exception(f"处理聊天请求时出错: {e}")
        raise HTTPException(status_code=500, detail=f"处理请求失败: {str(e)}")

# 为保持兼容性，保留旧的API路径，但内部都使用相同的函数
@router.post("/chat_with_model", response_model=MessageResponse)
async def api_chat_with_model(request: Request, current_user = Depends(get_current_user)):
    """与模型直接对话 (已废弃，请使用 /chat)"""
    return await api_chat(request, current_user)

@router.post("/chat_with_history", response_model=MessageResponse)
async def api_chat_with_history(request: Request, current_user = Depends(get_current_user)):
    """与包含历史记录的模型对话 (已废弃，请使用 /chat)"""
    return await api_chat(request, current_user)

@router.post("/chat_with_agent", response_model=MessageResponse)
async def api_chat_with_agent(request: Request, current_user = Depends(get_current_user)):
    """与代理对话（使用工具增强）"""
    return await api_chat(request, current_user)

@router.post("/chats/{chat_id}/generate-title")
async def generate_title(chat_id: int, current_user: dict = Depends(get_current_user)):
    """为对话生成标题"""
    chat = Chat.get_or_none((Chat.id == chat_id) & (Chat.user_id == current_user.id))
    if not chat:
        raise HTTPException(status_code=404, detail="聊天不存在")

    # 查找第一条AI消息
    first_ai_message = (
        Message.select()
        .where((Message.chat_id == chat_id) & (Message.role == "model"))
        .order_by(Message.timestamp)
        .first()
    )

    if not first_ai_message:
        raise HTTPException(status_code=404, detail="未找到AI消息，无法生成标题")

    # 使用LLM生成标题
    prompt = f"请根据以下内容，为这段对话生成一个简洁的标题，不超过10个字。内容：'{first_ai_message.message}'"
    try:
        response = await model.ainvoke(prompt)
        new_title = response.content.strip().strip('"“”')
    except Exception as e:
        logging.error(f"调用LLM生成标题失败: {e}")
        raise HTTPException(status_code=500, detail="生成标题失败")

    # 更新对话标题
    chat.title = new_title
    chat.save()

    return {"title": new_title}