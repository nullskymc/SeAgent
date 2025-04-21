# 此文件已被废弃，所有聊天功能统一使用 custom_agent.py 中的 chat_with_agent
# 保留此文件仅为了向后兼容，建议直接使用 custom_agent.py

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取Chroma配置
PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", "vector_db")
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "knowledge_base")
