import { useCallback } from "react";
import { Space } from "antd";
import { useGraphWorkbench } from "../../hooks/useGraphWorkbench";
import WorkbenchSidebarRail from "./WorkbenchSidebarRail";
import WorkbenchDrawer from "./WorkbenchDrawer";
import CommandEditor from "./CommandEditor";
import FrameStream from "./FrameStream";

const starterCommand = ":help";

const WorkbenchShell = () => {
  const {
    editorValue,
    setEditorValue,
    frames,
    history,
    favorites,
    showStarterCommands,
    selectedDrawer,
    setSelectedDrawer,
    runCommand,
    saveFavorite,
    removeFrame,
    isExecuting,
    clearFrames,
    setShowStarterCommands,
  } = useGraphWorkbench();

  const handleRun = useCallback(() => {
    void runCommand(editorValue || starterCommand);
  }, [editorValue, runCommand]);

  const handleRerun = useCallback(
    (command?: string) => {
      if (!command) return;
      void runCommand(command);
    },
    [runCommand],
  );

  return (
    <div
      data-testid="workbench-shell"
      style={{
        minHeight: "calc(100vh - 96px)",
        display: "grid",
        gridTemplateColumns: "64px 260px minmax(0, 1fr)",
        gap: 16,
        alignItems: "start",
      }}
    >
      <WorkbenchSidebarRail selectedDrawer={selectedDrawer} onSelect={setSelectedDrawer} />
      <WorkbenchDrawer
        selectedDrawer={selectedDrawer}
        history={history}
        favorites={favorites}
        showStarterCommands={showStarterCommands}
        onClose={() => setSelectedDrawer(null)}
        onPickCommand={(command) => {
          setEditorValue(command);
          setSelectedDrawer(null);
        }}
        onToggleStarterCommands={setShowStarterCommands}
      />
      <div style={{ display: "grid", gap: 16 }}>
        <CommandEditor
          value={editorValue}
          loading={isExecuting}
          showStarterCommands={showStarterCommands}
          onChange={setEditorValue}
          onRun={handleRun}
          onFavorite={() => saveFavorite(editorValue || starterCommand)}
          onClear={() => {
            setEditorValue("");
            clearFrames();
          }}
        />
        <FrameStream
          frames={frames}
          isExecuting={isExecuting}
          onDismissFrame={removeFrame}
          onRerunFrame={handleRerun}
        />
      </div>
    </div>
  );
};

export default WorkbenchShell;
