"""RAG查询引擎"""
from llama_index.core import get_response_synthesizer
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.response_synthesizers import ResponseMode
from rag.retriever import RetrieverManager
from rag.prompt_template import QA_PROMPT_TEMPLATE
from config import SIMILARITY_TOP_K


class RAGEngine:
    def __init__(self, index, use_hybrid=False, nodes=None):
        self.index = index
        self.retriever_manager = RetrieverManager(index)
        if use_hybrid:
            self.retriever = self.retriever_manager.create_hybrid_retriever(nodes=nodes, top_k=SIMILARITY_TOP_K)
            print("✅ 使用混合检索器（向量+BM25）")
        else:
            self.retriever = self.retriever_manager.create_vector_retriever(top_k=SIMILARITY_TOP_K)
            print("✅ 使用向量检索器")
        self.response_synthesizer = get_response_synthesizer(response_mode=ResponseMode.COMPACT)
        self.query_engine = RetrieverQueryEngine(
            retriever=self.retriever, response_synthesizer=self.response_synthesizer)
        self.query_engine.update_prompts({"response_synthesizer:text_qa_template": QA_PROMPT_TEMPLATE})

    def query(self, question: str) -> dict:
        print(f"\n🤖 RAG查询: '{question}'")
        response = self.query_engine.query(question)
        sources = []
        if hasattr(response, "source_nodes") and response.source_nodes:
            for node in response.source_nodes:
                sources.append({
                    "filename": node.metadata.get("file_name", "未知文档"),
                    "page": node.metadata.get("page_label", None),
                    "text": node.text[:200] + "..." if len(node.text) > 200 else node.text,
                    "score": float(node.score) if node.score else None
                })
        answer = str(response)
        print(f"   回答: {answer[:100]}...")
        return {"answer": answer, "sources": sources}
