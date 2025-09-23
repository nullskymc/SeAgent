import asyncio
import os
import json
from typing import Dict, Any, Optional, List
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import HumanMessage, AIMessage
from langchain_mcp_adapters.client import MultiServerMCPClient

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

当需要使用特定领域的知识时，你会调用相应的专家代理来协助处理。
"""

# 专家代理系统提示
EXPERT_SYSTEM_PROMPT = """你是一个专门的{expertise}专家代理。你的任务是协助主代理解决{expertise}相关的问题。
请专注于你的专业领域，并提供准确、详细的解答。
"""

def get_expert_agent(expertise: str):
    """创建专家代理"""
    # 专家特定工具（这里可以扩展为不同专家有不同的工具）
    expert_tools = base_tools.copy()

    # 创建专家提示模板
    expert_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", EXPERT_SYSTEM_PROMPT.format(expertise=expertise)),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}"),
            MessagesPlaceholder(variable_name='agent_scratchpad'),
        ]
    )

    # 创建专家代理和执行器
    expert_agent = create_tool_calling_agent(model, expert_tools, expert_prompt)
    expert_executor = AgentExecutor(agent=expert_agent, tools=expert_tools, verbose=True)

    return expert_executor

async def load_mcp_tools(mcp_config_path: str) -> List[Any]:
    """从JSON配置文件加载MCP工具"""
    try:
        if os.path.exists(mcp_config_path):
            with open(mcp_config_path, 'r', encoding='utf-8') as f:
                mcp_configs = json.load(f)

            # 创建MCP客户端
            client = MultiServerMCPClient(mcp_configs)

            # 获取工具
            tools = await client.get_tools()
            return tools
        else:
            print(f"MCP配置文件不存在: {mcp_config_path}")
            return []
    except Exception as e:
        print(f"加载MCP工具时出错: {e}")
        return []

def get_multi_agent_executor(user_id=None, collection_name=None, mcp_config_path=None):
    """
    获取多代理执行器
    :param user_id: 用户ID
    :param collection_name: 知识库集合名称
    :param mcp_config_path: MCP配置文件路径
    :return: 配置好的代理执行器
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

    # 合并基础工具
    tools = base_tools + [retriever_tool]

    # 加载MCP工具（如果提供了配置路径）
    if mcp_config_path:
        mcp_tools = asyncio.run(load_mcp_tools(mcp_config_path))
        tools.extend(mcp_tools)

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
    multi_agent = create_tool_calling_agent(model, tools, prompt)
    agent_executor = AgentExecutor(
        agent=multi_agent,
        tools=tools,
        verbose=True,
        streaming=True,
        handle_parsing_errors=True,
        stream_runnable=True
    )

    return agent_executor

async def chat_with_multi_agent_original(msg, session_id, user_id=None, collection_name=None, mcp_config_path=None):
    """
    使用多代理与用户聊天
    :param msg: 用户消息
    :param session_id: 会话ID
    :param user_id: 用户ID
    :param collection_name: 知识库集合名称
    :param mcp_config_path: MCP配置文件路径
    :return: 代理回复
    """
    # 获取多代理执行器
    agent_executor = get_multi_agent_executor(user_id, collection_name, mcp_config_path)

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

# 流式版本的聊天函数
async def stream_chat_with_multi_agent(msg, session_id, user_id=None, collection_name=None, mcp_config_path=None):
    """
    使用多代理与用户聊天（流式版本）
    :param msg: 用户消息
    :param session_id: 会话ID
    :param user_id: 用户ID
    :param collection_name: 知识库集合名称
    :param mcp_config_path: MCP配置文件路径
    :yield: 代理回复的流式数据
    """
    # 获取多代理执行器
    agent_executor = get_multi_agent_executor(user_id, collection_name, mcp_config_path)

    # 添加聊天历史
    agent_with_chat_history = RunnableWithMessageHistory(
        agent_executor,
        get_session_history,
        input_messages_key="question",
        history_messages_key="chat_history",
    )

    # 使用LangChain的内置流式API
    async for chunk in agent_with_chat_history.astream(
        {"question": msg},
        config={"configurable": {"session_id": session_id}},
    ):
        # 处理不同类型的流式输出
        if isinstance(chunk, dict):
            # 如果是字典，检查不同的字段
            for key, value in chunk.items():
                if key in ['output', 'content'] and value:
                    yield value
                elif key == 'agent_scratchpad':
                    continue  # 忽略中间处理步骤
                elif key == 'messages' and value:
                    # 处理消息列表
                    for msg in value:
                        if hasattr(msg, 'content') and msg.content:
                            yield msg.content
        elif hasattr(chunk, 'content'):
            # 如果是消息对象，提取content
            if chunk.content:
                yield chunk.content
        elif hasattr(chunk, 'text'):
            # 处理有text属性的对象
            if chunk.text:
                yield chunk.text
        elif chunk is not None and str(chunk).strip():
            # 其他情况直接yield chunk（如果不是None且不为空）
            yield str(chunk)