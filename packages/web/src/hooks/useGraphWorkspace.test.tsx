import { ReactNode } from "react";
import { act, renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ConfigProvider } from "antd";
import zhCN from "antd/locale/zh_CN";
import { graphApi } from "../services/api";
import { useGraphStore } from "../stores/graphStore";
import { useGraphWorkspace } from "./useGraphWorkspace";
import type { GraphData, GraphQueryResponse, GraphSceneInfo, HerbGraphResponse } from "../types/graph";

const defaultScene: GraphSceneInfo = {
  truncated: false,
  node_limit_hit: false,
  relationship_limit_hit: false,
  info_message: null,
};

const herbGraph: HerbGraphResponse = {
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
  scene: defaultScene,
};

const advancedGraph: GraphData = {
  center: null,
  nodes: [
    {
      id: "efficacy-1",
      name: "补气",
      labels: ["Efficacy"],
      status: "verified",
    },
  ],
  edges: [],
};

const advancedResponse: GraphQueryResponse = {
  summary: {
    mode: "advanced-query",
    matched_nodes: 1,
    matched_edges: 0,
    truncated: false,
    active_filters: ["名称包含: 补气"],
  },
  graph: advancedGraph,
  scene: defaultScene,
};

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
      mutations: {
        retry: false,
      },
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

describe("useGraphWorkspace", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    useGraphStore.setState({
      graphData: null,
      selectedItem: null,
      depth: 1,
      loading: false,
    });
  });

  it("keeps herb graph data when an advanced query fails", async () => {
    vi.spyOn(graphApi, "getHerbGraph").mockResolvedValue(herbGraph);
    let rejectAdvanced: ((reason?: unknown) => void) | undefined;
    const queryGraphSpy = vi.spyOn(graphApi, "queryGraph").mockImplementation(
      () =>
        new Promise<GraphQueryResponse>((_resolve, reject) => {
          rejectAdvanced = reject;
        }),
    );

    const { result } = renderHook(() => useGraphWorkspace("人参"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.graphData).toEqual(herbGraph));

    let advancedPromise: Promise<GraphQueryResponse> | undefined;
    await act(async () => {
      advancedPromise = result.current.runAdvancedQuery({
        node: { name_contains: "补气" },
        depth: 2,
      });
    });

    await waitFor(() => expect(queryGraphSpy).toHaveBeenCalledTimes(1));
    expect(result.current.loading).toBe(true);
    expect(result.current.graphData).toEqual(herbGraph);

    rejectAdvanced?.(new Error("advanced failed"));

    await expect(advancedPromise).rejects.toThrow("advanced failed");
    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.mode).toBe("herb");
    expect(result.current.graphData).toEqual(herbGraph);
    expect(result.current.querySummary).toBeNull();
  });

  it("uses the latest depth when refetching an active advanced query", async () => {
    vi.spyOn(graphApi, "getHerbGraph").mockResolvedValue(herbGraph);
    const queryGraphSpy = vi
      .spyOn(graphApi, "queryGraph")
      .mockResolvedValueOnce(advancedResponse)
      .mockResolvedValueOnce(advancedResponse);

    const { result } = renderHook(() => useGraphWorkspace("人参"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.graphData).toEqual(herbGraph));

    await act(async () => {
      await result.current.runAdvancedQuery({
        node: { name_contains: "补气" },
        depth: 2,
      });
    });

    await waitFor(() => expect(result.current.mode).toBe("advanced-query"));

    act(() => {
      result.current.setDepth(3);
    });

    await act(async () => {
      await result.current.refetch();
    });

    expect(queryGraphSpy.mock.calls[0]?.[0]).toEqual({
      node: { name_contains: "补气" },
      depth: 2,
    });
    expect(queryGraphSpy.mock.calls[1]?.[0]).toEqual({
      node: { name_contains: "补气" },
      depth: 3,
    });
  });
});
