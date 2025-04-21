from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from pydantic import BaseModel

from database.db import db
from database.models.message import Message, MessageResponse, MessageCreate, Chat, ChatCreate, ChatResponse, ChatUpdate
from routes.auth import get_current_user, get_user_id, get_user_id_from_token

router = APIRouter()

# 对话列表响应模型
class ChatListResponse(BaseModel):
    id: int
    user_id: int
    title: str
    last_message: Optional[str] = None
    updated_at: str


@router.get("/", response_model=List[MessageResponse], dependencies=[Depends(db)])
async def get_messages(skip: int = 0, limit: int = 100):
    """
    获取所有消息
    """
    messages = Message.select().offset(skip).limit(limit)
    return [
        {
            "id": msg.id,
            "user_id": msg.user_id,
            "message": msg.message,
            "timestamp": msg.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            "role": msg.role
        } for msg in messages
    ]


@router.get("/{message_id}", response_model=MessageResponse, dependencies=[Depends(db)])
async def get_message(message_id: int):
    """
    获取单个消息
    """
    message = Message.get_or_none(Message.id == message_id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="消息不存在"
        )
    
    return {
        "id": message.id,
        "user_id": message.user_id,
        "message": message.message,
        "timestamp": message.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
        "role": message.role
    }


@router.get("/user/{user_id}", response_model=List[MessageResponse], dependencies=[Depends(db)])
async def get_user_messages(user_id: int, skip: int = 0, limit: int = 100):
    """
    获取指定用户的所有消息
    """
    messages = Message.select().where(Message.user_id == user_id).offset(skip).limit(limit)
    return [
        {
            "id": msg.id,
            "user_id": msg.user_id,
            "message": msg.message,
            "timestamp": msg.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            "role": msg.role
        } for msg in messages
    ]


@router.delete("/{message_id}")
async def delete_message(message_id: int, current_user = Depends(get_current_user)):
    """
    删除消息
    """
    message = Message.get_or_none(Message.id == message_id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="消息不存在"
        )
    
    # 确保用户只能删除自己的消息（角色为user的消息）
    if message.role == 'user' and message.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限删除此消息"
        )
    
    # 获取所属的聊天会话
    chat_id = message.chat_id_id
    
    # 删除消息
    message.delete_instance()
    
    # 更新聊天会话的更新时间
    chat = Chat.get_or_none(Chat.id == chat_id)
    if chat:
        chat.updated_at = datetime.now()
        chat.save()
    
    return {"detail": "消息已删除"}


@router.post("/chat", response_model=ChatResponse)
async def create_chat(chat_data: ChatCreate, current_user = Depends(get_current_user)):
    """创建新的聊天会话"""
    # 确保用户只能为自己创建会话
    if chat_data.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只能为当前登录用户创建聊天会话"
        )
    
    # 创建新的聊天会话
    new_chat = Chat.create(
        user_id=chat_data.user_id,
        title=chat_data.title
    )
    
    # 创建一条系统消息作为会话的开始
    Message.create(
        chat_id=new_chat.id,
        user_id=chat_data.user_id,
        message=f"对话开始: {chat_data.title}",
        role="system"
    )
    
    return {
        "id": new_chat.id,
        "user_id": new_chat.user_id,
        "title": new_chat.title,
        "created_at": new_chat.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        "updated_at": new_chat.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
    }


@router.get("/chats", response_model=List[ChatResponse])
async def get_my_chats(user_id: Optional[int] = Depends(get_user_id)):
    """获取当前用户的所有对话"""
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="需要提供用户ID参数或有效的认证token"
        )
    
    from database.models.message import get_user_chats
    from peewee import fn
    
    # 获取用户的所有聊天会话及最新一条消息
    chats_query = get_user_chats(user_id)
    
    result = []
    for chat in chats_query:
        # 获取消息数量
        message_count = Message.select(fn.COUNT('*')).where(
            (Message.chat_id == chat.id) & 
            (Message.role != "system")  # 不计算系统消息
        ).scalar()
        
        # 获取最新一条非系统消息
        last_message = Message.select().where(
            (Message.chat_id == chat.id) & 
            (Message.role != "system")
        ).order_by(Message.timestamp.desc()).first()
        
        # 构造响应，确保是一个包含所需字段的字典
        chat_data = {
            "id": chat.id,
            "user_id": chat.user_id,
            "title": chat.title,
            "created_at": chat.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            "updated_at": chat.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            "last_message": last_message.message if last_message else None,
            "message_count": message_count
        }
        result.append(chat_data)
    
    # 调试输出
    print(f"返回的聊天列表数据: {result}")
    return result


@router.get("/chats/{user_id}", response_model=List[ChatResponse], dependencies=[Depends(db)])
async def get_user_chats_by_id(user_id: int):
    """获取指定用户的所有对话"""
    try:
        from database.models.message import get_user_chats
        from peewee import fn
        
        # 调试信息
        print(f"请求 /chats/{user_id} - 开始处理")
        
        # 获取用户的所有聊天会话
        chats_query = get_user_chats(user_id)
        
        result = []
        for chat in chats_query:
            try:
                # 获取消息数量
                message_count = Message.select(fn.COUNT('*')).where(
                    (Message.chat_id == chat.id) & 
                    (Message.role != "system")  # 不计算系统消息
                ).scalar()
                
                # 获取最新一条非系统消息
                last_message = Message.select().where(
                    (Message.chat_id == chat.id) & 
                    (Message.role != "system")
                ).order_by(Message.timestamp.desc()).first()
                
                # 打印调试信息
                print(f"处理聊天ID: {chat.id}, 标题: {chat.title}, 消息数量: {message_count}")
                
                # 构造响应，只包含ChatResponse模型中定义的字段
                chat_data = {
                    "id": chat.id,
                    "user_id": chat.user_id,
                    "title": chat.title,
                    "created_at": chat.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    "updated_at": chat.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                    "message_count": message_count,
                    "last_message": last_message.message if last_message else None
                }
                result.append(chat_data)
                
            except Exception as e:
                print(f"处理聊天ID: {chat.id} 时出错: {str(e)}")
        
        # 调试输出完整结果
        print(f"返回的聊天列表数据: {result}")
        return result
        
    except Exception as e:
        # 捕获并打印所有异常
        print(f"处理 /chats/{user_id} 请求时出错: {str(e)}")
        raise


@router.get("/chat/{chat_id}", response_model=Dict[str, Any])
async def get_chat(chat_id: int, current_user = Depends(get_current_user)):
    """获取特定聊天的详细信息和最新消息"""
    # 检查聊天是否存在以及是否归属于当前用户
    chat = Chat.get_or_none((Chat.id == chat_id) & (Chat.is_active == 1))
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="聊天不存在或已被删除"
        )
    
    if chat.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限访问此聊天"
        )
    
    # 获取聊天的详细信息
    from peewee import fn
    
    # 获取消息数量
    message_count = Message.select(fn.COUNT('*')).where(
        (Message.chat_id == chat_id) & 
        (Message.role != "system")
    ).scalar()
    
    # 获取最近的消息（不包括系统消息）
    messages = Message.select().where(
        (Message.chat_id == chat_id) & 
        (Message.role != "system")
    ).order_by(Message.timestamp.desc()).limit(20)
    
    message_list = []
    for msg in messages:
        message_list.append({
            "id": msg.id,
            "chat_id": msg.chat_id_id,  # 注意这里使用chat_id_id而不是chat_id
            "user_id": msg.user_id,
            "message": msg.message,
            "timestamp": msg.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            "role": msg.role
        })
    
    return {
        "chat": {
            "id": chat.id,
            "user_id": chat.user_id,
            "title": chat.title,
            "created_at": chat.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            "updated_at": chat.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            "message_count": message_count
        },
        "messages": message_list
    }


@router.get("/chat/{chat_id}/messages", response_model=List[MessageResponse])
async def get_chat_messages(
    chat_id: int, 
    skip: int = 0, 
    limit: int = 20, 
    current_user = Depends(get_current_user)
):
    """获取特定聊天的消息列表"""
    # 检查聊天是否存在以及是否归属于当前用户
    chat = Chat.get_or_none((Chat.id == chat_id) & (Chat.is_active == 1))
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="聊天不存在或已被删除"
        )
    
    if chat.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限访问此聊天"
        )
    
    # 获取聊天消息
    messages = Message.select().where(
        (Message.chat_id == chat_id) & 
        (Message.role != "system")  # 不返回系统消息
    ).order_by(Message.timestamp).offset(skip).limit(limit)
    
    return [
        {
            "id": msg.id,
            "chat_id": msg.chat_id_id,  # 注意这里使用chat_id_id而不是chat_id
            "user_id": msg.user_id,
            "message": msg.message,
            "timestamp": msg.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            "role": msg.role
        } for msg in messages
    ]


@router.put("/chat/{chat_id}", response_model=ChatResponse)
async def update_chat(
    chat_id: int, 
    chat_data: ChatUpdate, 
    current_user = Depends(get_current_user)
):
    """更新聊天信息（如标题）"""
    # 检查聊天是否存在以及是否归属于当前用户
    chat = Chat.get_or_none((Chat.id == chat_id) & (Chat.is_active == 1))
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="聊天不存在或已被删除"
        )
    
    if chat.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限更新此聊天"
        )
    
    # 更新聊天信息
    if chat_data.title:
        chat.title = chat_data.title
    
    chat.updated_at = datetime.now()
    chat.save()
    
    return {
        "id": chat.id,
        "user_id": chat.user_id,
        "title": chat.title,
        "created_at": chat.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        "updated_at": chat.updated_at.strftime('%Y-%m-%d %H:%M:%S')
    }


@router.delete("/chat/{chat_id}")
async def delete_chat(chat_id: int, current_user = Depends(get_current_user)):
    """删除聊天（软删除）"""
    # 检查聊天是否存在以及是否归属于当前用户
    chat = Chat.get_or_none((Chat.id == chat_id) & (Chat.is_active == 1))
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="聊天不存在或已被删除"
        )
    
    if chat.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="没有权限删除此聊天"
        )
    
    # 软删除聊天（将is_active设为0）
    chat.is_active = 0
    chat.updated_at = datetime.now()
    chat.save()
    
    return {"detail": "聊天已删除"}


@router.get("/user-chats/{user_id}", response_model=List[dict])
async def get_simple_user_chats(user_id: int):
    """简化版：获取指定用户的所有对话"""
    try:
        # 直接使用简单的SQL查询而不是复杂的ORM操作
        chats = Chat.select().where(
            (Chat.user_id == user_id) & 
            (Chat.is_active == 1)
        ).order_by(Chat.updated_at.desc())
        
        result = []
        for chat in chats:
            # 查找最新消息
            last_message = Message.select().where(
                (Message.chat_id == chat.id) & 
                (Message.role != "system")
            ).order_by(Message.timestamp.desc()).first()
            
            # 构造简单的字典响应
            chat_data = {
                "id": chat.id,
                "user_id": chat.user_id,
                "title": chat.title,
                "created_at": chat.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                "updated_at": chat.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
                "message_count": Message.select().where(
                    (Message.chat_id == chat.id) & 
                    (Message.role != "system")
                ).count(),
                "last_message": last_message.message if last_message else None
            }
            result.append(chat_data)
        
        print(f"返回用户 {user_id} 的聊天列表: {result}")
        return result
    
    except Exception as e:
        print(f"获取用户 {user_id} 聊天列表出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取聊天列表失败: {str(e)}")