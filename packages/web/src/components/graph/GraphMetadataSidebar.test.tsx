import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import GraphMetadataSidebar from "./GraphMetadataSidebar";
import { renderWithProviders } from "../../test/render-with-providers";

describe("GraphMetadataSidebar", () => {
  it("renders summary and triggers label highlight actions", async () => {
    const user = userEvent.setup();
    const onHighlightLabel = vi.fn();

    renderWithProviders(
      <GraphMetadataSidebar
        summary={{
          nodeCount: 12,
          relationshipCount: 18,
          labelCount: 4,
          relationshipTypeCount: 6,
          propertyKeyCount: 11,
          indexCount: 2,
          constraintCount: 1,
          truncated: false,
          generatedAt: "2026-03-23T10:00:00Z",
        }}
        labels={[{ name: "Herb", count: 3, propertyKeys: ["name"] }]}
        relationshipTypes={[]}
        propertyKeys={[]}
        schema={{ indexes: [], constraints: [] }}
        onHighlightLabel={onHighlightLabel}
      />,
    );

    expect(screen.getByText("图数据库信息")).toBeInTheDocument();
    expect(screen.getByText("节点 · 12")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /药材/ })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /药材/ }));
    expect(onHighlightLabel).toHaveBeenCalledWith("Herb");
  });
});
