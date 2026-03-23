import { create } from "zustand";
import type { WorkbenchFrame, WorkbenchHistoryItem } from "../types/workbench";

type WorkbenchDrawer = "guides" | "history" | "favorites" | "settings" | null;

interface GraphWorkbenchState {
  editorValue: string;
  frames: WorkbenchFrame[];
  history: WorkbenchHistoryItem[];
  favorites: WorkbenchHistoryItem[];
  showStarterCommands: boolean;
  selectedDrawer: WorkbenchDrawer;
  isExecuting: boolean;

  setEditorValue: (value: string) => void;
  setFrames: (frames: WorkbenchFrame[]) => void;
  appendFrames: (frames: WorkbenchFrame[]) => void;
  addHistoryItem: (item: WorkbenchHistoryItem) => void;
  addFavoriteItem: (item: WorkbenchHistoryItem) => void;
  removeFrame: (frameId: string) => void;
  setShowStarterCommands: (show: boolean) => void;
  setSelectedDrawer: (drawer: WorkbenchDrawer) => void;
  setExecuting: (executing: boolean) => void;
  clearFrames: () => void;
}

export const useGraphWorkbenchStore = create<GraphWorkbenchState>((set) => ({
  editorValue: "",
  frames: [],
  history: [],
  favorites: [],
  showStarterCommands: true,
  selectedDrawer: null,
  isExecuting: false,

  setEditorValue: (value) => set({ editorValue: value }),
  setFrames: (frames) => set({ frames }),
  appendFrames: (frames) =>
    set((state) => ({ frames: [...state.frames, ...frames] })),
  addHistoryItem: (item) =>
    set((state) => ({ history: [item, ...state.history] })),
  addFavoriteItem: (item) =>
    set((state) => ({
      favorites: [
        item,
        ...state.favorites.filter((favorite) => favorite.command !== item.command),
      ],
    })),
  removeFrame: (frameId) =>
    set((state) => ({
      frames: state.frames.filter((frame) => frame.id !== frameId),
    })),
  setShowStarterCommands: (show) => set({ showStarterCommands: show }),
  setSelectedDrawer: (drawer) => set({ selectedDrawer: drawer }),
  setExecuting: (executing) => set({ isExecuting: executing }),
  clearFrames: () => set({ frames: [] }),
}));
