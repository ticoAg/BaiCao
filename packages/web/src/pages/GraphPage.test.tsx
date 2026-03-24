import { useState } from "react";
import { Route, Routes } from "react-router-dom";
import { act, fireEvent, screen } from "@testing-library/react";
import GraphPage from "./GraphPage";
import { renderWithProviders } from "../test/render-with-providers";
import { useGraphWorkbenchPage } from "../hooks/useGraphWorkbenchPage";
import type { GraphData } from "../types/graph";
import { graphApi } from "../services/api";

// Mock D3 SVG rendering since jsdom doesn't support SVG layout
vi.mock("../lib/graph-viz", () => ({
  Visualization: vi.fn().mockImplementation(() => ({
    init: vi.fn(),
    precomputeAndStart: vi.fn(),
    update: vi.fn(),
    destroy: vi.fn(),
    resize: vi.fn(),
    zoomIn: vi.fn(),
    zoomOut: vi.fn(),
    zoomToFit: vi.fn(),
    on: vi.fn().mockReturnThis(),
    trigger: vi.fn(),
    forceSimulation: { simulation: { stop: vi.fn() } },
  })),
  VizGraph: {
    fromGraphData: vi.fn().mockReturnValue({
      nodes: vi.fn().mockReturnValue([]),
      relationships: vi.fn().mockReturnValue([]),
      findNode: vi.fn(),
      addNodes: vi.fn(),
      addRelationships: vi.fn(),
      collapseNode: vi.fn(),
    }),
  },
  VizNode: vi.fn(),
  VizRelationship: vi.fn(),
  GraphEventHandler: vi.fn().mockImplementation(() => ({
    bindEventHandlers: vi.fn(),
  })),
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

  it("renders the SVG canvas when graph data is present", () => {
    renderWithProviders(
      <Routes>
        <Route path="/graph/:name?" element={<GraphPage />} />
      </Routes>,
      "/graph/人参",
    );

    expect(screen.getByTestId("graph-canvas-workspace")).toBeInTheDocument();
  });
});
