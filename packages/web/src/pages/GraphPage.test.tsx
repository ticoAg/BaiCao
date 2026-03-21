import { Route, Routes } from "react-router-dom";
import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import GraphPage from "./GraphPage";
import { renderWithProviders } from "../test/render-with-providers";
import { nodeStyleMap } from "../types/graph";

type MockNetworkGraphProps = {
  data: {
    nodes: Array<{ id: string; style: { labelFill: string } }>;
  };
};

const mockNetworkGraph = vi.fn((props?: unknown) => (
  <div data-testid="network-graph" data-props={props ? "captured" : "missing"} />
));
const mockUseGraph = vi.fn();
const mockUseGraphWorkspace = vi.fn();

vi.mock("@ant-design/graphs", () => ({
  NetworkGraph: (props: unknown) => mockNetworkGraph(props),
}));

vi.mock("../hooks/useGraph", () => ({
  useGraph: (...args: unknown[]) => mockUseGraph(...args),
}));

vi.mock("../hooks/useGraphWorkspace", () => ({
  useGraphWorkspace: (...args: unknown[]) => mockUseGraphWorkspace(...args),
}));

const createWorkspaceResult = (overrides?: Record<string, unknown>) => ({
  graphData: {
    center: {
      id: "herb-1",
      name: "人参",
      labels: ["Herb"],
      status: "verified",
    },
    nodes: [
      {
        id: "herb-1",
        name: "人参",
        labels: ["Herb"],
        status: "verified",
      },
      {
        id: "efficacy-1",
        name: "大补元气",
        labels: ["Efficacy"],
        status: "verified",
      },
    ],
    edges: [],
  },
  querySummary: null,
  mode: "herb" as const,
  loading: false,
  selected: null,
  setSelected: vi.fn(),
  depth: 1,
  setDepth: vi.fn(),
  refetch: vi.fn(),
  runAdvancedQuery: vi.fn(),
  ...overrides,
});

describe("GraphPage", () => {
  beforeEach(() => {
    mockNetworkGraph.mockClear();
    mockUseGraph.mockReset();
    mockUseGraphWorkspace.mockReset();
    mockUseGraph.mockReturnValue(createWorkspaceResult());
    mockUseGraphWorkspace.mockReturnValue(createWorkspaceResult());
  });

  it("uses nodeStyleMap text colors for graph labels", () => {
    mockUseGraphWorkspace.mockReturnValue(createWorkspaceResult());

    renderWithProviders(
      <Routes>
        <Route path="/graph/:name?" element={<GraphPage />} />
      </Routes>,
      "/graph/人参",
    );

    const [graphProps] =
      mockNetworkGraph.mock.calls[mockNetworkGraph.mock.calls.length - 1] ?? [];
    const typedGraphProps = graphProps as MockNetworkGraphProps;
    const centerNode = typedGraphProps.data.nodes.find((node) => node.id === "herb-1");
    const efficacyNode = typedGraphProps.data.nodes.find(
      (node) => node.id === "efficacy-1",
    );

    expect(centerNode).toBeDefined();
    expect(efficacyNode).toBeDefined();

    if (!centerNode || !efficacyNode) {
      throw new Error("Expected graph nodes to be present in NetworkGraph props");
    }

    expect(centerNode.style.labelFill).toBe(nodeStyleMap.Herb.textColor);
    expect(efficacyNode.style.labelFill).toBe(nodeStyleMap.Efficacy.textColor);
    expect(mockUseGraphWorkspace).toHaveBeenCalledWith("人参");
    expect(mockUseGraph).not.toHaveBeenCalled();
  });

  it("renders on /graph without a name param and calls the workspace hook", () => {
    mockUseGraphWorkspace.mockReturnValue(
      createWorkspaceResult({
        graphData: null,
        selected: null,
      }),
    );

    renderWithProviders(
      <Routes>
        <Route path="/graph/:name?" element={<GraphPage />} />
      </Routes>,
      "/graph",
    );

    expect(mockUseGraphWorkspace).toHaveBeenCalledWith(undefined);
    expect(mockUseGraph).not.toHaveBeenCalled();
  });

  it("renders the graph workspace and query panel on /graph without a name param", () => {
    mockUseGraphWorkspace.mockReturnValue(
      createWorkspaceResult({
        graphData: null,
        selected: null,
      }),
    );

    renderWithProviders(
      <Routes>
        <Route path="/graph/:name?" element={<GraphPage />} />
      </Routes>,
      "/graph",
    );

    expect(screen.getByText("图谱条件查询")).toBeInTheDocument();
    expect(screen.getByTestId("graph-workspace").getAttribute("style")).toContain(
      "min-height: calc(100vh - 160px)",
    );
  });

  it("shows advanced query summary details in advanced-query mode", () => {
    mockUseGraphWorkspace.mockReturnValue(
      createWorkspaceResult({
        mode: "advanced-query",
        querySummary: {
          mode: "advanced-query",
          matched_nodes: 8,
          matched_edges: 12,
          truncated: true,
          active_filters: ["节点名称包含: 补气", "关系类型: HAS_EFFICACY"],
        },
      }),
    );

    renderWithProviders(
      <Routes>
        <Route path="/graph/:name?" element={<GraphPage />} />
      </Routes>,
      "/graph",
    );

    const summary = screen.getByTestId("graph-query-summary");

    expect(within(summary).getByText("高级图谱查询结果")).toBeInTheDocument();
    expect(within(summary).getByText("命中节点")).toBeInTheDocument();
    expect(within(summary).getByText("8")).toBeInTheDocument();
    expect(within(summary).getByText("关系类型: HAS_EFFICACY")).toBeInTheDocument();
  });

  it("syncs panel depth changes back to the workspace store", async () => {
    const user = userEvent.setup();
    const setDepth = vi.fn();

    mockUseGraphWorkspace.mockReturnValue(
      createWorkspaceResult({
        graphData: null,
        selected: null,
        depth: 1,
        setDepth,
      }),
    );

    renderWithProviders(
      <Routes>
        <Route path="/graph/:name?" element={<GraphPage />} />
      </Routes>,
      "/graph",
    );

    const depthInput = screen.getByRole("spinbutton", { name: "深度" });
    await user.clear(depthInput);
    await user.type(depthInput, "3");

    expect(setDepth).toHaveBeenCalledWith(3);
  });
});
