import logging
import json
import os
from fastapi import APIRouter, Depends, Request, HTTPException, Path, UploadFile, File
from fastapi.responses import StreamingResponse
from datetime import datetime
from pydantic import ValidationError, BaseModel, Field
from typing import Dict, Any, Optional

from database.models.message import Message, MessageCreate, MessageResponse, Chat
from database.db import db
from routes.auth import get_current_user
from utils.multi_agent import chat_with_multi_agent_original, stream_chat_with_multi_agent

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

        # 构建MCP配置文件路径（如果用户上传了MCP配置）
        mcp_config_path = None
        if data.user_id:
            user_mcp_config = f"./mcp_configs/user_{data.user_id}.json"
            if os.path.exists(user_mcp_config):
                mcp_config_path = user_mcp_config

        # 与多代理对话，传入用户ID和知识库集合名称
        result = await chat_with_multi_agent_original(
            data.message,
            data.user_id,
            user_id=str(current_user.id),
            collection_name=data.collection_name,
            mcp_config_path=mcp_config_path
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


@router.post("/chat/stream")
async def api_chat_stream(request: Request, current_user = Depends(get_current_user)):
    """流式聊天API接口 (POST方法，用于SSE)"""
    try:
        # 获取原始请求数据
        body = await request.json()
        logging.info(f"Stream request headers: {request.headers}")
        logging.info(f"Stream request body: {body}")

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

        # 构建MCP配置文件路径（如果用户上传了MCP配置）
        mcp_config_path = None
        if data.user_id:
            user_mcp_config = f"./mcp_configs/user_{data.user_id}.json"
            if os.path.exists(user_mcp_config):
                mcp_config_path = user_mcp_config

        # 保存用户消息到数据库
        new_message = Message.create(
            chat_id=data.chat_id,
            user_id=data.user_id,
            message=data.message,
            role=data.role
        )

        # 返回流式响应
        async def generate():
            try:
                # 收集完整的AI响应
                full_response = ""

                # 流式调用多代理
                async for chunk in stream_chat_with_multi_agent(
                    data.message,
                    data.user_id,
                    user_id=str(current_user.id),
                    collection_name=data.collection_name,
                    mcp_config_path=mcp_config_path
                ):
                    # 累积响应内容
                    full_response += chunk
                    # 发送每个chunk
                    yield f"data: {json.dumps({'content': chunk})}\n\n"

                # 保存完整的AI响应到数据库
                model_message = Message.create(
                    chat_id=data.chat_id,
                    user_id=data.user_id,
                    message=full_response,
                    role="model"
                )

                # 发送结束标记
                yield "data: [DONE]\n\n"
            except Exception as e:
                logging.exception(f"流式处理聊天请求时出错: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")

    except Exception as e:
        logging.exception(f"处理流式聊天请求时出错: {e}")
        raise HTTPException(status_code=500, detail=f"处理请求失败: {str(e)}")

@router.post("/mcp/upload")
async def upload_mcp_config(file: UploadFile = File(...), user_id: str = None, current_user = Depends(get_current_user)):
    """上传MCP配置文件"""
    try:
        if not user_id:
            raise HTTPException(status_code=400, detail="必须提供用户ID")

        # 验证文件类型
        if not file.filename.endswith('.json'):
            raise HTTPException(status_code=400, detail="只支持JSON文件")

        # 保存文件
        mcp_config_path = f"./mcp_configs/user_{user_id}.json"

        # 读取文件内容
        content = await file.read()

        # 验证JSON格式
        try:
            json.loads(content)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="文件内容不是有效的JSON格式")

        # 保存文件
        with open(mcp_config_path, "wb") as f:
            f.write(content)

        return {"message": "MCP配置文件上传成功", "path": mcp_config_path}

    except Exception as e:
        logging.exception(f"上传MCP配置文件时出错: {e}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


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