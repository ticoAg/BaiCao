import { screen } from "@testing-library/react";
import HomePage from "./HomePage";
import { renderWithProviders } from "../test/render-with-providers";

describe("HomePage", () => {
  it("renders the homepage entry points and feature summary", () => {
    renderWithProviders(<HomePage />);

    expect(screen.getByText("欢迎使用白草药坛")).toBeInTheDocument();
    expect(screen.getByText("知识搜索")).toBeInTheDocument();
    expect(screen.getByText("图谱浏览")).toBeInTheDocument();
    expect(screen.getByText("验证管理")).toBeInTheDocument();
    expect(screen.getByText("智能问答")).toBeInTheDocument();
  });
});
