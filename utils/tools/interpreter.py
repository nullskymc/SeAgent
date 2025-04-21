import contextlib
import io
import logging

import requests
from langchain.agents import initialize_agent
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.tools import tool
from langchain.tools.retriever import create_retriever_tool
from langchain_community.vectorstores import Chroma

from adapter.openai_api import embeddings

logging.basicConfig(level=logging.INFO)


def run(code: str) -> str:
    # 去除code第一行可能出现的缩进
    code = code.strip()
    if code.startswith("    "):
        code = code[4:]

    output = io.StringIO()
    try:
        with contextlib.redirect_stdout(output):
            exec(code, {})
    except Exception as e:
        return str(e)
    return output.getvalue()


@tool
def Interpreter(code: str) -> str:
    """
    此函数解释并执行提供的代码，严格去除首行出现的缩进并保证代码符合Python语法。
    """
    logging.info("Tool: interpreter")
    return run(code)


@tool
def getTime(code: str) -> str:
    """
    此函数返回当前时间
    """
    import time
    logging.info("Tool: get_time")
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


if __name__ == "__main__":
    from adapter.openai_api import model as llm
    tools = [getTime, Interpreter, ]
    # 示例使用
    memory = ConversationBufferWindowMemory(memory_key='chat_history', k=3, return_messages=True)
    chat_agent = initialize_agent(
        agent='chat-conversational-react-description',
        tools=tools,
        memory=memory,
        verbose=True,
        max_interations=3,
        llm=llm,
        handle_prasing_error=True
    )
    query = "来一首古诗"
    response = chat_agent.invoke(query)
