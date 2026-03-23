import { useEffect } from "react";
import { Route, Routes } from "react-router-dom";
import { act, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import GraphPage from "./GraphPage";
import { renderWithProviders } from "../test/render-with-providers";
import { graphApi } from "../services/api";

type MockNetworkGraphProps = {
  data: {
    nodes: Array<{ id: string; style: { labelFill: string; labelPlacement: string } }>;
  };
  onReady?: (graph: MockGraphInstance) => void;
  containerStyle?: {
    width?: string;
    height?: string;
  };
};

type GraphHandler = (event?: { target?: { id?: string } }) => void;

type MockGraphInstance = {
  on: ReturnType<typeof vi.fn>;
  getZoom: ReturnType<typeof vi.fn>;
  zoomTo: ReturnType<typeof vi.fn>;
  fitView: ReturnType<typeof vi.fn>;
  focusElement: ReturnType<typeof vi.fn>;
  getEdgeData: ReturnType<typeof vi.fn>;
};

const graphHandlers = new Map<string, GraphHandler>();

const mockGraphInstance: MockGraphInstance = {
  on: vi.fn((eventName: string, handler: GraphHandler) => {
    graphHandlers.set(eventName, handler);
  }),
  getZoom: vi.fn(() => 1),
  zoomTo: vi.fn(),
  fitView: vi.fn(),
  focusElement: vi.fn(),
  getEdgeData: vi.fn(),
};

const triggerGraphEvent = (eventName: string, event?: { target?: { id?: string } }) => {
  const handler = graphHandlers.get(eventName);
  if (!handler) {
    throw new Error(`Missing graph handler for ${eventName}`);
  }
  act(() => {
    handler(event);
  });
};

const mockNetworkGraph = vi.fn((props?: unknown) => {
  const typedProps = props as MockNetworkGraphProps | undefined;

  function MockGraphMount() {
    useEffect(() => {
      typedProps?.onReady?.(mockGraphInstance);
    }, []);

    return (
      <div data-testid="network-graph" data-props={props ? "captured" : "missing"} />
    );
  }

  return <MockGraphMount />;
});
const mockUseGraph = vi.fn();
const mockUseGraphWorkspace = vi.fn();

vi.mock("../services/api", () => ({
  graphApi: {
    expandNodeGraph: vi.fn(),
  },
}));

vi.mock("@ant-design/graphs/es/components/network-graph", () => ({
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
  resetAdvancedQuery: vi.fn(),
  ...overrides,
});

describe("GraphPage", () => {
  beforeEach(() => {
    graphHandlers.clear();
    mockNetworkGraph.mockClear();
    mockGraphInstance.on.mockClear();
    mockGraphInstance.getZoom.mockClear();
    mockGraphInstance.zoomTo.mockClear();
    mockGraphInstance.fitView.mockClear();
    mockGraphInstance.focusElement.mockClear();
    mockGraphInstance.getEdgeData.mockClear();
    mockUseGraph.mockReset();
    mockUseGraphWorkspace.mockReset();
    mockUseGraph.mockReturnValue(createWorkspaceResult());
    mockUseGraphWorkspace.mockReturnValue(createWorkspaceResult());
  });

  it("renders node labels inside the circles with graph-aware text colors", () => {
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

    expect(centerNode.style.labelPlacement).toBe("center");
    expect(efficacyNode.style.labelPlacement).toBe("center");
    expect(centerNode.style.labelFill).toBe("#FFFFFF");
    expect(efficacyNode.style.labelFill).toBe("#2A2C34");
    expect(mockUseGraphWorkspace).toHaveBeenCalledWith("人参");
    expect(mockUseGraph).not.toHaveBeenCalled();
  });

  it("stretches the graph renderer to fill the canvas surface", () => {
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

    expect(typedGraphProps.containerStyle).toEqual({
      width: "100%",
      height: "100%",
    });
  });

  it("does not clear selection again when the canvas is already in empty selection state", () => {
    const setSelected = vi.fn();

    mockUseGraphWorkspace.mockReturnValue(
      createWorkspaceResult({
        selected: null,
        setSelected,
      }),
    );

    renderWithProviders(
      <Routes>
        <Route path="/graph/:name?" element={<GraphPage />} />
      </Routes>,
      "/graph/人参",
    );

    triggerGraphEvent("canvas:click");

    expect(setSelected).not.toHaveBeenCalled();
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

    expect(screen.getAllByRole("button", { name: /打开查询器/ }).length).toBeGreaterThan(0);
    expect(screen.getByTestId("graph-workspace").getAttribute("style")).toContain(
      "height: calc(100vh - 64px)",
    );
  });

  it("uses a query entry card and removes duplicated top-bar depth control", () => {
    renderWithProviders(
      <Routes>
        <Route path="/graph/:name?" element={<GraphPage />} />
      </Routes>,
      "/graph/人参",
    );

    expect(screen.getByText("当前图谱")).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: /打开查询器/ }).length).toBeGreaterThan(0);
    expect(screen.queryByText("探索深度")).not.toBeInTheDocument();
  });

  it("shows advanced query summary inside the query entry card in advanced-query mode", () => {
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

    expect(screen.getByText("当前查询")).toBeInTheDocument();
    expect(screen.getByText("8 个命中节点 · 12 条命中关系")).toBeInTheDocument();
    expect(screen.getByText("关系类型: HAS_EFFICACY")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "编辑查询" })).toBeInTheDocument();
  });

  it("shows graph overview details when nothing is locked in the inspector", () => {
    mockUseGraphWorkspace.mockReturnValue(
      createWorkspaceResult({
        selected: null,
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
            {
              id: "meridian-1",
              name: "脾经",
              labels: ["Meridian"],
              status: "verified",
            },
          ],
          edges: [
            {
              id: "edge-1",
              source: { id: "herb-1", name: "人参" },
              target: { id: "efficacy-1", name: "大补元气" },
              rel_type: "HAS_EFFICACY",
              status: "verified",
            },
            {
              id: "edge-2",
              source: { id: "herb-1", name: "人参" },
              target: { id: "meridian-1", name: "脾经" },
              rel_type: "BELONGS_TO_MERIDIAN",
              status: "verified",
            },
          ],
        },
      }),
    );

    renderWithProviders(
      <Routes>
        <Route path="/graph/:name?" element={<GraphPage />} />
      </Routes>,
      "/graph/人参",
    );

    expect(screen.getByTestId("graph-floating-legend")).toBeInTheDocument();
    const selectionCard = within(screen.getByTestId("graph-selection-card"));
    expect(selectionCard.getByText("图谱概览")).toBeInTheDocument();
    expect(selectionCard.getByText("3 个节点")).toBeInTheDocument();
    expect(selectionCard.getByText("2 条关系")).toBeInTheDocument();
    expect(selectionCard.getByText(/Herb/)).toBeInTheDocument();
    expect(selectionCard.getByText(/HAS_EFFICACY/)).toBeInTheDocument();
  });

  it("gives the empty canvas state a clear next action", async () => {
    const user = userEvent.setup();

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

    await user.click(screen.getByRole("button", { name: "立即开始查询" }));

    expect(screen.getByRole("dialog", { name: "图谱查询器" })).toBeInTheDocument();
  });

  it("opens the query drawer from the query entry card", async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <Routes>
        <Route path="/graph/:name?" element={<GraphPage />} />
      </Routes>,
      "/graph",
    );

    await user.click(screen.getByRole("button", { name: /打开查询器/ }));

    expect(screen.getByRole("dialog", { name: "图谱查询器" })).toBeInTheDocument();
  });

  it("previews hovered nodes in the inspector and falls back to the locked selection on mouse leave", () => {
    mockUseGraphWorkspace.mockReturnValue(
      createWorkspaceResult({
        selected: {
          type: "node",
          data: {
            id: "herb-1",
            name: "人参",
            labels: ["Herb"],
            status: "verified",
          },
        },
      }),
    );

    renderWithProviders(
      <Routes>
        <Route path="/graph/:name?" element={<GraphPage />} />
      </Routes>,
      "/graph/人参",
    );

    const selectionCard = within(screen.getByTestId("graph-selection-card"));
    expect(selectionCard.getByText("人参")).toBeInTheDocument();

    triggerGraphEvent("node:mouseenter", { target: { id: "efficacy-1" } });
    expect(selectionCard.getByText("大补元气")).toBeInTheDocument();

    triggerGraphEvent("node:mouseleave");
    expect(selectionCard.getByText("人参")).toBeInTheDocument();
  });

  it("allows collapsing and reopening the inspector panel", async () => {
    const user = userEvent.setup();

    renderWithProviders(
      <Routes>
        <Route path="/graph/:name?" element={<GraphPage />} />
      </Routes>,
      "/graph/人参",
    );

    const collapseButton = screen.getByRole("button", { name: "收起详情面板" });
    expect(collapseButton).toHaveAttribute("aria-expanded", "true");

    await user.click(collapseButton);

    const expandButton = screen.getByRole("button", { name: "展开详情面板" });
    expect(expandButton).toHaveAttribute("aria-expanded", "false");
  });

  it("shows a dismissible canvas interaction hint", async () => {
    const user = userEvent.setup();

    renderWithProviders(
      <Routes>
        <Route path="/graph/:name?" element={<GraphPage />} />
      </Routes>,
      "/graph/人参",
    );

    expect(screen.getByText("滚轮缩放，拖拽平移，悬停预览详情")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "关闭画布操作提示" }));

    expect(
      screen.queryByText("滚轮缩放，拖拽平移，悬停预览详情"),
    ).not.toBeInTheDocument();
  });

  it("expands one-hop neighbors on node double-click and collapses them on the second double-click", async () => {
    vi.mocked(graphApi.expandNodeGraph).mockResolvedValue({
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
          id: "trait-1",
          name: "补气固脱",
          labels: ["Trait"],
          status: "verified",
        },
      ],
      edges: [
        {
          id: "edge-expand-1",
          rel_type: "HAS_TRAIT",
          status: "verified",
          source: { id: "herb-1", name: "人参", labels: ["Herb"], status: "verified" },
          target: { id: "trait-1", name: "补气固脱", labels: ["Trait"], status: "verified" },
        },
      ],
    });

    renderWithProviders(
      <Routes>
        <Route path="/graph/:name?" element={<GraphPage />} />
      </Routes>,
      "/graph/人参",
    );

    triggerGraphEvent("node:dblclick", { target: { id: "herb-1" } });

    await waitFor(() => {
      expect(graphApi.expandNodeGraph).toHaveBeenCalledWith("herb-1", 1, 20);
    });

    await waitFor(() => {
      const [expandedProps] =
        mockNetworkGraph.mock.calls[mockNetworkGraph.mock.calls.length - 1] ?? [];
      const expandedData = (expandedProps as MockNetworkGraphProps).data;
      expect(expandedData.nodes.map((node) => node.id)).toContain("trait-1");
    });

    triggerGraphEvent("node:dblclick", { target: { id: "herb-1" } });

    await waitFor(() => {
      const [collapsedProps] =
        mockNetworkGraph.mock.calls[mockNetworkGraph.mock.calls.length - 1] ?? [];
      const collapsedData = (collapsedProps as MockNetworkGraphProps).data;
      expect(collapsedData.nodes.map((node) => node.id)).not.toContain("trait-1");
    });
  });
});
