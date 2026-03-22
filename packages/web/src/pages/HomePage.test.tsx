import { screen } from "@testing-library/react";
import HomePage from "./HomePage";
import { renderWithProviders } from "../test/render-with-providers";

describe("HomePage", () => {
  it("renders the homepage entry points and feature summary", () => {
    renderWithProviders(<HomePage />);

    expect(screen.getByRole("heading", { name: "白草药坛" })).toBeInTheDocument();
    expect(screen.getByText("可溯源的中药材知识图谱智能问答系统")).toBeInTheDocument();
    expect(screen.getByText("知识搜索")).toBeInTheDocument();
    expect(screen.getByText("图谱浏览")).toBeInTheDocument();
    expect(screen.getByText("验证管理")).toBeInTheDocument();
    expect(screen.getAllByText("智能问答").length).toBeGreaterThan(0);
  });
});
