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

    # 创建代理和执行器，优化流式配置
    multi_agent = create_tool_calling_agent(model, tools, prompt)
    agent_executor = AgentExecutor(
        agent=multi_agent,
        tools=tools,
        verbose=True,
        streaming=True,  # 确保开启流式输出
        handle_parsing_errors=True,
        stream_runnable=True,  # 确保Runnable也支持流式
        return_intermediate_steps=True,  # 返回中间步骤以支持工具调用追踪
        max_iterations=10,  # 限制最大迭代次数
        early_stopping_method="generate"  # 优化停止策略
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

# 改进的流式版本的聊天函数，利用LangChain的事件系统实现真正的流式输出
async def stream_chat_with_multi_agent(msg, session_id, user_id=None, collection_name=None, mcp_config_path=None):
    """
    使用多代理与用户聊天（优化的流式版本）
    使用LangChain的事件系统实现真正的字符级流式输出
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

    # 存储工具调用信息和流式文本
    tool_calls = []
    streaming_text = ""
    is_streaming_response = False
    
    try:
        # 使用LangChain的高级事件API进行更精细的流式控制
        async for event in agent_with_chat_history.astream_events(
            {"question": msg},
            config={
                "configurable": {"session_id": session_id},
                "callbacks": []  # 使用默认回调
            },
            version="v2"  # 使用更新的事件API版本
        ):
            event_type = event.get("event", "")
            event_name = event.get("name", "")
            event_data = event.get("data", {})
            
            # 调试：记录所有事件类型
            logging.debug(f"Event: {event_type}, Name: {event_name}, Data keys: {list(event_data.keys()) if isinstance(event_data, dict) else 'not dict'}")
            
            # 处理不同类型的事件
            if event_type == "on_tool_start":
                # 工具开始调用
                tool_name = event_name
                tool_input = event_data.get("input", {})
                
                logging.info(f"🔧 工具开始调用: {tool_name}, 输入: {tool_input}")
                
                tool_call_info = {
                    "type": "tool_call",
                    "name": tool_name,
                    "input": tool_input,
                    "status": "started"
                }
                tool_calls.append(tool_call_info)
                yield f"[TOOL_CALL_START]{json.dumps(tool_call_info, ensure_ascii=False)}[TOOL_CALL_END]"
            
            elif event_type == "on_tool_end":
                # 工具调用结束
                tool_name = event_name
                tool_output = event_data.get("output", "")
                
                logging.info(f"📋 工具调用结束: {tool_name}, 输出: {tool_output}")
                
                tool_result_info = {
                    "type": "tool_result",
                    "name": tool_name,
                    "output": str(tool_output),
                    "status": "completed"
                }
                yield f"[TOOL_RESULT_START]{json.dumps(tool_result_info, ensure_ascii=False)}[TOOL_RESULT_END]"
                
                # 更新tool_calls中对应的工具状态
                for tool_call in tool_calls:
                    if tool_call.get("name") == tool_name:
                        tool_call["status"] = "completed"
                        tool_call["output"] = str(tool_output)
                        break
            
            elif event_type == "on_llm_stream":
                # LLM流式输出 - 这是真正的字符级流式输出
                is_streaming_response = True
                chunk_content = event_data.get("chunk", {})
                
                # 处理OpenAI格式的流式chunk
                if hasattr(chunk_content, 'content') and chunk_content.content:
                    content = chunk_content.content
                    streaming_text += content
                    yield f"[MODEL_RESPONSE]{content}"
                
                # 处理字符串格式的chunk
                elif isinstance(chunk_content, str) and chunk_content:
                    streaming_text += chunk_content
                    yield f"[MODEL_RESPONSE]{chunk_content}"
                
                # 处理字典格式的chunk
                elif isinstance(chunk_content, dict):
                    if "content" in chunk_content and chunk_content["content"]:
                        content = chunk_content["content"]
                        streaming_text += content
                        yield f"[MODEL_RESPONSE]{content}"
                    elif "text" in chunk_content and chunk_content["text"]:
                        text = chunk_content["text"]
                        streaming_text += text
                        yield f"[MODEL_RESPONSE]{text}"
            
            elif event_type == "on_llm_end":
                # LLM输出结束
                # 如果streaming_text为空，尝试从event_data中获取完整输出
                if not streaming_text:
                    output = event_data.get("output", {})
                    if hasattr(output, 'content'):
                        streaming_text = output.content
                        # 实现字符级流式输出
                        if streaming_text and not is_streaming_response:
                            # 如果没有收到流式chunk，模拟字符级输出
                            for i, char in enumerate(streaming_text):
                                yield f"[MODEL_RESPONSE]{char}"
                                # 可选：添加小延迟来模拟打字机效果
                                if i % 10 == 9:  # 每10个字符检查一下
                                    await asyncio.sleep(0.01)  # 非常小的延迟
                    elif isinstance(output, dict) and "content" in output:
                        streaming_text = output["content"]
                        if streaming_text and not is_streaming_response:
                            # 模拟字符级输出
                            for i, char in enumerate(streaming_text):
                                yield f"[MODEL_RESPONSE]{char}"
                                if i % 10 == 9:
                                    await asyncio.sleep(0.01)
            
            elif event_type == "on_agent_action":
                # 代理动作（中间步骤）
                action = event_data.get("action", {})
                if hasattr(action, 'tool') and hasattr(action, 'tool_input'):
                    intermediate_info = {
                        "type": "intermediate_step",
                        "name": action.tool,
                        "input": action.tool_input,
                        "log": getattr(action, 'log', '')
                    }
                    yield f"[INTERMEDIATE_START]{json.dumps(intermediate_info)}[INTERMEDIATE_END]"
            
            elif event_type == "on_chain_end":
                # 链结束，检查是否是agent_executor的最终输出
                if event_name == "AgentExecutor":
                    output = event_data.get("output", {})
                    if isinstance(output, dict) and "output" in output:
                        final_output = output["output"]
                        # 如果没有通过流式获取到内容，使用最终输出
                        if not streaming_text and final_output:
                            # 实现字符级流式输出
                            for i, char in enumerate(final_output):
                                yield f"[MODEL_RESPONSE]{char}"
                                if i % 10 == 9:
                                    await asyncio.sleep(0.01)
        
        # 发送工具调用总结信息 - 但不作为MODEL_RESPONSE发送
        if tool_calls:
            summary_info = {
                "type": "tool_summary",
                "tool_calls": tool_calls
            }
            # 注意：这里不再yield，避免出现在用户消息中
            logging.info(f"工具调用总结: {len(tool_calls)} 个工具被调用")
    
    except Exception as e:
        logging.error(f"流式聊天过程中出错: {e}")
        # 如果流式处理失败，回退到原始实现
        logging.info("回退到原始流式实现")
        yield f"[MODEL_RESPONSE]抱歉，处理您的请求时遇到了一些问题。让我重新尝试...\n\n"
        
        # 回退逻辑：使用原始的astream方法
        try:
            async for chunk in agent_with_chat_history.astream(
                {"question": msg},
                config={"configurable": {"session_id": session_id}},
            ):
                if isinstance(chunk, dict) and "output" in chunk and chunk["output"]:
                    # 对回退的输出也实现字符级流式
                    output_text = chunk["output"]
                    for i, char in enumerate(output_text):
                        yield f"[MODEL_RESPONSE]{char}"
                        if i % 5 == 4:  # 回退时稍微快一些
                            await asyncio.sleep(0.005)
                    break
        except Exception as fallback_error:
            logging.error(f"回退实现也失败: {fallback_error}")
            yield f"[MODEL_RESPONSE]抱歉，系统遇到了技术问题，请稍后重试。"