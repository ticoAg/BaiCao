import { create } from "zustand";
import type { SelectedItem } from "../types/graph";
import type { GraphWorkbenchInspectorMode } from "../types/graphWorkbench";

interface GraphWorkbenchStoreState {
  selectedItem: SelectedItem | null;
  hoveredItem: SelectedItem | null;
  highlightedLabel: string | null;
  highlightedRelationshipType: string | null;
  inspectorMode: GraphWorkbenchInspectorMode;
  isMetadataSidebarCollapsed: boolean;
  isInspectorCollapsed: boolean;

  setSelectedItem: (item: SelectedItem | null) => void;
  setHoveredItem: (item: SelectedItem | null) => void;
  setHighlightedLabel: (label: string | null) => void;
  setHighlightedRelationshipType: (relType: string | null) => void;
  setInspectorMode: (mode: GraphWorkbenchInspectorMode) => void;
  setMetadataSidebarCollapsed: (collapsed: boolean) => void;
  setInspectorCollapsed: (collapsed: boolean) => void;
  clearSelection: () => void;
}

export const useGraphWorkbenchStore = create<GraphWorkbenchStoreState>((set) => ({
  selectedItem: null,
  hoveredItem: null,
  highlightedLabel: null,
  highlightedRelationshipType: null,
  inspectorMode: "overview",
  isMetadataSidebarCollapsed: false,
  isInspectorCollapsed: false,

  setSelectedItem: (item) =>
    set({
      selectedItem: item,
      inspectorMode: item ? "details" : "overview",
    }),
  setHoveredItem: (item) => set({ hoveredItem: item }),
  setHighlightedLabel: (label) => set({ highlightedLabel: label }),
  setHighlightedRelationshipType: (relType) => set({ highlightedRelationshipType: relType }),
  setInspectorMode: (mode) => set({ inspectorMode: mode }),
  setMetadataSidebarCollapsed: (collapsed) => set({ isMetadataSidebarCollapsed: collapsed }),
  setInspectorCollapsed: (collapsed) => set({ isInspectorCollapsed: collapsed }),
  clearSelection: () =>
    set((state) => {
      if (!state.selectedItem && state.inspectorMode === "overview") {
        return state;
      }

      return {
        selectedItem: null,
        inspectorMode: "overview",
      };
    }),
}));
