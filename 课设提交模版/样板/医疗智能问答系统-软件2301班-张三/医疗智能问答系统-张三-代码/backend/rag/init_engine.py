"""RAG引擎初始化"""
import os
from rag.embedding_setup import configure_settings
from rag.vector_store import VectorStoreManager
from rag.document_processor import load_documents
from chat.engine import ChatEngine
from config import DATA_DIR


def initialize_rag_engine():
    print("\n" + "="*60)
    print("🚀 开始初始化RAG引擎")
    print("="*60)
    print("\n📋 步骤1: 配置LLM和Embedding...")
    llm, embed_model = configure_settings()
    print("\n📋 步骤2: 初始化向量数据库...")
    vector_store_manager = VectorStoreManager()
    existing_count = vector_store_manager.get_document_count()
    if existing_count > 0:
        print(f"\n📋 步骤3: 发现已存储的向量数据({existing_count}条)，加载索引...")
        index = vector_store_manager.get_index()
        print("✅ 索引加载完成")
    else:
        print(f"\n📋 步骤3: 未发现向量数据，尝试加载文档...")
        data_files = []
        if os.path.exists(DATA_DIR):
            for f in os.listdir(DATA_DIR):
                if f.endswith(('.pdf', '.docx', '.doc', '.txt')):
                    data_files.append(f)
        if data_files:
            print(f"   发现 {len(data_files)} 个文档: {data_files}")
            print("\n📋 步骤4: 加载文档并向量化...")
            documents = load_documents()
            index = vector_store_manager.add_documents(documents)
            print("✅ 文档向量化完成")
        else:
            print(f"   ⚠️ {DATA_DIR} 目录中没有文档")
            print("="*60 + "\n")
            return None
    print("\n📋 步骤5: 初始化对话引擎...")
    nodes = list(index.docstore.docs.values()) if hasattr(index, 'docstore') else None
    chat_engine = ChatEngine(index=index, use_hybrid=False, nodes=nodes)
    print("\n" + "="*60)
    print("✅ RAG引擎初始化完成！")
    print(f"   - 知识库向量数: {vector_store_manager.get_document_count()}")
    print("="*60 + "\n")
    return chat_engine


def rebuild_index():
    print("\n🔄 重新构建知识库索引...")
    vector_store_manager = VectorStoreManager()
    vector_store_manager.clear_all()
    documents = load_documents()
    if not documents:
        print("⚠️ 没有文档可加载")
        return None
    index = vector_store_manager.add_documents(documents)
    nodes = list(index.docstore.docs.values()) if hasattr(index, 'docstore') else None
    chat_engine = ChatEngine(index=index, use_hybrid=False, nodes=nodes)
    print("✅ 知识库索引重建完成")
    return chat_engine
