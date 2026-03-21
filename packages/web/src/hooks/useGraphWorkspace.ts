import { useCallback, useEffect, useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { message } from "antd";
import { graphApi } from "../services/api";
import { useGraphStore } from "../stores/graphStore";
import type {
  GraphData,
  GraphQueryRequest,
  GraphQueryResponse,
  GraphQuerySummary,
} from "../types/graph";

type GraphWorkspaceMode = "idle" | "herb" | "advanced-query";

export function useGraphWorkspace(name: string | undefined) {
  const { selectedItem, depth, setSelected, setDepth, setGraphData, setLoading } =
    useGraphStore();
  const [advancedRequest, setAdvancedRequest] = useState<GraphQueryRequest | null>(null);

  useEffect(() => {
    setAdvancedRequest(null);
  }, [name]);

  const herbQuery = useQuery({
    queryKey: ["graphWorkspace", "herb", name, depth],
    queryFn: () => graphApi.getHerbGraph(name!, depth),
    enabled: Boolean(name) && !advancedRequest,
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
    if (advancedRequest) {
      return advancedQuery.data?.graph ?? null;
    }

    return herbQuery.data ?? null;
  }, [advancedQuery.data, advancedRequest, herbQuery.data]);

  const querySummary: GraphQuerySummary | null = advancedRequest
    ? advancedQuery.data?.summary ?? null
    : null;

  const mode: GraphWorkspaceMode = advancedRequest
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
      const nextRequest = {
        ...request,
        depth: request.depth ?? depth,
      };

      if (typeof nextRequest.depth === "number" && nextRequest.depth !== depth) {
        setDepth(nextRequest.depth);
      }

      setAdvancedRequest(nextRequest);
      return advancedQuery.mutateAsync(nextRequest);
    },
    [advancedQuery, depth, setDepth],
  );

  const refetch = useCallback(async () => {
    if (advancedRequest) {
      if (!advancedQuery.isPending) {
        await advancedQuery.mutateAsync(advancedRequest);
      }
      return;
    }

    await herbQuery.refetch();
  }, [advancedQuery, advancedRequest, herbQuery]);

  return {
    graphData,
    querySummary,
    mode,
    loading,
    error: advancedRequest ? advancedQuery.error : herbQuery.error,
    selected: selectedItem,
    setSelected,
    depth,
    setDepth,
    refetch,
    runAdvancedQuery,
  };
}
