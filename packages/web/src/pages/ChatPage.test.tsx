import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ChatPage from "./ChatPage";
import { renderWithProviders } from "../test/render-with-providers";
import { chatApi, provenanceApi } from "../services/api";
import { useChatStore } from "../stores/chatStore";
import type { ChatAgentFinalPayload, GraphAgentEvidence } from "../types/chat";

vi.mock("../components/graph/MiniGraphCanvas", () => ({
  default: ({ graphData }: { graphData: { nodes: unknown[] } }) => (
    <div data-testid="mini-graph-canvas">{graphData.nodes.length} nodes</div>
  ),
}));

const emptySubgraphMeta = {
  center_node_id: null,
  actual_depth: 0,
  fallback_used: false,
  node_count: 0,
  edge_count: 0,
};

function finalPayload(overrides: Partial<ChatAgentFinalPayload> = {}): ChatAgentFinalPayload {
  return {
    answer: "可考虑陈皮。",
    provider_reasoning: [],
    evidence: [],
    related_nodes: [],
    related_edges: [],
    subgraph_meta: emptySubgraphMeta,
    reasoning_trace: [],
    tool_calls: [],
    session_id: "sid-cite",
    ...overrides,
  };
}

function mockStream(evidence: GraphAgentEvidence[], answer = "可考虑陈皮。") {
  vi.spyOn(chatApi, "stream").mockImplementation((_question, _sessionId, callbacks) => {
    callbacks?.onSession?.("sid-cite", "turn-cite");
    callbacks?.onAnswerChunk?.(answer);
    callbacks?.onFinal?.(finalPayload({ answer, evidence }));
    return new AbortController();
  });
}

async function askQuestion(user: ReturnType<typeof userEvent.setup>, question = "陈皮有什么功效？") {
  renderWithProviders(<ChatPage />);
  await user.type(screen.getByPlaceholderText("输入您的问题，例如：陈皮有什么功效？"), question);
  await user.click(screen.getByRole("button", { name: /发送/ }));
}

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

  it("renders a citation, opens lineage with entity_id, and prefills review from evidence", async () => {
    const user = userEvent.setup();
    const lineageSpy = vi.spyOn(provenanceApi, "getEntityLineage").mockResolvedValue({
      entity: { id: "herb-chenpi", name: "陈皮" },
      evidence: { id: "ev-1", content: "陈皮理气健脾。" },
      source: { id: "src-pharmacopoeia", name: "中国药典（2020年版）" },
    });
    vi.spyOn(provenanceApi, "getEntityEvidence").mockResolvedValue({
      evidence: [
        {
          evidence: {
            id: "ev-detail",
            content: "药典证据详情。",
            source_name: "中国药典（2020年版）",
            status: "verified",
          },
          source: {
            id: "src-pharmacopoeia",
            name: "中国药典（2020年版）",
            status: "verified",
          },
        },
      ],
      count: 1,
    });
    vi.spyOn(provenanceApi, "checkCompleteness").mockResolvedValue({
      entity: { id: "herb-chenpi" },
      has_evidence: true,
      has_source: true,
      chain_complete: true,
    });
    mockStream(
      [
        {
          entity_id: "herb-chenpi",
          evidence_id: "ev-1",
          snippet: "陈皮理气健脾。",
          source_id: "src-pharmacopoeia",
          source_name: "中国药典（2020年版）",
        },
      ],
      "陈皮可理气健脾。",
    );

    await askQuestion(user);

    expect(await screen.findByText("陈皮可理气健脾。")).toBeInTheDocument();
    expect(screen.getByText("陈皮理气健脾。")).toBeInTheDocument();
    expect(screen.getAllByText("中国药典（2020年版）").length).toBeGreaterThan(0);
    expect(screen.getByTestId("chat-citation")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "查看溯源 herb-chenpi" }));

    expect(await screen.findByText("证据溯源：herb-chenpi")).toBeInTheDocument();
    expect(await screen.findByText("药典证据详情。")).toBeInTheDocument();
    await waitFor(() => {
      expect(lineageSpy).toHaveBeenCalledWith("herb-chenpi");
    });
    expect(lineageSpy).not.toHaveBeenCalledWith("src-pharmacopoeia");

    await user.click(screen.getByRole("button", { name: "关闭抽屉" }));
    await user.click(screen.getByRole("button", { name: "申请审查 herb-chenpi" }));

    expect(screen.getByLabelText("实体ID")).toHaveValue("herb-chenpi");
    expect(screen.getByLabelText("来源ID")).toHaveValue("src-pharmacopoeia");
    expect(screen.getByLabelText("审查内容")).toHaveValue("陈皮理气健脾。");
  });

  it("does not render citation actions when final.evidence is empty", async () => {
    const user = userEvent.setup();
    mockStream([], "暂无足够图谱证据。");

    await askQuestion(user, "外寒入里怎么办");

    expect(await screen.findByText("暂无足够图谱证据。")).toBeInTheDocument();
    expect(screen.queryByTestId("chat-citation")).not.toBeInTheDocument();
    expect(screen.queryByTestId("graph-agent-evidence-list")).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /查看溯源/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /申请审查/ })).not.toBeInTheDocument();
  });

  it("keeps citation actions when source is missing and still opens lineage by entity_id", async () => {
    const user = userEvent.setup();
    const lineageSpy = vi.spyOn(provenanceApi, "getEntityLineage").mockResolvedValue({
      entity: { id: "herb-chenpi", name: "陈皮" },
      evidence: { id: "ev-2", content: "陈皮味苦、辛。" },
      source: {},
    });
    vi.spyOn(provenanceApi, "getEntityEvidence").mockResolvedValue({ evidence: [], count: 0 });
    vi.spyOn(provenanceApi, "checkCompleteness").mockResolvedValue({
      entity: { id: "herb-chenpi" },
      has_evidence: true,
      has_source: false,
      chain_complete: false,
    });
    mockStream(
      [
        {
          entity_id: "herb-chenpi",
          evidence_id: "ev-2",
          snippet: "陈皮味苦、辛。",
        },
      ],
      "陈皮味苦、辛，性温。",
    );

    await askQuestion(user);

    expect(await screen.findByText("陈皮味苦、辛，性温。")).toBeInTheDocument();
    expect(screen.getAllByText("来源未标注").length).toBeGreaterThan(0);
    expect(screen.getByTestId("chat-citation")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "查看溯源 herb-chenpi" }));
    await waitFor(() => {
      expect(lineageSpy).toHaveBeenCalledWith("herb-chenpi");
    });

    await user.click(screen.getByRole("button", { name: "关闭抽屉" }));
    await user.click(screen.getByRole("button", { name: "申请审查 herb-chenpi" }));

    expect(screen.getByLabelText("实体ID")).toHaveValue("herb-chenpi");
    expect(screen.getByLabelText("来源ID")).toHaveValue("");
    expect(screen.getByLabelText("审查内容")).toHaveValue("陈皮味苦、辛。");
  });
});
