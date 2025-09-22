from langchain_chroma import Chroma
from langchain_text_splitters import CharacterTextSplitter
import os
from dotenv import load_dotenv

from adapter.openai_api import embeddings
from utils.loader import text_loader

# 加载环境变量
load_dotenv()

# 获取Chroma配置
PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", "vector_db")
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "knowledge_base")

# 以某一系列文本创建以Chroma为后端的向量数据库
def create_vector_db(data_path, db_path=None, loader=text_loader, collection_name=None):
    """
    创建Chroma向量数据库
    :param data_path: 数据文件路径
    :param db_path: 数据库路径，默认为环境变量中配置的路径
    :param loader: 加载器函数
    :param collection_name: 集合名称，默认为环境变量中配置的名称
    :return: 创建的Chroma向量数据库
    """
    if db_path is None:
        db_path = PERSIST_DIRECTORY
    
    if collection_name is None:
        collection_name = COLLECTION_NAME

    # 确保目录存在
    if not os.path.exists(db_path):
        os.makedirs(db_path)
        
    # 加载文档
    documents = loader(data_path)
    
    # 拆分文档
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    docs = text_splitter.split_documents(documents)
    
    # 创建向量数据库
    db = Chroma.from_documents(
        documents=docs, 
        embedding=embeddings,
        persist_directory=db_path,
        collection_name=collection_name
    )
    
    # 持久化到磁盘
    db.persist()
    
    return db

def merge_collections(base_db_path, new_data_path, loader=text_loader, collection_name=None):
    """
    将新数据合并到现有的Chroma集合中
    :param base_db_path: 基础数据库路径
    :param new_data_path: 新数据文件路径
    :param loader: 加载器函数
    :param collection_name: 集合名称，默认为环境变量中配置的名称
    :return: 更新后的Chroma数据库
    """
    if collection_name is None:
        collection_name = COLLECTION_NAME
        
    # 加载现有数据库
    db = Chroma(
        persist_directory=base_db_path,
        embedding_function=embeddings,
        collection_name=collection_name
    )
    
    # 加载新文档
    documents = loader(new_data_path)
    
    # 拆分文档
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    docs = text_splitter.split_documents(documents)
    
    # 添加到现有集合
    db.add_documents(docs)
    
    # 持久化到磁盘
    db.persist()
    
    return db

if __name__ == "__main__":
    # 创建数据库示例
    create_vector_db("../testdata/py2.txt")
    
    # 合并新数据示例
    # merge_collections(PERSIST_DIRECTORY, "../testdata/new_data.txt")
