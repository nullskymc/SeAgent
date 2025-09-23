import logging
import os
import sqlite3

from database.db import db
from database.models import MODELS

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_chat_id_to_message():
    """为message表添加chat_id字段"""
    try:
        # 获取数据库文件路径
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'chatroom.db')
        
        logger.info(f"连接到数据库: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查message表是否已有chat_id字段
        cursor.execute("PRAGMA table_info(message)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'chat_id' not in columns:
            logger.info("正在为message表添加chat_id字段...")
            cursor.execute("ALTER TABLE message ADD COLUMN chat_id INTEGER;")
            conn.commit()
            logger.info("成功添加chat_id字段")
        else:
            logger.info("message表已有chat_id字段，无需修改")
        
        conn.close()
        logger.info("数据库迁移完成")
        return True
    except Exception as e:
        logger.error(f"数据库迁移失败: {e}")
        return False

def add_tool_calls_to_message():
    """为message表添加tool_calls字段"""
    try:
        # 获取数据库文件路径
        db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'chatroom.db')
        
        logger.info(f"连接到数据库: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查message表是否已有tool_calls字段
        cursor.execute("PRAGMA table_info(message)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'tool_calls' not in columns:
            logger.info("正在为message表添加tool_calls字段...")
            cursor.execute("ALTER TABLE message ADD COLUMN tool_calls JSON;")
            conn.commit()
            logger.info("成功添加tool_calls字段")
        else:
            logger.info("message表已有tool_calls字段，无需修改")
        
        conn.close()
        logger.info("tool_calls字段添加完成")
        return True
    except Exception as e:
        logger.error(f"添加tool_calls字段失败: {e}")
        return False

def create_chat_table():
    """创建Chat表，如果不存在"""
    try:
        logger.info("确保Chat表已创建...")
        if not db.is_closed():
            db.close()
        db.connect()

        # 只创建Chat表
        chat_model = next((model for model in MODELS if model.__name__ == 'Chat'), None)
        if chat_model:
            db.create_tables([chat_model], safe=True)
            logger.info("Chat表创建成功或已存在")
        else:
            logger.error("在MODELS中找不到Chat模型")

        db.close()
        return True
    except Exception as e:
        logger.error(f"创建Chat表失败: {e}")
        return False


def create_mcp_tool_table():
    """创建McpTool表，如果不存在"""
    try:
        logger.info("确保McpTool表已创建...")
        if not db.is_closed():
            db.close()
        db.connect()

        # 只创建McpTool表
        mcp_tool_model = next((model for model in MODELS if model.__name__ == 'McpTool'), None)
        if mcp_tool_model:
            db.create_tables([mcp_tool_model], safe=True)
            logger.info("McpTool表创建成功或已存在")
        else:
            logger.error("在MODELS中找不到McpTool模型")

        db.close()
        return True
    except Exception as e:
        logger.error(f"创建McpTool表失败: {e}")
        return False

if __name__ == "__main__":
    logger.info("开始数据库迁移...")

    # 添加chat_id字段到message表
    if add_chat_id_to_message():
        # 添加tool_calls字段到message表
        if add_tool_calls_to_message():
            # 创建Chat表
            if create_chat_table():
                # 创建McpTool表
                if create_mcp_tool_table():
                    logger.info("数据库迁移全部完成")
                else:
                    logger.error("创建McpTool表失败")
            else:
                logger.error("创建Chat表失败")
        else:
            logger.error("添加tool_calls字段失败")
    else:
        logger.error("迁移message表失败")