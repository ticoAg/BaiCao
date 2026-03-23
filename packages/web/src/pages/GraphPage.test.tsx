import { useEffect } from "react";
import { Route, Routes } from "react-router-dom";
import { screen } from "@testing-library/react";
import GraphPage from "./GraphPage";
import { renderWithProviders } from "../test/render-with-providers";
import { useGraphWorkbenchPage } from "../hooks/useGraphWorkbenchPage";
import type { GraphData } from "../types/graph";

type MockGraphInstance = {
  on: ReturnType<typeof vi.fn>;
  fitView: ReturnType<typeof vi.fn>;
  getEdgeData: ReturnType<typeof vi.fn>;
};

type MockNetworkGraphProps = {
  onReady?: (graph: MockGraphInstance) => void;
  containerStyle?: { width?: string; height?: string };
  data?: {
    nodes: Array<{ id: string; style?: { opacity?: number } }>;
  };
};

const mockGraphInstance: MockGraphInstance = {
  on: vi.fn(),
  fitView: vi.fn(),
  getEdgeData: vi.fn(),
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
  setDepth: vi.fn(),
  refetch: vi.fn(),
  runAdvancedQuery: vi.fn(),
  resetAdvancedQuery: vi.fn(),
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
  setHoveredItem: vi.fn(),
  setInspectorMode: vi.fn(),
  setMetadataSidebarCollapsed: vi.fn(),
  setInspectorCollapsed: vi.fn(),
  clearSelection: vi.fn(),
  selectNode: vi.fn(),
  selectEdge: vi.fn(),
  highlightLabel: vi.fn(),
  highlightRelationshipType: vi.fn(),
  ...overrides,
});

describe("GraphPage", () => {
  beforeEach(() => {
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
});
