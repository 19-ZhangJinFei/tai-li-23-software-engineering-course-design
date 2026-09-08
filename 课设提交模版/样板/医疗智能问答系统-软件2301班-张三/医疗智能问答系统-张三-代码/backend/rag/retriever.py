"""检索器配置"""
from llama_index.core.retrievers import VectorIndexRetriever
from config import SIMILARITY_TOP_K


class RetrieverManager:
    def __init__(self, index):
        self.index = index

    def create_vector_retriever(self, top_k: int = None) -> VectorIndexRetriever:
        if top_k is None:
            top_k = SIMILARITY_TOP_K
        return VectorIndexRetriever(index=self.index, similarity_top_k=top_k)

    def create_bm25_retriever(self, nodes=None, top_k: int = None):
        from llama_index.retrievers.bm25 import BM25Retriever
        if top_k is None:
            top_k = SIMILARITY_TOP_K
        if nodes is None:
            nodes = list(self.index.docstore.docs.values())
        return BM25Retriever.from_defaults(nodes=nodes, similarity_top_k=top_k)

    def create_hybrid_retriever(self, nodes=None, top_k: int = None):
        from llama_index.core.retrievers import QueryFusionRetriever
        if top_k is None:
            top_k = SIMILARITY_TOP_K
        vector_retriever = self.create_vector_retriever(top_k=top_k)
        bm25_retriever = self.create_bm25_retriever(nodes=nodes, top_k=top_k)
        return QueryFusionRetriever(retrievers=[vector_retriever, bm25_retriever],
                                    similarity_top_k=top_k, num_queries=1, mode="reciprocal_rerank")

    def retrieve(self, query: str, retriever=None, top_k: int = None):
        if retriever is None:
            retriever = self.create_vector_retriever(top_k=top_k)
        nodes = retriever.retrieve(query)
        print(f"\n🔍 检索查询: '{query}'")
        print(f"   返回 {len(nodes)} 个结果:")
        for i, node in enumerate(nodes):
            score = node.score if node.score else 0
            text_preview = node.text[:80] + "..." if len(node.text) > 80 else node.text
            filename = node.metadata.get("file_name", "未知")
            print(f"   [{i+1}] 相似度={score:.4f} | {filename}")
        return nodes
