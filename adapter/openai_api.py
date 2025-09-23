import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

"""OpenAI API适配器"""

# 加载.env文件中的环境变量
load_dotenv()

# 从环境变量获取API密钥和基础URL
openai_api_key = os.getenv("OPENAI_API_KEY")
openai_api_base = os.getenv("OPENAI_API_BASE")

# 设置环境变量
os.environ["OPENAI_API_KEY"] = openai_api_key
os.environ["OPENAI_API_BASE"] = openai_api_base

# 初始化ChatOpenAI模型
model = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL_NAME", "glm-4"),
    streaming=True,
    temperature=0.7
)

# 初始化OpenAI嵌入模型
embeddings = OpenAIEmbeddings(
    model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
    openai_api_key=openai_api_key,
    openai_api_base=openai_api_base
)

if __name__ == "__main__":
    doc = "如何学好编程？"
    vec = embeddings.embed_documents([doc])
    response = model.invoke("如何学好编程？")
    print(vec)
    print(response)
