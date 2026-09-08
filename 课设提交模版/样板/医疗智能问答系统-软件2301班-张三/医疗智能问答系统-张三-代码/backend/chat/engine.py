"""多轮对话引擎"""
import uuid
from llama_index.core.chat_engine import CondenseQuestionChatEngine
from llama_index.core.memory import ChatMemoryBuffer
from rag.retriever import RetrieverManager
from rag.prompt_template import QA_PROMPT_TEMPLATE, CONDENSE_PROMPT_TEMPLATE
from config import SIMILARITY_TOP_K


class ChatEngine:
    def __init__(self, index, use_hybrid=False, nodes=None):
        self.index = index
        self.use_hybrid = use_hybrid
        self.nodes = nodes
        self.sessions: dict[str, CondenseQuestionChatEngine] = {}
        self.create_session()

    def create_session(self, session_id: str = None) -> str:
        if session_id is None:
            session_id = str(uuid.uuid4())
        memory = ChatMemoryBuffer.from_defaults(token_limit=3000)
        retriever_manager = RetrieverManager(self.index)
        if self.use_hybrid:
            retriever = retriever_manager.create_hybrid_retriever(nodes=self.nodes, top_k=SIMILARITY_TOP_K)
        else:
            retriever = retriever_manager.create_vector_retriever(top_k=SIMILARITY_TOP_K)
        chat_engine = CondenseQuestionChatEngine.from_defaults(retriever=retriever, memory=memory, verbose=True)
        chat_engine.update_prompts({
            "condense_prompt": CONDENSE_PROMPT_TEMPLATE,
            "response_synthesizer:text_qa_template": QA_PROMPT_TEMPLATE,
        })
        self.sessions[session_id] = chat_engine
        print(f"✅ 创建对话会话: {session_id}")
        return session_id

    def chat(self, message: str, session_id: str = None) -> dict:
        if session_id is None:
            session_id = self.create_session()
        if session_id not in self.sessions:
            session_id = self.create_session(session_id)
        chat_engine = self.sessions[session_id]
        print(f"\n💬 对话 [{session_id[:8]}...]: '{message}'")
        response = chat_engine.chat(message)
        sources = []
        if hasattr(response, "source_nodes") and response.source_nodes:
            for node in response.source_nodes:
                sources.append({
                    "filename": node.metadata.get("file_name", "未知文档"),
                    "page": node.metadata.get("page_label", None),
                    "text": node.text[:200] + "..." if len(node.text) > 200 else node.text,
                    "score": float(node.score) if node.score else None
                })
        return {"answer": str(response), "sources": sources, "session_id": session_id}

    def get_chat_history(self, session_id: str) -> list:
        if session_id not in self.sessions:
            return []
        chat_engine = self.sessions[session_id]
        memory = chat_engine.memory
        history = []
        for message in memory.get_all():
            role = "user" if message.role == "user" else "assistant"
            history.append({"role": role, "content": str(message.content)})
        return history

    def clear_session(self, session_id: str):
        if session_id in self.sessions:
            self.sessions[session_id].memory.reset()
            print(f"✅ 已清除会话 {session_id} 的历史")

    def list_sessions(self) -> list:
        return list(self.sessions.keys())
