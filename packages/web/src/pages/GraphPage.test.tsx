import { Route, Routes } from "react-router-dom";
import { act, fireEvent, screen } from "@testing-library/react";
import GraphPage from "./GraphPage";
import { renderWithProviders } from "../test/render-with-providers";
import { useGraphWorkbenchPage } from "../hooks/useGraphWorkbenchPage";
import type { GraphData } from "../types/graph";
import cytoscape from "cytoscape";

const graphMocks = vi.hoisted(() => {
  const handlers = new Map<string, (event: { target: { id: () => string } }) => void>();
  const collection = { removeClass: vi.fn(), forEach: vi.fn() };
  const instance = {
    on: vi.fn((event: string, selector: string | Function, handler?: Function) => {
      handlers.set(`${event}:${typeof selector === "string" ? selector : "canvas"}`, (handler || selector) as any);
    }),
    elements: vi.fn(() => collection),
    nodes: vi.fn(() => collection),
    edges: vi.fn(() => collection),
    resize: vi.fn(),
    fit: vi.fn(),
    zoom: vi.fn(() => 1),
    destroy: vi.fn(),
  };
  return { handlers, instance, create: vi.fn(() => instance) };
});

vi.mock("cytoscape", () => ({ default: graphMocks.create }));

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
    graphMocks.create.mockClear();
    graphMocks.handlers.clear();
    stableGraphWorkbenchActions.selectNode.mockClear();
    mockedUseGraphWorkbenchPage.mockReturnValue(createHookResult());
  });

  it("renders a concise graph result and inspector together", () => {
    renderWithProviders(
      <Routes>
        <Route path="/graph/:name?" element={<GraphPage />} />
      </Routes>,
      "/graph/人参",
    );

    expect(screen.getByText("人参 · 关联图谱")).toBeInTheDocument();
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
    expect(screen.getAllByRole("button", { name: /打开查询器/ })).toHaveLength(2);
    expect(screen.queryByTestId("graph-inspector-panel")).not.toBeInTheDocument();
  });

  it("maps graph data into Cytoscape and selects a node", () => {
    mockedUseGraphWorkbenchPage.mockReturnValue(createHookResult({
      graphData: {
        ...defaultGraphData,
        edges: [{
          id: "rel-1",
          rel_type: "具有功效",
          status: "verified",
          source: { id: "herb-1", name: "人参" },
          target: { id: "eff-1", name: "补气" },
        }],
      },
    }));
    renderWithProviders(
      <Routes>
        <Route path="/graph/:name?" element={<GraphPage />} />
      </Routes>,
      "/graph/人参",
    );

    expect(screen.getByLabelText("图谱可视化")).toBeInTheDocument();
    const options = vi.mocked(cytoscape).mock.calls[0][0] as import("cytoscape").CytoscapeOptions;
    expect(options?.elements).toEqual(expect.arrayContaining([
      expect.objectContaining({ data: expect.objectContaining({ id: "herb-1", label: "人参" }) }),
    ]));
    act(() => graphMocks.handlers.get("tap:node")?.({ target: { id: () => "herb-1" } }));
    expect(stableGraphWorkbenchActions.selectNode).toHaveBeenCalledWith(defaultGraphData.nodes[0]);
  });

  it("shows disconnected results as a readable list", () => {
    renderWithProviders(
      <Routes><Route path="/graph/:name?" element={<GraphPage />} /></Routes>,
      "/graph/人参",
    );

    expect(screen.getByLabelText("匹配节点")).toBeInTheDocument();
    expect(graphMocks.create).not.toHaveBeenCalled();
    fireEvent.click(screen.getByText("人参"));
    expect(stableGraphWorkbenchActions.selectNode).toHaveBeenCalledWith(defaultGraphData.nodes[0]);
  });
});
