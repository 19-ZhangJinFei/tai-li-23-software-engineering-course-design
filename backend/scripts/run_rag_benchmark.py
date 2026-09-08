"""Run the repeatable 20-grounded/5-refusal RAG acceptance benchmark."""
from __future__ import annotations

import json
import os
from pathlib import Path

import httpx


BASE_URL = os.getenv("BENCHMARK_API_URL", "http://localhost:8000/api/v1")
QUESTIONS = Path(__file__).resolve().parents[1] / "benchmarks" / "questions.json"
REFUSAL_TEXT = "当前课程资料中未找到可靠依据"


def parse_done(body: str) -> dict:
    for block in body.split("\n\n"):
        lines = block.splitlines()
        if "event: done" not in lines:
            continue
        raw = next((line[6:] for line in lines if line.startswith("data: ")), None)
        if raw:
            return json.loads(raw)["message"]
    raise RuntimeError("SSE response did not contain a done event")


def ask(client: httpx.Client, headers: dict[str, str], course_id: str, question: str) -> dict:
    conversation = client.post("/conversations", headers=headers, json={"course_id": course_id})
    conversation.raise_for_status()
    conversation_id = conversation.json()["data"]["id"]
    response = client.post(
        f"/conversations/{conversation_id}/messages",
        headers=headers,
        json={"content": question},
    )
    response.raise_for_status()
    return parse_done(response.text)


def main() -> None:
    dataset = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    with httpx.Client(base_url=BASE_URL, timeout=300) as client:
        login = client.post("/auth/login", json={
            "email": os.getenv("DEMO_STUDENT_EMAIL", "student@demo.com"),
            "password": os.getenv("DEMO_STUDENT_PASSWORD", "Student@123456"),
        })
        login.raise_for_status()
        headers = {"Authorization": f"Bearer {login.json()['data']['access_token']}"}
        courses = client.get("/courses", headers=headers)
        courses.raise_for_status()
        course_id = courses.json()["data"]["items"][0]["id"]

        source_hits = 0
        cited_answers = 0
        failures: list[str] = []
        for item in dataset["grounded"]:
            message = ask(client, headers, course_id, item["question"])
            citations = message.get("citations", [])
            cited_answers += bool(citations)
            hit = any(c.get("document_name") == item["expected_source"] for c in citations[:5])
            source_hits += hit
            if not hit:
                failures.append(f"SOURCE MISS: {item['question']} -> {[c.get('document_name') for c in citations]}")

        refusal_hits = 0
        for item in dataset["ungrounded"]:
            message = ask(client, headers, course_id, item["question"])
            refused = REFUSAL_TEXT in message.get("content", "") and not message.get("citations")
            refusal_hits += refused
            if not refused:
                failures.append(f"REFUSAL MISS: {item['question']}")

    grounded_total = len(dataset["grounded"])
    refusal_total = len(dataset["ungrounded"])
    report = {
        "top5_source_rate": round(source_hits / grounded_total, 3),
        "citation_rate": round(cited_answers / grounded_total, 3),
        "refusal_rate": round(refusal_hits / refusal_total, 3),
        "source_hits": f"{source_hits}/{grounded_total}",
        "refusal_hits": f"{refusal_hits}/{refusal_total}",
        "failures": failures,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["top5_source_rate"] < 0.8 or report["citation_rate"] < 0.9 or refusal_hits != refusal_total:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
