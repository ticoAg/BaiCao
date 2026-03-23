import { screen } from "@testing-library/react";
import Header from "./Header";
import { renderWithProviders } from "../test/render-with-providers";

describe("Header", () => {
  it("shows a navigation entry for the data pipeline workbench", () => {
    renderWithProviders(<Header />, "/data/pipeline");

    expect(screen.getByRole("link", { name: "数据处理" })).toBeInTheDocument();
  });
});
