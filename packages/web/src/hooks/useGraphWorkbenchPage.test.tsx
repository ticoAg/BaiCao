import { ReactNode } from "react";
import { act, renderHook } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
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
      <QueryClientProvider client={queryClient}>{children}
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

  it("keeps the scene error visible when graph loading failed", () => {
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

    const { result } = renderHook(() => useGraphWorkbenchPage("人参"), {
      wrapper: createWrapper(),
    });

    expect(result.current.sceneError).toBeInstanceOf(Error);
    expect(result.current.graphData).toBeNull();
  });

  it("switches inspector mode to details when selecting a node", async () => {
    const { result } = renderHook(() => useGraphWorkbenchPage("人参"), {
      wrapper: createWrapper(),
    });

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
    const { result } = renderHook(() => useGraphWorkbenchPage("人参"), {
      wrapper: createWrapper(),
    });

    act(() => {
      result.current.highlightLabel("Herb");
    });

    expect(result.current.highlightedLabel).toBe("Herb");
    expect(result.current.graphData).toEqual(herbGraph);
  });
});
