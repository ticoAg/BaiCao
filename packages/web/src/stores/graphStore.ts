// Graph 状态管理
import { create } from "zustand";
import type { GraphData, SelectedItem } from "../types/graph";

interface GraphState {
  graphData: GraphData | null;
  selectedItem: SelectedItem | null;
  depth: number;
  loading: boolean;

  setGraphData: (data: GraphData | null) => void;
  setSelected: (item: SelectedItem | null) => void;
  setDepth: (depth: number) => void;
  setLoading: (loading: boolean) => void;
}

export const useGraphStore = create<GraphState>((set) => ({
  graphData: null,
  selectedItem: null,
  depth: 1,
  loading: false,

  setGraphData: (data) => set({ graphData: data }),
  setSelected: (item) => set({ selectedItem: item }),
  setDepth: (depth) => set({ depth }),
  setLoading: (loading) => set({ loading }),
}));
