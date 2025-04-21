from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain_community.document_loaders.csv_loader import CSVLoader


def text_loader(url):
    # 文本文档加载器
    loader = TextLoader(url)
    docs = loader.load()
    return docs


def csv_loader(url):
    # csv文档加载器
    loader = CSVLoader(file_path=url)
    docs = loader.load()
    return docs


def pdf_loader(url):
    # pdf文档加载器
    loader = PyPDFLoader(url)
    docs = loader.load_and_split()
    return docs
