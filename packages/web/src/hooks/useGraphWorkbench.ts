import { useCallback } from "react";
import { message } from "antd";
import { workbenchApi } from "../services/workbenchApi";
import { useGraphWorkbenchStore } from "../stores/workbenchStore";
import type {
  CypherValidationRequest,
  WorkbenchCommandSource,
  WorkbenchExecuteResponse,
} from "../types/workbench";

export function useGraphWorkbench() {
  const {
    editorValue,
    frames,
    history,
    favorites,
    showStarterCommands,
    selectedDrawer,
    isExecuting,
    setEditorValue,
    appendFrames,
    addHistoryItem,
    addFavoriteItem,
    removeFrame,
    setShowStarterCommands,
    setSelectedDrawer,
    setExecuting,
    clearFrames,
  } = useGraphWorkbenchStore();

  const runCommand = useCallback(
    async (command: string, source: WorkbenchCommandSource = "workbench") => {
      const trimmed = command.trim();
      if (!trimmed) return null;

      setExecuting(true);
      try {
        const result: WorkbenchExecuteResponse = await workbenchApi.execute({
          command: trimmed,
          source,
        });
        appendFrames(result.frames);
        addHistoryItem(result.historyItem);
        return result;
      } catch (error) {
        const detail =
          (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
          "执行命令失败";
        message.error(detail);
        return null;
      } finally {
        setExecuting(false);
      }
    },
    [addHistoryItem, appendFrames, setExecuting],
  );

  const validateCypher = useCallback(
    async (payload: CypherValidationRequest) => {
      return workbenchApi.validateCypher(payload);
    },
    [],
  );

  const saveFavorite = useCallback(
    (command: string, source: WorkbenchCommandSource = "workbench") => {
      const trimmed = command.trim();
      if (!trimmed) {
        message.warning("先输入一条命令，再加入收藏");
        return;
      }

      addFavoriteItem({
        command: trimmed,
        source,
        executedAt: new Date().toISOString(),
      });
      message.success("已加入收藏");
    },
    [addFavoriteItem],
  );

  return {
    editorValue,
    frames,
    history,
    favorites,
    showStarterCommands,
    selectedDrawer,
    isExecuting,
    setEditorValue,
    removeFrame,
    setShowStarterCommands,
    setSelectedDrawer,
    runCommand,
    validateCypher,
    saveFavorite,
    clearFrames,
  };
}
