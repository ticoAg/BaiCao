import { renderHook, act } from "@testing-library/react";
import { chatApi } from "../services/api";
import { useChatStore } from "../stores/chatStore";
import { normalizeGraphAgentEvidence, useChat } from "./useChat";

describe("normalizeGraphAgentEvidence", () => {
  it("keeps entity_id separate from source_id", () => {
    const [item] = normalizeGraphAgentEvidence([
      {
        entity_id: "herb-chenpi",
        evidence_id: "ev-1",
        snippet: "陈皮理气健脾。",
        source_id: "src-pharmacopoeia",
        source_name: "中国药典（2020年版）",
      },
    ]);

    expect(item).toMatchObject({
      entity_id: "herb-chenpi",
      evidence_id: "ev-1",
      snippet: "陈皮理气健脾。",
      source_id: "src-pharmacopoeia",
      source_name: "中国药典（2020年版）",
    });
    expect(item.entity_id).not.toBe(item.source_id);
  });

  it("keeps source fields empty when the citation has no source", () => {
    const [item] = normalizeGraphAgentEvidence([
      {
        entity_id: "herb-chenpi",
        evidence_id: "ev-2",
        snippet: "陈皮味苦、辛。",
        source_id: "  ",
        source_name: "",
      },
    ]);

    expect(item.entity_id).toBe("herb-chenpi");
    expect(item.source_id).toBeUndefined();
    expect(item.source_name).toBeUndefined();
  });
});

describe("useChat evidence mapping", () => {
  beforeEach(() => {
    useChatStore.getState().clearMessages();
    vi.restoreAllMocks();
  });

  it("stores final.evidence onto the assistant message", async () => {
    vi.spyOn(chatApi, "stream").mockImplementation((_question, _sessionId, callbacks) => {
      callbacks?.onFinal?.({
        answer: "陈皮可理气健脾。",
        provider_reasoning: [],
        evidence: [
          {
            entity_id: "herb-chenpi",
            evidence_id: "ev-1",
            snippet: "陈皮理气健脾。",
            source_id: "src-pharmacopoeia",
            source_name: "中国药典（2020年版）",
          },
        ],
        related_nodes: [],
        related_edges: [],
        subgraph_meta: {
          center_node_id: null,
          actual_depth: 0,
          fallback_used: false,
          node_count: 0,
          edge_count: 0,
        },
        reasoning_trace: [],
        tool_calls: [],
        session_id: "sid-cite",
      });
      return new AbortController();
    });

    const { result } = renderHook(() => useChat());
    await act(async () => {
      await result.current.sendMessage("陈皮有什么功效？");
    });

    const assistant = result.current.messages.find((message) => message.role === "assistant");
    expect(assistant?.evidence).toEqual([
      {
        entity_id: "herb-chenpi",
        evidence_id: "ev-1",
        snippet: "陈皮理气健脾。",
        source_id: "src-pharmacopoeia",
        source_name: "中国药典（2020年版）",
      },
    ]);
  });
});
