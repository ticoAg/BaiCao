import { screen } from "@testing-library/react";
import { renderWithProviders } from "../../test/render-with-providers";
import ReviewRequestModal from "./ReviewRequestModal";

describe("ReviewRequestModal", () => {
  it("prefills entity_id, source_id and evidence quote", () => {
    renderWithProviders(
      <ReviewRequestModal
        open
        onClose={() => undefined}
        prefill={{
          entityType: "herb",
          entityId: "herb-chenpi",
          sourceId: "src-pharmacopoeia",
          content: "陈皮理气健脾。",
        }}
      />,
    );

    expect(screen.getByLabelText("实体ID")).toHaveValue("herb-chenpi");
    expect(screen.getByLabelText("来源ID")).toHaveValue("src-pharmacopoeia");
    expect(screen.getByLabelText("审查内容")).toHaveValue("陈皮理气健脾。");
  });

  it("leaves source_id empty when the citation has no source", () => {
    renderWithProviders(
      <ReviewRequestModal
        open
        onClose={() => undefined}
        prefill={{
          entityType: "herb",
          entityId: "herb-chenpi",
          content: "陈皮味苦、辛。",
        }}
      />,
    );

    expect(screen.getByLabelText("实体ID")).toHaveValue("herb-chenpi");
    expect(screen.getByLabelText("来源ID")).toHaveValue("");
    expect(screen.getByLabelText("审查内容")).toHaveValue("陈皮味苦、辛。");
  });
});
