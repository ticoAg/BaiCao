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
});
