import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import GraphInspectorPanel from "./GraphInspectorPanel";
import { renderWithProviders } from "../../test/render-with-providers";

describe("GraphInspectorPanel", () => {
  it("renders overview and triggers reverse highlight actions", async () => {
    const user = userEvent.setup();
    const onHighlightRelationshipType = vi.fn();

    renderWithProviders(
      <GraphInspectorPanel
        selectedItem={null}
        nodeCount={2}
        relationshipCount={1}
        labelStats={[{ key: "Herb", count: 1 }]}
        relTypeStats={[{ key: "具有功效", count: 1, label: "具有功效" }]}
        onHighlightRelationshipType={onHighlightRelationshipType}
      />,
    );

    expect(screen.getByText("图谱概览")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /具有功效/ }));
    expect(onHighlightRelationshipType).toHaveBeenCalledWith("具有功效");
  });
});
