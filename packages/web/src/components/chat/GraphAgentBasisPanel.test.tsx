import { screen } from "@testing-library/react";
import { renderWithProviders } from "../../test/render-with-providers";
import GraphAgentBasisPanel from "./GraphAgentBasisPanel";

describe("GraphAgentBasisPanel evidence summary", () => {
  it("shows snippet and source name for a citation", () => {
    renderWithProviders(
      <GraphAgentBasisPanel
        evidence={[
          {
            entity_id: "herb-chenpi",
            evidence_id: "ev-1",
            snippet: "陈皮理气健脾。",
            source_id: "src-pharmacopoeia",
            source_name: "中国药典（2020年版）",
          },
        ]}
      />,
    );

    expect(screen.getByTestId("graph-agent-evidence-list")).toBeInTheDocument();
    expect(screen.getByText("陈皮理气健脾。")).toBeInTheDocument();
    expect(screen.getByTestId("chat-evidence-source")).toHaveTextContent("来源：中国药典（2020年版）");
  });

  it("does not render the evidence section when there is no citation", () => {
    renderWithProviders(
      <GraphAgentBasisPanel
        evidence={[]}
        providerReasoning={[{ text: "先查节点" }]}
      />,
    );

    expect(screen.queryByTestId("graph-agent-evidence-list")).not.toBeInTheDocument();
    expect(screen.queryByTestId("chat-evidence-source")).not.toBeInTheDocument();
  });

  it("keeps a stable source slot when source is missing", () => {
    renderWithProviders(
      <GraphAgentBasisPanel
        evidence={[
          {
            entity_id: "herb-chenpi",
            evidence_id: "ev-2",
            snippet: "陈皮味苦、辛。",
          },
        ]}
      />,
    );

    expect(screen.getByText("陈皮味苦、辛。")).toBeInTheDocument();
    expect(screen.getByTestId("chat-evidence-source")).toHaveTextContent("来源：来源未标注");
  });
});
