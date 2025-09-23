import asyncio
import os
import json
import logging
from typing import Dict, Any, Optional, List
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import HumanMessage, AIMessage
from langchain_mcp_adapters.client import MultiServerMCPClient

from adapter.openai_api import model
from database.memory_session import get_session_history
from database.models.mcp import McpTool
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

def convert_mcp_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    转换MCP配置格式以适配langchain-mcp-adapters要求
    处理两种格式：
    1. 直接的服务器配置格式（正确格式）
    2. 包含mcpServers包装的格式（需要转换）
    """
    # 如果配置已经是正确的格式（直接包含服务器配置），直接返回
    if not config:
        return {}
    
    # 检查是否是包含mcpServers包装的格式
    if 'mcpServers' in config and isinstance(config['mcpServers'], dict):
        # 转换格式：移除mcpServers包装并转换type为transport
        converted = {}
        for server_name, server_config in config['mcpServers'].items():
            # 创建转换后的配置
            converted_config = {}
            for key, value in server_config.items():
                # 将type转换为transport
                if key == 'type':
                    converted_config['transport'] = value
                else:
                    converted_config[key] = value
            converted[server_name] = converted_config
        return converted
    
    # 检查是否是直接的服务器配置但使用了type而不是transport
    converted = {}
    for key, value in config.items():
        if isinstance(value, dict):
            # 转换type为transport
            converted_config = {}
            for sub_key, sub_value in value.items():
                if sub_key == 'type':
                    converted_config['transport'] = sub_value
                else:
                    converted_config[sub_key] = sub_value
            converted[key] = converted_config
        else:
            converted[key] = value
    
    return converted

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

async def load_mcp_tools(mcp_config_path: str = None, user_id: int = None) -> List[Any]:
    """从JSON配置文件或数据库加载MCP工具"""
    try:
        mcp_configs = {}

        # 如果提供了用户ID，优先从数据库加载
        if user_id is not None:
            # 查询用户激活的MCP工具
            tools = McpTool.select().where(
                (McpTool.user_id == user_id) &
                (McpTool.is_active == 1)
            )

            # 合并所有工具配置，并转换格式
            for tool in tools:
                # 转换配置格式（如果需要）
                converted_config = convert_mcp_config(tool.config)
                mcp_configs.update(converted_config)

        # 如果没有从数据库加载到配置且提供了文件路径，则从文件加载
        if not mcp_configs and mcp_config_path and os.path.exists(mcp_config_path):
            with open(mcp_config_path, 'r', encoding='utf-8') as f:
                file_configs = json.load(f)
                # 转换配置格式（如果需要）
                converted_file_configs = convert_mcp_config(file_configs)
                mcp_configs.update(converted_file_configs)

        # 如果有配置则创建MCP客户端
        if mcp_configs:
            # 创建MCP客户端
            client = MultiServerMCPClient(mcp_configs)
            # 获取工具
            tools = await client.get_tools()
            return tools
        else:
            # 没有MCP配置
            return []
    except Exception as e:
        logging.error(f"加载MCP工具时出错: {e}")
        return []

async def get_multi_agent_executor(user_id=None, collection_name=None, mcp_config_path=None):
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

    # 加载MCP工具（优先从数据库加载，如果没有则从文件加载）
    mcp_tools = []
    if user_id:
        # 如果有用户ID，尝试从数据库加载MCP工具
        mcp_tools = await load_mcp_tools(mcp_config_path, int(user_id))
    elif mcp_config_path:
        # 如果没有用户ID但有配置路径，从文件加载
        mcp_tools = await load_mcp_tools(mcp_config_path)

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
    agent_executor = await get_multi_agent_executor(user_id, collection_name, mcp_config_path)

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
    :yield: 代理回复的流式数据，区分工具调用和模型响应
    """
    # 获取多代理执行器
    agent_executor = await get_multi_agent_executor(user_id, collection_name, mcp_config_path)

    # 添加聊天历史
    agent_with_chat_history = RunnableWithMessageHistory(
        agent_executor,
        get_session_history,
        input_messages_key="question",
        history_messages_key="chat_history",
    )

    # 存储工具调用信息
    tool_calls = []
    
    # 使用LangChain的内置流式API
    async for chunk in agent_with_chat_history.astream(
        {"question": msg},
        config={"configurable": {"session_id": session_id}},
    ):
        # 处理不同类型的流式输出
        if isinstance(chunk, dict):
            # 处理工具调用事件
            if "actions" in chunk:
                # 工具调用开始
                for action in chunk["actions"]:
                    # 根据debug结果，action是一个AgentAction对象，具有tool和tool_input属性
                    if hasattr(action, 'tool') and hasattr(action, 'tool_input'):
                        tool_call_info = {
                            "type": "tool_call",
                            "name": action.tool,
                            "input": action.tool_input,
                            "log": getattr(action, 'log', '')
                        }
                        tool_calls.append(tool_call_info)
                        yield f"[TOOL_CALL_START]{json.dumps(tool_call_info)}[TOOL_CALL_END]"
            
            elif "steps" in chunk:
                # 工具调用完成
                for step in chunk["steps"]:
                    # 根据debug结果，step是一个元组 (action, observation)
                    if isinstance(step, tuple) and len(step) >= 2:
                        action, observation = step
                        # action是一个AgentAction对象
                        if hasattr(action, 'tool') and hasattr(action, 'tool_input'):
                            tool_result_info = {
                                "type": "tool_result",
                                "name": action.tool,
                                "input": action.tool_input,
                                "output": str(observation)
                            }
                            yield f"[TOOL_RESULT_START]{json.dumps(tool_result_info)}[TOOL_RESULT_END]"
            
            elif "intermediate_step" in chunk:
                # 中间步骤
                for step in chunk["intermediate_step"]:
                    # 根据debug结果，step是一个元组 (action, observation)
                    if isinstance(step, tuple) and len(step) >= 2:
                        action, observation = step
                        # action是一个AgentAction对象
                        if hasattr(action, 'tool') and hasattr(action, 'tool_input'):
                            intermediate_info = {
                                "type": "intermediate_step",
                                "name": action.tool,
                                "input": action.tool_input,
                                "output": str(observation)
                            }
                            yield f"[INTERMEDIATE_START]{json.dumps(intermediate_info)}[INTERMEDIATE_END]"
            
            # 处理模型最终响应
            elif "output" in chunk and chunk["output"]:
                # 模型最终输出
                yield f"[MODEL_RESPONSE]{chunk['output']}"
            
            # 处理其他字段
            elif "content" in chunk and chunk["content"]:
                yield f"[MODEL_RESPONSE]{chunk['content']}"
            
            elif "messages" in chunk and chunk["messages"]:
                # 处理消息列表
                for msg in chunk["messages"]:
                    if hasattr(msg, 'content') and msg.content:
                        yield f"[MODEL_RESPONSE]{msg.content}"
        
        elif hasattr(chunk, 'content'):
            # 如果是消息对象，提取content
            if chunk.content:
                yield f"[MODEL_RESPONSE]{chunk.content}"
        
        elif hasattr(chunk, 'text'):
            # 处理有text属性的对象
            if chunk.text:
                yield f"[MODEL_RESPONSE]{chunk.text}"
        
        elif chunk is not None and str(chunk).strip():
            # 其他情况直接yield chunk（如果不是None且不为空）
            yield f"[MODEL_RESPONSE]{str(chunk)}"
    
    # 发送工具调用总结信息
    if tool_calls:
        summary_info = {
            "type": "tool_summary",
            "tool_calls": tool_calls
        }
        yield f"[TOOL_SUMMARY_START]{json.dumps(summary_info)}[TOOL_SUMMARY_END]"