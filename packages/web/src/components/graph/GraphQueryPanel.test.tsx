import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import GraphQueryPanel from "./GraphQueryPanel";
import { renderWithProviders } from "../../test/render-with-providers";

describe("GraphQueryPanel", () => {
  it("submits a trimmed advanced query payload", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn().mockResolvedValue(undefined);

    renderWithProviders(<GraphQueryPanel depth={2} onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText("节点名称包含"), "  补气  ");
    await user.type(screen.getByRole("spinbutton", { name: "limit" }), "25");
    await user.click(screen.getByRole("button", { name: /执行图谱查询/ }));

    expect(onSubmit).toHaveBeenCalledWith({
      node: { name_contains: "补气" },
      depth: 2,
      limit: 25,
    });
  });

  it("blocks submitting an empty query", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn().mockResolvedValue(undefined);

    renderWithProviders(<GraphQueryPanel depth={1} onSubmit={onSubmit} />);

    await user.click(screen.getByRole("button", { name: /执行图谱查询/ }));

    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("resets all query fields and keeps the configured depth value", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn().mockResolvedValue(undefined);

    renderWithProviders(<GraphQueryPanel depth={2} onSubmit={onSubmit} />);

    await user.type(screen.getByLabelText("节点名称包含"), "人参");
    await user.type(screen.getByRole("spinbutton", { name: "limit" }), "25");
    await user.click(screen.getByRole("button", { name: "重置条件" }));

    expect(screen.getByLabelText("节点名称包含")).toHaveValue("");
    expect(screen.getByRole("spinbutton", { name: "查询深度" })).toHaveValue("2");
    expect(screen.getByRole("spinbutton", { name: "limit" })).toHaveValue("");
  });

  it("hides developer payload preview by default and expands it on demand", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn().mockResolvedValue(undefined);

    renderWithProviders(<GraphQueryPanel depth={1} onSubmit={onSubmit} />);

    expect(screen.queryByText("实时请求预览 (JSON payload)")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "开发者预览" }));

    expect(screen.getByText("实时请求预览 (JSON payload)")).toBeInTheDocument();
  });
});
