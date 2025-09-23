from langchain_community.chat_message_histories import ChatMessageHistory
from typing import Dict

# 内存存储会话历史
session_histories: Dict[str, ChatMessageHistory] = {}


def get_session_history(session_id):
    """
    获取会话历史（内存版本，支持异步）
    :param session_id: 会话ID
    :return: ChatMessageHistory 实例
    """
    if session_id not in session_histories:
        session_histories[session_id] = ChatMessageHistory()
    return session_histories[session_id]
