"""向量数据库管理"""
import chromadb
from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from config import CHROMA_DB_PATH, CHROMA_COLLECTION_NAME


class VectorStoreManager:
    def __init__(self):
        self.chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        self.chroma_collection = self.chroma_client.get_or_create_collection(
            name=CHROMA_COLLECTION_NAME, metadata={"hnsw:space": "cosine"})
        self.vector_store = ChromaVectorStore(chroma_collection=self.chroma_collection)
        self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
        print(f"✅ ChromaDB初始化完成: path={CHROMA_DB_PATH}")

    def add_documents(self, documents):
        index = VectorStoreIndex.from_documents(documents, storage_context=self.storage_context, show_progress=True)
        count = self.chroma_collection.count()
        print(f"✅ 文档向量化完成，当前共有 {count} 个向量")
        return index

    def get_index(self):
        return VectorStoreIndex(storage_context=self.storage_context)

    def delete_document(self, filename: str):
        self.chroma_collection.delete(where={"file_name": filename})
        print(f"✅ 已删除文档 {filename} 的向量数据")

    def get_document_count(self) -> int:
        return self.chroma_collection.count()

    def clear_all(self):
        self.chroma_client.delete_collection(CHROMA_COLLECTION_NAME)
        self.chroma_collection = self.chroma_client.get_or_create_collection(
            name=CHROMA_COLLECTION_NAME, metadata={"hnsw:space": "cosine"})
        print("✅ 已清空向量数据库")
