import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ChatPage from "./ChatPage";
import { renderWithProviders } from "../test/render-with-providers";
import { chatApi } from "../services/api";

describe("ChatPage", () => {
  it("submits a question and renders answer context", async () => {
    const user = userEvent.setup();
    vi.spyOn(chatApi, "ask").mockResolvedValue({
      answer: "关于「人参」的信息：\n- 分类：补气药\n- 主要功效：大补元气",
      reasoning_chain: [
        {
          step: 1,
          description: "识别问题类型：功效查询",
          entities: ["人参"],
          confidence: 0.95,
        },
      ],
      sources: [
        {
          id: "source-1",
          name: "中国药典（2020年版）",
          citation: "来源：中国药典（2020年版）",
        },
      ],
      graph_data: {
        center: {
          id: "herb-1",
          name: "人参",
          status: "verified",
          labels: ["Herb"],
        },
        nodes: [],
        edges: [],
      },
      workbench_frames: [
        {
          id: "frame-graph-1",
          type: "graph",
          title: "人参图谱",
          status: "ok",
          command: "查人参图谱",
          payload: {
            graph: {
              center: null,
              nodes: [],
              edges: [],
            },
            summary: "graph",
            mode: "exact",
          },
        },
      ],
      session_id: "session-1",
    });

    renderWithProviders(<ChatPage />);

    await user.type(
      screen.getByPlaceholderText("输入您的问题，例如：陈皮有什么功效？"),
      "人参有什么功效？",
    );
    await user.click(screen.getByRole("button", { name: /发送/ }));

    expect(await screen.findByText(/关于「人参」的信息/)).toBeInTheDocument();
    expect(screen.getByText("推理链")).toBeInTheDocument();
    expect(screen.getByText("中国药典（2020年版）")).toBeInTheDocument();
    expect(screen.getByText("Workbench 结果")).toBeInTheDocument();
    expect(screen.getByText("人参图谱")).toBeInTheDocument();
  });
});
