"""文档处理模块"""
import os
from typing import List
from llama_index.core import Document, SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter
from config import DATA_DIR, CHUNK_SIZE, CHUNK_OVERLAP


def load_documents(data_dir: str = None) -> List[Document]:
    if data_dir is None:
        data_dir = DATA_DIR
    if not os.path.exists(data_dir):
        raise FileNotFoundError(f"文档目录不存在: {data_dir}")
    reader = SimpleDirectoryReader(input_dir=data_dir, required_exts=[".pdf", ".docx", ".doc", ".txt"],
                                   recursive=False, exclude_hidden=True, filename_as_id=True)
    documents = reader.load_data()
    print(f"✅ 成功加载 {len(documents)} 个文档")
    for doc in documents:
        filename = doc.metadata.get("file_name", "未知")
        print(f"   - {filename}: {len(doc.text)} 个字符")
    return documents


def split_documents_into_nodes(documents: List[Document], chunk_size: int = None, chunk_overlap: int = None) -> List:
    if chunk_size is None:
        chunk_size = CHUNK_SIZE
    if chunk_overlap is None:
        chunk_overlap = CHUNK_OVERLAP
    splitter = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    nodes = splitter.get_nodes_from_documents(documents)
    print(f"✅ 文档分块完成: {len(documents)} 个文档 → {len(nodes)} 个节点")
    return nodes


if __name__ == "__main__":
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"⚠️ 请将医学文档放入 {DATA_DIR} 目录后重试")
    else:
        documents = load_documents()
        nodes = split_documents_into_nodes(documents)
        if nodes:
            print(f"\n第一个节点完整内容:")
            print(f"ID: {nodes[0].id_}")
            print(f"Text: {nodes[0].text[:200]}")
