import { useEffect, useState } from "react";
import { Route, Routes } from "react-router-dom";
import { act, fireEvent, screen } from "@testing-library/react";
import GraphPage from "./GraphPage";
import { renderWithProviders } from "../test/render-with-providers";
import { useGraphWorkbenchPage } from "../hooks/useGraphWorkbenchPage";
import type { GraphData } from "../types/graph";
import { graphApi } from "../services/api";

type MockGraphInstance = {
  on: ReturnType<typeof vi.fn>;
  fitCenter: ReturnType<typeof vi.fn>;
  fitView: ReturnType<typeof vi.fn>;
  getEdgeData: ReturnType<typeof vi.fn>;
  getElementPosition: ReturnType<typeof vi.fn>;
  getNodeData: ReturnType<typeof vi.fn>;
  stopLayout: ReturnType<typeof vi.fn>;
};

type MockNetworkGraphProps = {
  onReady?: (graph: MockGraphInstance) => void;
  containerStyle?: { width?: string; height?: string };
  behaviors?: Array<{ key?: string; type?: string }>;
  layout?: { type?: string };
  data?: {
    nodes: Array<{ id: string; style?: { opacity?: number } }>;
  };
};

const mockGraphInstance: MockGraphInstance = {
  on: vi.fn(),
  fitCenter: vi.fn(),
  fitView: vi.fn(),
  getEdgeData: vi.fn(),
  getElementPosition: vi.fn((id: string) => {
    if (id === "herb-1") return { x: 0, y: 0 };
    if (id === "eff-1") return { x: 180, y: 0 };
    return { x: 40, y: 40 };
  }),
  getNodeData: vi.fn((id?: string) => {
    const nodeMap: Record<string, { id: string; style: { x: number; y: number } }> = {
      "herb-1": { id: "herb-1", style: { x: 0, y: 0 } },
      "eff-1": { id: "eff-1", style: { x: 180, y: 0 } },
    };

    if (!id) {
      return Object.values(nodeMap);
    }

    return nodeMap[id] ?? { id, style: { x: 40, y: 40 } };
  }),
  stopLayout: vi.fn(),
};

const mockNetworkGraph = vi.fn((props?: unknown) => {
  const typedProps = props as MockNetworkGraphProps | undefined;

  function MockGraphMount() {
    useEffect(() => {
      typedProps?.onReady?.(mockGraphInstance);
    }, []);

    return <div data-testid="network-graph" />;
  }

  return <MockGraphMount />;
});

vi.mock("@ant-design/graphs/es/components/network-graph", () => ({
  NetworkGraph: (props: unknown) => mockNetworkGraph(props),
}));

vi.mock("../hooks/useGraphWorkbenchPage", () => ({
  useGraphWorkbenchPage: vi.fn(),
}));

const mockedUseGraphWorkbenchPage = vi.mocked(useGraphWorkbenchPage);
type GraphWorkbenchPageHookResult = ReturnType<typeof useGraphWorkbenchPage>;

const defaultGraphData: GraphData = {
  center: {
    id: "herb-1",
    name: "人参",
    labels: ["Herb"],
    status: "verified",
  },
  nodes: [
    { id: "herb-1", name: "人参", labels: ["Herb"], status: "verified" },
    { id: "eff-1", name: "补气", labels: ["Efficacy"], status: "verified" },
  ],
  edges: [],
};

const stableGraphWorkbenchActions = {
  setDepth: vi.fn(),
  refetch: vi.fn(),
  runAdvancedQuery: vi.fn(),
  resetAdvancedQuery: vi.fn(),
  setHoveredItem: vi.fn(),
  setInspectorMode: vi.fn(),
  setMetadataSidebarCollapsed: vi.fn(),
  setInspectorCollapsed: vi.fn(),
  clearSelection: vi.fn(),
  selectNode: vi.fn(),
  selectEdge: vi.fn(),
  highlightLabel: vi.fn(),
  highlightRelationshipType: vi.fn(),
};

const createHookResult = (
  overrides?: Partial<GraphWorkbenchPageHookResult>,
): GraphWorkbenchPageHookResult => ({
  graphData: defaultGraphData,
  scene: {
    truncated: false,
    node_limit_hit: false,
    relationship_limit_hit: false,
    info_message: null,
  },
  sceneError: null,
  querySummary: null,
  mode: "herb",
  loading: false,
  depth: 1,
  setDepth: stableGraphWorkbenchActions.setDepth,
  refetch: stableGraphWorkbenchActions.refetch,
  runAdvancedQuery: stableGraphWorkbenchActions.runAdvancedQuery,
  resetAdvancedQuery: stableGraphWorkbenchActions.resetAdvancedQuery,
  metaSummary: {
    nodeCount: 12,
    relationshipCount: 18,
    labelCount: 4,
    relationshipTypeCount: 6,
    propertyKeyCount: 11,
    indexCount: 2,
    constraintCount: 1,
    truncated: false,
    generatedAt: "2026-03-23T10:00:00Z",
  },
  metaLabels: [{ name: "Herb", count: 3, propertyKeys: ["name", "category"] }],
  metaRelationshipTypes: [{ name: "HAS_EFFICACY", count: 2, propertyKeys: ["status"] }],
  metaPropertyKeys: [{ name: "name", usedByLabels: ["Herb"], usedByRelationshipTypes: [] }],
  metaSchema: {
    indexes: [{ name: "idx_herb_name", labelsOrTypes: ["Herb"], properties: ["name"] }],
    constraints: [{ name: "constraint_herb_name", labelsOrTypes: ["Herb"], properties: ["name"] }],
  },
  metaLoading: false,
  metaError: null,
  selectedItem: null,
  hoveredItem: null,
  highlightedLabel: null,
  highlightedRelationshipType: null,
  inspectorMode: "overview",
  isMetadataSidebarCollapsed: false,
  isInspectorCollapsed: false,
  setHoveredItem: stableGraphWorkbenchActions.setHoveredItem,
  setInspectorMode: stableGraphWorkbenchActions.setInspectorMode,
  setMetadataSidebarCollapsed: stableGraphWorkbenchActions.setMetadataSidebarCollapsed,
  setInspectorCollapsed: stableGraphWorkbenchActions.setInspectorCollapsed,
  clearSelection: stableGraphWorkbenchActions.clearSelection,
  selectNode: stableGraphWorkbenchActions.selectNode,
  selectEdge: stableGraphWorkbenchActions.selectEdge,
  highlightLabel: stableGraphWorkbenchActions.highlightLabel,
  highlightRelationshipType: stableGraphWorkbenchActions.highlightRelationshipType,
  ...overrides,
});

describe("GraphPage", () => {
  beforeEach(() => {
    mockNetworkGraph.mockClear();
    mockGraphInstance.on.mockClear();
    mockGraphInstance.fitCenter.mockClear();
    mockGraphInstance.fitView.mockClear();
    mockGraphInstance.getEdgeData.mockClear();
    mockGraphInstance.getElementPosition.mockClear();
    mockGraphInstance.getNodeData.mockClear();
    mockGraphInstance.stopLayout.mockClear();
    mockedUseGraphWorkbenchPage.mockReturnValue(createHookResult());
  });

  it("renders database information, graph result view, and inspector together", () => {
    renderWithProviders(
      <Routes>
        <Route path="/graph/:name?" element={<GraphPage />} />
      </Routes>,
      "/graph/人参",
    );

    expect(screen.getByText("Database information")).toBeInTheDocument();
    expect(screen.getByTestId("graph-canvas-workspace")).toBeInTheDocument();
    expect(screen.getByText("图谱概览")).toBeInTheDocument();
  });

  it("renders on /graph without a name param and calls the page hook", () => {
    mockedUseGraphWorkbenchPage.mockReturnValue(
      createHookResult({
        graphData: null,
      }),
    );

    renderWithProviders(
      <Routes>
        <Route path="/graph/:name?" element={<GraphPage />} />
      </Routes>,
      "/graph",
    );

    expect(mockedUseGraphWorkbenchPage).toHaveBeenCalledWith(undefined);
    expect(screen.getByRole("button", { name: /打开查询器/ })).toBeInTheDocument();
  });

  it("stretches the graph renderer to fill the canvas surface", () => {
    renderWithProviders(
      <Routes>
        <Route path="/graph/:name?" element={<GraphPage />} />
      </Routes>,
      "/graph/人参",
    );

    const [graphProps] = mockNetworkGraph.mock.calls[mockNetworkGraph.mock.calls.length - 1] ?? [];
    const typedGraphProps = graphProps as MockNetworkGraphProps;

    expect(typedGraphProps.containerStyle).toEqual({
      width: "100%",
      height: "100%",
    });
  });

  it("dims non-matching nodes when a label highlight is active", () => {
    mockedUseGraphWorkbenchPage.mockReturnValue(
      createHookResult({
        highlightedLabel: "Herb",
      }),
    );

    renderWithProviders(
      <Routes>
        <Route path="/graph/:name?" element={<GraphPage />} />
      </Routes>,
      "/graph/人参",
    );

    const [graphProps] = mockNetworkGraph.mock.calls[mockNetworkGraph.mock.calls.length - 1] ?? [];
    const typedGraphProps = graphProps as MockNetworkGraphProps;
    const herbNode = typedGraphProps.data?.nodes.find((node) => node.id === "herb-1");
    const efficacyNode = typedGraphProps.data?.nodes.find((node) => node.id === "eff-1");

    expect(herbNode?.style?.opacity).toBe(1);
    expect(efficacyNode?.style?.opacity).toBe(0.24);
  });

  it("does not rerender the graph canvas when only inspector selection changes", () => {
    let hookResult = createHookResult();
    mockedUseGraphWorkbenchPage.mockImplementation(() => hookResult);

    function Harness() {
      const [, setVersion] = useState(0);

      return (
        <>
          <button
            type="button"
            onClick={() => {
              hookResult = createHookResult({
                selectedItem: {
                  type: "node",
                  data: defaultGraphData.nodes[0],
                },
              });
              setVersion((current) => current + 1);
            }}
          >
            mutate-selection
          </button>
          <Routes>
            <Route path="/graph/:name?" element={<GraphPage />} />
          </Routes>
        </>
      );
    }

    renderWithProviders(<Harness />, "/graph/人参");

    expect(mockNetworkGraph).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByRole("button", { name: "mutate-selection" }));

    expect(mockNetworkGraph).toHaveBeenCalledTimes(1);
  });

  it("does not refit the whole graph after expanding a node subgraph", async () => {
    vi.useFakeTimers();
    const expandNodeGraphSpy = vi.spyOn(graphApi, "expandNodeGraph").mockResolvedValue({
      center: {
        id: "eff-1",
        name: "补气",
        labels: ["Efficacy"],
        status: "verified",
      },
      nodes: [
        { id: "eff-1", name: "补气", labels: ["Efficacy"], status: "verified" },
        { id: "meridian-1", name: "心经", labels: ["Meridian"], status: "verified" },
      ],
      edges: [
        {
          source: { id: "herb-1", name: "人参" },
          target: { id: "meridian-1", name: "心经" },
          rel_type: "ENTERS_MERIDIAN",
          status: "verified",
        },
      ],
    });

    renderWithProviders(
      <Routes>
        <Route path="/graph/:name?" element={<GraphPage />} />
      </Routes>,
      "/graph/人参",
    );

    await act(async () => {
      vi.runAllTimers();
    });

    await act(async () => {
      vi.runAllTimers();
    });

    expect(mockGraphInstance.fitCenter).toHaveBeenCalledTimes(1);
    expect(mockGraphInstance.fitView).not.toHaveBeenCalled();

    const dblclickHandler = mockGraphInstance.on.mock.calls.find(
      ([eventName]) => eventName === "node:dblclick",
    )?.[1] as ((event: { id: string }) => Promise<void>) | undefined;

    expect(dblclickHandler).toBeDefined();

    await act(async () => {
      await dblclickHandler?.({ id: "eff-1" });
    });

    await act(async () => {
      vi.runAllTimers();
    });

    expect(expandNodeGraphSpy).toHaveBeenCalledWith("eff-1", 1, 20);
    expect(mockGraphInstance.fitCenter).toHaveBeenCalledTimes(1);
    expect(mockGraphInstance.fitView).not.toHaveBeenCalled();

    vi.useRealTimers();
  });

  it("enables node dragging and switches to a stable layout after node positions are hydrated", async () => {
    vi.useFakeTimers();

    renderWithProviders(
      <Routes>
        <Route path="/graph/:name?" element={<GraphPage />} />
      </Routes>,
      "/graph/人参",
    );

    await act(async () => {
      vi.runAllTimers();
    });

    const [graphProps] = mockNetworkGraph.mock.calls[mockNetworkGraph.mock.calls.length - 1] ?? [];
    const typedGraphProps = graphProps as MockNetworkGraphProps;

    expect(typedGraphProps.behaviors).toEqual(
      expect.arrayContaining([
        expect.objectContaining({ type: "drag-canvas" }),
        expect.objectContaining({ type: "zoom-canvas" }),
        expect.objectContaining({ type: "drag-element" }),
      ]),
    );
    expect(typedGraphProps.layout?.type).toBe("preset");

    vi.useRealTimers();
  });
});
