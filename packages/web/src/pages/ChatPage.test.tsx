import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ChatPage from "./ChatPage";
import { renderWithProviders } from "../test/render-with-providers";
import { graphAgentApi } from "../services/api";

vi.mock("../components/graph/MiniGraphCanvas", () => ({
  default: ({ graphData }: { graphData: { nodes: unknown[] } }) => (
    <div data-testid="mini-graph-canvas">{graphData.nodes.length} nodes</div>
  ),
}));

describe("ChatPage", () => {
  it("submits a question and renders graph agent answer basis", async () => {
    const user = userEvent.setup();
    vi.spyOn(graphAgentApi, "ask").mockResolvedValue({
      answer: "依据图谱找到人参：人参具有大补元气的功效。",
      evidence: [
        {
          node_id: "eff-1",
          snippet: "《中国药典》记载人参大补元气。",
        },
      ],
      related_nodes: [
        {
          id: "herb-1",
          name: "人参",
          status: "verified",
          labels: ["Herb"],
        },
        {
          id: "eff-1",
          name: "大补元气",
          status: "verified",
          labels: ["Efficacy"],
        },
      ],
      related_edges: [
        {
          id: "edge-1",
          type: "具有功效",
          status: "verified",
          source: { id: "herb-1", name: "人参", labels: ["Herb"], status: "verified" },
          target: { id: "eff-1", name: "大补元气", labels: ["Efficacy"], status: "verified" },
        },
      ],
      subgraph_meta: {
        center_node_id: "herb-1",
        actual_depth: 1,
        fallback_used: false,
        node_count: 2,
        edge_count: 1,
      },
      reasoning_trace: [
        {
          kind: "planner",
          summary: "schema targets: ['功效'] / ['具有功效']",
        },
      ],
      tool_calls: [
        {
          tool_name: "search_nodes",
          arguments: { query: "人参", limit: 5 },
          summary: "召回 1 个候选",
          result_summary: "命中 1 个候选",
        },
      ],
    });

    renderWithProviders(<ChatPage />);

    await user.type(
      screen.getByPlaceholderText("输入您的问题，例如：陈皮有什么功效？"),
      "人参有什么功效？",
    );
    await user.click(screen.getByRole("button", { name: /发送/ }));

    expect(graphAgentApi.ask).toHaveBeenCalledWith("人参有什么功效？");
    expect((await screen.findAllByText("大补元气")).length).toBeGreaterThan(0);
    expect(screen.getByText("依据子图")).toBeInTheDocument();
    expect(screen.getByTestId("mini-graph-canvas")).toHaveTextContent("2 nodes");
    expect(screen.getByText(/《中国药典》记载人参大补元气/)).toBeInTheDocument();
    expect(screen.getByText("reasoning_trace")).toBeInTheDocument();
    expect(screen.getByText("search_nodes")).toBeInTheDocument();
    expect(screen.getByText(/"query": "人参"/)).toBeInTheDocument();
    expect(screen.getByText("命中 1 个候选")).toBeInTheDocument();
  });

  it("renders generated cypher and graph tool result for abstract query", async () => {
    const user = userEvent.setup();
    vi.spyOn(graphAgentApi, "ask").mockResolvedValue({
      answer: "可考虑桂枝、荆芥，并结合发汗解表思路处理。",
      evidence: [],
      related_nodes: [{ id: "药材:桂枝", name: "桂枝", status: "verified", labels: ["Herb"] }],
      related_edges: [],
      subgraph_meta: {
        center_node_id: "药材:桂枝",
        actual_depth: 1,
        fallback_used: false,
        node_count: 1,
        edge_count: 0,
      },
      reasoning_trace: [{ kind: "planner", summary: "识别为抽象病证问题" }],
      tool_calls: [
        {
          tool_name: "graph_cypher_qa",
          arguments: {
            question: "治感冒的中药都有哪些，怎么做",
            generated_cypher: "MATCH (h)-[:TREATS]->(d {name:'感冒'}) RETURN h.name LIMIT 8",
          },
          summary: "使用 schema-aware graph cypher agent 查询图谱",
          result_summary: "返回 2 个药材候选",
          status: "completed",
        },
      ],
    });

    renderWithProviders(<ChatPage />);
    await user.type(
      screen.getByPlaceholderText("输入您的问题，例如：陈皮有什么功效？"),
      "治感冒的中药都有哪些，怎么做",
    );
    await user.click(screen.getByRole("button", { name: /发送/ }));

    expect(await screen.findByText("graph_cypher_qa")).toBeInTheDocument();
    expect(screen.getByText(/MATCH \(h\)-\[:TREATS\]->/)).toBeInTheDocument();
    expect(screen.getByText("返回 2 个药材候选")).toBeInTheDocument();
  });
});
