"""Embedding和LLM配置"""
from llama_index.core import Settings
from config import DASHSCOPE_API_KEY, EMBEDDING_MODEL, LLM_MODEL


def configure_embedding():
    from llama_index.embeddings.dashscope import DashScopeEmbedding
    return DashScopeEmbedding(model_name=EMBEDDING_MODEL, api_key=DASHSCOPE_API_KEY)


def configure_llm():
    from llama_index.llms.dashscope import DashScopeGenerator
    return DashScopeGenerator(model=LLM_MODEL, api_key=DASHSCOPE_API_KEY)


def configure_settings():
    embed_model = configure_embedding()
    llm = configure_llm()
    Settings.embed_model = embed_model
    Settings.llm = llm
    from llama_index.core.node_parser import SentenceSplitter
    Settings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=50)
    print(f"✅ LlamaIndex全局配置完成: LLM={LLM_MODEL}, Embedding={EMBEDDING_MODEL}")
    return llm, embed_model
