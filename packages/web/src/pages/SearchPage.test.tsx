import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import SearchPage from "./SearchPage";
import { renderWithProviders } from "../test/render-with-providers";
import { graphApi } from "../services/api";

describe("SearchPage", () => {
  it("searches herbs and renders result cards", async () => {
    const user = userEvent.setup();
    vi.spyOn(graphApi, "search").mockResolvedValue([
      {
        node: {
          id: "herb-1",
          name: "人参",
          source: "中国药典（2020年版）",
          status: "verified",
        },
        labels: ["Herb"],
      },
    ]);

    renderWithProviders(<SearchPage />);

    await user.type(screen.getByPlaceholderText("输入药材名称搜索..."), "人参");
    await user.click(screen.getByRole("button", { name: /搜\s*索/ }));

    expect(await screen.findByText("人参")).toBeInTheDocument();
    expect(screen.getByText("来源: 中国药典（2020年版）")).toBeInTheDocument();
    await waitFor(() => expect(graphApi.search).toHaveBeenCalledWith("人参"));
  });
});
