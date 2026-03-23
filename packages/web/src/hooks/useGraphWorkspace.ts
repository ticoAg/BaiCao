import { useCallback, useEffect, useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { message } from "antd";
import { graphApi } from "../services/api";
import { useGraphStore } from "../stores/graphStore";
import type {
  GraphData,
  GraphSceneInfo,
  GraphQueryRequest,
  GraphQueryResponse,
  GraphQuerySummary,
  HerbGraphResponse,
} from "../types/graph";

type GraphWorkspaceMode = "idle" | "herb" | "advanced-query";

function withCurrentDepth(request: GraphQueryRequest, depth: number): GraphQueryRequest {
  return {
    ...request,
    depth: request.depth ?? depth,
  };
}

export function useGraphWorkspace(name: string | undefined) {
  const { selectedItem, depth, setSelected, setDepth, setGraphData, setLoading } =
    useGraphStore();
  const [activeAdvancedRequest, setActiveAdvancedRequest] =
    useState<GraphQueryRequest | null>(null);
  const [activeAdvancedResponse, setActiveAdvancedResponse] =
    useState<GraphQueryResponse | null>(null);

  useEffect(() => {
    setActiveAdvancedRequest(null);
    setActiveAdvancedResponse(null);
  }, [name]);

  const herbQuery = useQuery({
    queryKey: ["graphWorkspace", "herb", name, depth],
    queryFn: () => graphApi.getHerbGraph(name!, depth),
    enabled: Boolean(name) && !activeAdvancedRequest,
  });

  const advancedQuery = useMutation({
    mutationFn: graphApi.queryGraph,
    onError: (error: unknown) => {
      const errMsg = (error as any)?.response?.data?.detail || "高级图谱查询失败";
      message.error(errMsg);
    },
  });

  useEffect(() => {
    if (herbQuery.error) {
      const errMsg =
        (herbQuery.error as any)?.response?.data?.detail || "加载图谱失败";
      message.error(errMsg);
    }
  }, [herbQuery.error]);

  const graphData: GraphData | null = useMemo(() => {
    if (activeAdvancedResponse) {
      return activeAdvancedResponse.graph;
    }

    if (herbQuery.data) {
      const { center, nodes, edges } = herbQuery.data;
      return { center, nodes, edges };
    }

    return null;
  }, [activeAdvancedResponse, herbQuery.data]);

  const scene: GraphSceneInfo = useMemo(() => {
    if (activeAdvancedResponse?.scene) {
      return activeAdvancedResponse.scene;
    }

    return (
      herbQuery.data?.scene ?? {
        truncated: false,
        node_limit_hit: false,
        relationship_limit_hit: false,
        info_message: null,
      }
    );
  }, [activeAdvancedResponse, herbQuery.data]);

  const querySummary: GraphQuerySummary | null = activeAdvancedResponse
    ? activeAdvancedResponse.summary
    : null;

  const mode: GraphWorkspaceMode = activeAdvancedRequest
    ? "advanced-query"
    : name
      ? "herb"
      : "idle";

  const loading = herbQuery.isLoading || advancedQuery.isPending;

  useEffect(() => {
    setLoading(loading);
  }, [loading, setLoading]);

  useEffect(() => {
    setGraphData(graphData);

    if (!graphData) {
      setSelected(null);
      return;
    }

    if (graphData.center) {
      setSelected({ type: "node", data: graphData.center });
      return;
    }

    if (graphData.nodes[0]) {
      setSelected({ type: "node", data: graphData.nodes[0] });
      return;
    }

    setSelected(null);
  }, [graphData, setGraphData, setSelected]);

  const runAdvancedQuery = useCallback(
    async (request: GraphQueryRequest): Promise<GraphQueryResponse> => {
      const currentDepth = useGraphStore.getState().depth;
      const nextRequest = withCurrentDepth(request, currentDepth);

      if (typeof nextRequest.depth === "number" && nextRequest.depth !== currentDepth) {
        setDepth(nextRequest.depth);
      }

      const response = await advancedQuery.mutateAsync(nextRequest);
      setActiveAdvancedRequest(nextRequest);
      setActiveAdvancedResponse(response);
      return response;
    },
    [advancedQuery, depth, setDepth],
  );

  const refetch = useCallback(async () => {
    if (activeAdvancedRequest) {
      if (!advancedQuery.isPending) {
        const currentDepth = useGraphStore.getState().depth;
        const nextRequest = {
          ...activeAdvancedRequest,
          depth: currentDepth,
        };
        const response = await advancedQuery.mutateAsync(nextRequest);
        setActiveAdvancedRequest(nextRequest);
        setActiveAdvancedResponse(response);
      }
      return;
    }

    await herbQuery.refetch();
  }, [activeAdvancedRequest, advancedQuery, herbQuery]);

  const resetAdvancedQuery = useCallback(() => {
    setActiveAdvancedRequest(null);
    setActiveAdvancedResponse(null);
  }, []);

  return {
    graphData,
    scene,
    querySummary,
    mode,
    loading,
    error: advancedQuery.error ?? herbQuery.error,
    selected: selectedItem,
    setSelected,
    depth,
    setDepth,
    refetch,
    runAdvancedQuery,
    resetAdvancedQuery,
  };
}
