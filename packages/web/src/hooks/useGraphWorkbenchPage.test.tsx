import { ReactNode } from "react";
import { act, renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ConfigProvider } from "antd";
import zhCN from "antd/locale/zh_CN";
import { graphWorkbenchApi } from "../services/graphWorkbenchApi";
import { useGraphWorkbenchStore } from "../stores/graphWorkbenchStore";
import { useGraphWorkspace } from "./useGraphWorkspace";
import { useGraphWorkbenchPage } from "./useGraphWorkbenchPage";
import type { GraphData, GraphSceneInfo } from "../types/graph";

vi.mock("./useGraphWorkspace");

const mockedUseGraphWorkspace = vi.mocked(useGraphWorkspace);

const herbGraph: GraphData = {
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
  ],
  edges: [],
};

const defaultScene: GraphSceneInfo = {
  truncated: false,
  node_limit_hit: false,
  relationship_limit_hit: false,
  info_message: null,
};

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return function Wrapper({ children }: { children: ReactNode }) {
    return (
      <QueryClientProvider client={queryClient}>
        <ConfigProvider locale={zhCN}>{children}</ConfigProvider>
      </QueryClientProvider>
    );
  };
}

describe("useGraphWorkbenchPage", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    useGraphWorkbenchStore.setState({
      selectedItem: null,
      hoveredItem: null,
      highlightedLabel: null,
      highlightedRelationshipType: null,
      inspectorMode: "overview",
      isMetadataSidebarCollapsed: false,
      isInspectorCollapsed: false,
    });

    mockedUseGraphWorkspace.mockReturnValue({
      graphData: herbGraph,
      scene: defaultScene,
      querySummary: null,
      mode: "herb",
      loading: false,
      error: null,
      selected: null,
      setSelected: vi.fn(),
      depth: 1,
      setDepth: vi.fn(),
      refetch: vi.fn(),
      runAdvancedQuery: vi.fn(),
      resetAdvancedQuery: vi.fn(),
    });
  });

  it("keeps metadata available even when graph scene loading failed", async () => {
    mockedUseGraphWorkspace.mockReturnValue({
      graphData: null,
      scene: defaultScene,
      querySummary: null,
      mode: "idle",
      loading: false,
      error: new Error("scene failed"),
      selected: null,
      setSelected: vi.fn(),
      depth: 1,
      setDepth: vi.fn(),
      refetch: vi.fn(),
      runAdvancedQuery: vi.fn(),
      resetAdvancedQuery: vi.fn(),
    });

    vi.spyOn(graphWorkbenchApi, "getMetaSummary").mockResolvedValue({
      nodeCount: 12,
      relationshipCount: 18,
      labelCount: 4,
      relationshipTypeCount: 6,
      propertyKeyCount: 11,
      indexCount: 2,
      constraintCount: 1,
      truncated: false,
      generatedAt: "2026-03-23T10:00:00Z",
    });

    const { result } = renderHook(() => useGraphWorkbenchPage("人参"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.metaSummary?.nodeCount).toBe(12));
    expect(result.current.sceneError).toBeInstanceOf(Error);
    expect(result.current.graphData).toBeNull();
  });

  it("switches inspector mode to details when selecting a node", async () => {
    vi.spyOn(graphWorkbenchApi, "getMetaSummary").mockResolvedValue({
      nodeCount: 12,
      relationshipCount: 18,
      labelCount: 4,
      relationshipTypeCount: 6,
      propertyKeyCount: 11,
      indexCount: 2,
      constraintCount: 1,
      truncated: false,
      generatedAt: "2026-03-23T10:00:00Z",
    });

    const { result } = renderHook(() => useGraphWorkbenchPage("人参"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.metaSummary).not.toBeNull());

    act(() => {
      result.current.selectNode({
        id: "herb-1",
        name: "人参",
        labels: ["Herb"],
        status: "verified",
      });
    });

    expect(result.current.inspectorMode).toBe("details");
    expect(result.current.selectedItem?.type).toBe("node");
  });

  it("updates highlighted label without clearing the current graph scene", async () => {
    vi.spyOn(graphWorkbenchApi, "getMetaSummary").mockResolvedValue({
      nodeCount: 12,
      relationshipCount: 18,
      labelCount: 4,
      relationshipTypeCount: 6,
      propertyKeyCount: 11,
      indexCount: 2,
      constraintCount: 1,
      truncated: false,
      generatedAt: "2026-03-23T10:00:00Z",
    });

    const { result } = renderHook(() => useGraphWorkbenchPage("人参"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.metaSummary).not.toBeNull());

    act(() => {
      result.current.highlightLabel("Herb");
    });

    expect(result.current.highlightedLabel).toBe("Herb");
    expect(result.current.graphData).toEqual(herbGraph);
  });
});
