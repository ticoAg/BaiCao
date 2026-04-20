import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ChatPage from "./ChatPage";
import { renderWithProviders } from "../test/render-with-providers";
import { chatApi } from "../services/api";
import { useChatStore } from "../stores/chatStore";

vi.mock("../components/graph/MiniGraphCanvas", () => ({
  default: ({ graphData }: { graphData: { nodes: unknown[] } }) => (
    <div data-testid="mini-graph-canvas">{graphData.nodes.length} nodes</div>
  ),
}));

describe("ChatPage", () => {
  beforeEach(() => {
    useChatStore.getState().clearMessages();
    vi.restoreAllMocks();
  });

  it("renders provider reasoning only when stream emits native reasoning chunks", async () => {
    const user = userEvent.setup();
    vi.spyOn(chatApi, "stream").mockImplementation((_question, _sessionId, callbacks) => {
      callbacks?.onSession?.("sid-1", "turn-1");
      callbacks?.onProviderReasoning?.({ id: "rs-1", text: "先定位病证锚点，再查药材关系" });
      callbacks?.onToolStart?.({
        call_id: "call-1",
        tool_name: "search_nodes",
        arguments: { query: "感冒", limit: 5 },
      });
      callbacks?.onToolResult?.({
        call_id: "call-1",
        tool_name: "search_nodes",
        result_summary: "返回 2 个候选节点",
      });
      callbacks?.onAnswerChunk?.("可考虑桂枝。");
      callbacks?.onFinal?.({
        answer: "可考虑桂枝。",
        provider_reasoning: [{ id: "rs-1", text: "先定位病证锚点，再查药材关系" }],
        evidence: [],
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
        session_id: "sid-1",
      });
      return new AbortController();
    });

    renderWithProviders(<ChatPage />);

    await user.type(
      screen.getByPlaceholderText("输入您的问题，例如：陈皮有什么功效？"),
      "感冒怎么办",
    );
    await user.click(screen.getByRole("button", { name: /发送/ }));

    expect(await screen.findByText("先定位病证锚点，再查药材关系")).toBeInTheDocument();
    expect(screen.getByText("provider_reasoning")).toBeInTheDocument();
    expect(screen.getByText("search_nodes")).toBeInTheDocument();
    expect(screen.getByText(/"query": "感冒"/)).toBeInTheDocument();
    expect(screen.getByText("返回 2 个候选节点")).toBeInTheDocument();
    expect(screen.getByText("可考虑桂枝。")).toBeInTheDocument();
  });

  it("does not render reasoning panel when provider reasoning is absent", async () => {
    const user = userEvent.setup();
    vi.spyOn(chatApi, "stream").mockImplementation((_question, _sessionId, callbacks) => {
      callbacks?.onSession?.("sid-2", "turn-2");
      callbacks?.onAnswerChunk?.("暂无足够图谱证据。");
      callbacks?.onFinal?.({
        answer: "暂无足够图谱证据。",
        provider_reasoning: [],
        evidence: [],
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
        session_id: "sid-2",
      });
      return new AbortController();
    });

    renderWithProviders(<ChatPage />);
    await user.type(
      screen.getByPlaceholderText("输入您的问题，例如：陈皮有什么功效？"),
      "外寒入里怎么办",
    );
    await user.click(screen.getByRole("button", { name: /发送/ }));

    expect(await screen.findByText("暂无足够图谱证据。")).toBeInTheDocument();
    expect(screen.queryByText("provider_reasoning")).not.toBeInTheDocument();
  });
});
