from typing import Any


def extract_provider_reasoning_chunks(payload: dict[str, Any]) -> list[dict[str, str]]:
    chunks: list[dict[str, str]] = []
    for item in payload.get("output", []):
        if not isinstance(item, dict) or item.get("type") != "reasoning":
            continue
        item_id = item.get("id")
        for summary in item.get("summary", []):
            if isinstance(summary, dict) and isinstance(summary.get("text"), str):
                chunk = {"text": summary["text"]}
                if isinstance(item_id, str):
                    chunk["id"] = item_id
                chunks.append(chunk)
    return chunks
