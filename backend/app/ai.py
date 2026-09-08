from __future__ import annotations
import hashlib
import json
import math
import re
from typing import Iterable
from openai import OpenAI
from .config import settings


def _normalize(v: list[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / norm for x in v]


class AIProvider:
    def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError

    def generate(self, prompt: str) -> str:
        raise NotImplementedError

    def generate_json(self, prompt: str) -> dict:
        text = self.generate(prompt)
        match = re.search(r"\{.*\}", text, re.S)
        return json.loads(match.group(0) if match else text)


class FakeAIProvider(AIProvider):
    """Deterministic provider for tests and keyless course demonstrations."""

    def embed(self, texts: list[str]) -> list[list[float]]:
        result = []
        for text in texts:
            vector = [0.0] * settings.embedding_dimension
            compact = re.sub(r"\s+", "", text.lower())
            tokens = list(compact) + [compact[i:i + 2] for i in range(max(0, len(compact) - 1))]
            for token in tokens:
                digest = hashlib.sha256(token.encode("utf-8")).digest()
                idx = int.from_bytes(digest[:4], "big") % len(vector)
                vector[idx] += 1.0 if digest[4] % 2 else -1.0
            result.append(_normalize(vector))
        return result

    def generate(self, prompt: str) -> str:
        source_block = re.search(r"<sources>\s*(.*?)\s*</sources>", prompt, re.S)
        sources = re.findall(r"\[(S\d+)\]\s*(.+?)(?=\n\[S\d+\]|\Z)",
                             source_block.group(1) if source_block else "", re.S)
        if sources:
            lines = [s[1].strip().replace("\n", " ")[:180] for s in sources[:2]]
            return "根据课程资料，" + "；".join(lines) + "。" + " ".join(f"[{s[0]}]" for s in sources[:2])
        return "已根据课程资料完成生成。"


class DashScopeProvider(AIProvider):
    def __init__(self):
        self.client = OpenAI(api_key=settings.dashscope_api_key, base_url=settings.dashscope_base_url)

    def embed(self, texts: list[str]) -> list[list[float]]:
        response = self.client.embeddings.create(
            model=settings.dashscope_embedding_model,
            input=texts,
            dimensions=settings.embedding_dimension,
        )
        return [item.embedding for item in response.data]

    def generate(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=settings.dashscope_chat_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return response.choices[0].message.content or ""


def get_ai() -> AIProvider:
    if settings.ai_mode == "dashscope" and settings.dashscope_api_key:
        return DashScopeProvider()
    return FakeAIProvider()


def cosine_similarity(a: Iterable[float], b: Iterable[float]) -> float:
    a, b = list(a), list(b)
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    return dot / (na * nb) if na and nb else 0.0
