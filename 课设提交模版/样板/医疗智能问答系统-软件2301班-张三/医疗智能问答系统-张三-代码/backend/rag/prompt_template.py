"""Prompt模板设计"""
from llama_index.core import PromptTemplate

QA_PROMPT_TEMPLATE = PromptTemplate("""
你是一个医疗领域的专业问答助手。请根据以下检索到的医学知识库内容，回答用户的问题。

## 回答要求：
1. 仅基于下方"知识库内容"回答问题，不要编造信息
2. 如果知识库中没有相关信息，请回答："根据现有知识库无法回答该问题"
3. 回答要准确、专业、清晰
4. 在回答末尾标注引用的来源文档

## 知识库内容：
{context_str}

## 用户问题：
{query_str}

## 回答：
""")

CONDENSE_PROMPT_TEMPLATE = PromptTemplate("""
给定以下对话历史和用户的追问，请将追问重写为一个独立、完整的问题。

## 对话历史：
{chat_history}

## 用户追问：
{question}

## 重写后的完整问题：
""")


def format_sources(nodes) -> str:
    sources = []
    for i, node in enumerate(nodes):
        filename = node.metadata.get("file_name", "未知文档")
        page = node.metadata.get("page_label", "")
        text = node.text[:100] + "..." if len(node.text) > 100 else node.text
        source_str = f"[{i+1}] {filename}"
        if page:
            source_str += f" 第{page}页"
        source_str += f"\n    内容: {text}"
        sources.append(source_str)
    return "\n".join(sources)
