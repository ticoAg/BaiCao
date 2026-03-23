import { useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import type { GraphEdge, GraphNode } from "../types/graph";
import { graphWorkbenchApi } from "../services/graphWorkbenchApi";
import { useGraphWorkbenchStore } from "../stores/graphWorkbenchStore";
import { useGraphWorkspace } from "./useGraphWorkspace";

export function useGraphWorkbenchPage(name: string | undefined) {
  const workspace = useGraphWorkspace(name);
  const {
    selectedItem,
    hoveredItem,
    highlightedLabel,
    highlightedRelationshipType,
    inspectorMode,
    isMetadataSidebarCollapsed,
    isInspectorCollapsed,
    setSelectedItem,
    setHoveredItem,
    setHighlightedLabel,
    setHighlightedRelationshipType,
    setInspectorMode,
    setMetadataSidebarCollapsed,
    setInspectorCollapsed,
    clearSelection,
  } = useGraphWorkbenchStore();

  const metaSummaryQuery = useQuery({
    queryKey: ["graphWorkbench", "meta", "summary"],
    queryFn: graphWorkbenchApi.getMetaSummary,
  });

  const selectNode = useCallback(
    (node: GraphNode) => {
      setSelectedItem({ type: "node", data: node });
    },
    [setSelectedItem],
  );

  const selectEdge = useCallback(
    (edge: GraphEdge & { sourceName?: string; targetName?: string }) => {
      setSelectedItem({ type: "edge", data: edge });
    },
    [setSelectedItem],
  );

  const highlightLabel = useCallback(
    (label: string | null) => {
      setHighlightedLabel(label);
    },
    [setHighlightedLabel],
  );

  const highlightRelationshipType = useCallback(
    (relType: string | null) => {
      setHighlightedRelationshipType(relType);
    },
    [setHighlightedRelationshipType],
  );

  return {
    graphData: workspace.graphData,
    scene: workspace.scene,
    sceneError: workspace.error,
    querySummary: workspace.querySummary,
    mode: workspace.mode,
    loading: workspace.loading,
    depth: workspace.depth,
    setDepth: workspace.setDepth,
    refetch: workspace.refetch,
    runAdvancedQuery: workspace.runAdvancedQuery,
    resetAdvancedQuery: workspace.resetAdvancedQuery,

    metaSummary: metaSummaryQuery.data ?? null,
    metaLoading: metaSummaryQuery.isLoading,
    metaError: metaSummaryQuery.error ?? null,

    selectedItem,
    hoveredItem,
    highlightedLabel,
    highlightedRelationshipType,
    inspectorMode,
    isMetadataSidebarCollapsed,
    isInspectorCollapsed,
    setHoveredItem,
    setInspectorMode,
    setMetadataSidebarCollapsed,
    setInspectorCollapsed,
    clearSelection,
    selectNode,
    selectEdge,
    highlightLabel,
    highlightRelationshipType,
  };
}
