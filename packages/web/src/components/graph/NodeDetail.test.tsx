import { screen } from "@testing-library/react";
import NodeDetail from "./NodeDetail";
import { renderWithProviders } from "../../test/render-with-providers";

describe("NodeDetail", () => {
  it("renders long verification fields in truncated form with copy actions", () => {
    renderWithProviders(
      <NodeDetail
        node={{
          id: "herb-1",
          name: "人参",
          labels: ["Herb"],
          status: "verified",
          verification_id: "44444444-4444-4444-4444-444444444443",
          verified_by: "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        }}
      />,
    );

    expect(screen.getByText("药材")).toBeInTheDocument();
    expect(screen.getByText("444444...4443")).toBeInTheDocument();
    expect(screen.getByText("aaaaaa...eeee")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "复制验证ID" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "复制验证人" })).toBeInTheDocument();
  });
});
