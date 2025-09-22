import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.tools import create_retriever_tool

from adapter.openai_api import embeddings

# 加载环境变量
load_dotenv()

# 获取Chroma配置
PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", "vector_db")
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "knowledge_base")

def get_retriever_tool(path=None, collection_name=None):
    """
    创建基于Chroma的检索工具
    :param path: 向量数据库路径，默认使用环境变量中的配置
    :param collection_name: 集合名称，默认使用环境变量中的配置
    :return: 检索工具
    """
    if path is None:
        path = PERSIST_DIRECTORY
    
    if collection_name is None:
        collection_name = COLLECTION_NAME
    
    # 加载Chroma数据库
    db = Chroma(
        persist_directory=path,
        embedding_function=embeddings,
        collection_name=collection_name
    )
    
    # 创建检索器
    retriever = db.as_retriever(
        search_kwargs={"k": 5}  # 检索前5个最相关的文档
    )
    
    # 创建检索工具，将名称改为符合OpenAI API规范的英文
    retriever_tool = create_retriever_tool(
        retriever,
        "knowledge_base",  # 修改为英文名称
        "这里存储着有关于问题的背景资料，you must use this tool!"
    )
    
    return retriever_tool
