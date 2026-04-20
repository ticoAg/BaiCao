from app.services.chat_agent_runtime.provider_reasoning import extract_provider_reasoning_chunks


def test_extract_provider_reasoning_chunks_returns_empty_when_provider_has_no_reasoning():
    chunks = extract_provider_reasoning_chunks({"output": [{"type": "message", "content": []}]})

    assert chunks == []


def test_extract_provider_reasoning_chunks_preserves_native_reasoning_text():
    chunks = extract_provider_reasoning_chunks(
        {
            "output": [
                {
                    "type": "reasoning",
                    "id": "rs-1",
                    "summary": [{"type": "summary_text", "text": "先定位病证锚点，再查药材关系"}],
                }
            ]
        }
    )

    assert chunks == [{"id": "rs-1", "text": "先定位病证锚点，再查药材关系"}]
