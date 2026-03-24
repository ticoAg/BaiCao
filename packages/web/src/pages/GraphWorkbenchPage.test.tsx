import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import GraphWorkbenchPage from "./GraphWorkbenchPage";
import { renderWithProviders } from "../test/render-with-providers";
import { useGraphWorkbenchStore } from "../stores/workbenchStore";
import { workbenchApi } from "../services/workbenchApi";

// Mock D3 SVG rendering since jsdom doesn't support SVG layout
vi.mock("../lib/graph-viz", () => ({
  Visualization: vi.fn().mockImplementation(() => ({
    init: vi.fn(),
    precomputeAndStart: vi.fn(),
    update: vi.fn(),
    destroy: vi.fn(),
    resize: vi.fn(),
    zoomIn: vi.fn(),
    zoomOut: vi.fn(),
    zoomToFit: vi.fn(),
    on: vi.fn().mockReturnThis(),
    trigger: vi.fn(),
    forceSimulation: { simulation: { stop: vi.fn() } },
  })),
  VizGraph: {
    fromGraphData: vi.fn().mockReturnValue({
      nodes: vi.fn().mockReturnValue([]),
      relationships: vi.fn().mockReturnValue([]),
      findNode: vi.fn(),
      addNodes: vi.fn(),
      addRelationships: vi.fn(),
      collapseNode: vi.fn(),
    }),
  },
  VizNode: vi.fn(),
  VizRelationship: vi.fn(),
  GraphEventHandler: vi.fn().mockImplementation(() => ({
    bindEventHandlers: vi.fn(),
  })),
}));

describe("GraphWorkbenchPage", () => {
  beforeEach(() => {
    useGraphWorkbenchStore.setState({
      editorValue: "",
      frames: [],
      history: [],
      favorites: [],
      showStarterCommands: true,
      selectedDrawer: null,
      isExecuting: false,
    });
  });

  it("renders a browser-style shell with rail, editor, and frame stream", () => {
    renderWithProviders(<GraphWorkbenchPage />, "/graph/workbench");

    expect(screen.getByTestId("workbench-shell")).toBeInTheDocument();
    expect(screen.getByTestId("workbench-rail")).toBeInTheDocument();
    expect(screen.getByTestId("workbench-editor")).toBeInTheDocument();
    expect(screen.getByTestId("workbench-frame-stream")).toBeInTheDocument();
  });

  it("opens the history drawer from the rail", async () => {
    const user = userEvent.setup();
    renderWithProviders(<GraphWorkbenchPage />, "/graph/workbench");

    await user.click(screen.getByRole("button", { name: "打开历史抽屉" }));

    expect(
      within(screen.getByTestId("workbench-drawer")).getAllByText("命令历史").length,
    ).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "打开历史抽屉" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });

  it("shows guide sections in the guides drawer", async () => {
    const user = userEvent.setup();

    renderWithProviders(<GraphWorkbenchPage />, "/graph/workbench");

    await user.click(screen.getByRole("button", { name: "打开指南抽屉" }));

    expect(screen.getByText("开始探索")).toBeInTheDocument();
    expect(screen.getByText("常用命令")).toBeInTheDocument();
  });

  it("recalls a history command back into the editor", async () => {
    const user = userEvent.setup();

    useGraphWorkbenchStore.setState({
      editorValue: "",
      frames: [],
      selectedDrawer: null,
      isExecuting: false,
      favorites: [],
      showStarterCommands: true,
      history: [
        {
          command: "查人参的功效",
          source: "workbench",
          executedAt: "2026-03-23T10:00:00Z",
        },
      ],
    });

    renderWithProviders(<GraphWorkbenchPage />, "/graph/workbench");

    await user.click(screen.getByRole("button", { name: "打开历史抽屉" }));
    await user.click(screen.getByRole("button", { name: "回填命令 查人参的功效" }));

    expect(screen.getByPlaceholderText("输入 :help、Cypher，或自然语言查询")).toHaveValue(
      "查人参的功效",
    );
  });

  it("inserts a starter command into the editor when clicked", async () => {
    const user = userEvent.setup();

    renderWithProviders(<GraphWorkbenchPage />, "/graph/workbench");

    await user.click(screen.getByRole("button", { name: "插入起手命令 :help" }));

    expect(screen.getByPlaceholderText("输入 :help、Cypher，或自然语言查询")).toHaveValue(
      ":help",
    );
  });

  it("runs the current command with ctrl+enter", async () => {
    const user = userEvent.setup();

    vi.spyOn(workbenchApi, "execute").mockResolvedValue({
      command: ":help",
      frames: [
        {
          id: "frame-help",
          type: "text",
          title: "命令帮助",
          status: "ok",
          payload: { markdown: "支持 :help / :clear / Cypher / 自然语言查询" },
          command: ":help",
        },
      ],
      historyItem: {
        command: ":help",
        source: "workbench",
        executedAt: "2026-03-23T10:10:00Z",
      },
    });

    renderWithProviders(<GraphWorkbenchPage />, "/graph/workbench");

    const editor = screen.getByPlaceholderText("输入 :help、Cypher，或自然语言查询");
    await user.type(editor, ":help");
    await user.keyboard("{Control>}{Enter}{/Control}");

    expect(await screen.findByText("命令帮助")).toBeInTheDocument();
    expect(await screen.findByText("支持 :help / :clear / Cypher / 自然语言查询")).toBeInTheDocument();
  });

  it("shows a pending execution frame while a command is running", () => {
    useGraphWorkbenchStore.setState({
      editorValue: "查人参的功效",
      frames: [],
      history: [],
      favorites: [],
      showStarterCommands: true,
      selectedDrawer: null,
      isExecuting: true,
    });

    renderWithProviders(<GraphWorkbenchPage />, "/graph/workbench");

    expect(screen.getByText("正在执行命令...")).toBeInTheDocument();
    expect(screen.getByText("结果会以新的 frame 追加到 stream 顶部。")).toBeInTheDocument();
  });

  it("saves the current command to favorites and recalls it from the drawer", async () => {
    const user = userEvent.setup();

    renderWithProviders(<GraphWorkbenchPage />, "/graph/workbench");

    const editor = screen.getByPlaceholderText("输入 :help、Cypher，或自然语言查询");
    await user.type(editor, "查人参和功效关系");
    await user.click(screen.getByRole("button", { name: "收藏当前命令" }));
    await user.click(screen.getByRole("button", { name: "清空编辑器与结果" }));
    await user.click(screen.getByRole("button", { name: "打开收藏抽屉" }));
    await user.click(
      screen.getByRole("button", {
        name: "回填收藏命令 查人参和功效关系",
      }),
    );

    expect(screen.getByPlaceholderText("输入 :help、Cypher，或自然语言查询")).toHaveValue(
      "查人参和功效关系",
    );
  });

  it("toggles starter commands from settings drawer", async () => {
    const user = userEvent.setup();

    renderWithProviders(<GraphWorkbenchPage />, "/graph/workbench");

    expect(screen.getByRole("button", { name: "插入起手命令 :help" })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "打开设置抽屉" }));
    await user.click(screen.getByRole("switch", { name: "显示起手命令" }));

    expect(screen.queryByRole("button", { name: "插入起手命令 :help" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "打开设置抽屉" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });

  it("dismisses a single frame from the stream", async () => {
    const user = userEvent.setup();

    useGraphWorkbenchStore.setState({
      editorValue: "",
      history: [],
      favorites: [],
      showStarterCommands: true,
      selectedDrawer: null,
      isExecuting: false,
      frames: [
        {
          id: "frame-help",
          type: "text",
          title: "命令帮助",
          status: "ok",
          command: ":help",
          payload: {
            markdown: "支持 workbench 的基础命令。",
          },
        },
      ],
    });

    renderWithProviders(<GraphWorkbenchPage />, "/graph/workbench");

    await user.click(screen.getByRole("button", { name: "关闭结果 frame-help" }));

    expect(screen.queryByText("命令帮助")).not.toBeInTheDocument();
  });

  it("shows frame metadata in frame chrome", () => {
    useGraphWorkbenchStore.setState({
      editorValue: "",
      history: [],
      favorites: [],
      showStarterCommands: true,
      selectedDrawer: null,
      isExecuting: false,
      frames: [
        {
          id: "frame-help",
          type: "text",
          title: "命令帮助",
          status: "ok",
          command: ":help",
          payload: {
            markdown: "支持 workbench 的基础命令。",
          },
        },
      ],
    });

    renderWithProviders(<GraphWorkbenchPage />, "/graph/workbench");

    expect(screen.getByText("命令来源 workbench")).toBeInTheDocument();
    expect(screen.getByText("结果帧")).toBeInTheDocument();
  });

  it("reruns a frame command from frame chrome", async () => {
    const user = userEvent.setup();

    vi.spyOn(workbenchApi, "execute").mockResolvedValue({
      command: ":help",
      frames: [
        {
          id: "frame-help-rerun",
          type: "text",
          title: "命令帮助（重跑）",
          status: "ok",
          payload: { markdown: "这是重新执行后的结果。" },
          command: ":help",
        },
      ],
      historyItem: {
        command: ":help",
        source: "workbench",
        executedAt: "2026-03-23T11:40:00Z",
      },
    });

    useGraphWorkbenchStore.setState({
      editorValue: "",
      history: [],
      favorites: [],
      showStarterCommands: true,
      selectedDrawer: null,
      isExecuting: false,
      frames: [
        {
          id: "frame-help",
          type: "text",
          title: "命令帮助",
          status: "ok",
          command: ":help",
          payload: {
            markdown: "支持 workbench 的基础命令。",
          },
        },
      ],
    });

    renderWithProviders(<GraphWorkbenchPage />, "/graph/workbench");

    await user.click(screen.getByRole("button", { name: "重新执行命令 :help" }));

    expect(await screen.findByText("命令帮助（重跑）")).toBeInTheDocument();
    expect(await screen.findByText("这是重新执行后的结果。")).toBeInTheDocument();
  });

  it("renders graph and error frames inside the stream", async () => {
    useGraphWorkbenchStore.setState({
      editorValue: "",
      history: [],
      favorites: [],
      showStarterCommands: true,
      selectedDrawer: null,
      isExecuting: false,
      frames: [
        {
          id: "frame-graph",
          type: "graph",
          title: "人参图谱",
          status: "ok",
          command: "查人参图谱",
          payload: {
            graph: {
              center: {
                id: "herb-1",
                name: "人参",
                labels: ["Herb"],
                status: "verified",
              },
              nodes: [
                {
                  id: "herb-1",
                  name: "人参",
                  labels: ["Herb"],
                  status: "verified",
                },
              ],
              edges: [],
            },
            summary: "以人参为中心的图谱结果",
            mode: "exact",
          },
        },
        {
          id: "frame-error",
          type: "error",
          title: "Cypher 校验失败",
          status: "error",
          command: "MATCH (n) DELETE n",
          payload: {
            message: "Write operations are not allowed.",
          },
        },
      ],
    });

    renderWithProviders(<GraphWorkbenchPage />, "/graph/workbench");

    expect(await screen.findByText("人参图谱")).toBeInTheDocument();
    expect(await screen.findByText("图谱概览")).toBeInTheDocument();
    expect(await screen.findByText("Cypher 校验失败")).toBeInTheDocument();
    expect(await screen.findByText("Write operations are not allowed.")).toBeInTheDocument();
  });
});
