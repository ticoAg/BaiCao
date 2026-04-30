// Graph hook - react-query + zustand
import { useCallback, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { message } from "../components/ui/index";
import { graphApi } from "../services/api";
import { useGraphStore } from "../stores/graphStore";

export function useGraph(name: string | undefined) {
  const { selectedItem, depth, setSelected, setDepth, setGraphData, setLoading } =
    useGraphStore();

  const {
    data: graphData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ["herbGraph", name, depth],
    queryFn: () => graphApi.getHerbGraph(name!, depth),
    enabled: !!name,
  });

  // 同步 loading 状态到 store
  useEffect(() => {
    setLoading(isLoading);
  }, [isLoading, setLoading]);

  // 同步 graphData 到 store，并自动选中 center 节点
  useEffect(() => {
    if (graphData) {
      setGraphData(graphData);
      if (graphData.center) {
        setSelected({ type: "node", data: graphData.center });
      }
    }
  }, [graphData, setGraphData, setSelected]);

  // 错误提示
  useEffect(() => {
    if (error) {
      const errMsg =
        (error as any)?.response?.data?.detail || "加载图谱失败";
      message.error(errMsg);
    }
  }, [error]);

  const handleRefetch = useCallback(() => {
    void refetch();
  }, [refetch]);

  return {
    graphData: graphData ?? null,
    loading: isLoading,
    error,
    selected: selectedItem,
    setSelected,
    depth,
    setDepth,
    refetch: handleRefetch,
  };
}
