import asyncio
import os

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory

from adapter.openai_api import model
from database.memory_session import get_session_history
from utils.tools.interpreter import Interpreter, getTime
from utils.tools.retriever import get_retriever_tool
from utils.tools.code_assistant import (
    code_analyzer, 
    code_generator, 
    code_fixer,
    code_documentation,
    dependency_analyzer
)
from utils.tools.code_reviewer import (
    code_quality_check,
    security_review,
    best_practices_advisor
)

# 默认知识库工具 - 只作为备用
default_retriever_tool = get_retriever_tool(path="./vector_db/know_db")

# 基础工具集，不包含知识库检索工具
base_tools = [
    # 基本工具
    getTime, 
    Interpreter,
    
    # 代码助手工具
    code_analyzer,
    code_generator,
    code_fixer,
    code_documentation,
    dependency_analyzer,
    
    # 代码审查工具
    code_quality_check,
    security_review,
    best_practices_advisor
]

# 系统提示
SYSTEM_PROMPT = """你是一个智能代码助手，擅长编程和解决技术问题。你可以：
1. 分析代码结构和语法
2. 根据描述生成代码
3. 修复代码中的错误
4. 检查代码质量并提供改进建议
5. 审查代码安全性
6. 提供编程语言最佳实践
7. 执行简单的代码示例

请使用中文回答问题，并充分利用提供的工具来解决用户的问题。
"""

def get_agent_executor(user_id=None, collection_name=None):
    """
    根据用户ID和知识库集合名称获取定制的agent executor
    :param user_id: 用户ID
    :param collection_name: 知识库集合名称
    :return: 配置好的agent executor
    """
    # 确定使用的检索工具
    if user_id and collection_name:
        # 用户特定知识库路径
        user_kb_path = os.path.join("./vector_db", f"user_{user_id}", collection_name)
        if os.path.exists(user_kb_path):
            # 用户特定知识库存在，使用用户的知识库
            retriever_tool = get_retriever_tool(path=user_kb_path, collection_name=collection_name)
        else:
            # 用户特定知识库不存在，使用默认知识库
            retriever_tool = default_retriever_tool
    else:
        # 没有指定用户ID或集合名称，使用默认知识库
        retriever_tool = default_retriever_tool

    # 合并工具
    tools = base_tools + [retriever_tool]
    
    # 创建提示模板
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}"),
            MessagesPlaceholder(variable_name='agent_scratchpad'),
        ]
    )
    
    # 创建代理和执行器
    chat_agent = create_tool_calling_agent(model, tools, prompt)
    agent_executor = AgentExecutor(agent=chat_agent, tools=tools)
    
    return agent_executor

async def chat_with_agent(msg, session_id, user_id=None, collection_name=None):
    """
    使用代理与用户聊天
    :param msg: 用户消息
    :param session_id: 会话ID
    :param user_id: 用户ID
    :param collection_name: 知识库集合名称
    :return: 代理回复
    """
    # 获取定制的agent executor
    agent_executor = get_agent_executor(user_id, collection_name)
    
    # 添加聊天历史
    agent_with_chat_history = RunnableWithMessageHistory(
        agent_executor,
        get_session_history,
        input_messages_key="question",
        history_messages_key="chat_history",
    )
    
    # 调用代理
    res = agent_with_chat_history.invoke(
        {"question": msg},
        config={"configurable": {"session_id": session_id}},
    )
    
    return res['output']


if __name__ == "__main__":
    # 测试默认知识库
    res = asyncio.run(chat_with_agent("你好", "123"))
    print(res)
    
    # 测试用户知识库
    # res = asyncio.run(chat_with_agent("关于网络的知识", "123", user_id="2", collection_name="network"))
    # print(res)
