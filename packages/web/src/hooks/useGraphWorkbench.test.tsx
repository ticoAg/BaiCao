import { ReactNode } from "react";
import { act, renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ConfigProvider } from "antd";
import zhCN from "antd/locale/zh_CN";
import { useGraphWorkbenchStore } from "../stores/workbenchStore";
import { workbenchApi } from "../services/workbenchApi";
import { useGraphWorkbench } from "./useGraphWorkbench";

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
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

describe("useGraphWorkbench", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    useGraphWorkbenchStore.setState({
      editorValue: "",
      frames: [],
      history: [],
      selectedDrawer: null,
      isExecuting: false,
    });
  });

  it("appends returned frames to the stream when a command succeeds", async () => {
    vi.spyOn(workbenchApi, "execute").mockResolvedValue({
      command: ":help",
      frames: [
        {
          id: "frame-help",
          type: "text",
          title: "命令帮助",
          status: "ok",
          payload: { markdown: "help" },
          command: ":help",
        },
      ],
      historyItem: {
        command: ":help",
        source: "workbench",
      },
    });

    const { result } = renderHook(() => useGraphWorkbench(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      await result.current.runCommand(":help");
    });

    await waitFor(() => expect(result.current.frames).toHaveLength(1));
    expect(result.current.frames[0].type).toBe("text");
    expect(result.current.history[0].command).toBe(":help");
    expect(result.current.isExecuting).toBe(false);
  });
});
